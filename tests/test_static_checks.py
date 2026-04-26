from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.diff_parser import parse_diff_file, parse_unified_diff
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

    def test_assertion_removed_without_replacement_warns(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/tests/test_payments.py b/tests/test_payments.py
index 1111111..2222222 100644
--- a/tests/test_payments.py
+++ b/tests/test_payments.py
@@ -1,4 +1,3 @@
 def test_paid_status():
     result = status({"paid": True})
-    assert result == "paid"
     assert result is not None
"""
        )
        findings, _ = run_static_checks(diff)
        finding = _finding(findings, "tests_assertions_removed_without_replacement")

        self.assertEqual(finding.severity, Severity.MEDIUM)
        self.assertEqual(finding.confidence, Confidence.MEDIUM)

    def test_assertion_replaced_does_not_create_tests_weakened_finding(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/tests/test_payments.py b/tests/test_payments.py
index 1111111..2222222 100644
--- a/tests/test_payments.py
+++ b/tests/test_payments.py
@@ -1,3 +1,3 @@
 def test_paid_status():
     result = status({"paid": True})
-    assert result == "paid"
+    assert result in {"paid", "settled"}
"""
        )
        findings, _ = run_static_checks(diff)

        self.assertNotIn("tests_assertions_removed_without_replacement", {finding.id for finding in findings})
        self.assertNotIn("deleted_tests", {finding.id for finding in findings})

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

    def test_guardrail_can_explicitly_mark_read_model_high_risk(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/operator/read_model.py b/operator/read_model.py
index 1111111..2222222 100644
--- a/operator/read_model.py
+++ b/operator/read_model.py
@@ -1,2 +1,3 @@
 class OperatorReadModel:
     market_id: str
+    last_seen_at: str | None = None
"""
        )
        with TemporaryDirectory() as tmp:
            guardrails_path = Path(tmp) / "forgebench.yml"
            guardrails_path.write_text(
                """
risk_files:
  high:
    - "operator/read_model.py"
""".strip()
                + "\n",
                encoding="utf-8",
            )
            guardrails = load_guardrails(guardrails_path)
        findings, _ = evaluate_guardrails(diff, guardrails)

        finding = _finding(findings, "high_risk_guardrail_file")
        self.assertIn("operator/read_model.py", finding.files)

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

    def test_read_view_and_response_models_are_not_persistence_by_default(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/app/read_model.py b/app/read_model.py
index 1111111..2222222 100644
--- a/app/read_model.py
+++ b/app/read_model.py
@@ -1,2 +1,3 @@
 class OperatorReadModel:
     market_id: str
+    last_seen_at: str | None = None
diff --git a/app/view_model.py b/app/view_model.py
index 1111111..2222222 100644
--- a/app/view_model.py
+++ b/app/view_model.py
@@ -1,2 +1,3 @@
 class PaymentViewModel:
     label: str
+    subtitle: str
diff --git a/app/response_model.py b/app/response_model.py
index 1111111..2222222 100644
--- a/app/response_model.py
+++ b/app/response_model.py
@@ -1,2 +1,3 @@
 class PaymentResponse:
     id: str
+    status: str
"""
        )
        findings, signals = run_static_checks(diff)

        self.assertNotIn("persistence_schema_changed", {finding.id for finding in findings})
        self.assertEqual(signals["persistence_or_schema_files_changed"], [])

    def test_migration_and_schema_files_still_trigger_persistence(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/db/migrations/001_add_paid_at.sql b/db/migrations/001_add_paid_at.sql
new file mode 100644
index 0000000..2222222
--- /dev/null
+++ b/db/migrations/001_add_paid_at.sql
@@ -0,0 +1 @@
+ALTER TABLE payments ADD COLUMN paid_at TEXT;
diff --git a/prisma/schema.prisma b/prisma/schema.prisma
index 1111111..2222222 100644
--- a/prisma/schema.prisma
+++ b/prisma/schema.prisma
@@ -1,3 +1,4 @@
 model Payment {
   id String @id
+  paidAt String?
 }
"""
        )
        findings, signals = run_static_checks(diff)

        finding = _finding(findings, "persistence_schema_changed")
        self.assertIn("db/migrations/001_add_paid_at.sql", finding.files)
        self.assertIn("prisma/schema.prisma", signals["persistence_or_schema_files_changed"])


def _finding(findings, finding_id):
    for finding in findings:
        if finding.id == finding_id:
            return finding
    raise AssertionError(f"missing finding {finding_id}")


if __name__ == "__main__":
    unittest.main()
