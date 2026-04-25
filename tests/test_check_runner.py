from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

from forgebench.check_runner import findings_from_check_results, run_check_command, run_configured_checks
from forgebench.guardrails import load_guardrails
from forgebench.models import CheckCommand, CheckStatus, Confidence, Severity


FIXTURES = Path(__file__).parent / "fixtures"


class CheckRunnerTests(unittest.TestCase):
    def test_passing_check_returns_passed(self) -> None:
        result = run_check_command(
            CheckCommand("test", f"{sys.executable} -c \"print('ok')\"", 5),
            Path.cwd(),
        )

        self.assertEqual(result.status, CheckStatus.PASSED)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("ok", result.stdout_excerpt)

    def test_failing_check_returns_failed(self) -> None:
        result = run_check_command(
            CheckCommand("test", f"{sys.executable} -c \"import sys; print('bad'); sys.exit(1)\"", 5),
            Path.cwd(),
        )

        self.assertEqual(result.status, CheckStatus.FAILED)
        self.assertEqual(result.exit_code, 1)
        self.assertIn("bad", result.stdout_excerpt)

    def test_timeout_returns_timed_out(self) -> None:
        result = run_check_command(
            CheckCommand("test", f"{sys.executable} -c \"import time; time.sleep(2)\"", 1),
            Path.cwd(),
        )

        self.assertEqual(result.status, CheckStatus.TIMED_OUT)
        self.assertTrue(result.timed_out)

    def test_missing_command_returns_error_or_failed_with_message(self) -> None:
        result = run_check_command(
            CheckCommand("test", "forgebench_missing_command_12345", 5),
            Path.cwd(),
        )

        self.assertIn(result.status, {CheckStatus.ERROR, CheckStatus.FAILED})
        self.assertTrue(result.error_message)

    def test_null_command_returns_not_configured(self) -> None:
        result = run_check_command(CheckCommand("test", None, 5), Path.cwd())

        self.assertEqual(result.status, CheckStatus.NOT_CONFIGURED)
        self.assertTrue(result.skipped)

    def test_run_configured_checks_executes_fixture_commands(self) -> None:
        guardrails = load_guardrails(FIXTURES / "checks_all_pass.yml")

        checks = run_configured_checks(Path.cwd(), guardrails)

        self.assertTrue(checks.run_requested)
        self.assertEqual(checks.summary["passed"], 4)
        self.assertEqual(checks.summary["failed"], 0)

    def test_failed_test_command_creates_blocker_finding(self) -> None:
        guardrails = load_guardrails(FIXTURES / "checks_test_fail.yml")
        checks = run_configured_checks(Path.cwd(), guardrails)

        finding = _finding(findings_from_check_results(checks.results), "tests_failed")

        self.assertEqual(finding.severity, Severity.BLOCKER)
        self.assertEqual(finding.confidence, Confidence.HIGH)

    def test_failed_build_command_creates_blocker_finding(self) -> None:
        guardrails = load_guardrails(FIXTURES / "checks_build_fail.yml")
        checks = run_configured_checks(Path.cwd(), guardrails)

        finding = _finding(findings_from_check_results(checks.results), "build_failed")

        self.assertEqual(finding.severity, Severity.BLOCKER)

    def test_failed_typecheck_command_creates_blocker_finding(self) -> None:
        guardrails = load_guardrails(FIXTURES / "checks_typecheck_fail.yml")
        checks = run_configured_checks(Path.cwd(), guardrails)

        finding = _finding(findings_from_check_results(checks.results), "typecheck_failed")

        self.assertEqual(finding.severity, Severity.BLOCKER)

    def test_failed_lint_command_creates_medium_finding(self) -> None:
        guardrails = load_guardrails(FIXTURES / "checks_lint_fail.yml")
        checks = run_configured_checks(Path.cwd(), guardrails)

        finding = _finding(findings_from_check_results(checks.results), "lint_failed")

        self.assertEqual(finding.severity, Severity.MEDIUM)
        self.assertEqual(finding.confidence, Confidence.HIGH)

    def test_timed_out_test_command_creates_high_finding(self) -> None:
        guardrails = load_guardrails(FIXTURES / "checks_timeout.yml")
        checks = run_configured_checks(Path.cwd(), guardrails)

        finding = _finding(findings_from_check_results(checks.results), "tests_timed_out")

        self.assertEqual(finding.severity, Severity.HIGH)
        self.assertEqual(finding.confidence, Confidence.MEDIUM)

    def test_invalid_repo_path_returns_error_result(self) -> None:
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            guardrails = load_guardrails(FIXTURES / "checks_all_pass.yml")

            checks = run_configured_checks(missing, guardrails)

            self.assertEqual(checks.results[0].status, CheckStatus.ERROR)


def _finding(findings, finding_id):
    for finding in findings:
        if finding.id == finding_id:
            return finding
    raise AssertionError(f"missing finding {finding_id}: {[finding.id for finding in findings]}")


if __name__ == "__main__":
    unittest.main()
