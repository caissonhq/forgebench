from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

VALID_FEEDBACK_CATEGORIES = {
    "bug",
    "false_positive",
    "feature_request",
    "calibration",
    "ux",
    "missed_concern",
    "other",
}
VALID_TRIAGE_PRIORITIES = {"critical", "high", "medium", "low"}


@dataclass(frozen=True)
class TriageResult:
    category: str
    priority: str
    rationale: str


def infer_category(entry: dict[str, Any]) -> str:
    explicit = str(entry.get("category") or "").strip().lower()
    if explicit in VALID_FEEDBACK_CATEGORIES:
        return explicit
    outcome = str(entry.get("outcome_label") or "").strip()
    if outcome == "false_positive":
        return "false_positive"
    if outcome == "missed_concern":
        return "missed_concern"
    if outcome == "calibration_gap":
        return "calibration"
    source = str(entry.get("source") or "").strip().lower()
    if source in {"feature_request", "discussion", "ideas"}:
        return "feature_request"
    status = str(entry.get("status") or "")
    if status == "wrong":
        return "calibration"
    if status == "dismissed":
        return "false_positive"
    return "other"


def infer_priority(entry: dict[str, Any], *, kind_frequency: Counter[str] | None = None) -> TriageResult:
    explicit = str(entry.get("triage") or entry.get("triage_priority") or "").strip().lower()
    category = infer_category(entry)
    if explicit in VALID_TRIAGE_PRIORITIES:
        return TriageResult(category=category, priority=explicit, rationale="explicit triage")

    outcome = str(entry.get("outcome_label") or "")
    severity = str(entry.get("severity") or "").lower()
    status = str(entry.get("status") or "")
    kind = str(entry.get("kind") or "")

    if outcome == "missed_concern" or category == "missed_concern":
        return TriageResult(category=category, priority="critical", rationale="missed merge-risk signal")
    if severity == "critical" and status in {"wrong", "dismissed"}:
        return TriageResult(category=category, priority="critical", rationale="critical-severity dismissal")
    if category == "feature_request" and str(entry.get("source") or "") in {"design_partner", "paid", "email"}:
        return TriageResult(category=category, priority="high", rationale="paid/design partner feature request")
    if kind_frequency and kind and kind_frequency.get(kind, 0) >= 3:
        return TriageResult(category=category, priority="high", rationale=f"recurring kind `{kind}` ({kind_frequency[kind]}×)")
    if status in {"dismissed", "wrong"} and kind:
        return TriageResult(category=category, priority="medium", rationale="false positive / calibration feedback")
    if category == "feature_request":
        return TriageResult(category=category, priority="medium", rationale="community feature request")
    return TriageResult(category=category, priority="low", rationale="informational feedback")


def enrich_entry(entry: dict[str, Any], *, kind_frequency: Counter[str] | None = None) -> dict[str, Any]:
    triage = infer_priority(entry, kind_frequency=kind_frequency)
    enriched = dict(entry)
    enriched.setdefault("category", triage.category)
    enriched.setdefault("triage", triage.priority)
    enriched.setdefault("triage_rationale", triage.rationale)
    return enriched


def compute_feedback_health(entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not entries:
        return {
            "volume": 0,
            "false_positive_rate": 0.0,
            "resolution_rate": 0.0,
            "avg_nps": None,
            "triage_counts": {},
            "category_counts": {},
            "top_issues": [],
            "sentiment_score": 0.0,
        }

    triage_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    nps_scores: list[float] = []
    resolved = 0
    dismissed_or_wrong = 0
    positive = 0

    kind_freq: Counter[str] = Counter()
    for entry in entries:
        kind = str(entry.get("kind") or "").strip()
        if kind and str(entry.get("status") or "") in {"dismissed", "wrong"}:
            kind_freq[kind] += 1

    for entry in entries:
        enriched = enrich_entry(entry, kind_frequency=kind_freq)
        triage_counts[enriched.get("triage", "low")] += 1
        category_counts[enriched.get("category", "other")] += 1
        kind = str(entry.get("kind") or "").strip()
        if kind:
            kind_counts[kind] += 1
        if entry.get("resolved"):
            resolved += 1
        status = str(entry.get("status") or "")
        if status in {"dismissed", "wrong"}:
            dismissed_or_wrong += 1
        if status == "accepted":
            positive += 1
        nps = entry.get("nps")
        if nps is not None:
            try:
                nps_scores.append(float(nps))
            except (TypeError, ValueError):
                pass

    total = len(entries)
    fp_rate = dismissed_or_wrong / total if total else 0.0
    resolution_rate = resolved / total if total else 0.0
    sentiment = (positive - dismissed_or_wrong) / total if total else 0.0
    avg_nps = sum(nps_scores) / len(nps_scores) if nps_scores else None

    top_issues = [
        {"kind": kind, "count": count, "priority": _kind_priority(kind, entries, kind_freq)}
        for kind, count in kind_counts.most_common(5)
    ]

    return {
        "volume": total,
        "false_positive_rate": round(fp_rate, 3),
        "resolution_rate": round(resolution_rate, 3),
        "avg_nps": round(avg_nps, 1) if avg_nps is not None else None,
        "triage_counts": dict(triage_counts),
        "category_counts": dict(category_counts),
        "top_issues": top_issues,
        "sentiment_score": round(sentiment, 3),
        "upgrade_signals": sum(1 for e in entries if str(e.get("category") or "") == "feature_request"),
    }


def _kind_priority(kind: str, entries: list[dict[str, Any]], kind_freq: Counter[str]) -> str:
    sample = next((e for e in entries if str(e.get("kind") or "") == kind), {})
    return infer_priority(sample, kind_frequency=kind_freq).priority


def priority_label(priority: str) -> str:
    mapping = {"critical": "P0", "high": "P1", "medium": "P2", "low": "P3"}
    return mapping.get(priority, "P3")