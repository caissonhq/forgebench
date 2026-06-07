from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from forgebench.feedback_digest import build_feedback_digest, parse_period


def generate_whats_new_from_feedback(
    feedback_logs: list[str | Path] | None = None,
    *,
    period: str = "7d",
    version: str = "upcoming",
) -> str:
    digest = build_feedback_digest(feedback_logs, period=period)
    lines = [
        f"## What's New (from user feedback) — {version}",
        "",
        f"_Draft generated {datetime.now(timezone.utc).date().isoformat()} from {digest.period_label} feedback._",
        "",
    ]
    if not digest.prioritized_insights:
        lines.append("- No high-priority feedback themes this period.")
        return "\n".join(lines)

    lines.append("### Shipped / in progress (feedback-driven)")
    for insight in digest.prioritized_insights[:5]:
        if insight.priority in {"critical", "high"}:
            lines.append(f"- **{insight.title}** — {insight.detail}")
    lines.append("")
    lines.append("### Thank you")
    lines.append("- Contributors who filed structured feedback (`forgebench feedback --paid`)")
    lines.append("- Design Partners sharing weekly digests")
    lines.append("")
    lines.append("### Try it")
    lines.append("```bash")
    lines.append("forgebench feedback digest --period " + digest.period_label)
    lines.append("forgebench weekly-review --period " + digest.period_label)
    lines.append("```")
    return "\n".join(lines)