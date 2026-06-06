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
) -> str:
    context = note.strip() or "Share what ForgeBench caught (or cleared) before merge."
    agent = agent_tool.strip() or "cursor / codex / claude"
    flow = workflow.strip() or "review → repair → re-review"
    return "\n".join(
        [
            "ForgeBench success story — share template",
            "",
            "Post to GitHub Discussions (Show and Tell):",
            SUCCESS_STORY_DISCUSSION_HINT,
            "",
            "---",
            "",
            "## My ForgeBench experience",
            "",
            f"**Posture:** {posture} · **Findings:** {finding_count}",
            f"**Agent:** {agent} · **Workflow:** {flow}",
            "",
            "### What happened",
            context,
            "",
            "### What I'd tell another team",
            "(Would you recommend ForgeBench? What surprised you?)",
            "",
            "### Optional",
            "- `forgebench share-report` HTML (attach or link)",
            "- Repo stack (Python/Node/etc.) without proprietary details",
            "",
            "---",
            "",
            f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} · local-only until you post",
        ]
    ) + "\n"