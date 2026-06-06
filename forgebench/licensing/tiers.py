from __future__ import annotations

from enum import IntEnum


class LicenseTier(IntEnum):
    FREE = 0
    TEAM = 1
    ENTERPRISE = 2


TIER_FEATURES: dict[LicenseTier, frozenset[str]] = {
    LicenseTier.FREE: frozenset(
        {
            "review",
            "review_pr",
            "calibrate",
            "benchmark",
            "doctor",
            "demo",
            "status",
            "init",
            "repair",
            "mcp",
            "validate",
            "telemetry",
            "analytics_dashboard",
        }
    ),
    LicenseTier.TEAM: frozenset(
        {
            "init_enterprise",
            "org_policy",
            "policy_dashboard",
            "policy_tests_ci",
            "analytics_cloud_export",
            "github_app_manifest",
            "benchmark_dashboard",
            "usage_reporting",
        }
    ),
    LicenseTier.ENTERPRISE: frozenset(
        {
            "policy_serve",
            "github_app_serve",
            "grok_verify",
            "audit_chain",
            "usage_reporting",
            "unlimited_seats",
        }
    ),
}

FEATURE_MIN_TIER: dict[str, LicenseTier] = {}
for tier in (LicenseTier.TEAM, LicenseTier.ENTERPRISE):
    for feature in TIER_FEATURES[tier]:
        FEATURE_MIN_TIER[feature] = tier


def tier_at_least(current: LicenseTier, required: LicenseTier) -> bool:
    return int(current) >= int(required)


def feature_requires_tier(feature: str) -> LicenseTier | None:
    return FEATURE_MIN_TIER.get(feature)


def tier_label(tier: LicenseTier) -> str:
    return {LicenseTier.FREE: "free", LicenseTier.TEAM: "team", LicenseTier.ENTERPRISE: "enterprise"}[tier]


def parse_tier(value: str) -> LicenseTier:
    normalized = value.strip().lower()
    if normalized in {"free", "open"}:
        return LicenseTier.FREE
    if normalized == "team":
        return LicenseTier.TEAM
    if normalized == "enterprise":
        return LicenseTier.ENTERPRISE
    raise ValueError(f"unknown license tier: {value}")