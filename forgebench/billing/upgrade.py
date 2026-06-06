from __future__ import annotations

from forgebench.billing.config import hosted_portal_url, sales_email
from forgebench.licensing.tiers import FEATURE_MIN_TIER, LicenseTier, feature_requires_tier, tier_label


FEATURE_VALUE_MESSAGES: dict[str, str] = {
    "init_enterprise": "Org policy wizard, CI kit, and team onboarding docs",
    "org_policy": "Shared guardrails across repos with org policy layers",
    "policy_dashboard": "Exportable policy compliance dashboard",
    "policy_tests_ci": "Policy simulation tests in CI",
    "analytics_cloud_export": "Cloud analytics export for customer success reviews",
    "github_app_manifest": "Self-hosted GitHub App enforcement kit",
    "benchmark_dashboard": "Public benchmark dashboard export",
    "usage_reporting": "Usage and quota reports for your team",
    "policy_serve": "Self-hosted policy service for centralized guardrails",
    "github_app_serve": "GitHub App webhook enforcement server",
    "grok_verify": "Grok-assisted policy verification quota",
    "audit_chain": "Tamper-evident audit chain for compliance",
}


def format_upgrade_prompt(feature: str, *, current_tier: LicenseTier = LicenseTier.FREE) -> str:
    required = feature_requires_tier(feature) or LicenseTier.TEAM
    value = FEATURE_VALUE_MESSAGES.get(feature, f"Paid feature: {feature}")
    tier_name = tier_label(required)
    lines = [
        f"Upgrade required: {feature}",
        "",
        f"Value: {value}",
        f"Your tier: {tier_label(current_tier)} → needs {tier_name}",
        "",
        "Next steps:",
        f"  1. forgebench subscribe {tier_name}",
        f"  2. forgebench license activate FB-{tier_name.upper()}-...",
        f"  3. forgebench portal  # usage, quotas, invoices",
        "",
        f"Questions? {sales_email()}",
        f"Portal: {hosted_portal_url()}",
    ]
    return "\n".join(lines)


def upgrade_cta(feature: str) -> str:
    required = feature_requires_tier(feature) or LicenseTier.TEAM
    return f"Run `forgebench upgrade --tier {tier_label(required)}` or `forgebench subscribe {tier_label(required)}`"


def tier_comparison_summary() -> str:
    lines = ["ForgeBench tiers:", ""]
    lines.append("  FREE: core review + calibration (always free)")
    for tier in (LicenseTier.TEAM, LicenseTier.ENTERPRISE):
        features = [name for name, required in FEATURE_MIN_TIER.items() if int(required) <= int(tier)]
        lines.append(f"  {tier_label(tier).upper()}: +{len(features)} paid capabilities")
    lines.extend(["", "Details: docs/pricing.md", f"Subscribe: forgebench subscribe team"])
    return "\n".join(lines)