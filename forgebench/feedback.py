from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


DEFAULT_FEEDBACK_LOG = Path("forgebench-output") / "feedback.jsonl"
VALID_FEEDBACK_STATUSES = {"accepted", "dismissed", "wrong"}


class FeedbackError(ValueError):
    pass


@dataclass(frozen=True)
class FeedbackSummary:
    total: int = 0
    status_counts: dict[str, int] = field(default_factory=dict)
    kind_counts: dict[str, Counter[str]] = field(default_factory=dict)
    missing_kind_count: int = 0
    malformed_count: int = 0


def append_feedback(
    uid: str,
    *,
    status: str,
    note: str | None = None,
    feedback_log: str | Path | None = None,
    kind: str | None = None,
    repo_name: str | None = None,
    source: str | None = None,
) -> Path:
    normalized_uid = uid.strip()
    if not normalized_uid:
        raise FeedbackError("finding UID is required.")
    if status not in VALID_FEEDBACK_STATUSES:
        raise FeedbackError("status must be one of: accepted, dismissed, wrong.")

    path = Path(feedback_log) if feedback_log else DEFAULT_FEEDBACK_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "uid": normalized_uid,
        "status": status,
        "note": note or "",
        "ts": datetime.now(timezone.utc).isoformat(),
        "fb_version": 1,
    }
    if kind:
        payload["kind"] = kind
    if repo_name:
        payload["repo"] = repo_name
    if source:
        payload["source"] = source

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return path


def summarize_feedback(feedback_logs: list[str | Path]) -> FeedbackSummary:
    status_counts: Counter[str] = Counter()
    kind_counts: dict[str, Counter[str]] = {
        "accepted": Counter(),
        "dismissed": Counter(),
        "wrong": Counter(),
    }
    total = 0
    missing_kind_count = 0
    malformed_count = 0

    for log_path in feedback_logs:
        path = Path(log_path)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                malformed_count += 1
                continue
            status = str(payload.get("status") or "")
            if status not in VALID_FEEDBACK_STATUSES:
                malformed_count += 1
                continue
            total += 1
            status_counts[status] += 1
            kind = str(payload.get("kind") or "").strip()
            if kind:
                kind_counts[status][kind] += 1
            else:
                missing_kind_count += 1

    return FeedbackSummary(
        total=total,
        status_counts={status: status_counts.get(status, 0) for status in sorted(VALID_FEEDBACK_STATUSES)},
        kind_counts=kind_counts,
        missing_kind_count=missing_kind_count,
        malformed_count=malformed_count,
    )


def format_feedback_summary(summary: FeedbackSummary) -> str:
    lines = [
        "ForgeBench feedback summary",
        "",
        f"Total entries: {summary.total}",
        f"accepted: {summary.status_counts.get('accepted', 0)}",
        f"dismissed: {summary.status_counts.get('dismissed', 0)}",
        f"wrong: {summary.status_counts.get('wrong', 0)}",
    ]
    kind_totals: Counter[str] = Counter()
    for counter in summary.kind_counts.values():
        kind_totals.update(counter)
    if kind_totals:
        lines.extend(["", "Counts by kind:"])
        for kind, count in kind_totals.most_common():
            lines.append(f"- {kind}: {count}")
    if summary.missing_kind_count:
        lines.append(f"Entries missing kind: {summary.missing_kind_count}")
    if summary.malformed_count:
        lines.append(f"Malformed entries skipped: {summary.malformed_count}")
    return "\n".join(lines)
