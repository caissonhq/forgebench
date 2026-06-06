from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from forgebench.cli import main
from forgebench.demo import format_demo_result, resolve_demo_case_dir, run_demo


class DemoTests(unittest.TestCase):
    def test_resolve_demo_case_dir(self) -> None:
        case_dir = resolve_demo_case_dir()
        self.assertTrue((case_dir / "patch.diff").exists())
        self.assertTrue((case_dir / "task.md").exists())

    def test_run_demo_writes_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_demo(repo_path=tmp, output_dir=Path(tmp) / "demo-out")
            self.assertEqual(result.case_name, "generic_dependency_without_tests_review")
            self.assertTrue(result.report_markdown.exists())
            self.assertTrue(result.report_json.exists())
            self.assertTrue(result.repair_prompt.exists())
            self.assertIn(result.posture, {"BLOCK", "REVIEW", "LOW_CONCERN"})

    def test_format_demo_result(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_demo(repo_path=tmp)
            text = format_demo_result(result)
            self.assertIn("ForgeBench demo complete", text)
            self.assertIn(result.posture, text)

    def test_cli_demo_json(self) -> None:
        with TemporaryDirectory() as tmp:
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(["demo", "--repo", tmp, "--json"])
            self.assertEqual(result, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["case"], "generic_dependency_without_tests_review")
            self.assertIn("posture", payload)


if __name__ == "__main__":
    unittest.main()