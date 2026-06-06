from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_POLICY_AUDIT_LOG = Path("forgebench-output") / "policy-audit.jsonl"
AUDIT_SCHEMA_VERSION = "1.0.0"

ALLOWED_AUDIT_EVENTS = {
    "policy_loaded",
    "policy_compiled",
    "policy_version_recorded",
    "policy_simulated",
    "policy_test_run",
    "formal_verification",
    "grok_verification",
    "policy_served",
}


@dataclass(frozen=True)
class PolicyAuditStatus:
    log_path: Path
    event_count: int


class PolicyAuditError(ValueError):
    pass


def record_policy_audit_event(
    event_type: str,
    *,
    payload: dict[str, Any] | None = None,
    log_path: str | Path | None = None,
) -> Path:
    normalized = event_type.strip()
    if normalized not in ALLOWED_AUDIT_EVENTS:
        raise PolicyAuditError(f"Unsupported policy audit event type: {event_type}")
    path = Path(log_path) if log_path else DEFAULT_POLICY_AUDIT_LOG
    event = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "event_type": normalized,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "payload": payload or {},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return path


def policy_audit_status(*, log_path: str | Path | None = None) -> PolicyAuditStatus:
    path = Path(log_path) if log_path else DEFAULT_POLICY_AUDIT_LOG
    count = 0
    if path.exists():
        count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return PolicyAuditStatus(log_path=path, event_count=count)


def export_policy_audit_bundle(*, log_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(log_path) if log_path else DEFAULT_POLICY_AUDIT_LOG
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
        "schema_version": AUDIT_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event_count": len(events),
        "malformed_lines": malformed,
        "events": events,
    }


def summarize_policy_audit(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        event_type = str(event.get("event_type") or "unknown")
        counts[event_type] = counts.get(event_type, 0) + 1
    return counts