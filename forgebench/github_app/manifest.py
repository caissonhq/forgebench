from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


MANIFEST_SCHEMA_VERSION = "1.0.0"


def export_github_app_manifest(
    *,
    name: str = "ForgeBench",
    homepage_url: str = "https://forgebench.dev",
    webhook_url: str = "https://your-org.example.com/forgebench/github-app/webhook",
    setup_url: str = "https://forgebench.dev/docs/early-access",
) -> dict[str, Any]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "name": name,
        "description": (
            "Org-level merge-risk policy enforcement for AI-generated pull requests. "
            "Self-hosted webhook receiver; ForgeBench review runs in your infrastructure."
        ),
        "url": homepage_url,
        "hook_attributes": {"url": webhook_url, "active": True},
        "redirect_url": setup_url,
        "setup_url": setup_url,
        "public": False,
        "default_permissions": {
            "checks": "write",
            "pull_requests": "read",
            "metadata": "read",
            "contents": "read",
        },
        "permission_notes": (
            "Minimum scope: read PR metadata, write Check Runs. "
            "Org enforcement consumes verified Check Run conclusions or signed attestations — not PR write."
        ),
        "default_events": [
            "pull_request",
            "pull_request_review",
            "check_run",
            "organization",
        ],
        "request_oauth_on_install": False,
        "org_policy_enforcement": {
            "mode": "check_run_gate",
            "supported_postures": ["BLOCK", "REVIEW", "LOW_CONCERN"],
            "default_org_rules": {
                "block_on_posture": "BLOCK",
                "require_review_on_posture": "REVIEW",
                "allow_low_concern": True,
            },
        },
        "privacy_note": (
            "Deploy this app in your own environment. ForgeBench does not operate a hosted "
            "GitHub App for customer code review by default."
        ),
    }