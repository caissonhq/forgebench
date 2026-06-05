from __future__ import annotations

import unittest

from forgebench.github_checks import build_check_run_payload
from forgebench.models import Confidence, EvidenceType, Finding, ForgeBenchReport, MergePosture, Severity


class GitHubChecksTests(unittest.TestCase):
    def test_build_check_run_payload_maps_posture_and_annotations(self) -> None:
        report = ForgeBenchReport(
            posture=MergePosture.REVIEW,
            summary="Review before merge.",
            task_summary="Task",
            changed_files=["app.py"],
            findings=[
                Finding(
                    id="implementation_without_tests",
                    title="Implementation changed without corresponding test updates",
                    severity=Severity.MEDIUM,
                    confidence=Confidence.MEDIUM,
                    evidence_type=EvidenceType.STATIC,
                    files=["app.py"],
                    explanation="No tests changed.",
                    suggested_fix="Add tests.",
                )
            ],
            static_signals={},
            guardrail_hits=[],
            generated_at="2026-06-05T00:00:00+00:00",
        )

        payload = build_check_run_payload(report, head_sha="abc123")

        self.assertEqual(payload["head_sha"], "abc123")
        self.assertEqual(payload["conclusion"], "neutral")
        annotations = payload["output"]["annotations"]
        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0]["path"], "app.py")
        self.assertEqual(annotations[0]["annotation_level"], "warning")


if __name__ == "__main__":
    unittest.main()