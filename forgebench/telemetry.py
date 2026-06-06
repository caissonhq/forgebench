from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.feedback import DEFAULT_FEEDBACK_LOG


TELEMETRY_ENV = "FORGEBENCH_TELEMETRY"
TELEMETRY_LOG = Path("forgebench-output") / "telemetry.jsonl"
TELEMETRY_FLAG = Path("forgebench-output") / ".telemetry-enabled"
TELEMETRY_SCHEMA_VERSION = "0.1.0"

SENSITIVE_KEY_MARKERS = ("path", "repo", "url", "author", "email", "token", "key", "secret")
ALLOWED_EVENT_TYPES = {
    "review_completed",
    "feedback_recorded",
    "benchmark_run",
    "dashboard_exported",
}


class TelemetryError(ValueError):
    pass


@dataclass(frozen=True)
class TelemetryStatus:
    enabled: bool
    log_path: Path
    event_count: int


def is_telemetry_enabled() -> bool:
    if os.environ.get(TELEMETRY_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return TELEMETRY_FLAG.exists()


def enable_telemetry(*, flag_path: str | Path | None = None) -> Path:
    path = Path(flag_path) if flag_path else TELEMETRY_FLAG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "enabled": True,
                "enabled_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "schema_version": TELEMETRY_SCHEMA_VERSION,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def disable_telemetry(*, flag_path: str | Path | None = None) -> None:
    path = Path(flag_path) if flag_path else TELEMETRY_FLAG
    if path.exists():
        path.unlink()


def telemetry_status(*, log_path: str | Path | None = None) -> TelemetryStatus:
    path = Path(log_path) if log_path else TELEMETRY_LOG
    count = 0
    if path.exists():
        count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return TelemetryStatus(enabled=is_telemetry_enabled(), log_path=path, event_count=count)


def record_telemetry_event(event_type: str, payload: dict[str, Any] | None = None) -> Path | None:
    if not is_telemetry_enabled():
        return None
    normalized_type = event_type.strip()
    if normalized_type not in ALLOWED_EVENT_TYPES:
        raise TelemetryError(f"Unsupported telemetry event type: {event_type}")

    event = {
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "event_type": normalized_type,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "payload": anonymize_payload(payload or {}),
    }
    TELEMETRY_LOG.parent.mkdir(parents=True, exist_ok=True)
    with TELEMETRY_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return TELEMETRY_LOG


def anonymize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    anonymized: dict[str, Any] = {}
    for key, value in payload.items():
        lowered = str(key).lower()
        if any(marker in lowered for marker in SENSITIVE_KEY_MARKERS):
            if isinstance(value, str) and value.strip():
                anonymized[f"{key}_hash"] = _stable_hash(value.strip())
            continue
        if isinstance(value, dict):
            anonymized[key] = anonymize_payload(value)
        elif isinstance(value, list):
            anonymized[key] = [_anonymize_list_item(item) for item in value]
        else:
            anonymized[key] = _sanitize_scalar(value)
    return anonymized


def export_telemetry_bundle(*, log_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(log_path) if log_path else TELEMETRY_LOG
    events: list[dict[str, Any]] = []
    malformed = 0
    if path.exists():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if isinstance(payload, dict):
                events.append(payload)

    return {
        "export_version": 1,
        "schema_version": TELEMETRY_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "opt_in": is_telemetry_enabled(),
        "event_count": len(events),
        "malformed_lines": malformed,
        "events": events,
        "privacy_note": (
            "ForgeBench telemetry is opt-in, local-only, and anonymized. "
            "No network upload is performed automatically. Share exports manually if desired."
        ),
    }


def summarize_telemetry_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    event_counts: dict[str, int] = {}
    posture_counts: dict[str, int] = {}
    agent_counts: dict[str, int] = {}
    for event in events:
        event_type = str(event.get("event_type") or "unknown")
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        posture = str(payload.get("posture") or "")
        if posture:
            posture_counts[posture] = posture_counts.get(posture, 0) + 1
        agent = str(payload.get("agent_tool") or "")
        if agent:
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
    return {
        "event_counts": event_counts,
        "posture_counts": posture_counts,
        "agent_counts": agent_counts,
    }


def _anonymize_list_item(item: Any) -> Any:
    if isinstance(item, dict):
        return anonymize_payload(item)
    if isinstance(item, str):
        return _redact_path_like(item)
    return _sanitize_scalar(item)


def _sanitize_scalar(value: Any) -> Any:
    if isinstance(value, str):
        return _redact_path_like(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)


def _redact_path_like(value: str) -> str:
    if "/" in value or "\\" in value:
        return "<redacted-path>"
    if re.search(r"@|api[_-]?key|token|secret", value, re.IGNORECASE):
        return "<redacted-secret>"
    return value


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]