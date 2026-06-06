from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from forgebench.cli import main
from forgebench.status import build_status_report, format_status_report


class StatusTests(unittest.TestCase):
    def test_build_status_report_includes_recommendations(self) -> None:
        report = build_status_report(repo_path=Path.cwd())
        self.assertTrue(report.version)
        self.assertTrue(report.recommendations)
        self.assertIn("forgebench demo", report.recommendations[0].lower() + report.recommendations[-1].lower())

    def test_format_status_report_plain_text(self) -> None:
        report = build_status_report(repo_path=Path.cwd())
        text = format_status_report(report)
        self.assertIn("ForgeBench status", text)
        self.assertIn("Health", text)
        self.assertIn("Configuration", text)

    def test_cli_status_json(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = main(["status", "--json", "--repo", str(Path.cwd())])
        payload = json.loads(stdout.getvalue())
        self.assertIn("version", payload)
        self.assertIn("checks", payload)
        self.assertIn(result, {0, 2})

    def test_cli_status_plain(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = main(["status", "--plain", "--repo", str(Path.cwd())])
        self.assertIn("ForgeBench status", stdout.getvalue())
        self.assertIn(result, {0, 2})

    def test_status_detects_enterprise_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "forgebench.yml").write_text("project: test\n", encoding="utf-8")
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / ".github" / "workflows" / "forgebench.yml").write_text("name: FB\n", encoding="utf-8")
            (root / ".github" / "forgebench.yml").write_text("project: ci\n", encoding="utf-8")
            report = build_status_report(repo_path=root)
            self.assertIsNotNone(report.guardrails_path)
            self.assertIsNotNone(report.ci_guardrails_path)


if __name__ == "__main__":
    unittest.main()