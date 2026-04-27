from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import stat
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from forgebench.cli import main
from forgebench.github_pr import (
    GH_MISSING_MESSAGE,
    GitHubPRError,
    GitHubPRClient,
    GitHubPRMetadata,
    PreparedPRWorktree,
    PRCheckoutInfo,
    finalize_pr_worktree,
    parse_pr_url,
    prepare_pr_worktree,
    run_github_pr_review,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
PR_URL = "https://github.com/caissonhq/forgebench/pull/42"


class GitHubPRTests(unittest.TestCase):
    def test_pr_url_parsing_valid_https(self) -> None:
        reference = parse_pr_url(PR_URL)

        self.assertEqual(reference.owner, "caissonhq")
        self.assertEqual(reference.repo, "forgebench")
        self.assertEqual(reference.number, 42)
        self.assertEqual(reference.url, PR_URL)

    def test_pr_url_parsing_valid_no_scheme(self) -> None:
        reference = parse_pr_url("github.com/caissonhq/forgebench/pull/42")

        self.assertEqual(reference.url, PR_URL)

    def test_pr_url_parsing_invalid(self) -> None:
        with self.assertRaises(GitHubPRError):
            parse_pr_url("https://example.com/caissonhq/forgebench/pull/42")

    def test_pr_url_parsing_missing_pr_number(self) -> None:
        with self.assertRaisesRegex(GitHubPRError, "missing a PR number"):
            parse_pr_url("https://github.com/caissonhq/forgebench/pull")

    def test_pr_url_parsing_non_integer_pr_number(self) -> None:
        with self.assertRaisesRegex(GitHubPRError, "invalid PR number"):
            parse_pr_url("https://github.com/caissonhq/forgebench/pull/not-a-number")

    def test_metadata_fetch_parses_gh_json(self) -> None:
        completed = _completed(
            stdout=json.dumps(
                {
                    "title": "Add PR intake",
                    "body": "Fetch PR metadata.",
                    "number": 42,
                    "url": PR_URL,
                    "headRefName": "feature/pr-intake",
                    "baseRefName": "main",
                    "changedFiles": 3,
                    "additions": 40,
                    "deletions": 2,
                    "author": {"login": "octocat"},
                }
            )
        )
        with patch("forgebench.github_pr.subprocess.run", return_value=completed):
            metadata = GitHubPRClient().fetch_pr_metadata(parse_pr_url(PR_URL), cwd=ROOT)

        self.assertEqual(metadata.title, "Add PR intake")
        self.assertEqual(metadata.author, "octocat")
        self.assertEqual(metadata.changed_files, 3)

    def test_metadata_fetch_handles_gh_failure(self) -> None:
        completed = _completed(returncode=1, stderr="authentication required")
        with patch("forgebench.github_pr.subprocess.run", return_value=completed):
            with self.assertRaisesRegex(GitHubPRError, "authentication required"):
                GitHubPRClient().fetch_pr_metadata(parse_pr_url(PR_URL), cwd=ROOT)

    def test_missing_gh_gives_clear_error(self) -> None:
        with patch("forgebench.github_pr.subprocess.run", side_effect=FileNotFoundError("gh")):
            with self.assertRaisesRegex(GitHubPRError, "GitHub CLI"):
                GitHubPRClient().fetch_pr_metadata(parse_pr_url(PR_URL), cwd=ROOT)

    def test_patch_fetch_writes_patch_file(self) -> None:
        diff = (FIXTURES / "docs_only.patch").read_text(encoding="utf-8")
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "patch.diff"
            with patch("forgebench.github_pr.subprocess.run", return_value=_completed(stdout=diff)):
                written = GitHubPRClient().fetch_pr_patch(parse_pr_url(PR_URL), output, cwd=ROOT)

            self.assertEqual(written, output)
            self.assertEqual(output.read_text(encoding="utf-8"), diff)

    def test_patch_fetch_handles_empty_diff(self) -> None:
        with TemporaryDirectory() as tmp:
            with patch("forgebench.github_pr.subprocess.run", return_value=_completed(stdout="")):
                with self.assertRaisesRegex(GitHubPRError, "diff is empty"):
                    GitHubPRClient().fetch_pr_patch(parse_pr_url(PR_URL), Path(tmp) / "patch.diff", cwd=ROOT)

    def test_task_generation_includes_title_body_url(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_github_pr_review(repo_path=ROOT, pr_url=PR_URL, output_dir=Path(tmp) / "out", client=FakeGitHubPRClient())
            task = result.intake.task_path.read_text(encoding="utf-8")

        self.assertIn("GitHub PR Review", task)
        self.assertIn(PR_URL, task)
        self.assertIn("Add PR intake", task)
        self.assertIn("Fetch PR metadata and run ForgeBench.", task)

    def test_review_pr_uses_existing_run_review_path_and_generates_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            result = run_github_pr_review(repo_path=ROOT, pr_url=PR_URL, output_dir=out, client=FakeGitHubPRClient())

            self.assertTrue((out / "patch.diff").exists())
            self.assertTrue((out / "task.md").exists())
            self.assertTrue((out / "forgebench-report.md").exists())
            self.assertTrue((out / "forgebench-report.json").exists())
            self.assertTrue((out / "repair-prompt.md").exists())
            self.assertTrue((out / "pr-comment.md").exists())
            self.assertEqual(result.review_result.written_paths["markdown"], out / "forgebench-report.md")

    def test_default_review_pr_does_not_post_comment(self) -> None:
        client = FakeGitHubPRClient()
        with TemporaryDirectory() as tmp:
            run_github_pr_review(repo_path=ROOT, pr_url=PR_URL, output_dir=Path(tmp) / "out", client=client)

        self.assertEqual(client.comments, [])

    def test_post_comment_calls_posting_function(self) -> None:
        client = FakeGitHubPRClient()
        with TemporaryDirectory() as tmp:
            result = run_github_pr_review(
                repo_path=ROOT,
                pr_url=PR_URL,
                output_dir=Path(tmp) / "out",
                post_comment=True,
                client=client,
            )

        self.assertTrue(result.comment_posted)
        self.assertEqual(len(client.comments), 1)
        self.assertIn("## ForgeBench Merge Risk Report", client.comments[0])

    def test_posting_failure_is_reported_but_artifacts_remain(self) -> None:
        client = FakeGitHubPRClient(comment_error="permission denied")
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            result = run_github_pr_review(
                repo_path=ROOT,
                pr_url=PR_URL,
                output_dir=out,
                post_comment=True,
                client=client,
            )

            self.assertFalse(result.comment_posted)
            self.assertIn("permission denied", result.comment_error or "")
            self.assertTrue((out / "forgebench-report.md").exists())
            self.assertTrue((out / "pr-comment.md").exists())

    def test_pr_comment_stays_concise(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_github_pr_review(repo_path=ROOT, pr_url=PR_URL, output_dir=Path(tmp) / "out", client=FakeGitHubPRClient())
            comment = result.comment_path.read_text(encoding="utf-8")

        self.assertIn("## ForgeBench Merge Risk Report", comment)
        self.assertIn("Generic mode: no forgebench.yml found", comment)
        self.assertIn("ForgeBench does not prove code is safe", comment)
        self.assertNotIn("diff --git", comment)
        self.assertNotIn("You are repairing an AI-generated code change", comment)
        self.assertLess(len(comment), 4000)

    def test_review_pr_with_run_checks_includes_checkout_caveat(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_github_pr_review(
                repo_path=ROOT,
                pr_url=PR_URL,
                guardrails_path=FIXTURES / "checks_all_pass.yml",
                output_dir=Path(tmp) / "out",
                run_checks=True,
                client=FakeGitHubPRClient(),
            )
            markdown = result.review_result.written_paths["markdown"].read_text(encoding="utf-8")
            comment = result.comment_path.read_text(encoding="utf-8")

        caveat = "Deterministic checks were run against the current local checkout, not the PR checkout."
        self.assertIn(caveat, markdown)
        self.assertIn(caveat, comment)
        self.assertEqual(result.pr_checkout.checks_target, "current_checkout")

    def test_checkout_pr_creates_checkout_metadata(self) -> None:
        with TemporaryDirectory() as tmp:
            temp = Path(tmp)
            worktree = temp / "worktree"
            worktree.mkdir()
            prepared = _prepared_worktree(worktree)
            cleaned = PRCheckoutInfo(
                requested=True,
                status="cleaned_up",
                worktree_path=str(worktree),
                checks_target="not_run",
            )
            with patch("forgebench.github_pr.prepare_pr_worktree", return_value=prepared), patch(
                "forgebench.github_pr.finalize_pr_worktree", return_value=cleaned
            ):
                result = run_github_pr_review(
                    repo_path=ROOT,
                    pr_url=PR_URL,
                    output_dir=temp / "out",
                    checkout_pr=True,
                    client=FakeGitHubPRClient(),
                )

            self.assertEqual(result.pr_checkout.status, "cleaned_up")
            self.assertEqual(result.pr_checkout.worktree_path, str(worktree))
            self.assertEqual(result.review_result.report.pr_checkout.status, "cleaned_up")

    def test_run_checks_with_checkout_pr_uses_worktree_path(self) -> None:
        with TemporaryDirectory() as tmp:
            temp = Path(tmp)
            worktree = temp / "worktree"
            worktree.mkdir()
            prepared = _prepared_worktree(worktree)
            cleaned = PRCheckoutInfo(
                requested=True,
                status="cleaned_up",
                worktree_path=str(worktree),
                checks_target="pr_worktree",
            )
            with patch("forgebench.github_pr.prepare_pr_worktree", return_value=prepared), patch(
                "forgebench.github_pr.finalize_pr_worktree", return_value=cleaned
            ):
                result = run_github_pr_review(
                    repo_path=ROOT,
                    pr_url=PR_URL,
                    guardrails_path=FIXTURES / "checks_all_pass.yml",
                    output_dir=temp / "out",
                    run_checks=True,
                    checkout_pr=True,
                    client=FakeGitHubPRClient(),
                )

            markdown = result.review_result.written_paths["markdown"].read_text(encoding="utf-8")
            comment = result.comment_path.read_text(encoding="utf-8")

        self.assertEqual(result.pr_checkout.checks_target, "pr_worktree")
        self.assertIn(f"- Repo: {worktree}", markdown)
        self.assertIn("Deterministic checks were run against the checked-out PR worktree.", markdown)
        self.assertIn("Ran against PR worktree.", comment)

    def test_failed_checkout_still_produces_static_review_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            with patch("forgebench.github_pr.prepare_pr_worktree", side_effect=GitHubPRError("fetch failed")):
                result = run_github_pr_review(
                    repo_path=ROOT,
                    pr_url=PR_URL,
                    guardrails_path=FIXTURES / "checks_all_pass.yml",
                    output_dir=out,
                    run_checks=True,
                    checkout_pr=True,
                    client=FakeGitHubPRClient(),
                )

            self.assertEqual(result.pr_checkout.status, "failed")
            self.assertFalse(result.review_result.report.deterministic_checks.run_requested)
            self.assertTrue((out / "forgebench-report.md").exists())
            self.assertTrue((out / "forgebench-report.json").exists())
            self.assertTrue((out / "pr-comment.md").exists())

    def test_worktree_cleanup_happens_by_default(self) -> None:
        commands: list[list[str]] = []

        def fake_run(command, **kwargs):
            commands.append(list(command))
            return _completed(stdout="")

        prepared = _prepared_worktree(Path("/tmp/forgebench-pr-smoke"))
        with patch("forgebench.github_pr.subprocess.run", side_effect=fake_run):
            checkout = finalize_pr_worktree(prepared, ROOT, checks_target="pr_worktree")

        self.assertEqual(checkout.status, "cleaned_up")
        self.assertTrue(any(command[3:5] == ["worktree", "remove"] for command in commands))
        self.assertTrue(any(command[3:5] == ["update-ref", "-d"] for command in commands))

    def test_keep_worktree_preserves_worktree_path(self) -> None:
        commands: list[list[str]] = []

        def fake_run(command, **kwargs):
            commands.append(list(command))
            return _completed(stdout="")

        prepared = _prepared_worktree(Path("/tmp/forgebench-pr-smoke"))
        with patch("forgebench.github_pr.subprocess.run", side_effect=fake_run):
            checkout = finalize_pr_worktree(prepared, ROOT, checks_target="pr_worktree", keep_worktree=True)

        self.assertEqual(checkout.status, "kept")
        self.assertEqual(checkout.worktree_path, "/tmp/forgebench-pr-smoke")
        self.assertFalse(any(command[3:5] == ["worktree", "remove"] for command in commands))

    def test_cleanup_failure_is_reported(self) -> None:
        def fake_run(command, **kwargs):
            if command[3:5] == ["worktree", "remove"]:
                return _completed(returncode=1, stderr="dirty worktree")
            return _completed(stdout="")

        prepared = _prepared_worktree(Path("/tmp/forgebench-pr-smoke"))
        with patch("forgebench.github_pr.subprocess.run", side_effect=fake_run):
            checkout = finalize_pr_worktree(prepared, ROOT, checks_target="pr_worktree")

        self.assertEqual(checkout.status, "cleanup_failed")
        self.assertTrue(checkout.kept)
        self.assertIn("dirty worktree", checkout.cleanup_error or "")

    def test_report_includes_pr_checkout_section_and_json_object(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            result = run_github_pr_review(repo_path=ROOT, pr_url=PR_URL, output_dir=out, client=FakeGitHubPRClient())
            markdown = result.review_result.written_paths["markdown"].read_text(encoding="utf-8")
            payload = json.loads(result.review_result.written_paths["json"].read_text(encoding="utf-8"))

        self.assertIn("## PR Checkout", markdown)
        self.assertIn("pr_checkout", payload)
        self.assertEqual(payload["pr_checkout"]["status"], "not_requested")

    def test_pr_comment_includes_checks_target(self) -> None:
        with TemporaryDirectory() as tmp:
            temp = Path(tmp)
            worktree = temp / "worktree"
            worktree.mkdir()
            prepared = _prepared_worktree(worktree)
            cleaned = PRCheckoutInfo(
                requested=True,
                status="cleaned_up",
                worktree_path=str(worktree),
                checks_target="pr_worktree",
            )
            with patch("forgebench.github_pr.prepare_pr_worktree", return_value=prepared), patch(
                "forgebench.github_pr.finalize_pr_worktree", return_value=cleaned
            ):
                result = run_github_pr_review(
                    repo_path=ROOT,
                    pr_url=PR_URL,
                    guardrails_path=FIXTURES / "checks_all_pass.yml",
                    output_dir=temp / "out",
                    run_checks=True,
                    checkout_pr=True,
                    client=FakeGitHubPRClient(),
                )
                comment = result.comment_path.read_text(encoding="utf-8")

        self.assertIn("Ran against PR worktree.", comment)

    def test_prepare_pr_worktree_uses_no_destructive_git_commands(self) -> None:
        commands: list[list[str]] = []

        def fake_run(command, **kwargs):
            commands.append(list(command))
            return _completed(stdout="")

        with TemporaryDirectory() as tmp, patch("forgebench.github_pr.subprocess.run", side_effect=fake_run):
            prepare_pr_worktree(parse_pr_url(PR_URL), ROOT, worktree_dir=tmp)

        forbidden = {"checkout", "reset", "clean", "rebase", "merge"}
        used = {part for command in commands for part in command}
        self.assertTrue(forbidden.isdisjoint(used))
        self.assertTrue(any("pull/42/head:" in part for command in commands for part in command))
        self.assertTrue(any(command[3:6] == ["worktree", "add", "--detach"] for command in commands))

    def test_worktree_paths_are_unique_and_safe(self) -> None:
        def fake_run(command, **kwargs):
            return _completed(stdout="")

        with TemporaryDirectory() as tmp, patch("forgebench.github_pr.subprocess.run", side_effect=fake_run):
            first = prepare_pr_worktree(parse_pr_url(PR_URL), ROOT, worktree_dir=tmp)
            second = prepare_pr_worktree(parse_pr_url(PR_URL), ROOT, worktree_dir=tmp)

        self.assertNotEqual(first.info.worktree_path, second.info.worktree_path)
        self.assertIn("forgebench-pr-caissonhq-forgebench-42-", first.info.worktree_path or "")

    def test_review_pr_works_with_llm_review_command_provider(self) -> None:
        with TemporaryDirectory() as tmp:
            script = Path(tmp) / "reviewer.py"
            script.write_text(
                "import json\n"
                "print(json.dumps({'reviewer_name': 'Mock', 'summary': 'No additional findings.', 'findings': []}))\n",
                encoding="utf-8",
            )
            result = run_github_pr_review(
                repo_path=ROOT,
                pr_url=PR_URL,
                output_dir=Path(tmp) / "out",
                llm_review=True,
                llm_provider="command",
                llm_command=f"python3 {script}",
                client=FakeGitHubPRClient(),
            )

        self.assertTrue(result.review_result.report.llm_review.enabled)
        self.assertEqual(result.review_result.report.llm_review.status.value, "completed")

    def test_cli_review_pr_positional_url_works_with_fake_gh(self) -> None:
        with TemporaryDirectory() as tmp:
            temp = Path(tmp)
            bin_dir = temp / "bin"
            bin_dir.mkdir()
            _write_fake_gh(bin_dir / "gh")
            out_dir = temp / "out"
            original_path = os.environ.get("PATH", "")
            os.environ["PATH"] = str(bin_dir) + os.pathsep + original_path
            try:
                stdout = StringIO()
                with redirect_stdout(stdout):
                    result = main(["review-pr", PR_URL, "--repo", str(ROOT), "--out", str(out_dir)])
            finally:
                os.environ["PATH"] = original_path

            self.assertEqual(result, 0)
            self.assertIn("ForgeBench GitHub PR review complete.", stdout.getvalue())
            self.assertIn("GitHub comment:\n- not requested", stdout.getvalue())
            self.assertTrue((out_dir / "patch.diff").exists())
            self.assertTrue((out_dir / "task.md").exists())
            self.assertTrue((out_dir / "pr-comment.md").exists())

    def test_cli_review_pr_accepts_checkout_flags(self) -> None:
        with TemporaryDirectory() as tmp:
            temp = Path(tmp)
            bin_dir = temp / "bin"
            bin_dir.mkdir()
            _write_fake_gh(bin_dir / "gh")
            out_dir = temp / "out"
            worktree = temp / "worktree"
            worktree.mkdir()
            prepared = _prepared_worktree(worktree)
            cleaned = PRCheckoutInfo(
                requested=True,
                status="cleaned_up",
                worktree_path=str(worktree),
                checks_target="not_run",
            )
            original_path = os.environ.get("PATH", "")
            os.environ["PATH"] = str(bin_dir) + os.pathsep + original_path
            try:
                stdout = StringIO()
                with patch("forgebench.github_pr.prepare_pr_worktree", return_value=prepared), patch(
                    "forgebench.github_pr.finalize_pr_worktree", return_value=cleaned
                ), redirect_stdout(stdout):
                    result = main(
                        [
                            "review-pr",
                            PR_URL,
                            "--repo",
                            str(ROOT),
                            "--out",
                            str(out_dir),
                            "--checkout-pr",
                            "--keep-worktree",
                            "--worktree-dir",
                            str(temp / "worktrees"),
                        ]
                    )
            finally:
                os.environ["PATH"] = original_path

            self.assertEqual(result, 0)
            self.assertIn("PR checkout:", stdout.getvalue())
            self.assertIn("status: cleaned_up", stdout.getvalue())


class FakeGitHubPRClient(GitHubPRClient):
    def __init__(self, comment_error: str | None = None) -> None:
        self.comments: list[str] = []
        self.comment_error = comment_error

    def fetch_pr_metadata(self, ref, cwd: str | Path | None = None) -> GitHubPRMetadata:
        return GitHubPRMetadata(
            owner=ref.owner,
            repo=ref.repo,
            number=ref.number,
            title="Add PR intake",
            body="Fetch PR metadata and run ForgeBench.",
            author="octocat",
            base_ref="main",
            head_ref="feature/pr-intake",
            changed_files=1,
            additions=1,
            deletions=0,
            url=ref.url,
        )

    def fetch_pr_patch(self, ref, output_path: str | Path, cwd: str | Path | None = None) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text((FIXTURES / "docs_only.patch").read_text(encoding="utf-8"), encoding="utf-8")
        return path

    def post_pr_comment(self, ref, comment_path: str | Path, cwd: str | Path | None = None) -> None:
        if self.comment_error:
            raise GitHubPRError(self.comment_error)
        self.comments.append(Path(comment_path).read_text(encoding="utf-8"))


def _prepared_worktree(path: Path) -> PreparedPRWorktree:
    return PreparedPRWorktree(
        info=PRCheckoutInfo(
            requested=True,
            status="prepared",
            worktree_path=str(path),
            checks_target="not_run",
        ),
        temp_ref="refs/forgebench/pr-42-test",
    )


def _write_fake_gh(path: Path) -> None:
    diff = json.dumps((FIXTURES / "docs_only.patch").read_text(encoding="utf-8"))
    script = f"""#!/usr/bin/env python3
import json
import sys

args = sys.argv[1:]
if args[:2] == ["pr", "view"]:
    print(json.dumps({{
        "title": "Add PR intake",
        "body": "Fetch PR metadata and run ForgeBench.",
        "number": 42,
        "url": "{PR_URL}",
        "headRefName": "feature/pr-intake",
        "baseRefName": "main",
        "changedFiles": 1,
        "additions": 1,
        "deletions": 0,
        "author": {{"login": "octocat"}}
    }}))
elif args[:2] == ["pr", "diff"]:
    print({diff})
elif args[:2] == ["pr", "comment"]:
    print("commented")
else:
    print("unexpected gh args: " + " ".join(args), file=sys.stderr)
    sys.exit(2)
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    completed = Mock()
    completed.stdout = stdout
    completed.stderr = stderr
    completed.returncode = returncode
    return completed


if __name__ == "__main__":
    unittest.main()
