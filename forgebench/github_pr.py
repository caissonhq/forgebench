from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from forgebench.review import ReviewInputError, ReviewResult, run_review


class GitHubPRError(ValueError):
    pass


@dataclass(frozen=True)
class GitHubPRReference:
    owner: str
    repo: str
    number: int
    url: str


@dataclass(frozen=True)
class GitHubPRData:
    reference: GitHubPRReference
    title: str
    body: str
    diff_text: str
    author: str | None = None
    head_ref: str | None = None
    base_ref: str | None = None

    def task_text(self) -> str:
        body = self.body.strip() or "(No PR body provided.)"
        return (
            "Task context:\n"
            "This task was derived from GitHub PR metadata.\n\n"
            f"PR: {self.reference.url}\n"
            f"Title: {self.title.strip() or '(No PR title provided.)'}\n\n"
            "Body:\n"
            f"{body}\n"
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "url": self.reference.url,
            "owner": self.reference.owner,
            "repo": self.reference.repo,
            "number": self.reference.number,
            "title": self.title,
            "body": self.body,
            "author": self.author,
            "head_ref": self.head_ref,
            "base_ref": self.base_ref,
        }


@dataclass(frozen=True)
class GitHubPRReviewResult:
    review_result: ReviewResult
    pr: GitHubPRData
    comment_posted: bool = False
    comment_error: str | None = None


class GitHubPRClient:
    def fetch_pr(self, pr_url: str, cwd: str | Path | None = None) -> GitHubPRData:
        reference = parse_github_pr_url(pr_url)
        metadata = self._run_json(
            [
                "gh",
                "pr",
                "view",
                pr_url,
                "--json",
                "title,body,number,url,headRefName,baseRefName,author",
            ],
            cwd=cwd,
        )
        diff_text = self._run_text(["gh", "pr", "diff", pr_url], cwd=cwd)
        title = str(metadata.get("title") or "")
        body = str(metadata.get("body") or "")
        author = metadata.get("author")
        author_login = author.get("login") if isinstance(author, dict) else None
        return GitHubPRData(
            reference=reference,
            title=title,
            body=body,
            diff_text=diff_text,
            author=str(author_login) if author_login else None,
            head_ref=_optional_string(metadata.get("headRefName")),
            base_ref=_optional_string(metadata.get("baseRefName")),
        )

    def post_comment(self, pr_url: str, body: str, cwd: str | Path | None = None) -> None:
        command = ["gh", "pr", "comment", pr_url, "--body-file", "-"]
        try:
            completed = subprocess.run(
                command,
                cwd=Path(cwd) if cwd else None,
                input=body,
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            raise GitHubPRError(f"failed to run gh: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
            raise GitHubPRError(f"failed to post PR comment: {detail}")

    def _run_text(self, command: list[str], cwd: str | Path | None = None) -> str:
        try:
            completed = subprocess.run(
                command,
                cwd=Path(cwd) if cwd else None,
                text=True,
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            raise GitHubPRError(f"failed to run gh: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
            raise GitHubPRError(f"gh command failed: {detail}")
        return completed.stdout

    def _run_json(self, command: list[str], cwd: str | Path | None = None) -> dict[str, object]:
        output = self._run_text(command, cwd=cwd)
        try:
            payload = json.loads(output)
        except json.JSONDecodeError as exc:
            raise GitHubPRError(f"gh returned invalid JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise GitHubPRError("gh returned JSON that was not an object")
        return payload


def parse_github_pr_url(pr_url: str) -> GitHubPRReference:
    parsed = urlparse(pr_url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
        raise GitHubPRError(f"not a GitHub PR URL: {pr_url}")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 4 or parts[2] != "pull":
        raise GitHubPRError(f"not a GitHub PR URL: {pr_url}")
    try:
        number = int(parts[3])
    except ValueError as exc:
        raise GitHubPRError(f"GitHub PR URL has an invalid PR number: {pr_url}") from exc
    return GitHubPRReference(owner=parts[0], repo=parts[1], number=number, url=_canonical_pr_url(parts[0], parts[1], number))


def run_github_pr_review(
    repo_path: str | Path,
    pr_url: str,
    guardrails_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    run_checks: bool = False,
    post_comment: bool = False,
    llm_review: bool = False,
    llm_provider: str | None = None,
    llm_command: str | None = None,
    llm_timeout: int = 60,
    llm_max_diff_chars: int = 20000,
    client: GitHubPRClient | None = None,
) -> GitHubPRReviewResult:
    repo = Path(repo_path)
    if not repo.exists() or not repo.is_dir():
        raise ReviewInputError(f"repo path does not exist or is not a directory: {repo}")
    out_dir = Path(output_dir) if output_dir else Path("forgebench-output")
    out_dir.mkdir(parents=True, exist_ok=True)

    pr_client = client or GitHubPRClient()
    pr = pr_client.fetch_pr(pr_url, cwd=repo)
    if not pr.diff_text.strip():
        raise GitHubPRError(f"GitHub PR diff is empty: {pr.reference.url}")

    diff_path = out_dir / "github-pr.diff"
    task_path = out_dir / "github-pr-task.md"
    metadata_path = out_dir / "github-pr-metadata.json"
    diff_path.write_text(pr.diff_text, encoding="utf-8")
    task_path.write_text(pr.task_text(), encoding="utf-8")
    metadata_path.write_text(json.dumps(pr.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    review_result = run_review(
        repo_path=repo,
        diff_path=diff_path,
        task_path=task_path,
        guardrails_path=guardrails_path,
        output_dir=out_dir,
        run_checks=run_checks,
        llm_review=llm_review,
        llm_provider=llm_provider,
        llm_command=llm_command,
        llm_timeout=llm_timeout,
        llm_max_diff_chars=llm_max_diff_chars,
    )

    comment_posted = False
    comment_error: str | None = None
    if post_comment:
        try:
            pr_client.post_comment(pr.reference.url, _build_comment_body(review_result), cwd=repo)
            comment_posted = True
        except GitHubPRError as exc:
            comment_error = str(exc)

    return GitHubPRReviewResult(
        review_result=review_result,
        pr=pr,
        comment_posted=comment_posted,
        comment_error=comment_error,
    )


def _build_comment_body(review_result: ReviewResult) -> str:
    report = review_result.written_paths["markdown"].read_text(encoding="utf-8", errors="replace")
    prefix = "<!-- forgebench-review -->\n"
    max_chars = 60000
    body = prefix + report
    if len(body) <= max_chars:
        return body
    return body[: max_chars - 80].rstrip() + "\n\n[ForgeBench report truncated for GitHub comment length.]\n"


def _canonical_pr_url(owner: str, repo: str, number: int) -> str:
    return f"https://github.com/{owner}/{repo}/pull/{number}"


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
