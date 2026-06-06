from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.licensing.store import LicenseRecord, effective_tier, has_feature, load_license
from forgebench.licensing.tiers import LicenseTier, feature_requires_tier, tier_at_least


class QuotaExceeded(PermissionError):
    pass


class LicenseRequired(PermissionError):
    pass


QUOTA_PATH = Path("forgebench-output") / "quota-usage.json"

DEFAULT_DAILY_LIMITS: dict[LicenseTier, dict[str, int]] = {
    LicenseTier.FREE: {
        "grok_verify": 0,
        "policy_serve_requests": 0,
        "analytics_cloud_export": 0,
    },
    LicenseTier.TEAM: {
        "grok_verify": 50,
        "policy_serve_requests": 0,
        "analytics_cloud_export": 10,
    },
    LicenseTier.ENTERPRISE: {
        "grok_verify": 1000,
        "policy_serve_requests": 100_000,
        "analytics_cloud_export": 1000,
    },
}


@dataclass(frozen=True)
class QuotaStatus:
    quota_name: str
    used: int
    limit: int
    remaining: int
    tier: str


def require_feature(feature: str, *, record: LicenseRecord | None = None) -> LicenseRecord:
    current = record or load_license()
    if not current.valid and feature_requires_tier(feature) is not None:
        raise LicenseRequired(
            f"Feature '{feature}' requires a valid Team or Enterprise license. "
            "Run: forgebench license activate <KEY>"
        )
    if not has_feature(feature, record=current):
        required = feature_requires_tier(feature)
        raise LicenseRequired(
            f"Feature '{feature}' requires {required.name.lower() if required else 'team'} tier or higher. "
            "See docs/pricing.md"
        )
    _record_paid_feature_milestone(current)
    return current


def _record_paid_feature_milestone(record: LicenseRecord) -> None:
    try:
        from forgebench.adoption import record_milestone

        if record.valid and tier_at_least(effective_tier(record), LicenseTier.TEAM):
            record_milestone("first_paid_feature")
    except Exception:
        pass


def check_quota(quota_name: str, *, amount: int = 1, record: LicenseRecord | None = None) -> QuotaStatus:
    tier = effective_tier(record)
    limits = DEFAULT_DAILY_LIMITS.get(tier, DEFAULT_DAILY_LIMITS[LicenseTier.FREE])
    limit = int(limits.get(quota_name, 0))
    used = _read_usage(quota_name)
    remaining = max(0, limit - used)
    return QuotaStatus(
        quota_name=quota_name,
        used=used,
        limit=limit,
        remaining=remaining,
        tier=tier.name.lower(),
    )


def consume_quota(quota_name: str, *, amount: int = 1, record: LicenseRecord | None = None) -> QuotaStatus:
    status = check_quota(quota_name, amount=amount, record=record)
    if status.limit <= 0:
        raise QuotaExceeded(
            f"Quota '{quota_name}' is not available on {status.tier} tier. Upgrade at docs/pricing.md"
        )
    if status.used + amount > status.limit:
        raise QuotaExceeded(
            f"Daily quota exceeded for '{quota_name}' ({status.used}/{status.limit}). Resets at UTC midnight."
        )
    _write_usage(quota_name, status.used + amount)
    return check_quota(quota_name, record=record)


def export_quota_report() -> dict[str, Any]:
    tier = effective_tier()
    limits = DEFAULT_DAILY_LIMITS.get(tier, DEFAULT_DAILY_LIMITS[LicenseTier.FREE])
    quotas = {name: check_quota(name).__dict__ for name in limits}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tier": tier.name.lower(),
        "quotas": quotas,
    }


def _read_usage(quota_name: str) -> int:
    payload = _load_quota_file()
    today = date.today().isoformat()
    day_bucket = payload.get(today) if isinstance(payload.get(today), dict) else {}
    return int(day_bucket.get(quota_name, 0))


def _write_usage(quota_name: str, value: int) -> None:
    payload = _load_quota_file()
    today = date.today().isoformat()
    day_bucket = payload.get(today) if isinstance(payload.get(today), dict) else {}
    day_bucket[quota_name] = value
    payload[today] = day_bucket
    QUOTA_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUOTA_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_quota_file() -> dict[str, Any]:
    if not QUOTA_PATH.exists():
        return {}
    try:
        payload = json.loads(QUOTA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}