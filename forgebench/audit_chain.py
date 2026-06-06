from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.policy_audit import ALLOWED_AUDIT_EVENTS, PolicyAuditError


AUDIT_CHAIN_SCHEMA = "1.1.0"
DEFAULT_AUDIT_CHAIN_LOG = Path("forgebench-output") / "audit-chain.jsonl"
_CHAIN_HEAD_FILE = Path("forgebench-output") / ".audit-chain-head"


def record_tamper_evident_event(
    event_type: str,
    *,
    payload: dict[str, Any] | None = None,
    log_path: str | Path | None = None,
) -> Path:
    normalized = event_type.strip()
    if normalized not in ALLOWED_AUDIT_EVENTS:
        raise PolicyAuditError(f"Unsupported audit event type: {event_type}")
    path = Path(log_path) if log_path else DEFAULT_AUDIT_CHAIN_LOG
    prev_hash = _read_chain_head(path)
    event = {
        "schema_version": AUDIT_CHAIN_SCHEMA,
        "event_type": normalized,
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prev_hash": prev_hash,
        "payload": payload or {},
    }
    event_hash = _hash_event(event)
    event["hash"] = event_hash
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    _write_chain_head(path, event_hash)
    return path


def verify_audit_chain(*, log_path: str | Path | None = None) -> tuple[bool, list[str]]:
    path = Path(log_path) if log_path else DEFAULT_AUDIT_CHAIN_LOG
    errors: list[str] = []
    if not path.exists():
        return True, errors
    prev_hash = "0" * 64
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"line {line_number}: invalid JSON")
            continue
        if not isinstance(event, dict):
            errors.append(f"line {line_number}: not an object")
            continue
        if event.get("prev_hash") != prev_hash:
            errors.append(f"line {line_number}: prev_hash mismatch (possible tampering)")
        stored_hash = str(event.get("hash") or "")
        body = {key: value for key, value in event.items() if key != "hash"}
        expected = _hash_event(body)
        if stored_hash != expected:
            errors.append(f"line {line_number}: hash mismatch (possible tampering)")
        prev_hash = stored_hash
    return not errors, errors


def _hash_event(event: dict[str, Any]) -> str:
    canonical = json.dumps(event, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _read_chain_head(path: Path) -> str:
    head_path = path.parent / f".{path.name}.head"
    if head_path.exists():
        return head_path.read_text(encoding="utf-8").strip() or ("0" * 64)
    return "0" * 64


def _write_chain_head(path: Path, head_hash: str) -> None:
    head_path = path.parent / f".{path.name}.head"
    head_path.write_text(head_hash + "\n", encoding="utf-8")