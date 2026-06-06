from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


FORGEBENCH_CHECK_NAME = "ForgeBench"
VALID_POSTURES = {"BLOCK", "REVIEW", "LOW_CONCERN"}


class AttestationError(ValueError):
    pass


def posture_from_check_run_payload(payload: dict[str, Any]) -> str | None:
    check_run = payload.get("check_run")
    if not isinstance(check_run, dict):
        return None
    if str(check_run.get("name") or "").strip() != FORGEBENCH_CHECK_NAME:
        return None
    output = check_run.get("output") if isinstance(check_run.get("output"), dict) else {}
    title = str(output.get("title") or "")
    for posture in VALID_POSTURES:
        if posture in title.upper():
            return posture
    conclusion = str(check_run.get("conclusion") or "").lower()
    if conclusion == "failure":
        return "BLOCK"
    if conclusion == "neutral":
        return "REVIEW"
    if conclusion == "success":
        return "LOW_CONCERN"
    return None


def verify_signed_attestation(
    *,
    secret: str,
    signature_header: str,
    org_id: str,
    pr_number: int,
    head_sha: str,
    posture: str,
    policy_fingerprint: str | None,
) -> bool:
    if not signature_header.startswith("sha256="):
        return False
    expected = signature_header.split("=", 1)[1]
    canonical = _attestation_canonical(
        org_id=org_id,
        pr_number=pr_number,
        head_sha=head_sha,
        posture=posture,
        policy_fingerprint=policy_fingerprint,
    )
    digest = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected)


def sign_attestation(
    *,
    secret: str,
    org_id: str,
    pr_number: int,
    head_sha: str,
    posture: str,
    policy_fingerprint: str | None,
) -> str:
    canonical = _attestation_canonical(
        org_id=org_id,
        pr_number=pr_number,
        head_sha=head_sha,
        posture=posture,
        policy_fingerprint=policy_fingerprint,
    )
    digest = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _attestation_canonical(
    *,
    org_id: str,
    pr_number: int,
    head_sha: str,
    posture: str,
    policy_fingerprint: str | None,
) -> str:
    normalized_posture = posture.strip().upper()
    if normalized_posture not in VALID_POSTURES:
        raise AttestationError(f"Unsupported posture for attestation: {posture}")
    body = {
        "org_id": org_id,
        "pr_number": pr_number,
        "head_sha": head_sha,
        "posture": normalized_posture,
        "policy_fingerprint": policy_fingerprint or "",
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"))