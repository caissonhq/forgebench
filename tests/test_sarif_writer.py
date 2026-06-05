from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.models import Confidence, EvidenceType, Finding, ForgeBenchReport, MergePosture, Severity
from forgebench.sarif_writer import build_sarif_report, write_sarif_report


class SarifWriterTests(unittest.TestCase):
    def test_build_sarif_report_maps_findings(self) -> None:
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

        payload = build_sarif_report(report)

        self.assertEqual(payload["version"], "2.1.0")
        run = payload["runs"][0]
        self.assertEqual(run["tool"]["driver"]["name"], "ForgeBench")
        self.assertEqual(len(run["results"]), 1)
        self.assertEqual(run["results"][0]["ruleId"], "implementation_without_tests")
        self.assertEqual(run["results"][0]["level"], "warning")
        self.assertEqual(run["properties"]["posture"], "REVIEW")

    def test_write_sarif_report_writes_file(self) -> None:
        report = ForgeBenchReport(
            posture=MergePosture.LOW_CONCERN,
            summary="Low concern.",
            task_summary="Task",
            changed_files=[],
            findings=[],
            static_signals={},
            guardrail_hits=[],
            generated_at="2026-06-05T00:00:00+00:00",
        )

        with TemporaryDirectory() as tmp:
            path = write_sarif_report(tmp, report)
            self.assertTrue(path.exists())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["runs"][0]["properties"]["finding_count"], 0)


if __name__ == "__main__":
    unittest.main()