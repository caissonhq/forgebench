from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.feedback_digest import build_feedback_digest, parse_period
from forgebench.feedback_triage import priority_label


ROADMAP_PATH = Path(__file__).resolve().parents[1] / "ROADMAP.md"
TABLE_HEADER = "| Priority | Request | Status | Notes |"
TABLE_SEP = "|----------|---------|--------|-------|"


@dataclass(frozen=True)
class RoadmapItem:
    priority: str
    request: str
    status: str
    notes: str
    source: str = "feedback"


@dataclass(frozen=True)
class RoadmapUpdateResult:
    suggestions: list[RoadmapItem]
    existing_count: int
    applied: bool
    roadmap_path: Path


def suggest_roadmap_items(
    *,
    feedback_logs: list[str | Path] | None = None,
    period: str = "7d",
) -> list[RoadmapItem]:
    days = parse_period(period)
    digest = build_feedback_digest(feedback_logs, days=days)
    items: list[RoadmapItem] = []
    for insight in digest.prioritized_insights:
        if insight.priority in {"critical", "high", "medium"}:
            items.append(
                RoadmapItem(
                    priority=priority_label(insight.priority),
                    request=insight.title,
                    status="In progress" if insight.priority == "critical" else "Planned",
                    notes=f"{insight.detail} · {insight.source_count} report(s) · EO-019",
                    source=insight.category,
                )
            )
    for candidate in digest.roadmap_candidates[:3]:
        if not any(candidate in item.request for item in items):
            items.append(
                RoadmapItem(
                    priority="P2",
                    request=candidate,
                    status="Planned",
                    notes="Auto-suggested from feedback digest · EO-019",
                )
            )
    return items


def update_roadmap(
    *,
    roadmap_path: str | Path | None = None,
    feedback_logs: list[str | Path] | None = None,
    period: str = "7d",
    apply: bool = False,
) -> RoadmapUpdateResult:
    path = Path(roadmap_path) if roadmap_path else ROADMAP_PATH
    suggestions = suggest_roadmap_items(feedback_logs=feedback_logs, period=period)
    existing = _parse_roadmap_table(path)
    merged = _merge_items(existing, suggestions)

    if apply and path.exists():
        text = path.read_text(encoding="utf-8")
        updated = _replace_table(text, merged)
        if updated != text:
            path.write_text(updated, encoding="utf-8")

    return RoadmapUpdateResult(
        suggestions=suggestions,
        existing_count=len(existing),
        applied=apply,
        roadmap_path=path,
    )


def format_roadmap_suggestions(result: RoadmapUpdateResult) -> str:
    lines = [
        "ForgeBench roadmap update suggestions",
        f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Existing items: {result.existing_count}",
        f"New suggestions: {len(result.suggestions)}",
        "",
    ]
    if not result.suggestions:
        lines.append("No new high-priority feedback themes detected.")
        return "\n".join(lines)
    for item in result.suggestions:
        lines.append(f"- [{item.priority}] {item.request}")
        lines.append(f"    Status: {item.status} · {item.notes}")
    lines.extend(
        [
            "",
            "Apply to ROADMAP.md:",
            "  forgebench roadmap update --apply",
            "  forgebench roadmap update --apply --period 14d",
        ]
    )
    if result.applied:
        lines.append(f"\nApplied to {result.roadmap_path}")
    return "\n".join(lines)


def _parse_roadmap_table(path: Path) -> list[RoadmapItem]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    section = _extract_feedback_section(text)
    if not section:
        return []
    items: list[RoadmapItem] = []
    for line in section.splitlines():
        if not line.startswith("|") or "Request" in line or "---" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 4:
            items.append(RoadmapItem(priority=cells[0], request=cells[1], status=cells[2], notes=cells[3]))
    return items


def _extract_feedback_section(text: str) -> str:
    match = re.search(
        r"### User-requested improvements.*?\n(.*?)(?=\n## |\Z)",
        text,
        re.DOTALL,
    )
    return match.group(1) if match else ""


def _merge_items(existing: list[RoadmapItem], suggestions: list[RoadmapItem]) -> list[RoadmapItem]:
    merged = list(existing)
    existing_requests = {item.request.lower() for item in existing}
    for item in suggestions:
        key = item.request.lower()
        if key not in existing_requests:
            merged.append(item)
            existing_requests.add(key)
    return merged


def _replace_table(text: str, items: list[RoadmapItem]) -> str:
    section_match = re.search(r"(### User-requested improvements[^\n]*\n)", text)
    if not section_match:
        return text
    table_lines = [TABLE_HEADER, TABLE_SEP]
    for item in items:
        table_lines.append(f"| {item.priority} | {item.request} | {item.status} | {item.notes} |")
    new_section = section_match.group(1) + "\n".join(table_lines) + "\n"
    old_section = re.search(
        r"### User-requested improvements.*?(?=\n## |\Z)",
        text,
        re.DOTALL,
    )
    if not old_section:
        return text
    return text[: old_section.start()] + new_section + text[old_section.end() :]