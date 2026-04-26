from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp
import json
import unittest

from forgebench.models import EvidenceType, MergePosture, Severity
from forgebench.review import run_review


ROOT = Path(__file__).resolve().parents[1]


class TestSkepticV2Tests(unittest.TestCase):
    def test_weak_verdict_creates_finding(self) -> None:
        result = _review(_weak_test_patch(), _weak_payload())

        finding = _finding(result, "test_skeptic_v2_weak_assertion_semantics")
        self.assertEqual(finding.evidence_type, EvidenceType.LLM)
        self.assertEqual(finding.severity, Severity.MEDIUM)
        self.assertEqual(finding.confidence.value, "MEDIUM")
        self.assertIn("Test Skeptic v2", result.written_paths["markdown"].read_text(encoding="utf-8"))

    def test_adequate_verdict_creates_no_finding(self) -> None:
        result = _review(_weak_test_patch(), {"verdict": "adequate", "rationale": "Assertions are adequate.", "evidence_lines": []})

        self.assertNotIn("test_skeptic_v2_weak_assertion_semantics", _finding_ids(result))

    def test_uncertain_verdict_creates_no_finding(self) -> None:
        result = _review(_weak_test_patch(), {"verdict": "uncertain", "rationale": "The evidence is insufficient.", "evidence_lines": []})

        self.assertNotIn("test_skeptic_v2_weak_assertion_semantics", _finding_ids(result))

    def test_docs_only_change_causes_no_lens_finding(self) -> None:
        result = _review(_docs_patch(), _weak_payload())

        self.assertNotIn("test_skeptic_v2_weak_assertion_semantics", _finding_ids(result))
        self.assertIn("test_skeptic_v2", _skipped_lens_ids(result))

    def test_strong_assertion_tests_do_not_trigger_lens(self) -> None:
        result = _review(_strong_assertion_patch(), _weak_payload())

        self.assertNotIn("test_skeptic_v2_weak_assertion_semantics", _finding_ids(result))
        self.assertIn("test_skeptic_v2", _skipped_lens_ids(result))

    def test_llm_cannot_set_high_or_blocker(self) -> None:
        payload = _weak_payload()
        payload["severity"] = "blocker"
        payload["confidence"] = "high"
        result = _review(_weak_test_patch(), payload)
        finding = _finding(result, "test_skeptic_v2_weak_assertion_semantics")

        self.assertEqual(finding.severity, Severity.MEDIUM)
        self.assertEqual(finding.confidence.value, "MEDIUM")

    def test_llm_lens_finding_can_escalate_low_concern_to_review(self) -> None:
        result = _review(_weak_test_patch(), _weak_payload())

        self.assertEqual(result.report.posture, MergePosture.REVIEW)
        self.assertIn("test_skeptic_v2_weak_assertion_semantics", _finding_ids(result))

    def test_llm_lens_finding_cannot_downgrade_review(self) -> None:
        result = _review(_review_patch_with_weak_tests(), _weak_payload())

        self.assertEqual(result.report.posture, MergePosture.REVIEW)

    def test_llm_lens_finding_cannot_downgrade_block(self) -> None:
        result = _review(
            _weak_test_patch(),
            _weak_payload(),
            guardrails="""
checks:
  test: "python3 -c 'import sys; sys.exit(1)'"
check_timeout_seconds: 5
""",
            run_checks=True,
        )

        self.assertEqual(result.report.posture, MergePosture.BLOCK)
        self.assertIn("tests_failed", _finding_ids(result))

    def test_repair_prompt_includes_advisory_lens_wording(self) -> None:
        result = _review(_weak_test_patch(), _weak_payload())
        prompt = result.written_paths["repair_prompt"].read_text(encoding="utf-8")

        self.assertIn("Test Skeptic v2 flagged weak test semantics", prompt)
        self.assertIn("Treat this as a review task, not proof.", prompt)

    def test_json_includes_skipped_lens_metadata(self) -> None:
        result = _review(_docs_patch(), _weak_payload())
        payload = json.loads(result.written_paths["json"].read_text(encoding="utf-8"))

        self.assertIn("metadata", payload["specialized_reviewers"])
        self.assertEqual(payload["specialized_reviewers"]["metadata"]["skipped_lenses"][0]["lens_id"], "test_skeptic_v2")


def _review(patch: str, llm_payload: dict[str, object], guardrails: str | None = None, run_checks: bool = False):
    with TemporaryDirectory() as tmp:
        temp = Path(tmp)
        patch_path = temp / "patch.diff"
        task_path = temp / "task.md"
        patch_path.write_text(patch.strip() + "\n", encoding="utf-8")
        task_path.write_text("Add paid-state behavior.", encoding="utf-8")
        guardrails_path = None
        if guardrails:
            guardrails_path = temp / "forgebench.yml"
            guardrails_path.write_text(guardrails.strip() + "\n", encoding="utf-8")
        result = run_review(
            repo_path=ROOT,
            diff_path=patch_path,
            task_path=task_path,
            guardrails_path=guardrails_path,
            output_dir=temp / "out",
            run_checks=run_checks,
            llm_review=True,
            llm_provider="mock",
            llm_mock_response=llm_payload,
        )
        # Keep artifacts readable after TemporaryDirectory cleanup for assertions.
        _materialize_artifacts(result)
        return result


def _materialize_artifacts(result) -> None:
    persistent = Path(mkdtemp(prefix="forgebench-test-skeptic-v2-"))
    persistent.mkdir(parents=True, exist_ok=True)
    rewritten = {}
    for key, path in result.written_paths.items():
        target = persistent / path.name
        target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        rewritten[key] = target
    result.written_paths.update(rewritten)


def _weak_payload() -> dict[str, object]:
    return {
        "verdict": "weak",
        "rationale": "The test executes the changed function but does not assert the paid result.",
        "evidence_lines": ["result = status({'paid': True})"],
    }


def _finding_ids(result) -> set[str]:
    return {finding.id for finding in result.report.findings}


def _skipped_lens_ids(result) -> set[str]:
    return {item["lens_id"] for item in result.report.specialized_reviewers.metadata.get("skipped_lenses", [])}


def _finding(result, finding_id: str):
    for finding in result.report.findings:
        if finding.id == finding_id:
            return finding
    raise AssertionError(f"missing finding {finding_id}")


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


def _weak_test_patch() -> str:
    return """
diff --git a/src/payments.py b/src/payments.py
index 1111111..2222222 100644
--- a/src/payments.py
+++ b/src/payments.py
@@ -1,2 +1,4 @@
 def status(payment):
-    return "unpaid"
+    if payment.get("paid"):
+        return "paid"
+    return "unpaid"
diff --git a/tests/test_payments.py b/tests/test_payments.py
index 1111111..2222222 100644
--- a/tests/test_payments.py
+++ b/tests/test_payments.py
@@ -1 +1,4 @@
 from src.payments import status
+
+def test_paid_status():
+    result = status({"paid": True})
"""


def _strong_assertion_patch() -> str:
    return """
diff --git a/src/payments.py b/src/payments.py
index 1111111..2222222 100644
--- a/src/payments.py
+++ b/src/payments.py
@@ -1,2 +1,4 @@
 def status(payment):
-    return "unpaid"
+    if payment.get("paid"):
+        return "paid"
+    return "unpaid"
diff --git a/tests/test_payments.py b/tests/test_payments.py
index 1111111..2222222 100644
--- a/tests/test_payments.py
+++ b/tests/test_payments.py
@@ -1 +1,5 @@
 from src.payments import status
+
+def test_paid_status():
+    result = status({"paid": True})
+    assert result == "paid"
"""


def _review_patch_with_weak_tests() -> str:
    return _weak_test_patch() + """
diff --git a/package.json b/package.json
index 1111111..2222222 100644
--- a/package.json
+++ b/package.json
@@ -1,3 +1,4 @@
 {
-  "name": "demo"
+  "name": "demo",
+  "private": true
 }
"""


if __name__ == "__main__":
    unittest.main()
