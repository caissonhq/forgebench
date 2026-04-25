from pathlib import Path
import unittest

from forgebench.check_runner import findings_from_check_results, run_configured_checks
from forgebench.diff_parser import parse_diff_file
from forgebench.guardrails import evaluate_guardrails, load_guardrails
from forgebench.models import MergePosture
from forgebench.posture import determine_posture
from forgebench.static_checks import run_static_checks


FIXTURES = Path(__file__).parent / "fixtures"


class PostureTests(unittest.TestCase):
    def test_docs_only_diff_results_in_low_concern(self) -> None:
        posture, _ = _posture_for_fixture("docs_only.patch")

        self.assertEqual(posture, MergePosture.LOW_CONCERN)

    def test_test_only_diff_results_in_low_concern(self) -> None:
        posture, _ = _posture_for_fixture("test_only_change.patch")

        self.assertEqual(posture, MergePosture.LOW_CONCERN)

    def test_posture_becomes_review_for_implementation_without_tests(self) -> None:
        posture, _ = _posture_for_fixture("simple.patch")

        self.assertEqual(posture, MergePosture.REVIEW)

    def test_ui_change_without_tests_results_in_review(self) -> None:
        posture, _ = _posture_for_fixture("ui_change_without_tests.patch")

        self.assertEqual(posture, MergePosture.REVIEW)

    def test_posture_becomes_block_for_deleted_tests(self) -> None:
        posture, _ = _posture_for_fixture("risky.patch")

        self.assertEqual(posture, MergePosture.BLOCK)

    def test_posture_becomes_block_for_forbidden_pattern(self) -> None:
        diff = parse_diff_file(FIXTURES / "risky.patch")
        static_findings, signals = run_static_checks(diff)
        guardrails = load_guardrails(FIXTURES / "guardrails.yml")
        guardrail_findings, guardrail_hits = evaluate_guardrails(diff, guardrails)

        posture, _ = determine_posture(static_findings + guardrail_findings, signals, guardrail_hits)

        self.assertEqual(posture, MergePosture.BLOCK)

    def test_persistence_change_without_tests_results_in_block(self) -> None:
        posture, summary = _posture_for_fixture("persistence_change_without_tests.patch")

        self.assertEqual(posture, MergePosture.BLOCK)
        self.assertIn("persistence", summary.lower())

    def test_dependency_change_without_tests_results_in_block(self) -> None:
        posture, summary = _posture_for_fixture("dependency_change_without_tests.patch")

        self.assertEqual(posture, MergePosture.BLOCK)
        self.assertIn("dependency", summary.lower())

    def test_generated_file_noise_results_in_review(self) -> None:
        posture, _ = _posture_for_fixture("generated_file_noise.patch")

        self.assertEqual(posture, MergePosture.REVIEW)

    def test_only_advisory_findings_remain_low_concern(self) -> None:
        diff = parse_diff_file(FIXTURES / "docs_only.patch")
        findings, signals = run_static_checks(diff)

        self.assertEqual({finding.id for finding in findings}, {"ui_copy_changed"})
        posture, _ = determine_posture(findings, signals, [])

        self.assertEqual(posture, MergePosture.LOW_CONCERN)

    def test_posture_block_when_tests_fail(self) -> None:
        posture, summary = _posture_for_fixture_with_checks("docs_only.patch", "checks_test_fail.yml")

        self.assertEqual(posture, MergePosture.BLOCK)
        self.assertIn("deterministic checks found failures", summary.lower())

    def test_posture_low_concern_when_docs_only_and_checks_pass(self) -> None:
        posture, summary = _posture_for_fixture_with_checks("docs_only.patch", "checks_all_pass.yml")

        self.assertEqual(posture, MergePosture.LOW_CONCERN)
        self.assertIn("configured deterministic checks passed", summary.lower())

    def test_posture_review_when_lint_fails(self) -> None:
        posture, summary = _posture_for_fixture_with_checks("docs_only.patch", "checks_lint_fail.yml")

        self.assertEqual(posture, MergePosture.REVIEW)
        self.assertIn("quality check failed", summary.lower())

    def test_posture_review_when_check_times_out(self) -> None:
        posture, summary = _posture_for_fixture_with_checks("docs_only.patch", "checks_timeout.yml")

        self.assertEqual(posture, MergePosture.REVIEW)
        self.assertIn("timed out", summary.lower())

    def test_posture_does_not_claim_checks_passed_when_not_run(self) -> None:
        posture, summary = _posture_for_fixture("docs_only.patch")

        self.assertEqual(posture, MergePosture.LOW_CONCERN)
        self.assertIn("deterministic checks were not run", summary.lower())
        self.assertNotIn("passed", summary.lower())


def _posture_for_fixture(name: str):
    diff = parse_diff_file(FIXTURES / name)
    findings, signals = run_static_checks(diff)
    return determine_posture(findings, signals, [])


def _posture_for_fixture_with_checks(diff_name: str, guardrails_name: str):
    diff = parse_diff_file(FIXTURES / diff_name)
    static_findings, signals = run_static_checks(diff)
    guardrails = load_guardrails(FIXTURES / guardrails_name)
    deterministic_checks = run_configured_checks(Path.cwd(), guardrails)
    findings = findings_from_check_results(deterministic_checks.results) + static_findings
    return determine_posture(findings, signals, [], deterministic_checks)


if __name__ == "__main__":
    unittest.main()
