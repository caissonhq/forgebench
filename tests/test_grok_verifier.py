from __future__ import annotations

import unittest

from forgebench.grok_verifier import verify_policy_with_grok


class GrokVerifierTests(unittest.TestCase):
    def test_mock_grok_verification(self) -> None:
        result = verify_policy_with_grok(
            policy_summary={"policy_version": "1.0.0"},
            simulation_summary={"posture": "LOW_CONCERN", "findings": []},
            mock_response={
                "status": "pass",
                "summary": "Policy behavior is consistent.",
                "obligations": ["posture_respects_policy_ceiling"],
                "satisfied": ["posture_respects_policy_ceiling"],
                "unsatisfied": [],
            },
        )
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.provider, "mock")


if __name__ == "__main__":
    unittest.main()