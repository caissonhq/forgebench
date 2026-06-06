from __future__ import annotations

from pathlib import Path
import unittest

from forgebench.policy_test import format_policy_test_report, run_policy_tests


ROOT = Path(__file__).resolve().parents[1]
POLICY_TESTS = ROOT / "examples" / "policy_tests"


class PolicyTestRunnerTests(unittest.TestCase):
    def test_policy_tests_pass_for_examples(self) -> None:
        result = run_policy_tests(POLICY_TESTS, repo_path=ROOT, audit=False)
        self.assertEqual(result.failed_count, 0)
        self.assertGreaterEqual(result.passed_count, 2)

    def test_policy_test_report_contains_pass_lines(self) -> None:
        result = run_policy_tests(POLICY_TESTS, repo_path=ROOT, audit=False)
        report = format_policy_test_report(result)
        self.assertIn("PASS", report)
        self.assertIn("docs_suppress_ui_copy", report)


if __name__ == "__main__":
    unittest.main()