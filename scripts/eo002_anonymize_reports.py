#!/usr/bin/env python3
"""Publish anonymized real dogfood reports for examples/ and the marketing site."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "dogfood_runs" / "eo002-2026-06-05"
OUT_ROOT = ROOT / "examples" / "real_reports"

REDACT_PATHS = {
    "/tmp/forgebench-eo002-clones/": "/tmp/example-repo/",
    "/Users/davidhorton/Developer/caissonhq/projects/forgebench/dogfood_runs/eo002-2026-06-05/": "dogfood-runs/eo002/",
    "caissonhq/24hragent": "example-org/agent-runtime",
    "Mohammed-Abdelhady/hyperflow": "example-org/agent-plugin",
    "pingdotgg/t3code": "example-org/desktop-monorepo",
    "Mohammed-Abdelhady": "example-author",
    "Hortyhort": "example-author",
    "juliusmarminge": "example-author",
    "PabloSzx": "example-author",
    "pranaygp": "example-author",
    "officebeats": "example-org",
    "getbourdon/bourdon": "example-org/metrics-dashboard",
    "tsumi233/cc-switch": "example-org/desktop-bridge",
}

CASES = [
    {
        "slug": "caissonhq-24hragent-1",
        "dir": "agent_env_secret_cleanup_low_concern",
        "title": "Agent security cleanup (LOW_CONCERN)",
        "agent": "Codex",
        "summary": "Real merged PR that removed a hardcoded API key pattern and added env-var tests.",
    },
    {
        "slug": "hyperflow-5",
        "dir": "agent_docs_scope_review",
        "title": "Docs task with script drift (REVIEW)",
        "agent": "Codex",
        "summary": "Real open PR where documentation edits also touched validation scripts; Scope Auditor and Test Skeptic fired.",
    },
    {
        "slug": "t3code-2968-effect",
        "dir": "monorepo_effect_refactor_review",
        "title": "Broad monorepo refactor (REVIEW)",
        "agent": "Cursor",
        "summary": "Real merged PR refactoring Effect fallbacks across 42 files; dependency and broad-surface signals.",
    },
]


def _redact(text: str) -> str:
    for old, new in sorted(REDACT_PATHS.items(), key=lambda item: -len(item[0])):
        text = text.replace(old, new)
    text = re.sub(r"/Users/[^/\s]+/", "/Users/example/", text)
    text = re.sub(r"@[\w.-]+", "@example.com", text)
    return text


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    index_lines = [
        "# ForgeBench Real Anonymized Reports",
        "",
        "These reports come from real agent-generated pull requests reviewed during EO-002 dogfood (2026-06-05).",
        "Paths, authors, and repository names are redacted. Diff hunks are preserved for teaching value.",
        "",
        "They are not synthetic fixtures. Do not treat them as customer endorsements.",
        "",
        "## Cases",
        "",
    ]

    for case in CASES:
        slug = case["slug"]
        case_dir = OUT_ROOT / case["dir"]
        case_dir.mkdir(parents=True, exist_ok=True)
        src_out = RUN_ROOT / slug / "forgebench-output"
        for name in ("forgebench-report.md", "forgebench-report.json", "repair-prompt.md", "pr-comment.md"):
            src = src_out / name
            if not src.exists():
                continue
            text = _redact(src.read_text(encoding="utf-8"))
            (case_dir / name).write_text(text, encoding="utf-8")

        shutil.copy2(RUN_ROOT / slug / "patch.diff", case_dir / "patch.diff")
        shutil.copy2(RUN_ROOT / slug / "task.md", case_dir / "task.md")
        (case_dir / "README.md").write_text(
            "\n".join(
                [
                    f"# {case['title']}",
                    "",
                    f"- Source: anonymized real PR ({case['agent']})",
                    f"- {case['summary']}",
                    "",
                    "Reproduce locally:",
                    "",
                    "```bash",
                    "forgebench review \\",
                    "  --repo . \\",
                    f"  --diff examples/real_reports/{case['dir']}/patch.diff \\",
                    f"  --task examples/real_reports/{case['dir']}/task.md",
                    "```",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        index_lines.append(f"- `{case['dir']}`: {case['title']}")

    (OUT_ROOT / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())