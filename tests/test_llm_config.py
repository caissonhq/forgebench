from __future__ import annotations

import os
import unittest
from unittest import mock

from forgebench.llm_config import resolve_llm_config


class LLMConfigTests(unittest.TestCase):
    def test_defaults_to_openai_when_api_key_present(self) -> None:
        with mock.patch.dict(os.environ, {"FORGEBENCH_LLM_API_KEY": "test-key"}, clear=False):
            config = resolve_llm_config(enabled=True)

        self.assertEqual(config.provider, "openai")
        self.assertEqual(config.openai_api_key, "test-key")

    def test_defaults_to_command_when_env_command_present(self) -> None:
        env = {"FORGEBENCH_LLM_COMMAND": "python reviewer.py"}
        with mock.patch.dict(os.environ, env, clear=True):
            config = resolve_llm_config(enabled=True)

        self.assertEqual(config.provider, "command")
        self.assertEqual(config.command, "python reviewer.py")

    def test_explicit_provider_overrides_env_inference(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"FORGEBENCH_LLM_API_KEY": "test-key", "FORGEBENCH_LLM_COMMAND": "python reviewer.py"},
            clear=False,
        ):
            config = resolve_llm_config(enabled=True, provider="mock")

        self.assertEqual(config.provider, "mock")


if __name__ == "__main__":
    unittest.main()