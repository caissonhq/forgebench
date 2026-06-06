from __future__ import annotations

import unittest

from forgebench.llm_ensemble import run_ensemble_json
from forgebench.models import LLMReviewerConfig, LLMReviewStatus


class LLMEnsembleTests(unittest.TestCase):
    def test_ensemble_merges_mock_model_findings(self) -> None:
        config = LLMReviewerConfig(
            enabled=True,
            provider="mock",
            ensemble_models=["mock-a", "mock-b"],
            ensemble_strategy="consensus",
            mock_response={
                "reviewer_name": "Mock",
                "summary": "Potential regression in capture().",
                "findings": [
                    {
                        "id": "llm_behavior_gap",
                        "title": "Behavior gap",
                        "severity": "MEDIUM",
                        "confidence": "MEDIUM",
                        "files": ["payments/service.py"],
                        "evidence": ["capture() lacks negative-path test."],
                        "explanation": "Ensemble concern.",
                        "suggested_fix": "Add tests.",
                    }
                ],
            },
        )
        result = run_ensemble_json(config, '{"task":"refund"}')

        self.assertEqual(result.status, LLMReviewStatus.COMPLETED)
        self.assertIsNotNone(result.payload)
        self.assertEqual(result.payload.get("ensemble_models"), ["mock-a", "mock-b"])
        self.assertEqual(len(result.payload.get("findings") or []), 1)


if __name__ == "__main__":
    unittest.main()