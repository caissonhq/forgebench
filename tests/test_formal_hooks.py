from __future__ import annotations

import unittest

from forgebench.formal_hooks import run_formal_verification_hooks
from forgebench.models import Confidence, EvidenceType, Finding, MergePosture, PolicyDecision, Severity


class FormalHooksTests(unittest.TestCase):
    def test_passes_for_consistent_low_concern(self) -> None:
        result = run_formal_verification_hooks(
            posture=MergePosture.LOW_CONCERN,
            findings=[],
            policy_decision=PolicyDecision(posture_ceiling=MergePosture.LOW_CONCERN),
            changed_files=["docs/README.md"],
        )
        self.assertTrue(result.passed)

    def test_detects_ceiling_violation(self) -> None:
        finding = Finding(
            id="implementation_without_tests",
            title="tests",
            severity=Severity.MEDIUM,
            confidence=Confidence.MEDIUM,
            evidence_type=EvidenceType.STATIC,
            files=["src/app.py"],
            explanation="Implementation changed without tests.",
            suggested_fix="Add tests.",
        )
        result = run_formal_verification_hooks(
            posture=MergePosture.REVIEW,
            findings=[finding],
            policy_decision=PolicyDecision(posture_ceiling=MergePosture.LOW_CONCERN),
            changed_files=["src/app.py"],
        )
        self.assertFalse(result.passed)
        self.assertTrue(any("ceiling" in item.lower() for item in result.violations))


if __name__ == "__main__":
    unittest.main()