from __future__ import annotations

import os
import re
from dataclasses import dataclass


class SecretValidationError(ValueError):
    pass


_PLACEHOLDER_RE = re.compile(r"(?i)(changeme|replace[-_]?me|your[-_]?|example|xxx|<.*>)")
_MIN_TOKEN_LEN = 16


@dataclass(frozen=True)
class SecretCheck:
    name: str
    present: bool
    valid: bool
    message: str


def validate_runtime_secrets(*, require_webhook_secret: bool = False) -> list[SecretCheck]:
    checks: list[SecretCheck] = []
    if require_webhook_secret:
        checks.append(_check_required_secret("FORGEBENCH_GITHUB_WEBHOOK_SECRET"))
    for env_name in (
        "FORGEBENCH_POLICY_ADMIN_TOKEN",
        "FORGEBENCH_POLICY_READONLY_TOKEN",
        "FORGEBENCH_LLM_API_KEY",
        "FORGEBENCH_GROK_API_KEY",
    ):
        value = os.environ.get(env_name, "").strip()
        if value:
            checks.append(_check_optional_secret(env_name, value))
    return checks


def require_webhook_secret() -> str:
    value = os.environ.get("FORGEBENCH_GITHUB_WEBHOOK_SECRET", "").strip()
    if not value:
        raise SecretValidationError(
            "FORGEBENCH_GITHUB_WEBHOOK_SECRET is required for GitHub App webhook service."
        )
    _reject_placeholder("FORGEBENCH_GITHUB_WEBHOOK_SECRET", value)
    if len(value) < _MIN_TOKEN_LEN:
        raise SecretValidationError("FORGEBENCH_GITHUB_WEBHOOK_SECRET must be at least 16 characters.")
    return value


def _check_required_secret(env_name: str) -> SecretCheck:
    value = os.environ.get(env_name, "").strip()
    if not value:
        return SecretCheck(env_name, present=False, valid=False, message="missing")
    try:
        _reject_placeholder(env_name, value)
    except SecretValidationError as exc:
        return SecretCheck(env_name, present=True, valid=False, message=str(exc))
    if len(value) < _MIN_TOKEN_LEN:
        return SecretCheck(env_name, present=True, valid=False, message="too short")
    return SecretCheck(env_name, present=True, valid=True, message="ok")


def _check_optional_secret(env_name: str, value: str) -> SecretCheck:
    try:
        _reject_placeholder(env_name, value)
    except SecretValidationError as exc:
        return SecretCheck(env_name, present=True, valid=False, message=str(exc))
    if len(value) < _MIN_TOKEN_LEN:
        return SecretCheck(env_name, present=True, valid=False, message="too short")
    return SecretCheck(env_name, present=True, valid=True, message="ok")


def _reject_placeholder(env_name: str, value: str) -> None:
    if _PLACEHOLDER_RE.search(value):
        raise SecretValidationError(f"{env_name} appears to contain a placeholder value.")