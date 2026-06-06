from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request


DEFAULT_GROK_BASE_URL = "https://api.x.ai/v1"
DEFAULT_GROK_MODEL = "grok-2-latest"
GROK_API_KEY_ENV = "FORGEBENCH_GROK_API_KEY"
GROK_BASE_URL_ENV = "FORGEBENCH_GROK_BASE_URL"
GROK_MODEL_ENV = "FORGEBENCH_GROK_MODEL"


class GrokVerifierError(ValueError):
    pass


@dataclass(frozen=True)
class GrokVerificationResult:
    status: str
    summary: str
    obligations: list[str]
    satisfied: list[str]
    unsatisfied: list[str]
    provider: str
    model: str
    raw: dict[str, Any] | None = None


def resolve_grok_config(
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    return {
        "api_key": (api_key or os.environ.get(GROK_API_KEY_ENV, "")).strip(),
        "base_url": (base_url or os.environ.get(GROK_BASE_URL_ENV, DEFAULT_GROK_BASE_URL)).strip(),
        "model": (model or os.environ.get(GROK_MODEL_ENV, DEFAULT_GROK_MODEL)).strip(),
        "timeout_seconds": timeout_seconds,
    }


def verify_policy_with_grok(
    *,
    policy_summary: dict[str, Any],
    simulation_summary: dict[str, Any],
    mock_response: dict[str, Any] | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
    timeout_seconds: int = 60,
) -> GrokVerificationResult:
    if mock_response is not None:
        return _result_from_payload(mock_response, provider="mock", model="mock")

    config = resolve_grok_config(api_key=api_key, base_url=base_url, model=model, timeout_seconds=timeout_seconds)
    if not config["api_key"]:
        raise GrokVerifierError(
            f"Grok verification requires {GROK_API_KEY_ENV} or an explicit api_key."
        )

    prompt = _build_prompt(policy_summary, simulation_summary)
    payload = _call_grok_json(prompt, config)
    return _result_from_payload(payload, provider="grok", model=config["model"])


def _build_prompt(policy_summary: dict[str, Any], simulation_summary: dict[str, Any]) -> str:
    return (
        "You verify ForgeBench merge-risk policy behavior.\n"
        "Return JSON with keys: status (pass|fail|review), summary, obligations (array), "
        "satisfied (array), unsatisfied (array).\n"
        "Be conservative. Do not claim formal proof.\n\n"
        f"Policy summary:\n{json.dumps(policy_summary, indent=2)}\n\n"
        f"Simulation summary:\n{json.dumps(simulation_summary, indent=2)}"
    )


def _call_grok_json(prompt: str, config: dict[str, Any]) -> dict[str, Any]:
    endpoint = f"{config['base_url'].rstrip('/')}/chat/completions"
    body = json.dumps(
        {
            "model": config["model"],
            "messages": [
                {
                    "role": "system",
                    "content": "Return only valid JSON for policy verification.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
    ).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=config["timeout_seconds"]) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise GrokVerifierError(f"Grok API HTTP {exc.code}: {detail[:300]}") from exc
    except error.URLError as exc:
        raise GrokVerifierError(f"Grok API request failed: {exc.reason}") from exc
    except TimeoutError as exc:
        raise GrokVerifierError(f"Grok API timed out after {config['timeout_seconds']} seconds.") from exc

    envelope = json.loads(raw)
    choices = envelope.get("choices")
    if not isinstance(choices, list) or not choices:
        raise GrokVerifierError("Grok API response did not include choices.")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise GrokVerifierError("Grok API response did not include message content.")
    parsed = json.loads(_extract_json_object(content))
    if not isinstance(parsed, dict):
        raise GrokVerifierError("Grok verification JSON must be an object.")
    return parsed


def _result_from_payload(payload: dict[str, Any], *, provider: str, model: str) -> GrokVerificationResult:
    return GrokVerificationResult(
        status=str(payload.get("status") or "review"),
        summary=str(payload.get("summary") or ""),
        obligations=[str(item) for item in payload.get("obligations") or []],
        satisfied=[str(item) for item in payload.get("satisfied") or []],
        unsatisfied=[str(item) for item in payload.get("unsatisfied") or []],
        provider=provider,
        model=model,
        raw=payload,
    )


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise GrokVerifierError("Grok response did not contain a JSON object.")
    return text[start : end + 1]