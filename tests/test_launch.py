from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.adoption_dashboard import export_adoption_dashboard
from forgebench.cli import main
from forgebench.feedback_share import format_success_story_share
from scripts.generate_release_notes import extract_version_notes


ROOT = Path(__file__).resolve().parents[1]


class LaunchTests(unittest.TestCase):
    def test_success_story_share_template(self) -> None:
        text = format_success_story_share(posture="REVIEW", finding_count=2, note="Caught missing tests")
        self.assertIn("success story", text.lower())
        self.assertIn("REVIEW", text)
        self.assertIn("Caught missing tests", text)
        self.assertIn("discussions", text)

    def test_cli_feedback_share(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["feedback", "--share", "--posture", "LOW_CONCERN", "--finding-count", "0", "--note", "Clean pass"])
        self.assertEqual(code, 0)
        self.assertIn("success story", stdout.getvalue().lower())

    def test_adoption_dashboard_export(self) -> None:
        with TemporaryDirectory() as tmp:
            result = export_adoption_dashboard(output_dir=tmp)
            self.assertTrue(result.index_path.exists())
            html = result.index_path.read_text(encoding="utf-8")
            self.assertIn("Adoption funnel", html)

    def test_cli_analytics_adoption_dashboard(self) -> None:
        with TemporaryDirectory() as tmp:
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["analytics", "adoption-dashboard", "--out", tmp])
            self.assertEqual(code, 0)
            self.assertTrue((Path(tmp) / "index.html").exists())

    def test_launch_docs_exist(self) -> None:
        self.assertTrue((ROOT / "docs" / "launch" / "RELEASE_v1.0.0.md").exists())
        self.assertTrue((ROOT / "docs" / "launch" / "announcements.md").exists())
        self.assertTrue((ROOT / "docs" / "launch" / "LAUNCH_EXECUTION_CHECKLIST.md").exists())

    def test_public_stats_manifest(self) -> None:
        stats = ROOT / "examples" / "launch" / "public-stats.json"
        self.assertTrue(stats.exists())
        self.assertIn("github_stars", stats.read_text(encoding="utf-8"))

    def test_release_notes_extracts_version_section(self) -> None:
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        notes = extract_version_notes(changelog, "1.0.0")
        self.assertIn("Public launch", notes)
        self.assertIn("forgebench quickstart", notes)
        self.assertNotIn("EO-010 (IDE)", notes)