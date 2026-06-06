from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from forgebench.github_app.enforcement import (
    OrgEnforcementConfig,
    OrgPolicyEnforcementResult,
    enforce_org_policy,
    enforcement_to_check_output,
    load_org_enforcement_config,
)
from forgebench.policy_audit import record_policy_audit_event


@dataclass(frozen=True)
class WebhookHandleResult:
    event_type: str
    action: str | None
    handled: bool
    enforcement: OrgPolicyEnforcementResult | None = None
    check_output: dict[str, Any] | None = None
    message: str = ""


def verify_github_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    if not signature_header.startswith("sha256="):
        return False
    expected = signature_header.split("=", 1)[1]
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected)


def handle_github_webhook(
    payload: dict[str, Any],
    *,
    config_path: str | None = None,
    default_posture: str = "REVIEW",
    finding_count: int = 0,
    policy_fingerprint: str | None = None,
) -> WebhookHandleResult:
    event_type = str(payload.get("_event_type") or "unknown")
    action = str(payload.get("action") or "") or None

    if not _is_pull_request_payload(payload):
        return WebhookHandleResult(
            event_type=event_type or action or "unknown",
            action=action,
            handled=False,
            message="Unsupported event",
        )

    if config_path is None:
        return WebhookHandleResult(
            event_type="pull_request",
            action=action,
            handled=False,
            message="Org enforcement config not provided.",
        )

    config = load_org_enforcement_config(config_path)
    posture = _extract_posture(payload, default_posture=default_posture)
    enforcement = enforce_org_policy(
        posture=posture,
        config=config,
        policy_fingerprint=policy_fingerprint,
        finding_count=finding_count,
    )
    check_output = enforcement_to_check_output(enforcement)
    if config.audit_required:
        record_policy_audit_event(
            "policy_served",
            payload={
                "surface": "github_app_webhook",
                "org_id": config.org_id,
                "posture": enforcement.posture,
                "allowed": enforcement.allowed,
            },
        )
    return WebhookHandleResult(
        event_type="pull_request",
        action=action,
        handled=True,
        enforcement=enforcement,
        check_output=check_output,
        message="Org policy enforcement evaluated.",
    )


def _is_pull_request_payload(payload: dict[str, Any]) -> bool:
    if str(payload.get("_event_type") or "") == "pull_request":
        return True
    if payload.get("pull_request") is not None:
        return True
    return isinstance(payload.get("forgebench"), dict)


def _extract_posture(payload: dict[str, Any], *, default_posture: str) -> str:
    forgebench = payload.get("forgebench")
    if isinstance(forgebench, dict):
        posture = str(forgebench.get("posture") or "").strip().upper()
        if posture:
            return posture
    labels = payload.get("labels")
    if isinstance(labels, list):
        for label in labels:
            if not isinstance(label, dict):
                continue
            name = str(label.get("name") or "").upper()
            if name in {"BLOCK", "REVIEW", "LOW_CONCERN"}:
                return name
    return default_posture