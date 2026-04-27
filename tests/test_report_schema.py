from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.diff_parser import parse_diff_file
from forgebench.guardrails import Guardrails
from forgebench.models import ForgeBenchReport, REPORT_SCHEMA_VERSION
from forgebench.posture import determine_posture
from forgebench.report_writer import write_reports
from forgebench.static_checks import run_static_checks


FIXTURES = Path(__file__).parent / "fixtures"

EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "config_mode",
    "guardrails_source",
    "first_run_guidance",
    "posture",
    "pre_llm_posture",
    "final_posture",
    "summary",
    "task_summary",
    "changed_files",
    "findings",
    "static_signals",
    "guardrail_hits",
    "deterministic_checks",
    "policy",
    "specialized_reviewers",
    "llm_review",
    "pr_checkout",
    "generated_at",
}


class ReportSchemaTests(unittest.TestCase):
    def test_json_report_schema_version_and_top_level_keys_are_pinned(self) -> None:
        report = _sample_report()
        with TemporaryDirectory() as tmp:
            written = write_reports(
                tmp,
                report,
                Guardrails(),
                "Update calculator behavior.",
                inputs={"repo": ".", "diff": "patch.diff", "task": "task.md", "guardrails": "none"},
            )
            payload = json.loads(written["json"].read_text(encoding="utf-8"))

        self.assertEqual(payload["schema_version"], REPORT_SCHEMA_VERSION)
        self.assertEqual(set(payload), EXPECTED_TOP_LEVEL_KEYS)
        self.assertEqual(payload["schema_version"], "1.2.0")
        self.assertIn("uid", payload["findings"][0])
        self.assertIn("kind", payload["findings"][0])


def _sample_report() -> ForgeBenchReport:
    diff = parse_diff_file(FIXTURES / "simple.patch")
    findings, signals = run_static_checks(diff)
    posture, summary = determine_posture(findings, signals, [])
    return ForgeBenchReport(
        posture=posture,
        summary=summary,
        task_summary="Update calculator behavior.",
        changed_files=diff.changed_files,
        findings=findings,
        static_signals=signals,
        guardrail_hits=[],
        generated_at="2026-04-26T00:00:00+00:00",
    )
