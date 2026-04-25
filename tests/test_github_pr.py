from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
import os
from pathlib import Path
import stat
import unittest
from tempfile import TemporaryDirectory

from forgebench.cli import main
from forgebench.github_pr import GitHubPRError, GitHubPRClient, GitHubPRData, parse_github_pr_url, run_github_pr_review


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
PR_URL = "https://github.com/caissonhq/forgebench/pull/42"


class GitHubPRTests(unittest.TestCase):
    def test_parse_github_pr_url(self) -> None:
        reference = parse_github_pr_url(PR_URL)

        self.assertEqual(reference.owner, "caissonhq")
        self.assertEqual(reference.repo, "forgebench")
        self.assertEqual(reference.number, 42)
        self.assertEqual(reference.url, PR_URL)

    def test_parse_github_pr_url_rejects_non_pr_url(self) -> None:
        with self.assertRaises(GitHubPRError):
            parse_github_pr_url("https://github.com/caissonhq/forgebench/issues/42")

    def test_run_github_pr_review_writes_fetched_inputs_and_reports(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            result = run_github_pr_review(
                repo_path=ROOT,
                pr_url=PR_URL,
                output_dir=out,
                client=FakeGitHubPRClient(),
            )

            self.assertEqual(result.pr.title, "Add PR intake")
            self.assertTrue((out / "github-pr.diff").exists())
            self.assertTrue((out / "github-pr-task.md").exists())
            self.assertTrue((out / "github-pr-metadata.json").exists())
            self.assertTrue((out / "forgebench-report.md").exists())
            self.assertFalse(result.comment_posted)

    def test_post_comment_is_not_called_unless_requested(self) -> None:
        client = FakeGitHubPRClient()
        with TemporaryDirectory() as tmp:
            run_github_pr_review(repo_path=ROOT, pr_url=PR_URL, output_dir=Path(tmp) / "out", client=client)

        self.assertEqual(client.comments, [])

    def test_post_comment_posts_markdown_report_when_requested(self) -> None:
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
        self.assertIn("# ForgeBench Merge Risk Report", client.comments[0])

    def test_cli_review_pr_works_with_fake_gh(self) -> None:
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
                    result = main(
                        [
                            "review-pr",
                            "--repo",
                            str(ROOT),
                            "--pr-url",
                            PR_URL,
                            "--out",
                            str(out_dir),
                        ]
                    )
            finally:
                os.environ["PATH"] = original_path

            self.assertEqual(result, 0)
            self.assertIn("ForgeBench GitHub PR review complete.", stdout.getvalue())
            self.assertTrue((out_dir / "forgebench-report.json").exists())
            metadata = json.loads((out_dir / "github-pr-metadata.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["title"], "Add PR intake")


class FakeGitHubPRClient(GitHubPRClient):
    def __init__(self) -> None:
        self.comments: list[str] = []

    def fetch_pr(self, pr_url: str, cwd: str | Path | None = None) -> GitHubPRData:
        return GitHubPRData(
            reference=parse_github_pr_url(pr_url),
            title="Add PR intake",
            body="Fetch PR metadata and run ForgeBench.",
            diff_text=(FIXTURES / "docs_only.patch").read_text(encoding="utf-8"),
            author="octocat",
            head_ref="feature/pr-intake",
            base_ref="main",
        )

    def post_comment(self, pr_url: str, body: str, cwd: str | Path | None = None) -> None:
        self.comments.append(body)


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
        "author": {{"login": "octocat"}}
    }}))
elif args[:2] == ["pr", "diff"]:
    print({diff})
elif args[:2] == ["pr", "comment"]:
    sys.stdin.read()
    print("commented")
else:
    print("unexpected gh args: " + " ".join(args), file=sys.stderr)
    sys.exit(2)
"""
    path.write_text(script, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


if __name__ == "__main__":
    unittest.main()
