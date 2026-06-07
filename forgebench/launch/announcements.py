from __future__ import annotations

from datetime import datetime, timezone

LAUNCH_URL = "https://forgebench.dev"
GITHUB_URL = "https://github.com/caissonhq/forgebench"
DISCUSSIONS_URL = "https://github.com/caissonhq/forgebench/discussions"


def format_x_launch_thread() -> str:
    return "\n".join(
        [
            "=== ForgeBench v1.0.0 — X Launch Thread (copy/paste) ===",
            "",
            "--- Tweet 1/6 (hook) ---",
            "Would a serious engineer merge this AI-generated diff?",
            "",
            "ForgeBench v1.0 is live — local merge-risk review for Cursor, Codex, Claude Code & Copilot.",
            "",
            "pipx install forgebench && forgebench quickstart",
            "",
            LAUNCH_URL,
            "",
            "--- Tweet 2/6 (what you get) ---",
            "ForgeBench reads your agent diff + original task prompt and returns:",
            "• Posture: BLOCK / REVIEW / LOW_CONCERN",
            "• Evidence-backed findings",
            "• Repair prompt → paste back into your agent",
            "",
            "No hosted review. Your code stays on your machine.",
            "",
            "--- Tweet 3/6 (60-second demo) ---",
            "Try it in 60 seconds:",
            "",
            "forgebench demo",
            "forgebench doctor --checklist",
            "",
            "--- Tweet 4/6 (teams) ---",
            "Engineering teams:",
            "",
            "forgebench team init",
            "",
            "Org policy · CI workflow · onboarding docs — one wizard.",
            "",
            "Design Partner program open → 50% Team discount + white-glove onboarding",
            "",
            DISCUSSIONS_URL,
            "",
            "--- Tweet 5/6 (integrations) ---",
            "Also shipping:",
            "⭐ VS Code sidebar extension",
            "📦 GitHub Action + self-hosted App kit",
            "📊 Merge Risk Benchmark (47+ golden cases)",
            "",
            GITHUB_URL,
            "",
            "--- Tweet 6/6 (CTA) ---",
            "Star us if merge-risk gates for agent PRs resonate ⭐",
            "",
            "Share your first review: forgebench feedback --share",
            "",
            f"ForgeBench does not prove code is safe. · {LAUNCH_URL}",
            "",
            f"Generated {datetime.now(timezone.utc).date().isoformat()}",
        ]
    )


def format_show_hn_post() -> str:
    return "\n".join(
        [
            "=== Show HN — copy title and body separately ===",
            "",
            "TITLE:",
            "Show HN: ForgeBench – merge-risk review for AI-generated diffs (local CLI, v1.0)",
            "",
            "BODY:",
            "Hi HN — we built ForgeBench to answer one question before merge:",
            "would a serious engineer ship this patch?",
            "",
            "Coding agents (Cursor, Codex, Claude Code, Copilot) ship diffs fast.",
            "Generic linters miss task drift, weak tests on behavior changes, and scope creep.",
            "ForgeBench is a local CLI that returns a cited merge posture",
            "(BLOCK / REVIEW / LOW_CONCERN), SARIF, and a repair prompt you paste back into your agent.",
            "",
            "Try it:",
            "",
            "  pipx install forgebench",
            "  forgebench quickstart",
            "",
            "Evidence hierarchy:",
            "1. Deterministic checks (optional --run-checks)",
            "2. Static risk signals on the diff",
            "3. Repo guardrails (forgebench.yml)",
            "4. Heuristic review lenses (scope, tests, contracts)",
            "5. Optional LLM review (advisory only)",
            "",
            "Deterministic failures are never downgraded. No hosted SaaS — runs on your machine.",
            "",
            "v1.0 includes: team init wizard, presets gallery, VS Code extension,",
            "self-hosted GitHub App kit, Merge Risk Benchmark (47+ golden cases).",
            "",
            "Open source core CLI. Team/Enterprise adds licensing, analytics, org policy serve.",
            "",
            f"{LAUNCH_URL}",
            f"{GITHUB_URL}",
            "",
            "We'd love feedback — especially false positives from real agent PRs.",
            "forgebench feedback --share generates a Discussion template.",
            "",
            "ForgeBench does not prove code is safe.",
        ]
    )


def format_launch_announcements_bundle() -> str:
    return "\n\n".join([format_x_launch_thread(), format_show_hn_post()])