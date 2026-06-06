from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any

from forgebench.licensing.tiers import LicenseTier, parse_tier, tier_label


class LicenseError(ValueError):
    pass


LICENSE_PREFIX = "FB"
DEFAULT_LICENSE_SECRET = "forgebench-dev-license-secret-change-in-production"


@dataclass(frozen=True)
class LicensePayload:
    tier: LicenseTier
    organization: str
    seats: int
    expires_at: str
    features: list[str]
    license_id: str


def _license_secret() -> bytes:
    raw = os.environ.get("FORGEBENCH_LICENSE_SECRET", DEFAULT_LICENSE_SECRET)
    return raw.encode("utf-8")


def generate_license_key(
    *,
    tier: str,
    organization: str,
    seats: int = 10,
    expires_at: str | None = None,
    features: list[str] | None = None,
    license_id: str | None = None,
) -> str:
    tier_enum = parse_tier(tier)
    expiry = expires_at or _default_expiry()
    payload = {
        "tier": tier_label(tier_enum),
        "organization": organization,
        "seats": seats,
        "expires_at": expiry,
        "features": features or [],
        "license_id": license_id or _stable_id(organization, tier_label(tier_enum)),
    }
    body = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True).encode("utf-8")).decode("ascii").rstrip("=")
    signature = _sign(body)
    return f"{LICENSE_PREFIX}-{tier_label(tier_enum).upper()}-{body}.{signature}"


def verify_license_key(key: str) -> LicensePayload:
    normalized = key.strip()
    if not normalized.startswith(f"{LICENSE_PREFIX}-"):
        raise LicenseError("license key must start with FB-")
    parts = normalized.split("-", 2)
    if len(parts) < 3:
        raise LicenseError("malformed license key")
    body_and_sig = parts[2]
    if "." not in body_and_sig:
        raise LicenseError("license key missing signature")
    body, signature = body_and_sig.rsplit(".", 1)
    expected = _sign(body)
    if not hmac.compare_digest(signature, expected):
        raise LicenseError("license key signature is invalid")
    padded = body + "=" * (-len(body) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except (json.JSONDecodeError, ValueError) as exc:
        raise LicenseError(f"license payload decode failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise LicenseError("license payload must be an object")
    tier = parse_tier(str(payload.get("tier") or "free"))
    expires_at = str(payload.get("expires_at") or "")
    if not expires_at:
        raise LicenseError("license key missing expires_at")
    _ensure_not_expired(expires_at)
    seats = int(payload.get("seats") or 1)
    if seats < 1:
        raise LicenseError("license seats must be >= 1")
    return LicensePayload(
        tier=tier,
        organization=str(payload.get("organization") or "Unknown"),
        seats=seats,
        expires_at=expires_at,
        features=[str(item) for item in payload.get("features") or []],
        license_id=str(payload.get("license_id") or ""),
    )


def activate_license_key(key: str, *, machine_id: str) -> dict[str, Any]:
    payload = verify_license_key(key)
    return {
        "key": key,
        "tier": payload.tier.name.lower(),
        "organization": payload.organization,
        "seats": payload.seats,
        "expires_at": payload.expires_at,
        "features": payload.features,
        "license_id": payload.license_id,
        "activated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "machine_id": machine_id,
        "activations": [machine_id],
    }


def _sign(body: str) -> str:
    digest = hmac.new(_license_secret(), body.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:32]


def _stable_id(organization: str, tier: str) -> str:
    return hashlib.sha256(f"{organization}:{tier}".encode("utf-8")).hexdigest()[:12]


def _default_expiry() -> str:
    return date.today().replace(year=date.today().year + 1).isoformat()


def _ensure_not_expired(expires_at: str) -> None:
    try:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        expiry = datetime.strptime(expires_at, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if now > expiry:
        raise LicenseError(f"license expired on {expires_at}")