from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.models import EvidenceType, MergePosture, Severity
from forgebench.review import run_review


ROOT = Path(__file__).resolve().parents[1]


class RegressionHunterTests(unittest.TestCase):
    def test_trigger_fires_on_removed_assertion_and_source_change(self) -> None:
        result = _review(_assertion_removed_patch())

        finding = _finding(result, "regression_hunter_load_bearing_assertion_removed")
        self.assertEqual(finding.evidence_type, EvidenceType.REVIEWER)
        self.assertEqual(finding.severity, Severity.HIGH)
        self.assertEqual(finding.confidence.value, "MEDIUM")
        self.assertEqual(result.report.posture, MergePosture.REVIEW)

    def test_trigger_does_not_fire_on_docs_only(self) -> None:
        result = _review(_docs_patch())

        self.assertNotIn("regression_hunter_load_bearing_assertion_removed", _finding_ids(result))
        self.assertEqual(result.report.posture, MergePosture.LOW_CONCERN)

    def test_trigger_does_not_fire_when_assertion_is_replaced(self) -> None:
        result = _review(_assertion_replaced_patch())

        self.assertNotIn("regression_hunter_load_bearing_assertion_removed", _finding_ids(result))
        self.assertNotEqual(result.report.posture, MergePosture.BLOCK)

    def test_finding_cannot_block_by_itself(self) -> None:
        result = _review(_assertion_removed_patch())

        self.assertEqual(result.report.posture, MergePosture.REVIEW)
        self.assertNotEqual(result.report.posture, MergePosture.BLOCK)

    def test_llm_verdict_creates_capped_finding(self) -> None:
        result = _review(
            _assertion_removed_patch(),
            llm_review=True,
            llm_payload={
                "verdict": "load_bearing",
                "rationale": "The removed assertion checks the changed paid status.",
                "evidence_lines": ['assert status({"paid": True}) == "paid"'],
                "severity": "blocker",
                "confidence": "high",
            },
        )

        finding = _finding(result, "regression_hunter_load_bearing_assertion_removed")
        self.assertEqual(finding.evidence_type, EvidenceType.LLM)
        self.assertEqual(finding.severity, Severity.HIGH)
        self.assertEqual(finding.confidence.value, "MEDIUM")
        self.assertEqual(result.report.posture, MergePosture.REVIEW)
        self.assertTrue(result.report.specialized_reviewers.metadata["llm_call_used"])

    def test_llm_replaced_verdict_creates_no_finding(self) -> None:
        result = _review(
            _assertion_removed_patch(),
            llm_review=True,
            llm_payload={
                "verdict": "replaced",
                "rationale": "An equivalent assertion is present.",
                "evidence_lines": [],
            },
        )

        self.assertNotIn("regression_hunter_load_bearing_assertion_removed", _finding_ids(result))

    def test_llm_finding_cannot_downgrade_block(self) -> None:
        result = _review(
            _assertion_removed_patch(),
            guardrails="""
checks:
  test: "python3 -c 'import sys; sys.exit(1)'"
check_timeout_seconds: 5
""",
            run_checks=True,
            llm_review=True,
            llm_payload={
                "verdict": "load_bearing",
                "rationale": "The removed assertion checks changed behavior.",
                "evidence_lines": [],
            },
        )

        self.assertEqual(result.report.posture, MergePosture.BLOCK)
        self.assertIn("tests_failed", _finding_ids(result))


def _review(
    patch: str,
    *,
    guardrails: str | None = None,
    run_checks: bool = False,
    llm_review: bool = False,
    llm_payload: dict[str, object] | None = None,
):
    with TemporaryDirectory() as tmp:
        temp = Path(tmp)
        patch_path = temp / "patch.diff"
        task_path = temp / "task.md"
        patch_path.write_text(patch.strip() + "\n", encoding="utf-8")
        task_path.write_text("Adjust paid-state behavior.", encoding="utf-8")
        guardrails_path = None
        if guardrails:
            guardrails_path = temp / "forgebench.yml"
            guardrails_path.write_text(guardrails.strip() + "\n", encoding="utf-8")
        return run_review(
            repo_path=ROOT,
            diff_path=patch_path,
            task_path=task_path,
            guardrails_path=guardrails_path,
            output_dir=temp / "out",
            run_checks=run_checks,
            llm_review=llm_review,
            llm_provider="mock" if llm_review else None,
            llm_mock_response=llm_payload,
        )


def _finding_ids(result) -> set[str]:
    return {finding.id for finding in result.report.findings}


def _finding(result, finding_id: str):
    for finding in result.report.findings:
        if finding.id == finding_id:
            return finding
    raise AssertionError(f"missing finding {finding_id}")


def _assertion_removed_patch() -> str:
    return """
diff --git a/src/payments.py b/src/payments.py
index 1111111..2222222 100644
--- a/src/payments.py
+++ b/src/payments.py
@@ -1,4 +1,5 @@
 def status(payment):
-    return "paid" if payment.get("paid") else "unpaid"
+    if payment.get("paid") or payment.get("settled"):
+        return "paid"
+    return "unpaid"
diff --git a/tests/test_payments.py b/tests/test_payments.py
index 1111111..2222222 100644
--- a/tests/test_payments.py
+++ b/tests/test_payments.py
@@ -1,5 +1,4 @@
 from src.payments import status
 
 def test_paid_status():
-    assert status({"paid": True}) == "paid"
     assert status({"paid": False}) == "unpaid"
"""


def _assertion_replaced_patch() -> str:
    return """
diff --git a/src/payments.py b/src/payments.py
index 1111111..2222222 100644
--- a/src/payments.py
+++ b/src/payments.py
@@ -1,4 +1,5 @@
 def status(payment):
-    return "paid" if payment.get("paid") else "unpaid"
+    if payment.get("paid") or payment.get("settled"):
+        return "paid"
+    return "unpaid"
diff --git a/tests/test_payments.py b/tests/test_payments.py
index 1111111..2222222 100644
--- a/tests/test_payments.py
+++ b/tests/test_payments.py
@@ -1,5 +1,5 @@
 from src.payments import status
 
 def test_paid_status():
-    assert status({"paid": True}) == "paid"
+    assert status({"paid": True}) in {"paid", "settled"}
     assert status({"paid": False}) == "unpaid"
"""


def _docs_patch() -> str:
    return """
diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Example
+Clearer wording.
"""


if __name__ == "__main__":
    unittest.main()
