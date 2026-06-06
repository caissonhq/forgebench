from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.models import ForgeBenchReport, MergePosture
from forgebench.prove_it import behavioral_from_static_signals, export_prove_it_plan
from forgebench.semantic.models import BehavioralDiffSummary, SymbolChange


class ProveItTests(unittest.TestCase):
    def test_export_prove_it_plan_writes_checklist(self) -> None:
        behavioral = BehavioralDiffSummary(
            enabled=True,
            changed_symbols=[
                SymbolChange(name="capture", kind="function", file_path="payments/service.py", parser="stdlib-ast")
            ],
            symbols_without_test_reference=["capture"],
        )
        report = ForgeBenchReport(
            posture=MergePosture.REVIEW,
            summary="Review before merge.",
            task_summary="Add capture",
            changed_files=["payments/service.py"],
            findings=[],
            static_signals=behavioral.to_dict(),
            guardrail_hits=[],
            generated_at="2026-06-05T00:00:00+00:00",
        )
        with TemporaryDirectory() as tmp:
            result = export_prove_it_plan(report=report, behavioral=behavioral, llm_config=None, output_dir=tmp)
            checklist = Path(result.checklist_path).read_text(encoding="utf-8")
            plan = json.loads(Path(result.plan_path).read_text(encoding="utf-8"))
            self.assertIn("Prove-it Checklist", checklist)
            self.assertTrue(plan["prove_it_mode"])

    def test_behavioral_from_static_signals_round_trip(self) -> None:
        behavioral = BehavioralDiffSummary(
            enabled=True,
            changed_symbols=[
                SymbolChange(name="capture", kind="function", file_path="payments/service.py", parser="stdlib-ast")
            ],
            symbols_without_test_reference=["capture"],
        )
        signals = {
            "semantic_analysis_enabled": True,
            "semantic_parsers_used": ["stdlib-ast"],
            "changed_symbols": [symbol.to_dict() for symbol in behavioral.changed_symbols],
            "cross_file_behavior_edges": [],
            "symbols_without_test_reference": ["capture"],
            "semantic_warnings": [],
        }
        restored = behavioral_from_static_signals(signals)
        self.assertEqual(restored.changed_symbols[0].name, "capture")


if __name__ == "__main__":
    unittest.main()