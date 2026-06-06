from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.mutation import build_mutation_plan
from forgebench.semantic.models import BehavioralDiffSummary, SymbolChange


class MutationSkeletonTests(unittest.TestCase):
    def test_build_mutation_plan_writes_candidates(self) -> None:
        behavioral = BehavioralDiffSummary(
            enabled=True,
            parsers_used=["stdlib-ast"],
            changed_symbols=[
                SymbolChange(name="capture", kind="function", file_path="payments/service.py", parser="stdlib-ast")
            ],
            symbols_without_test_reference=["capture"],
        )
        with TemporaryDirectory() as tmp:
            result = build_mutation_plan(behavioral, output_dir=tmp)
            payload = json.loads(Path(result.plan_path).read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "skeleton")
            self.assertEqual(payload["candidate_count"], 1)
            self.assertEqual(payload["candidates"][0]["symbol"], "capture")


if __name__ == "__main__":
    unittest.main()