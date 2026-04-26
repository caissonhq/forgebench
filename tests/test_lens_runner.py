from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.adversaries.models import ReviewerContext
from forgebench.adversaries.runner import run_specialized_reviewers
from forgebench.diff_parser import parse_unified_diff
from forgebench.llm_review import LLMReviewerConfig
from forgebench.models import DeterministicChecks, Guardrails
from forgebench.policy import apply_guardrails_policy
from forgebench.static_checks import run_static_checks


class LensRunnerTests(unittest.TestCase):
    def test_trigger_false_skips_lens(self) -> None:
        report = run_specialized_reviewers(_context(_docs_patch()), llm_config=LLMReviewerConfig(enabled=True, provider="mock"))

        self.assertEqual(_lens_status(report), "skipped")
        self.assertEqual(report.metadata["skipped_lenses"][0]["lens_id"], "test_skeptic_v2")

    def test_trigger_true_with_llm_disabled_skips_lens(self) -> None:
        report = run_specialized_reviewers(_context(_weak_test_patch()), llm_config=LLMReviewerConfig(enabled=False))

        self.assertEqual(_lens_status(report), "skipped")
        self.assertIn("disabled", report.metadata["skipped_lenses"][0]["reason"])

    def test_trigger_true_with_mock_provider_works(self) -> None:
        report = run_specialized_reviewers(
            _context(_weak_test_patch()),
            llm_config=LLMReviewerConfig(enabled=True, provider="mock", mock_response=_weak_payload()),
        )

        self.assertIn("test_skeptic_v2_weak_assertion_semantics", {finding.id for finding in report.findings})
        self.assertTrue(report.metadata["llm_call_used"])

    def test_trigger_true_with_command_provider_works(self) -> None:
        with TemporaryDirectory() as tmp:
            script = Path(tmp) / "lens.py"
            script.write_text("import json\nprint(json.dumps(" + repr(_weak_payload()) + "))\n", encoding="utf-8")
            report = run_specialized_reviewers(
                _context(_weak_test_patch()),
                llm_config=LLMReviewerConfig(enabled=True, provider="command", command=_python_command(script)),
            )

        self.assertIn("test_skeptic_v2_weak_assertion_semantics", {finding.id for finding in report.findings})
        self.assertTrue(report.metadata["llm_call_used"])

    def test_trigger_false_does_not_call_lens_command(self) -> None:
        command = f"{shlex.quote(sys.executable)} -c {shlex.quote('raise SystemExit(99)')}"
        report = run_specialized_reviewers(
            _context(_docs_patch()),
            llm_config=LLMReviewerConfig(enabled=True, provider="command", command=command),
        )

        self.assertEqual(_lens_status(report), "skipped")
        self.assertFalse(report.metadata["llm_call_used"])

    def test_skipped_reasons_appear_in_json(self) -> None:
        report = run_specialized_reviewers(_context(_docs_patch()), llm_config=LLMReviewerConfig(enabled=True, provider="mock"))
        payload = report.to_dict()

        self.assertIn("metadata", payload)
        self.assertEqual(payload["metadata"]["skipped_lenses"][0]["lens_id"], "test_skeptic_v2")

    def test_existing_reviewers_still_run(self) -> None:
        report = run_specialized_reviewers(_context(_weak_test_patch()), llm_config=LLMReviewerConfig(enabled=False))
        reviewer_ids = {result.reviewer_id for result in report.results}

        self.assertTrue({"scope_auditor", "test_skeptic", "contract_keeper", "product_guardrail_reviewer"}.issubset(reviewer_ids))


def _context(patch: str) -> ReviewerContext:
    diff = parse_unified_diff(patch)
    findings, signals = run_static_checks(diff)
    findings, signals, policy = apply_guardrails_policy(diff, findings, signals, Guardrails())
    return ReviewerContext(
        task_text="Add paid-state behavior.",
        diff=diff,
        static_signals=signals,
        findings=findings,
        guardrails=Guardrails(),
        guardrail_hits=[],
        policy=policy,
        deterministic_checks=DeterministicChecks(),
    )


def _lens_status(report) -> str:
    for result in report.results:
        if result.reviewer_id == "test_skeptic_v2":
            return result.status.value
    raise AssertionError("missing Test Skeptic v2 result")


def _weak_payload() -> dict[str, object]:
    return {
        "verdict": "weak",
        "rationale": "The test executes the changed function but does not assert the paid result.",
        "evidence_lines": ["result = status({'paid': True})"],
        "severity": "blocker",
        "confidence": "high",
    }


def _python_command(script: Path) -> str:
    return f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}"


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


if __name__ == "__main__":
    unittest.main()
