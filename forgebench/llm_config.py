from __future__ import annotations

import os

from forgebench.models import LLMReviewerConfig


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def resolve_llm_config(
    *,
    enabled: bool,
    provider: str | None = None,
    command: str | None = None,
    timeout_seconds: int = 60,
    max_diff_chars: int = 20000,
    mock_response: dict | None = None,
) -> LLMReviewerConfig:
    resolved_command = (command or "").strip() or os.environ.get("FORGEBENCH_LLM_COMMAND", "").strip() or None
    resolved_provider = provider
    if enabled and not resolved_provider:
        if os.environ.get("FORGEBENCH_LLM_API_KEY", "").strip():
            resolved_provider = "openai"
        elif resolved_command:
            resolved_provider = "command"
    return LLMReviewerConfig(
        enabled=enabled,
        provider=resolved_provider,
        command=resolved_command,
        timeout_seconds=timeout_seconds,
        max_diff_chars=max_diff_chars,
        mock_response=mock_response,
        openai_api_key=os.environ.get("FORGEBENCH_LLM_API_KEY"),
        openai_base_url=os.environ.get("FORGEBENCH_LLM_BASE_URL", DEFAULT_OPENAI_BASE_URL),
        openai_model=os.environ.get("FORGEBENCH_LLM_MODEL", DEFAULT_OPENAI_MODEL),
    )