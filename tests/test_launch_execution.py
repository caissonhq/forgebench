from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.cli import main
from forgebench.launch.announcements import format_show_hn_post, format_x_launch_thread
from forgebench.launch.discussions_seed import format_discussions_seed_pack, seed_discussion_posts
from forgebench.launch.stats import update_public_stats
from forgebench.launch.verify import launch_ready, verify_launch_readiness


ROOT = Path(__file__).resolve().parents[1]


class LaunchExecutionTests(unittest.TestCase):
    def test_verify_launch_readiness_core_pass(self) -> None:
        checks = verify_launch_readiness(repo_root=ROOT)
        names = {c.name for c in checks}
        self.assertIn("version", names)
        self.assertIn("release_pipeline", names)
        self.assertIn("launch_docs", names)
        version = next(c for c in checks if c.name == "version")
        self.assertEqual(version.status, "pass")

    def test_x_thread_contains_cta(self) -> None:
        text = format_x_launch_thread()
        self.assertIn("quickstart", text)
        self.assertIn("forgebench.dev", text)
        self.assertIn("Design Partner", text)

    def test_show_hn_has_title_and_body(self) -> None:
        text = format_show_hn_post()
        self.assertIn("Show HN", text)
        self.assertIn("pipx install forgebench", text)
        self.assertIn("does not prove code is safe", text)

    def test_discussions_seed_has_three_posts(self) -> None:
        posts = seed_discussion_posts()
        self.assertEqual(len(posts), 3)
        text = format_discussions_seed_pack()
        self.assertIn("FAQ", text)
        self.assertIn("Design Partner", text)

    def test_update_public_stats(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "stats.json"
            update_public_stats(path=path, github_stars=10, hn_points=42)
            payload = path.read_text(encoding="utf-8")
            self.assertIn("launch_date", payload)
            self.assertIn('"github_stars": 10', payload)

    def test_cli_launch_verify(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["launch", "verify"])
        self.assertIn(code, (0, 1))
        self.assertIn("launch readiness", stdout.getvalue())

    def test_cli_launch_announce(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["launch", "announce"])
        self.assertEqual(code, 0)
        self.assertIn("Show HN", stdout.getvalue())
        self.assertIn("Tweet 1/6", stdout.getvalue())

    def test_cli_launch_seed_discussions(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "seed.txt"
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["launch", "seed-discussions", "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue(out.exists())

    def test_cli_launch_stats(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "stats.json"
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["launch", "stats", "--stars", "5", "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertIn("github_stars", out.read_text(encoding="utf-8"))

    def test_cli_launch_checklist(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["launch", "checklist"])
        self.assertIn(code, (0, 1))
        self.assertIn("LAUNCH_DAY_CHECKLIST", stdout.getvalue())

    def test_launch_day_docs_exist(self) -> None:
        self.assertTrue((ROOT / "docs" / "launch" / "LAUNCH_DAY_CHECKLIST.md").exists())
        self.assertTrue((ROOT / "docs" / "launch" / "announcements-final.md").exists())
        self.assertTrue((ROOT / "docs" / "launch" / "BLOG_ANNOUNCEMENT.md").exists())
        self.assertTrue((ROOT / "docs" / "launch" / "launch-retrospective.md").exists())
        self.assertTrue((ROOT / "docs" / "launch" / "MARKETPLACE_STATUS.md").exists())

    def test_launch_ready_no_hard_failures_on_docs(self) -> None:
        checks = verify_launch_readiness(repo_root=ROOT)
        failed = [c.name for c in checks if c.status == "fail"]
        self.assertNotIn("version", failed)
        self.assertNotIn("changelog", failed)
        self.assertNotIn("release_pipeline", failed)


if __name__ == "__main__":
    unittest.main()