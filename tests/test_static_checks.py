from pathlib import Path
import unittest

from forgebench.diff_parser import parse_diff_file
from forgebench.guardrails import evaluate_guardrails, load_guardrails
from forgebench.models import Confidence, Severity
from forgebench.static_checks import run_static_checks


FIXTURES = Path(__file__).parent / "fixtures"


class StaticChecksTests(unittest.TestCase):
    def test_source_change_without_test_change_creates_finding(self) -> None:
        diff = parse_diff_file(FIXTURES / "simple.patch")
        findings, _ = run_static_checks(diff)

        self.assertIn("implementation_without_tests", {finding.id for finding in findings})

    def test_test_deletion_creates_high_confidence_finding(self) -> None:
        diff = parse_diff_file(FIXTURES / "risky.patch")
        findings, _ = run_static_checks(diff)
        finding = _finding(findings, "deleted_tests")

        self.assertEqual(finding.severity, Severity.HIGH)
        self.assertEqual(finding.confidence, Confidence.HIGH)
        self.assertIn("tests/test_calculator.py", finding.files)

    def test_dependency_file_change_creates_finding(self) -> None:
        diff = parse_diff_file(FIXTURES / "risky.patch")
        findings, _ = run_static_checks(diff)

        self.assertIn("dependency_surface_changed", {finding.id for finding in findings})

    def test_guardrail_high_risk_file_match_creates_finding(self) -> None:
        diff = parse_diff_file(FIXTURES / "risky.patch")
        guardrails = load_guardrails(FIXTURES / "guardrails.yml")
        findings, hits = evaluate_guardrails(diff, guardrails)

        finding = _finding(findings, "high_risk_guardrail_file")
        self.assertIn("app/TaxEngine/Calculator.swift", finding.files)
        self.assertTrue(any("**/TaxEngine/**" in hit for hit in hits))

    def test_forbidden_pattern_in_added_lines_creates_finding(self) -> None:
        diff = parse_diff_file(FIXTURES / "risky.patch")
        guardrails = load_guardrails(FIXTURES / "guardrails.yml")
        findings, hits = evaluate_guardrails(diff, guardrails)

        finding = _finding(findings, "forbidden_pattern_added")
        self.assertIn("app/TaxEngine/Calculator.swift", finding.files)
        self.assertTrue(any("subscription" in evidence for evidence in finding.evidence))
        self.assertTrue(any("subscription" in hit for hit in hits))

    def test_generated_files_are_detected(self) -> None:
        diff = parse_diff_file(FIXTURES / "generated_file_noise.patch")
        findings, signals = run_static_checks(diff)

        finding = _finding(findings, "generated_files_changed")
        self.assertEqual(finding.severity, Severity.MEDIUM)
        self.assertIn("dist/app.js", signals["generated_or_unrelated_files_changed"])


def _finding(findings, finding_id):
    for finding in findings:
        if finding.id == finding_id:
            return finding
    raise AssertionError(f"missing finding {finding_id}")


if __name__ == "__main__":
    unittest.main()
