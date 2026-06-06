from __future__ import annotations

import os

from forgebench.models import LLMReviewerConfig


DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
ENSEMBLE_MODELS_ENV = "FORGEBENCH_LLM_ENSEMBLE_MODELS"
ENSEMBLE_STRATEGY_ENV = "FORGEBENCH_LLM_ENSEMBLE_STRATEGY"


def resolve_llm_config(
    *,
    enabled: bool,
    provider: str | None = None,
    command: str | None = None,
    timeout_seconds: int = 60,
    max_diff_chars: int = 20000,
    mock_response: dict | None = None,
    ensemble_models: list[str] | None = None,
    ensemble_strategy: str | None = None,
) -> LLMReviewerConfig:
    resolved_command = (command or "").strip() or os.environ.get("FORGEBENCH_LLM_COMMAND", "").strip() or None
    resolved_provider = provider
    if enabled and not resolved_provider:
        if os.environ.get("FORGEBENCH_LLM_API_KEY", "").strip():
            resolved_provider = "openai"
        elif resolved_command:
            resolved_provider = "command"
    resolved_ensemble = list(ensemble_models or _parse_env_model_list(os.environ.get(ENSEMBLE_MODELS_ENV, "")))
    resolved_strategy = (ensemble_strategy or os.environ.get(ENSEMBLE_STRATEGY_ENV, "consensus")).strip() or "consensus"
    openai_model = os.environ.get("FORGEBENCH_LLM_MODEL", DEFAULT_OPENAI_MODEL)
    if resolved_ensemble and openai_model and openai_model not in resolved_ensemble:
        resolved_ensemble = [openai_model, *resolved_ensemble]
    return LLMReviewerConfig(
        enabled=enabled,
        provider=resolved_provider,
        command=resolved_command,
        timeout_seconds=timeout_seconds,
        max_diff_chars=max_diff_chars,
        mock_response=mock_response,
        openai_api_key=os.environ.get("FORGEBENCH_LLM_API_KEY"),
        openai_base_url=os.environ.get("FORGEBENCH_LLM_BASE_URL", DEFAULT_OPENAI_BASE_URL),
        openai_model=openai_model,
        ensemble_models=resolved_ensemble,
        ensemble_strategy=resolved_strategy,
    )


def _parse_env_model_list(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]