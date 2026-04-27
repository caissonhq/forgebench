from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
import unittest

from forgebench.cli import main


FIXTURES = Path(__file__).parent / "fixtures"


class CliTests(unittest.TestCase):
    def test_cli_creates_output_directory_and_writes_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "review",
                        "--repo",
                        str(Path.cwd()),
                        "--diff",
                        str(FIXTURES / "simple.patch"),
                        "--task",
                        str(FIXTURES / "task.md"),
                        "--out",
                        str(out_dir),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertIn("ForgeBench review complete.", stdout.getvalue())
            self.assertTrue((out_dir / "forgebench-report.md").exists())
            self.assertTrue((out_dir / "forgebench-report.json").exists())
            self.assertTrue((out_dir / "repair-prompt.md").exists())

    def test_cli_handles_missing_diff_path_cleanly(self) -> None:
        stderr = StringIO()

        with self.assertRaises(SystemExit) as raised:
            with redirect_stderr(stderr):
                main(
                    [
                        "review",
                        "--repo",
                        str(Path.cwd()),
                        "--diff",
                        str(FIXTURES / "missing.patch"),
                        "--task",
                        str(FIXTURES / "task.md"),
                    ]
                )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("diff file does not exist", stderr.getvalue())

    def test_cli_handles_missing_task_path_cleanly(self) -> None:
        stderr = StringIO()

        with self.assertRaises(SystemExit) as raised:
            with redirect_stderr(stderr):
                main(
                    [
                        "review",
                        "--repo",
                        str(Path.cwd()),
                        "--diff",
                        str(FIXTURES / "simple.patch"),
                        "--task",
                        str(FIXTURES / "missing.md"),
                    ]
                )

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("task file does not exist", stderr.getvalue())

    def test_cli_works_when_guardrails_are_omitted(self) -> None:
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "review",
                        "--repo",
                        str(Path.cwd()),
                        "--diff",
                        str(FIXTURES / "docs_only.patch"),
                        "--task",
                        str(FIXTURES / "task.md"),
                        "--out",
                        str(out_dir),
                    ]
                )

            self.assertEqual(result, 0)
            self.assertIn("Posture: LOW_CONCERN", stdout.getvalue())
            self.assertTrue((out_dir / "forgebench-report.json").exists())
            payload = json.loads((out_dir / "forgebench-report.json").read_text(encoding="utf-8"))
            markdown = (out_dir / "forgebench-report.md").read_text(encoding="utf-8")
            repair = (out_dir / "repair-prompt.md").read_text(encoding="utf-8")

        self.assertEqual(payload["config_mode"], "generic")
        self.assertTrue(payload["first_run_guidance"])
        self.assertIsNone(payload["guardrails_source"])
        self.assertIn("Generic review mode.", markdown)
        self.assertIn("This review ran with generic heuristics", repair)

    def test_cli_auto_discovers_repo_guardrails_as_configured(self) -> None:
        with TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            guardrails_path = repo / "forgebench.yml"
            guardrails_path.write_text("project: Configured Repo\n", encoding="utf-8")
            out_dir = Path(tmp) / "out"
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "review",
                        "--repo",
                        str(repo),
                        "--diff",
                        str(FIXTURES / "docs_only.patch"),
                        "--task",
                        str(FIXTURES / "task.md"),
                        "--out",
                        str(out_dir),
                    ]
                )
            payload = json.loads((out_dir / "forgebench-report.json").read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(payload["config_mode"], "configured")
        self.assertFalse(payload["first_run_guidance"])
        self.assertEqual(payload["guardrails_source"], str(guardrails_path))

    def test_run_checks_omitted_does_not_execute_commands(self) -> None:
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "review",
                        "--repo",
                        str(Path.cwd()),
                        "--diff",
                        str(FIXTURES / "docs_only.patch"),
                        "--task",
                        str(FIXTURES / "task.md"),
                        "--guardrails",
                        str(FIXTURES / "checks_test_fail.yml"),
                        "--out",
                        str(out_dir),
                    ]
                )

            payload = json.loads((out_dir / "forgebench-report.json").read_text(encoding="utf-8"))

            self.assertEqual(result, 0)
            self.assertIn("Posture: LOW_CONCERN", stdout.getvalue())
            self.assertFalse(payload["deterministic_checks"]["run_requested"])
            self.assertEqual(payload["deterministic_checks"]["results"], [])

    def test_run_checks_executes_configured_commands(self) -> None:
        with TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "out"
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "review",
                        "--repo",
                        str(Path.cwd()),
                        "--diff",
                        str(FIXTURES / "docs_only.patch"),
                        "--task",
                        str(FIXTURES / "task.md"),
                        "--guardrails",
                        str(FIXTURES / "checks_test_fail.yml"),
                        "--run-checks",
                        "--out",
                        str(out_dir),
                    ]
                )

            payload = json.loads((out_dir / "forgebench-report.json").read_text(encoding="utf-8"))

            self.assertEqual(result, 0)
            self.assertIn("Posture: BLOCK", stdout.getvalue())
            self.assertTrue(payload["deterministic_checks"]["run_requested"])
            self.assertEqual(payload["deterministic_checks"]["summary"]["failed"], 1)
            self.assertIn("tests_failed", {finding["id"] for finding in payload["findings"]})


if __name__ == "__main__":
    unittest.main()
