from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from forgebench.licensing.keys import LicenseError, LicensePayload, verify_license_key
from forgebench.licensing.store import machine_id


DEFAULT_LICENSE_SERVER_URL = "http://127.0.0.1:8793"


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    source: str
    payload: LicensePayload | None
    message: str
    online_response: dict[str, Any] | None = None


def validate_license_offline(key: str) -> ValidationResult:
    try:
        payload = verify_license_key(key)
    except LicenseError as exc:
        return ValidationResult(valid=False, source="offline", payload=None, message=str(exc))
    return ValidationResult(valid=True, source="offline", payload=payload, message="License valid (offline).")


def validate_license_online(
    key: str,
    *,
    server_url: str | None = None,
    machine: str | None = None,
    timeout: int = 10,
) -> ValidationResult:
    offline = validate_license_offline(key)
    if not offline.valid:
        return offline
    base = (server_url or os.environ.get("FORGEBENCH_LICENSE_SERVER_URL") or DEFAULT_LICENSE_SERVER_URL).rstrip("/")
    body = json.dumps({"key": key, "machine_id": machine or machine_id()}).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/v1/license/validate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return ValidationResult(
            valid=False,
            source="online",
            payload=offline.payload,
            message=f"License server rejected key ({exc.code}): {detail}",
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return ValidationResult(
            valid=offline.valid,
            source="offline-fallback",
            payload=offline.payload,
            message=f"Online check unavailable ({exc}); offline validation passed.",
            online_response=None,
        )
    if not isinstance(payload, dict):
        return ValidationResult(valid=False, source="online", payload=offline.payload, message="Invalid license server response.")
    allowed = bool(payload.get("valid"))
    message = str(payload.get("message") or ("License valid (online)." if allowed else "License rejected by server."))
    return ValidationResult(
        valid=allowed,
        source="online",
        payload=offline.payload,
        message=message,
        online_response=payload,
    )


def validate_license(
    key: str,
    *,
    prefer_online: bool = False,
    server_url: str | None = None,
) -> ValidationResult:
    if prefer_online or os.environ.get("FORGEBENCH_LICENSE_ONLINE", "").strip() in {"1", "true", "yes"}:
        return validate_license_online(key, server_url=server_url)
    return validate_license_offline(key)