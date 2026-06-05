from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from forgebench.llm_review import LLMJSONResult
from forgebench.models import LLMReviewStatus


class OpenAICompatibleError(ValueError):
    pass


def call_openai_compatible_json(
    prompt: str,
    *,
    api_key: str,
    base_url: str,
    model: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    if not api_key.strip():
        raise OpenAICompatibleError("OpenAI-compatible provider requires FORGEBENCH_LLM_API_KEY.")

    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a merge-risk reviewer. Return only valid JSON matching the requested schema.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise OpenAICompatibleError(f"OpenAI-compatible API HTTP {exc.code}: {_single_line(detail)}") from exc
    except error.URLError as exc:
        raise OpenAICompatibleError(f"OpenAI-compatible API request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise OpenAICompatibleError(f"OpenAI-compatible API timed out after {timeout_seconds} seconds.") from exc

    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OpenAICompatibleError(f"OpenAI-compatible API returned invalid JSON: {exc}") from exc

    choices = envelope.get("choices")
    if not isinstance(choices, list) or not choices:
        raise OpenAICompatibleError("OpenAI-compatible API response did not include choices.")

    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise OpenAICompatibleError("OpenAI-compatible API response did not include message content.")

    try:
        parsed = json.loads(_extract_json_object(content))
    except json.JSONDecodeError as exc:
        raise OpenAICompatibleError(f"OpenAI-compatible model returned non-JSON content: {exc}") from exc
    if not isinstance(parsed, dict):
        raise OpenAICompatibleError("OpenAI-compatible model JSON was not an object.")
    return parsed


def run_openai_json(config, prompt: str) -> LLMJSONResult:
    if not config.openai_api_key:
        return LLMJSONResult(
            enabled=True,
            provider="openai",
            status=LLMReviewStatus.FAILED,
            error_message="OpenAI-compatible provider selected but FORGEBENCH_LLM_API_KEY is not set.",
        )
    try:
        payload = call_openai_compatible_json(
            prompt,
            api_key=config.openai_api_key,
            base_url=config.openai_base_url or "https://api.openai.com/v1",
            model=config.openai_model or "gpt-4o-mini",
            timeout_seconds=config.timeout_seconds,
        )
    except OpenAICompatibleError as exc:
        return LLMJSONResult(
            enabled=True,
            provider="openai",
            status=LLMReviewStatus.FAILED,
            error_message=str(exc),
        )
    return LLMJSONResult(enabled=True, provider="openai", status=LLMReviewStatus.COMPLETED, payload=payload)


def _extract_json_object(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        return stripped
    return stripped[start : end + 1]


def _single_line(value: str) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= 500:
        return collapsed
    return collapsed[:497].rstrip() + "..."