from __future__ import annotations

import json
import unittest
from unittest import mock

from forgebench.llm_openai import _extract_json_object, call_openai_compatible_json
from forgebench.models import LLMReviewerConfig, LLMReviewStatus
from forgebench.llm_openai import run_openai_json


class OpenAIProviderTests(unittest.TestCase):
    def test_extract_json_object_strips_markdown_fence(self) -> None:
        payload = _extract_json_object("```json\n{\"findings\": []}\n```")

        self.assertEqual(json.loads(payload), {"findings": []})

    def test_run_openai_json_fails_without_api_key(self) -> None:
        config = LLMReviewerConfig(enabled=True, provider="openai", openai_api_key=None)
        result = run_openai_json(config, "prompt")

        self.assertEqual(result.status, LLMReviewStatus.FAILED)
        self.assertIn("FORGEBENCH_LLM_API_KEY", result.error_message or "")

    def test_call_openai_compatible_json_parses_response(self) -> None:
        response_body = json.dumps(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "reviewer_name": "General LLM Reviewer",
                                    "summary": "ok",
                                    "findings": [],
                                }
                            )
                        }
                    }
                ]
            }
        ).encode("utf-8")

        class FakeResponse:
            def __init__(self, body: bytes) -> None:
                self._body = body

            def read(self) -> bytes:
                return self._body

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                return False

        with mock.patch("forgebench.llm_openai.request.urlopen", return_value=FakeResponse(response_body)):
            payload = call_openai_compatible_json(
                "prompt",
                api_key="test",
                base_url="https://api.example.com/v1",
                model="test-model",
                timeout_seconds=5,
            )

        self.assertEqual(payload["summary"], "ok")


if __name__ == "__main__":
    unittest.main()