from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import types
import unittest
from unittest import mock

from forgebench.cli import main
from forgebench.doctor import DoctorStatus, format_doctor_report, run_doctor


class DoctorTests(unittest.TestCase):
    def test_run_doctor_reports_core_checks(self) -> None:
        report = run_doctor(repo_path=Path.cwd())

        names = {check.name for check in report.checks}
        self.assertTrue({"python", "forgebench", "pyyaml", "git", "output_dir", "repo"} <= names)
        self.assertEqual(report.checks[0].status, DoctorStatus.OK)

    def test_format_doctor_report_includes_version_and_next_steps(self) -> None:
        report = run_doctor(repo_path=Path.cwd())
        text = format_doctor_report(report)

        self.assertIn("ForgeBench doctor", text)
        self.assertIn("0.9.0", text)
        self.assertIn("forgebench review-pr PR_URL", text)

    def test_cli_doctor_exits_zero_when_core_checks_pass(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = main(["doctor", "--repo", str(Path.cwd())])

        self.assertEqual(result, 0)
        self.assertIn("ForgeBench doctor", stdout.getvalue())

    def test_cli_doctor_fails_when_python_version_too_old(self) -> None:
        stdout = StringIO()
        with mock.patch("forgebench.doctor.sys.version_info", types.SimpleNamespace(major=3, minor=9, micro=0)), redirect_stdout(stdout):
            result = main(["doctor"])

        self.assertEqual(result, 2)
        self.assertIn("requires >= 3.10", stdout.getvalue())

    def test_doctor_warns_when_repo_is_not_git(self) -> None:
        with TemporaryDirectory() as tmp:
            report = run_doctor(repo_path=tmp)

        repo_check = next(check for check in report.checks if check.name == "repo")
        self.assertEqual(repo_check.status, DoctorStatus.WARN)
        self.assertIn("not a git repo", repo_check.message)


if __name__ == "__main__":
    unittest.main()