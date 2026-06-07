from __future__ import annotations

from datetime import datetime, timezone

DISCUSSIONS_BASE = "https://github.com/caissonhq/forgebench/discussions/new"


def seed_discussion_posts() -> list[dict[str, str]]:
    return [
        {
            "category": "show-and-tell",
            "title": "First ForgeBench review — caught missing tests before merge",
            "body": _success_story_seed(),
            "url": f"{DISCUSSIONS_BASE}?category=show-and-tell",
        },
        {
            "category": "q-a",
            "title": "FAQ: How is ForgeBench different from linters and AI code review?",
            "body": _faq_seed(),
            "url": f"{DISCUSSIONS_BASE}?category=q-a",
        },
        {
            "category": "general",
            "title": "Design Partner program — apply for v1.0 pilot (50% Team discount)",
            "body": _design_partner_seed(),
            "url": f"{DISCUSSIONS_BASE}?category=general",
        },
    ]


def format_discussions_seed_pack() -> str:
    lines = [
        "GitHub Discussions — launch day seed posts",
        f"Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "Post these to kickstart community engagement after launch.",
        "",
    ]
    for index, post in enumerate(seed_discussion_posts(), start=1):
        lines.extend(
            [
                f"--- Post {index}: {post['category']} ---",
                f"Title: {post['title']}",
                f"URL: {post['url']}",
                "",
                post["body"],
                "",
            ]
        )
    return "\n".join(lines)


def _success_story_seed() -> str:
    return "\n".join(
        [
            "## My ForgeBench experience",
            "",
            "**Posture:** REVIEW · **Findings:** 3",
            "**Agent:** Cursor · **Workflow:** review → repair → re-review",
            "",
            "### What happened",
            "Ran `forgebench quickstart` after the v1.0 launch. First review flagged",
            "`implementation_without_tests` on a new API handler the agent added without real coverage.",
            "",
            "### Impact",
            "Pasted the repair prompt back into Cursor, added tests, re-ran review → LOW_CONCERN.",
            "",
            "### What I'd tell another team",
            "Worth 2 minutes before every agent PR. Local-first is a huge plus.",
            "",
            "Generate yours: `forgebench feedback --share`",
        ]
    )


def _faq_seed() -> str:
    return "\n".join(
        [
            "## Quick answers",
            "",
            "**Is ForgeBench a hosted code review service?**",
            "No. It runs locally on your machine. Optional self-hosted GitHub App for org enforcement.",
            "",
            "**How is it different from linters?**",
            "ForgeBench takes the *original task prompt* + diff and asks: did the agent stay on task?",
            "Posture is BLOCK / REVIEW / LOW_CONCERN with evidence — not pass/fail lint.",
            "",
            "**Does it prove code is safe?**",
            "No. It highlights merge risk before AI-generated code reaches main.",
            "",
            "**Try it:**",
            "```bash",
            "pipx install forgebench",
            "forgebench quickstart",
            "```",
        ]
    )


def _design_partner_seed() -> str:
    return "\n".join(
        [
            "We're inviting 8 engineering teams for a 4–6 week Design Partner pilot.",
            "",
            "**You get:**",
            "- 50% Team tier discount (up to 25 seats)",
            "- White-glove `forgebench partner onboard`",
            "- Priority support + roadmap input",
            "",
            "**We ask:**",
            "- Weekly async feedback (`forgebench feedback digest`)",
            "- One repo or squad scope",
            "",
            "**Apply:**",
            "1. `forgebench quickstart`",
            "2. Reply here with team size, stack, and agent tooling",
            "3. Or email hello@forgebench.dev",
        ]
    )