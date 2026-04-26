from __future__ import annotations

import json
import re
import subprocess
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from forgebench.models import CheckStatus, Confidence, ForgeBenchReport, PRCheckoutInfo
from forgebench.report_writer import write_reports
from forgebench.review import ReviewInputError, ReviewResult, run_review


GH_MISSING_MESSAGE = "GitHub PR intake requires GitHub CLI. Install gh and run gh auth login, then retry."


class GitHubPRError(ValueError):
    pass


@dataclass(frozen=True)
class GitHubPRRef:
    owner: str
    repo: str
    number: int
    url: str


@dataclass(frozen=True)
class GitHubPRMetadata:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str | None
    base_ref: str | None
    head_ref: str | None
    changed_files: int | None
    additions: int | None
    deletions: int | None
    url: str

    def to_dict(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "repo": self.repo,
            "number": self.number,
            "title": self.title,
            "body": self.body,
            "author": self.author,
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "changed_files": self.changed_files,
            "additions": self.additions,
            "deletions": self.deletions,
            "url": self.url,
        }


@dataclass(frozen=True)
class GitHubPRIntakeResult:
    ref: GitHubPRRef
    metadata: GitHubPRMetadata
    patch_path: Path
    task_path: Path
    source: str = "gh"


@dataclass(frozen=True)
class GitHubPRReviewResult:
    review_result: ReviewResult
    intake: GitHubPRIntakeResult
    comment_path: Path
    pr_checkout: PRCheckoutInfo = field(default_factory=PRCheckoutInfo)
    comment_posted: bool = False
    comment_error: str | None = None
    comment_requested: bool = False
    dry_run: bool = True


@dataclass(frozen=True)
class PreparedPRWorktree:
    info: PRCheckoutInfo
    temp_ref: str | None = None


# Backward-compatible names from the first local prototype.
GitHubPRReference = GitHubPRRef
GitHubPRData = GitHubPRMetadata


class GitHubPRClient:
    def fetch_pr_metadata(self, ref: GitHubPRRef, cwd: str | Path | None = None) -> GitHubPRMetadata:
        payload = self._run_json(
            [
                "gh",
                "pr",
                "view",
                str(ref.number),
                "-R",
                f"{ref.owner}/{ref.repo}",
                "--json",
                "title,body,author,baseRefName,headRefName,changedFiles,additions,deletions,url,number",
            ],
            cwd=cwd,
        )
        author = payload.get("author")
        author_login = author.get("login") if isinstance(author, dict) else None
        return GitHubPRMetadata(
            owner=ref.owner,
            repo=ref.repo,
            number=_int_or_default(payload.get("number"), ref.number),
            title=str(payload.get("title") or ""),
            body=str(payload.get("body") or ""),
            author=str(author_login) if author_login else None,
            base_ref=_optional_string(payload.get("baseRefName")),
            head_ref=_optional_string(payload.get("headRefName")),
            changed_files=_optional_int(payload.get("changedFiles")),
            additions=_optional_int(payload.get("additions")),
            deletions=_optional_int(payload.get("deletions")),
            url=str(payload.get("url") or ref.url),
        )

    def fetch_pr_patch(self, ref: GitHubPRRef, output_path: str | Path, cwd: str | Path | None = None) -> Path:
        output = self._run_text(
            [
                "gh",
                "pr",
                "diff",
                str(ref.number),
                "-R",
                f"{ref.owner}/{ref.repo}",
                "--patch",
                "--color",
                "never",
            ],
            cwd=cwd,
        )
        if not output.strip():
            raise GitHubPRError(f"GitHub PR diff is empty: {ref.url}")
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
        return path

    def post_pr_comment(self, ref: GitHubPRRef, comment_path: str | Path, cwd: str | Path | None = None) -> None:
        command = ["gh", "pr", "comment", str(ref.number), "-R", f"{ref.owner}/{ref.repo}", "--body-file", str(comment_path)]
        try:
            completed = subprocess.run(
                command,
                cwd=Path(cwd) if cwd else None,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise GitHubPRError(GH_MISSING_MESSAGE) from exc
        except OSError as exc:
            raise GitHubPRError(f"failed to run gh: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
            raise GitHubPRError(f"failed to post PR comment: {detail}")

    # Backward-compatible prototype methods.
    def fetch_pr(self, pr_url: str, cwd: str | Path | None = None):  # pragma: no cover - compatibility shim
        ref = parse_pr_url(pr_url)
        metadata = self.fetch_pr_metadata(ref, cwd=cwd)
        raise GitHubPRError("fetch_pr is deprecated; use fetch_pr_metadata and fetch_pr_patch")

    def post_comment(self, pr_url: str, body: str, cwd: str | Path | None = None) -> None:  # pragma: no cover
        ref = parse_pr_url(pr_url)
        temp_path = Path(cwd or ".") / "forgebench-pr-comment.tmp.md"
        temp_path.write_text(body, encoding="utf-8")
        try:
            self.post_pr_comment(ref, temp_path, cwd=cwd)
        finally:
            try:
                temp_path.unlink()
            except OSError:
                pass

    def _run_text(self, command: list[str], cwd: str | Path | None = None) -> str:
        try:
            completed = subprocess.run(
                command,
                cwd=Path(cwd) if cwd else None,
                text=True,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise GitHubPRError(GH_MISSING_MESSAGE) from exc
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


def parse_pr_url(url: str) -> GitHubPRRef:
    candidate = url.strip()
    if not candidate:
        raise GitHubPRError("GitHub PR URL is required.")
    if "://" not in candidate:
        candidate = "https://" + candidate
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
        raise GitHubPRError(f"not a GitHub PR URL: {url}")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 3 or parts[2] != "pull":
        raise GitHubPRError(f"not a GitHub PR URL: {url}")
    if len(parts) < 4:
        raise GitHubPRError(f"GitHub PR URL is missing a PR number: {url}")
    try:
        number = int(parts[3])
    except ValueError as exc:
        raise GitHubPRError(f"GitHub PR URL has an invalid PR number: {url}") from exc
    return GitHubPRRef(owner=parts[0], repo=parts[1], number=number, url=_canonical_pr_url(parts[0], parts[1], number))


def parse_github_pr_url(pr_url: str) -> GitHubPRRef:
    return parse_pr_url(pr_url)


def fetch_pr_metadata(ref: GitHubPRRef, client: GitHubPRClient | None = None, cwd: str | Path | None = None) -> GitHubPRMetadata:
    return (client or GitHubPRClient()).fetch_pr_metadata(ref, cwd=cwd)


def fetch_pr_patch(ref: GitHubPRRef, output_path: str | Path, client: GitHubPRClient | None = None, cwd: str | Path | None = None) -> Path:
    return (client or GitHubPRClient()).fetch_pr_patch(ref, output_path, cwd=cwd)


def create_task_from_pr(metadata: GitHubPRMetadata, output_path: str | Path) -> Path:
    body = metadata.body.strip() or "No PR body provided."
    task = (
        "GitHub PR Review\n\n"
        "PR:\n"
        f"{metadata.url}\n\n"
        "Title:\n"
        f"{metadata.title.strip() or '(No PR title provided.)'}\n\n"
        "Body:\n"
        f"{body}\n\n"
        "Author:\n"
        f"{metadata.author or 'unknown'}\n\n"
        "Base:\n"
        f"{metadata.base_ref or 'unknown'}\n\n"
        "Head:\n"
        f"{metadata.head_ref or 'unknown'}\n\n"
        "Changed files:\n"
        f"{_display_count(metadata.changed_files)}\n\n"
        "Additions:\n"
        f"{_display_count(metadata.additions)}\n\n"
        "Deletions:\n"
        f"{_display_count(metadata.deletions)}\n\n"
        "This task context was generated from GitHub PR metadata.\n"
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(task, encoding="utf-8")
    return path


def generate_pr_comment(
    report: ForgeBenchReport,
    metadata: GitHubPRMetadata,
    checks_run_against_local_checkout: bool = False,
) -> str:
    high_confidence = [finding for finding in report.findings if finding.confidence == Confidence.HIGH]
    lines = [
        "## ForgeBench Merge Risk Report",
        "",
        f"Posture: {report.posture.value}",
        "",
        "Summary:",
        report.summary,
        "",
        "High-confidence issues:",
    ]
    if high_confidence:
        for finding in high_confidence[:8]:
            lines.append(f"- {finding.title} — {finding.severity.value}/{finding.confidence.value}")
        if len(high_confidence) > 8:
            lines.append(f"- ...and {len(high_confidence) - 8} more high-confidence issue(s).")
    else:
        lines.append("- None.")

    lines.extend(["", "Deterministic checks:"])
    checkout = report.pr_checkout
    if checks_run_against_local_checkout and checkout.checks_target == "not_run":
        checkout = PRCheckoutInfo(requested=False, status="not_requested", checks_target="current_checkout")
    lines.extend(_deterministic_comment_lines(report, checkout))
    lines.extend(["", "Guardrails:"])
    lines.extend(_guardrail_comment_lines(report))
    lines.extend(["", "Specialized reviewers:"])
    lines.extend(_specialized_reviewer_comment_lines(report))
    lines.extend(["", "LLM review:"])
    lines.append(f"- {_llm_comment_summary(report)}")
    lines.extend(["", "Suggested next action:", _suggested_next_action(report)])
    lines.extend(
        [
            "",
            "Artifacts:",
            "- Full report generated locally",
            "- Repair prompt generated locally",
            "",
            "ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.",
        ]
    )
    return "\n".join(lines) + "\n"


def post_pr_comment(ref: GitHubPRRef, comment_body: str, client: GitHubPRClient | None = None, cwd: str | Path | None = None) -> None:
    temp_path = Path(cwd or ".") / "forgebench-pr-comment.tmp.md"
    temp_path.write_text(comment_body, encoding="utf-8")
    try:
        (client or GitHubPRClient()).post_pr_comment(ref, temp_path, cwd=cwd)
    finally:
        try:
            temp_path.unlink()
        except OSError:
            pass


def prepare_pr_worktree(
    ref: GitHubPRRef,
    repo_path: str | Path,
    worktree_dir: str | Path | None = None,
) -> PreparedPRWorktree:
    repo = Path(repo_path)
    _validate_git_repo_for_worktree(repo)

    parent = Path(worktree_dir) if worktree_dir else Path(tempfile.gettempdir()) / "forgebench-worktrees"
    parent.mkdir(parents=True, exist_ok=True)

    unique = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    temp_ref = f"refs/forgebench/pr-{ref.number}-{unique}"
    worktree_name = f"forgebench-pr-{_safe_path_part(ref.owner)}-{_safe_path_part(ref.repo)}-{ref.number}-{unique}"
    worktree_path = parent / worktree_name

    try:
        _run_git(repo, ["fetch", "origin", f"pull/{ref.number}/head:{temp_ref}"])
        _run_git(repo, ["worktree", "add", "--detach", str(worktree_path), temp_ref])
    except GitHubPRError:
        _delete_temp_ref(repo, temp_ref)
        raise

    return PreparedPRWorktree(
        info=PRCheckoutInfo(
            requested=True,
            status="prepared",
            worktree_path=str(worktree_path),
            checks_target="not_run",
            kept=False,
        ),
        temp_ref=temp_ref,
    )


def finalize_pr_worktree(
    prepared: PreparedPRWorktree | None,
    repo_path: str | Path,
    checks_target: str,
    keep_worktree: bool = False,
) -> PRCheckoutInfo:
    if prepared is None:
        return PRCheckoutInfo()

    repo = Path(repo_path)
    worktree_path = prepared.info.worktree_path
    cleanup_error: str | None = None
    status = "kept" if keep_worktree else "cleaned_up"
    kept = keep_worktree

    if keep_worktree:
        ref_error = _delete_temp_ref(repo, prepared.temp_ref)
        cleanup_error = ref_error
    else:
        if worktree_path:
            try:
                _run_git(repo, ["worktree", "remove", "--force", worktree_path])
            except GitHubPRError as exc:
                cleanup_error = str(exc)
                status = "cleanup_failed"
                kept = True
        ref_error = _delete_temp_ref(repo, prepared.temp_ref)
        if ref_error:
            cleanup_error = _join_errors(cleanup_error, ref_error)
            if status == "cleaned_up":
                status = "cleanup_failed"

    return PRCheckoutInfo(
        requested=True,
        status=status,
        worktree_path=worktree_path,
        checks_target=checks_target,
        error_message=prepared.info.error_message,
        kept=kept,
        cleanup_error=cleanup_error,
    )


def run_github_pr_review(
    repo_path: str | Path,
    pr_url: str,
    guardrails_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    run_checks: bool = False,
    post_comment: bool = False,
    comment_file: str | Path | None = None,
    dry_run: bool = False,
    llm_review: bool = False,
    llm_provider: str | None = None,
    llm_command: str | None = None,
    llm_timeout: int = 60,
    llm_max_diff_chars: int = 20000,
    checkout_pr: bool = False,
    keep_worktree: bool = False,
    worktree_dir: str | Path | None = None,
    reviewers_enabled: bool = True,
    client: GitHubPRClient | None = None,
) -> GitHubPRReviewResult:
    repo = Path(repo_path)
    if not repo.exists() or not repo.is_dir():
        raise ReviewInputError(f"repo path does not exist or is not a directory: {repo}")

    ref = parse_pr_url(pr_url)
    out_dir = Path(output_dir) if output_dir else Path("forgebench-output") / f"pr-{ref.owner}-{ref.repo}-{ref.number}"
    out_dir.mkdir(parents=True, exist_ok=True)

    pr_client = client or GitHubPRClient()
    metadata = pr_client.fetch_pr_metadata(ref, cwd=repo)
    patch_path = pr_client.fetch_pr_patch(ref, out_dir / "patch.diff", cwd=repo)
    task_path = create_task_from_pr(metadata, out_dir / "task.md")
    metadata_path = out_dir / "github-pr-metadata.json"
    metadata_path.write_text(json.dumps(metadata.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    prepared_worktree: PreparedPRWorktree | None = None
    checkout_info = _initial_checkout_info(checkout_pr, run_checks)
    review_repo = repo
    run_checks_for_review = run_checks
    input_notes = _input_notes_for_checkout(checkout_info, run_checks)

    if checkout_pr:
        try:
            prepared_worktree = prepare_pr_worktree(ref, repo, worktree_dir=worktree_dir)
            review_repo = Path(prepared_worktree.info.worktree_path or repo)
            checks_target = "pr_worktree" if run_checks else "not_run"
            checkout_info = PRCheckoutInfo(
                requested=True,
                status="prepared",
                worktree_path=prepared_worktree.info.worktree_path,
                checks_target=checks_target,
                kept=False,
            )
            input_notes = _input_notes_for_checkout(checkout_info, run_checks)
        except GitHubPRError as exc:
            checkout_info = PRCheckoutInfo(
                requested=True,
                status="failed",
                worktree_path=None,
                checks_target="not_run",
                error_message=str(exc),
                kept=False,
            )
            run_checks_for_review = False
            input_notes = _input_notes_for_checkout(checkout_info, run_checks)

    resolved_guardrails = _resolve_guardrails(review_repo, guardrails_path)

    review_result = run_review(
        repo_path=review_repo,
        diff_path=patch_path.resolve(),
        task_path=task_path.resolve(),
        guardrails_path=resolved_guardrails,
        output_dir=out_dir,
        run_checks=run_checks_for_review,
        llm_review=llm_review,
        llm_provider=llm_provider,
        llm_command=llm_command,
        llm_timeout=llm_timeout,
        llm_max_diff_chars=llm_max_diff_chars,
        input_notes=input_notes,
        pr_checkout=checkout_info,
        reviewers_enabled=reviewers_enabled,
    )

    if prepared_worktree is not None:
        checkout_info = finalize_pr_worktree(
            prepared_worktree,
            repo,
            checks_target="pr_worktree" if run_checks else "not_run",
            keep_worktree=keep_worktree,
        )
        review_result.report.pr_checkout = checkout_info
        review_result.written_paths.update(
            write_reports(
                out_dir,
                review_result.report,
                review_result.guardrails,
                review_result.task_text,
                inputs={
                    "repo": str(review_repo),
                    "diff": str(patch_path.resolve()),
                    "task": str(task_path.resolve()),
                    "guardrails": str(resolved_guardrails) if resolved_guardrails else "none",
                    "notes": input_notes,
                },
            )
        )

    pr_comment_path = Path(comment_file) if comment_file else out_dir / "pr-comment.md"
    pr_comment_path.parent.mkdir(parents=True, exist_ok=True)
    pr_comment_path.write_text(generate_pr_comment(review_result.report, metadata), encoding="utf-8")

    comment_posted = False
    comment_error: str | None = None
    should_post = post_comment and not dry_run
    if should_post:
        try:
            pr_client.post_pr_comment(ref, pr_comment_path, cwd=repo)
            comment_posted = True
        except GitHubPRError as exc:
            comment_error = str(exc)

    return GitHubPRReviewResult(
        review_result=review_result,
        intake=GitHubPRIntakeResult(ref=ref, metadata=metadata, patch_path=patch_path, task_path=task_path),
        comment_path=pr_comment_path,
        pr_checkout=checkout_info,
        comment_posted=comment_posted,
        comment_error=comment_error,
        comment_requested=post_comment,
        dry_run=not should_post,
    )


def _resolve_guardrails(repo: Path, guardrails_path: str | Path | None) -> Path | None:
    if guardrails_path:
        return Path(guardrails_path)
    candidate = repo / "forgebench.yml"
    return candidate if candidate.exists() else None


def _validate_git_repo_for_worktree(repo: Path) -> None:
    _run_git(repo, ["rev-parse", "--git-dir"])
    _run_git(repo, ["worktree", "list", "--porcelain"])
    _run_git(repo, ["remote", "get-url", "origin"])


def _run_git(repo: Path, args: list[str]) -> str:
    command = ["git", "-C", str(repo), *args]
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
    except FileNotFoundError as exc:
        raise GitHubPRError("PR checkout requires git to be installed and available on PATH.") from exc
    except OSError as exc:
        raise GitHubPRError(f"failed to run git: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise GitHubPRError(f"git command failed: {detail}")
    return completed.stdout


def _delete_temp_ref(repo: Path, temp_ref: str | None) -> str | None:
    if not temp_ref:
        return None
    try:
        _run_git(repo, ["update-ref", "-d", temp_ref])
    except GitHubPRError as exc:
        return str(exc)
    return None


def _initial_checkout_info(checkout_pr: bool, run_checks: bool) -> PRCheckoutInfo:
    if checkout_pr:
        return PRCheckoutInfo(requested=True, status="requested", checks_target="not_run")
    if run_checks:
        return PRCheckoutInfo(requested=False, status="not_requested", checks_target="current_checkout")
    return PRCheckoutInfo()


def _input_notes_for_checkout(checkout_info: PRCheckoutInfo, run_checks_requested: bool) -> list[str]:
    if checkout_info.status == "failed":
        notes = ["PR checkout failed; ForgeBench ran static review from the fetched patch."]
        if run_checks_requested:
            notes.append("Deterministic checks were skipped because the PR checkout could not be prepared.")
        return notes
    if checkout_info.checks_target == "pr_worktree":
        return ["Deterministic checks were run against the checked-out PR worktree."]
    if checkout_info.checks_target == "current_checkout":
        return ["Deterministic checks were run against the current local checkout, not the PR checkout."]
    if checkout_info.requested and checkout_info.status == "prepared":
        return ["PR checkout was prepared, but deterministic checks were not run because --run-checks was not passed."]
    return []


def _join_errors(first: str | None, second: str | None) -> str | None:
    if first and second:
        return f"{first}; {second}"
    return first or second


def _safe_path_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "repo"


def _canonical_pr_url(owner: str, repo: str, number: int) -> str:
    return f"https://github.com/{owner}/{repo}/pull/{number}"


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _int_or_default(value: object, default: int) -> int:
    parsed = _optional_int(value)
    return parsed if parsed is not None else default


def _display_count(value: int | None) -> str:
    return str(value) if value is not None else "unknown"


def _deterministic_comment_lines(report: ForgeBenchReport, checkout: PRCheckoutInfo) -> list[str]:
    checks = report.deterministic_checks
    if not checks.run_requested:
        lines = ["- Not run."]
        if checkout.status == "failed":
            lines.append(f"- PR checkout failed: {checkout.error_message or 'unknown error'}")
        elif checkout.requested and checkout.worktree_path:
            lines.append("- PR checkout was prepared, but checks were not run.")
        return lines
    summary = checks.summary
    lines = [
        (
            f"- passed={summary['passed']}, failed={summary['failed']}, timed_out={summary['timed_out']}, "
            f"not_configured={summary['not_configured']}, errors={summary['errors']}"
        )
    ]
    if checkout.checks_target == "pr_worktree":
        lines.append("- Ran against PR worktree.")
    elif checkout.checks_target == "current_checkout":
        lines.append("- Deterministic checks were run against the current local checkout, not the PR checkout.")
    failed = [result for result in checks.results if result.status in {CheckStatus.FAILED, CheckStatus.ERROR, CheckStatus.TIMED_OUT}]
    for result in failed[:4]:
        lines.append(f"- {result.name}: {result.status.value}")
    if len(failed) > 4:
        lines.append(f"- ...and {len(failed) - 4} more failing/timed-out check(s).")
    return lines


def _guardrail_comment_lines(report: ForgeBenchReport) -> list[str]:
    lines: list[str] = []
    if report.guardrail_hits:
        lines.append(f"- {len(report.guardrail_hits)} guardrail hit(s).")
    else:
        lines.append("- No guardrail hits.")
    if report.policy.suppressed_findings:
        lines.append(f"- {len(report.policy.suppressed_findings)} finding(s) suppressed by policy.")
    if report.policy.posture_ceiling:
        lines.append(f"- Posture ceiling applied: {report.policy.posture_ceiling.value}.")
    return lines


def _specialized_reviewer_comment_lines(report: ForgeBenchReport) -> list[str]:
    reviewers = report.specialized_reviewers
    if not reviewers.enabled:
        return ["- Not run."]
    if not reviewers.results:
        return ["- No reviewer results."]
    lines: list[str] = []
    for result in reviewers.results:
        if result.findings:
            titles = ", ".join(finding.title for finding in result.findings[:2])
            if len(result.findings) > 2:
                titles += f", and {len(result.findings) - 2} more"
            lines.append(f"- {result.reviewer_name}: {titles}")
        else:
            lines.append(f"- {result.reviewer_name}: no additional concern")
    return lines


def _llm_comment_summary(report: ForgeBenchReport) -> str:
    review = report.llm_review
    if not review.enabled:
        return "Not run."
    if review.status.value == "completed":
        return f"Completed with {len(review.findings)} advisory finding(s)."
    if review.status.value == "failed":
        return f"Failed: {review.error_message or 'unknown error'}"
    return review.status.value


def _suggested_next_action(report: ForgeBenchReport) -> str:
    if report.posture.value == "BLOCK":
        return "Do not merge yet. Address the blocking findings, regenerate the diff if needed, and rerun ForgeBench."
    if report.posture.value == "REVIEW":
        return "Review the listed risks before merge. If the patch was agent-generated, use the repair prompt locally."
    return "Proceed with normal human review. No required repair was identified."
