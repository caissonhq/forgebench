from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import re
from pathlib import Path
from typing import Any

from forgebench.feedback import DEFAULT_FEEDBACK_LOG, VALID_FEEDBACK_STATUSES, summarize_feedback
from forgebench.feedback_triage import compute_feedback_health, enrich_entry, infer_priority, priority_label


@dataclass(frozen=True)
class PrioritizedInsight:
    title: str
    detail: str
    priority: str
    category: str
    source_count: int
    suggested_action: str


@dataclass(frozen=True)
class FeedbackDigest:
    period_days: int
    period_label: str
    total_entries: int
    status_counts: dict[str, int]
    kind_counts: dict[str, int]
    top_kinds: list[tuple[str, int]]
    recent_notes: list[str]
    roadmap_candidates: list[str]
    prioritized_insights: list[PrioritizedInsight]
    health: dict[str, Any]
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))


def parse_period(period: str) -> int:
    normalized = period.strip().lower()
    match = re.fullmatch(r"(\d+)\s*([dwm])", normalized)
    if match:
        value, unit = int(match.group(1)), match.group(2)
        if unit == "d":
            return max(value, 1)
        if unit == "w":
            return max(value * 7, 1)
        if unit == "m":
            return max(value * 30, 1)
    if normalized.isdigit():
        return max(int(normalized), 1)
    return 7


def build_feedback_digest(
    feedback_logs: list[str | Path] | None = None,
    *,
    days: int | None = None,
    period: str | None = None,
) -> FeedbackDigest:
    period_days = days if days is not None else parse_period(period or "7d")
    period_label = period or f"{period_days}d"
    logs = [Path(item) for item in (feedback_logs or [DEFAULT_FEEDBACK_LOG])]
    cutoff = datetime.now(timezone.utc) - timedelta(days=max(period_days, 1))
    entries = _entries_since(logs, cutoff)
    enriched = [_enrich(e, entries) for e in entries]
    summary = summarize_feedback(logs)
    kind_totals: Counter[str] = Counter()
    for counter in summary.kind_counts.values():
        kind_totals.update(counter)
    recent_notes = [
        str(entry.get("note") or "").strip()
        for entry in entries[-10:]
        if str(entry.get("note") or "").strip()
    ]
    roadmap_candidates = _roadmap_candidates(enriched)
    prioritized = _prioritized_insights(enriched)
    health = compute_feedback_health(enriched)
    return FeedbackDigest(
        period_days=period_days,
        period_label=period_label,
        total_entries=len(entries),
        status_counts={status: sum(1 for e in entries if e.get("status") == status) for status in VALID_FEEDBACK_STATUSES},
        kind_counts=dict(kind_totals),
        top_kinds=kind_totals.most_common(5),
        recent_notes=recent_notes,
        roadmap_candidates=roadmap_candidates,
        prioritized_insights=prioritized,
        health=health,
    )


def format_feedback_digest(digest: FeedbackDigest) -> str:
    lines = [
        f"ForgeBench feedback digest — period {digest.period_label}",
        f"Generated: {digest.generated_at}",
        "",
        f"Entries in period: {digest.total_entries}",
        f"accepted: {digest.status_counts.get('accepted', 0)}",
        f"dismissed: {digest.status_counts.get('dismissed', 0)}",
        f"wrong: {digest.status_counts.get('wrong', 0)}",
        "",
        "Health metrics:",
        f"  false_positive_rate: {digest.health.get('false_positive_rate', 0)}",
        f"  resolution_rate: {digest.health.get('resolution_rate', 0)}",
        f"  sentiment_score: {digest.health.get('sentiment_score', 0)}",
    ]
    if digest.health.get("avg_nps") is not None:
        lines.append(f"  avg_nps: {digest.health.get('avg_nps')}")
    triage = digest.health.get("triage_counts") or {}
    if triage:
        lines.append(f"  triage: critical={triage.get('critical', 0)} high={triage.get('high', 0)} medium={triage.get('medium', 0)} low={triage.get('low', 0)}")
    if digest.prioritized_insights:
        lines.extend(["", "Prioritized insights:"])
        for insight in digest.prioritized_insights:
            lines.append(f"  [{priority_label(insight.priority)}] {insight.title}")
            lines.append(f"      {insight.detail}")
            lines.append(f"      → {insight.suggested_action}")
    if digest.top_kinds:
        lines.extend(["", "Top finding kinds:"])
        for kind, count in digest.top_kinds:
            lines.append(f"  - {kind}: {count}")
    if digest.roadmap_candidates:
        lines.extend(["", "Suggested roadmap items:"])
        for item in digest.roadmap_candidates:
            lines.append(f"  - {item}")
    if digest.recent_notes:
        lines.extend(["", "Recent notes:"])
        for note in digest.recent_notes[:5]:
            lines.append(f"  • {note}")
    lines.extend(
        [
            "",
            "Next steps:",
            "  forgebench feedback promote --uid FINDING_UID",
            "  forgebench roadmap update --period " + digest.period_label,
            "  forgebench weekly-review --period " + digest.period_label,
            "  forgebench feedback --suggest-guardrails",
        ]
    )
    return "\n".join(lines)


def _enrich(entry: dict[str, Any], all_entries: list[dict[str, Any]]) -> dict[str, Any]:
    kind_freq: Counter[str] = Counter()
    for item in all_entries:
        kind = str(item.get("kind") or "").strip()
        if kind and str(item.get("status") or "") in {"dismissed", "wrong"}:
            kind_freq[kind] += 1
    return enrich_entry(entry, kind_frequency=kind_freq)


def _prioritized_insights(entries: list[dict[str, Any]]) -> list[PrioritizedInsight]:
    insights: list[PrioritizedInsight] = []
    by_kind: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    for entry in entries:
        enriched = enrich_entry(entry)
        kind = str(entry.get("kind") or "").strip()
        if kind:
            by_kind[kind] += 1
        by_category[str(enriched.get("category") or "other")] += 1

    for kind, count in by_kind.most_common(5):
        sample = next((e for e in entries if str(e.get("kind") or "") == kind), {})
        triage = infer_priority(sample, kind_frequency=by_kind)
        if triage.priority in {"critical", "high", "medium"}:
            insights.append(
                PrioritizedInsight(
                    title=f"Calibrate `{kind}` findings",
                    detail=f"{count} feedback entries · {triage.rationale}",
                    priority=triage.priority,
                    category=triage.category,
                    source_count=count,
                    suggested_action="forgebench feedback promote --uid <UID> or --suggest-guardrails",
                )
            )

    missed = [e for e in entries if str(e.get("outcome_label") or "") == "missed_concern"]
    if missed:
        insights.insert(
            0,
            PrioritizedInsight(
                title="Missed merge-risk signals reported",
                detail=f"{len(missed)} missed_concern report(s) — highest priority",
                priority="critical",
                category="missed_concern",
                source_count=len(missed),
                suggested_action="Add golden cases + reviewer lens review",
            ),
        )

    features = by_category.get("feature_request", 0)
    if features:
        insights.append(
            PrioritizedInsight(
                title="Feature requests from users",
                detail=f"{features} request(s) in period",
                priority="medium",
                category="feature_request",
                source_count=features,
                suggested_action="forgebench roadmap update --period 7d",
            )
        )

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    insights.sort(key=lambda item: order.get(item.priority, 9))
    return insights[:8]


def _entries_since(logs: list[Path], cutoff: datetime) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for log_path in logs:
        if not log_path.exists():
            continue
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue
            ts_raw = str(payload.get("ts") or "")
            if not ts_raw:
                continue
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= cutoff:
                entries.append(payload)
    return entries


def _roadmap_candidates(entries: list[dict[str, Any]]) -> list[str]:
    dismissed_kinds: Counter[str] = Counter()
    for entry in entries:
        if str(entry.get("status") or "") in {"dismissed", "wrong"}:
            kind = str(entry.get("kind") or "").strip()
            if kind:
                dismissed_kinds[kind] += 1
    candidates: list[str] = []
    for kind, count in dismissed_kinds.most_common(3):
        candidates.append(f"Reduce false positives for `{kind}` ({count} dismissed/wrong in period)")
    feature_notes = [
        str(entry.get("note") or "").strip()
        for entry in entries
        if str(entry.get("category") or entry.get("source") or "") in {"feature_request", "discussion", "ideas"}
        and str(entry.get("note") or "").strip()
    ]
    candidates.extend(note[:120] for note in feature_notes[:3])
    return candidates