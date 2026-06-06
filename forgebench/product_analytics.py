from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PRODUCT_ANALYTICS_ENV = "FORGEBENCH_PRODUCT_ANALYTICS"
PRODUCT_ANALYTICS_FLAG = Path("forgebench-output") / ".product-analytics-enabled"
PRODUCT_ANALYTICS_LOG = Path("forgebench-output") / "product-analytics.jsonl"
PRODUCT_ANALYTICS_SCHEMA = "0.1.0"

ALLOWED_PRODUCT_EVENTS = {
    "cli_command",
    "license_activated",
    "license_report_exported",
    "analytics_dashboard_exported",
    "analytics_cloud_export",
    "onboarding_completed",
    "extension_command",
    "milestone_reached",
    "funnel_stage",
}


class ProductAnalyticsError(ValueError):
    pass


def is_product_analytics_enabled() -> bool:
    if os.environ.get(PRODUCT_ANALYTICS_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return PRODUCT_ANALYTICS_FLAG.exists()


def enable_product_analytics(*, flag_path: str | Path | None = None) -> Path:
    path = Path(flag_path) if flag_path else PRODUCT_ANALYTICS_FLAG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "enabled": True,
                "enabled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "schema_version": PRODUCT_ANALYTICS_SCHEMA,
                "scope": "product_adoption",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def disable_product_analytics(*, flag_path: str | Path | None = None) -> None:
    path = Path(flag_path) if flag_path else PRODUCT_ANALYTICS_FLAG
    if path.exists():
        path.unlink()


def product_analytics_status(*, log_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(log_path) if log_path else PRODUCT_ANALYTICS_LOG
    count = 0
    if path.exists():
        count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return {
        "enabled": is_product_analytics_enabled(),
        "log_path": str(path),
        "event_count": count,
        "schema_version": PRODUCT_ANALYTICS_SCHEMA,
        "distinct_from_review_telemetry": True,
    }


def record_product_event(event_type: str, payload: dict[str, Any] | None = None) -> Path | None:
    if not is_product_analytics_enabled():
        return None
    normalized = event_type.strip()
    if normalized not in ALLOWED_PRODUCT_EVENTS:
        raise ProductAnalyticsError(f"Unsupported product analytics event: {event_type}")
    event = {
        "schema_version": PRODUCT_ANALYTICS_SCHEMA,
        "event_type": normalized,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "payload": _sanitize_product_payload(payload or {}),
    }
    PRODUCT_ANALYTICS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PRODUCT_ANALYTICS_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return PRODUCT_ANALYTICS_LOG


def export_product_analytics_bundle(*, log_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(log_path) if log_path else PRODUCT_ANALYTICS_LOG
    events: list[dict[str, Any]] = []
    malformed = 0
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if isinstance(item, dict):
                events.append(item)
    return {
        "export_version": 1,
        "schema_version": PRODUCT_ANALYTICS_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "opt_in": is_product_analytics_enabled(),
        "event_count": len(events),
        "malformed_lines": malformed,
        "events": events,
        "summary": summarize_product_events(events),
        "privacy_note": (
            "Product analytics is opt-in and separate from review telemetry. "
            "Records adoption metrics (commands, license events) without diff content. "
            "No automatic cloud upload."
        ),
    }


def summarize_product_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    commands: dict[str, int] = {}
    tiers: dict[str, int] = {}
    for event in events:
        event_type = str(event.get("event_type") or "unknown")
        counts[event_type] = counts.get(event_type, 0) + 1
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        command = str(payload.get("command") or "")
        if command:
            commands[command] = commands.get(command, 0) + 1
        tier = str(payload.get("tier") or "")
        if tier:
            tiers[tier] = tiers.get(tier, 0) + 1
    return {
        "event_counts": counts,
        "command_counts": commands,
        "tier_counts": tiers,
        "distinct_days": _distinct_days(events),
    }


def _distinct_days(events: list[dict[str, Any]]) -> int:
    days: set[str] = set()
    for event in events:
        ts = str(event.get("ts") or "")
        if len(ts) >= 10:
            days.add(ts[:10])
    return len(days)


def _sanitize_product_payload(payload: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for key, value in payload.items():
        lowered = str(key).lower()
        if any(marker in lowered for marker in ("path", "repo", "url", "email", "token", "secret", "key")):
            if isinstance(value, str) and value.strip():
                sanitized[f"{key}_hash"] = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
            continue
        if isinstance(value, dict):
            sanitized[key] = _sanitize_product_payload(value)
        elif isinstance(value, list):
            sanitized[key] = value[:20]
        elif isinstance(value, (int, float, bool)) or value is None:
            sanitized[key] = value
        else:
            sanitized[key] = str(value)[:200]
    return sanitized