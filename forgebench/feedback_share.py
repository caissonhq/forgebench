from __future__ import annotations

from datetime import datetime, timezone

SUCCESS_STORY_DISCUSSION_HINT = "github.com/caissonhq/forgebench/discussions/new?category=show-and-tell"


def format_success_story_share(
    *,
    posture: str = "REVIEW",
    finding_count: int = 0,
    note: str = "",
    agent_tool: str = "",
    workflow: str = "",
    team_size: str = "",
    time_saved: str = "",
) -> str:
    context = note.strip() or "Share what ForgeBench caught (or cleared) before merge."
    agent = agent_tool.strip() or "cursor / codex / claude"
    flow = workflow.strip() or "review → repair → re-review"
    size = team_size.strip() or "solo / small team"
    saved = time_saved.strip() or "(optional — e.g. caught a missing test before merge)"
    return "\n".join(
        [
            "ForgeBench success story — share template",
            "",
            "Copy into GitHub Discussions (Show and Tell) or post on X:",
            SUCCESS_STORY_DISCUSSION_HINT,
            "",
            "---",
            "",
            "## My ForgeBench experience",
            "",
            f"**Posture:** {posture} · **Findings:** {finding_count}",
            f"**Agent:** {agent} · **Workflow:** {flow}",
            f"**Team:** {size}",
            "",
            "### What happened",
            context,
            "",
            "### Impact",
            saved,
            "",
            "### What I'd tell another team",
            "(Would you recommend ForgeBench? What surprised you? Any false positives?)",
            "",
            "### X / social one-liner (optional)",
            f"> Ran ForgeBench on an agent PR — got {posture} with {finding_count} finding(s). "
            "Local-first merge-risk review before main. `pipx install forgebench`",
            "",
            "### Attachments (optional)",
            "- `forgebench share-report` HTML",
            "- Stack (Python/Node/etc.) without proprietary details",
            "",
            "---",
            "",
            f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} · local-only until you post",
        ]
    ) + "\n"