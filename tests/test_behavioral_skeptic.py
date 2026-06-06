from __future__ import annotations

import unittest

from forgebench.adversaries.behavioral_skeptic import review
from forgebench.adversaries.models import ReviewerContext
from forgebench.diff_parser import parse_unified_diff
from forgebench.guardrails import Guardrails
from forgebench.models import Confidence, DeterministicChecks, EvidenceType, Finding, PolicyDecision, Severity


class BehavioralSkepticTests(unittest.TestCase):
    def test_flags_uncovered_changed_symbols(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/payments/service.py b/payments/service.py
index 1111111..2222222 100644
--- a/payments/service.py
+++ b/payments/service.py
@@ -1,2 +1,4 @@
+def refund(self, amount: int) -> int:
+    return amount
"""
        )
        result = review(
            ReviewerContext(
                task_text="Refund support",
                diff=diff,
                static_signals={
                    "source_files_changed": ["payments/service.py"],
                    "tests_changed": False,
                    "changed_symbols": [
                        {
                            "name": "refund",
                            "kind": "function",
                            "file_path": "payments/service.py",
                            "parser": "stdlib-ast",
                        }
                    ],
                    "symbols_without_test_reference": ["refund"],
                    "cross_file_behavior_edges": [],
                },
                findings=[
                    Finding(
                        id="implementation_without_tests",
                        title="Implementation without tests",
                        severity=Severity.MEDIUM,
                        confidence=Confidence.MEDIUM,
                        evidence_type=EvidenceType.STATIC,
                        files=["payments/service.py"],
                        evidence=["No likely test file changed in this patch."],
                        explanation="Static signal",
                        suggested_fix="Add tests",
                    )
                ],
                guardrails=Guardrails(),
                guardrail_hits=[],
                policy=PolicyDecision(),
                deterministic_checks=DeterministicChecks(),
            )
        )

        kinds = {finding.id for finding in result.findings}
        self.assertIn("behavioral_skeptic_uncovered_symbols", kinds)


if __name__ == "__main__":
    unittest.main()