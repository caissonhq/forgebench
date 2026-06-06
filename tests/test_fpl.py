from __future__ import annotations

import json
from pathlib import Path
import unittest

from forgebench.fpl.compiler import compile_fpl_document, compile_fpl_text
from forgebench.fpl.loader import compile_fpl_file, merge_fpl_into_payload
from forgebench.fpl.parser import FPLParseError, parse_fpl
from forgebench.guardrails import load_guardrails


ROOT = Path(__file__).resolve().parents[1]
FPL_EXAMPLE = ROOT / "examples" / "fpl" / "docs_policy.fpl"


class FPLTests(unittest.TestCase):
    def test_parse_docs_policy_example(self) -> None:
        document = parse_fpl(FPL_EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(document.version, "1.0.0")
        self.assertEqual(document.name, "docs-policy")
        self.assertEqual(document.categories[0].name, "docs")
        self.assertIn("ui_copy_changed", document.suppress_rules[0].finding_id)

    def test_compile_to_policy_dict(self) -> None:
        compiled = compile_fpl_text(FPL_EXAMPLE.read_text(encoding="utf-8"))
        policy = compiled["policy"]
        self.assertIn("path_categories", policy)
        self.assertIn("suppress_findings", policy)
        self.assertEqual(policy["posture_overrides"]["docs_only_changes"]["posture_ceiling"], "LOW_CONCERN")

    def test_invalid_directive_raises(self) -> None:
        with self.assertRaises(FPLParseError):
            parse_fpl("not_a_directive")

    def test_fpl_reference_merges_into_guardrails(self) -> None:
        case_dir = ROOT / "examples" / "policy_tests" / "fpl_docs_policy"
        guardrails = load_guardrails(case_dir / "forgebench.yml")
        self.assertEqual(guardrails.fpl_name, "docs-policy")
        self.assertIn("docs", guardrails.policy.path_categories)
        self.assertTrue(guardrails.policy.suppress_findings)

    def test_compile_fpl_file_round_trip(self) -> None:
        compiled = compile_fpl_file(FPL_EXAMPLE)
        self.assertEqual(compiled["fpl_name"], "docs-policy")

    def test_merge_fpl_into_payload(self) -> None:
        payload = merge_fpl_into_payload(
            {"project": "demo", "fpl": str(FPL_EXAMPLE.relative_to(ROOT))},
            ROOT,
            ROOT,
        )
        self.assertIn("policy", payload)
        self.assertIn("fpl_compiled_from", payload)


if __name__ == "__main__":
    unittest.main()