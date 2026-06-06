from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from forgebench.github_app.attestation import (
    posture_from_check_run_payload,
    verify_signed_attestation,
)
from forgebench.github_app.enforcement import (
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
    webhook_secret: str = "",
    attestation_signature: str | None = None,
    default_posture: str = "REVIEW",
    finding_count: int = 0,
    policy_fingerprint: str | None = None,
) -> WebhookHandleResult:
    event_type = str(payload.get("_event_type") or "unknown")
    action = str(payload.get("action") or "") or None

    if config_path is None:
        return WebhookHandleResult(
            event_type=event_type,
            action=action,
            handled=False,
            message="Org enforcement config not provided.",
        )

    posture_result = _resolve_trusted_posture(
        payload,
        event_type=event_type,
        webhook_secret=webhook_secret,
        attestation_signature=attestation_signature,
        policy_fingerprint=policy_fingerprint,
        default_posture=default_posture,
    )
    if posture_result is None:
        return WebhookHandleResult(
            event_type=event_type,
            action=action,
            handled=False,
            message="No trusted ForgeBench posture source in webhook payload.",
        )

    posture, source = posture_result
    config = load_org_enforcement_config(config_path)
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
                "posture_source": source,
            },
        )
    return WebhookHandleResult(
        event_type=event_type,
        action=action,
        handled=True,
        enforcement=enforcement,
        check_output=check_output,
        message=f"Org policy enforcement evaluated from {source}.",
    )


def _resolve_trusted_posture(
    payload: dict[str, Any],
    *,
    event_type: str,
    webhook_secret: str,
    attestation_signature: str | None,
    policy_fingerprint: str | None,
    default_posture: str,
) -> tuple[str, str] | None:
    if event_type == "check_run":
        posture = posture_from_check_run_payload(payload)
        if posture:
            return posture, "github_check_run"
        return None

    attestation = payload.get("forgebench_attestation")
    if isinstance(attestation, dict) and webhook_secret and attestation_signature:
        org_id = str(attestation.get("org_id") or "").strip()
        pr_number = _optional_int(attestation.get("pr_number"))
        head_sha = str(attestation.get("head_sha") or "").strip()
        posture = str(attestation.get("posture") or "").strip().upper()
        fingerprint = str(attestation.get("policy_fingerprint") or policy_fingerprint or "").strip() or None
        if org_id and pr_number is not None and head_sha and posture:
            if verify_signed_attestation(
                secret=webhook_secret,
                signature_header=attestation_signature,
                org_id=org_id,
                pr_number=pr_number,
                head_sha=head_sha,
                posture=posture,
                policy_fingerprint=fingerprint,
            ):
                return posture, "signed_attestation"
    return None


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None