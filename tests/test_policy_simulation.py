from __future__ import annotations

from pathlib import Path
import unittest

from forgebench.policy_simulation import simulate_policy


ROOT = Path(__file__).resolve().parents[1]


class PolicySimulationTests(unittest.TestCase):
    def test_simulate_docs_policy_case(self) -> None:
        case = ROOT / "examples" / "golden_cases" / "docs_only_policy_low_concern"
        result = simulate_policy(
            repo_path=ROOT,
            diff_path=case / "patch.diff",
            guardrails_path=case / "forgebench.yml",
        )
        self.assertEqual(result.posture.value, "LOW_CONCERN")
        self.assertIn("ui_copy_changed", result.suppressed_findings)
        self.assertIn("docs", result.active_categories)
        self.assertFalse(result.formal_violations)


if __name__ == "__main__":
    unittest.main()