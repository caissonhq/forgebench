from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from forgebench.feedback import DEFAULT_FEEDBACK_LOG
from forgebench.telemetry import TELEMETRY_LOG


@dataclass(frozen=True)
class RetentionResult:
    path: Path
    kept: int
    deleted: int
    purged_file: bool


def purge_jsonl_older_than(
    path: Path,
    *,
    max_age_days: int,
    dry_run: bool = False,
) -> RetentionResult:
    if max_age_days < 1:
        raise ValueError("max_age_days must be at least 1.")
    if not path.exists():
        return RetentionResult(path=path, kept=0, deleted=0, purged_file=False)
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    kept_lines: list[str] = []
    deleted = 0
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            kept_lines.append(line)
            continue
        ts = _parse_ts(payload.get("ts"))
        if ts is not None and ts < cutoff:
            deleted += 1
            continue
        kept_lines.append(line)
    if not dry_run:
        if kept_lines:
            path.write_text("\n".join(kept_lines) + "\n", encoding="utf-8")
        else:
            path.unlink(missing_ok=True)
    return RetentionResult(path=path, kept=len(kept_lines), deleted=deleted, purged_file=not kept_lines)


def apply_data_retention_policy(
    *,
    max_age_days: int = 90,
    dry_run: bool = False,
) -> dict[str, Any]:
    results = {
        "telemetry": purge_jsonl_older_than(TELEMETRY_LOG, max_age_days=max_age_days, dry_run=dry_run),
        "feedback": purge_jsonl_older_than(DEFAULT_FEEDBACK_LOG, max_age_days=max_age_days, dry_run=dry_run),
    }
    return {
        "max_age_days": max_age_days,
        "dry_run": dry_run,
        "results": {
            key: {
                "path": str(value.path),
                "kept": value.kept,
                "deleted": value.deleted,
                "purged_file": value.purged_file,
            }
            for key, value in results.items()
        },
    }


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed