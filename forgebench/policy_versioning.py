from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_VERSION_MANIFEST = Path("forgebench-output") / "policy-versions.jsonl"
POLICY_VERSION_SCHEMA = "1.0.0"


@dataclass(frozen=True)
class PolicyVersionRecord:
    policy_id: str
    version: str
    fingerprint: str
    source_path: str
    recorded_at: str
    parent_version: str | None = None
    change_summary: str = ""


def fingerprint_policy_payload(payload: dict[str, Any]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load_policy_text_fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_version_history(manifest_path: str | Path | None = None) -> list[PolicyVersionRecord]:
    path = Path(manifest_path) if manifest_path else DEFAULT_VERSION_MANIFEST
    if not path.exists():
        return []
    records: list[PolicyVersionRecord] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        records.append(
            PolicyVersionRecord(
                policy_id=str(payload.get("policy_id") or ""),
                version=str(payload.get("version") or ""),
                fingerprint=str(payload.get("fingerprint") or ""),
                source_path=str(payload.get("source_path") or ""),
                recorded_at=str(payload.get("recorded_at") or ""),
                parent_version=_optional_str(payload.get("parent_version")),
                change_summary=str(payload.get("change_summary") or ""),
            )
        )
    return records


def record_policy_version(
    *,
    policy_id: str,
    version: str,
    fingerprint: str,
    source_path: str | Path,
    manifest_path: str | Path | None = None,
    parent_version: str | None = None,
    change_summary: str = "",
) -> PolicyVersionRecord:
    record = PolicyVersionRecord(
        policy_id=policy_id,
        version=version,
        fingerprint=fingerprint,
        source_path=str(source_path),
        recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        parent_version=parent_version,
        change_summary=change_summary,
    )
    path = Path(manifest_path) if manifest_path else DEFAULT_VERSION_MANIFEST
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.__dict__, sort_keys=True) + "\n")
    return record


def resolve_policy_version(
    payload: dict[str, Any],
    *,
    source_path: str | Path,
    explicit_version: str | None = None,
) -> tuple[str, str]:
    version = explicit_version or _optional_str(payload.get("policy_version")) or _optional_str(payload.get("fpl_version")) or "0.0.0"
    policy_id = _optional_str(payload.get("fpl_name")) or _optional_str(payload.get("project")) or Path(source_path).stem
    fingerprint = fingerprint_policy_payload(payload)
    return policy_id, f"{policy_id}@{version}:{fingerprint[:12]}"


def bump_policy_version(current: str) -> str:
    parts = current.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        return "1.0.0"
    major, minor, patch = (int(part) for part in parts)
    return f"{major}.{minor}.{patch + 1}"


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None