#!/usr/bin/env python3
"""Create golden calibration cases from EO-002 dogfood artifacts."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "dogfood_runs" / "eo002-2026-06-05"
GOLDEN_ROOT = ROOT / "examples" / "golden_cases"

CASES: list[dict[str, object]] = [
    {
        "dir": "dogfood_docs_pr_low_concern",
        "slug": "caissonhq-forgebench-1",
        "expected_posture": "LOW_CONCERN",
        "required": ["ui_copy_changed"],
        "forbidden": ["implementation_without_tests", "deleted_tests", "persistence_schema_changed"],
        "allow_unlisted": True,
        "rationale": "Real docs-only agent PR smoke test; advisory copy may appear in generic mode but posture stays low.",
    },
    {
        "dir": "dogfood_agent_security_tests_low_concern",
        "slug": "caissonhq-24hragent-1",
        "expected_posture": "LOW_CONCERN",
        "required": [],
        "forbidden": ["implementation_without_tests", "deleted_tests", "forbidden_pattern_added"],
        "allow_unlisted": False,
        "rationale": "Real Codex security cleanup with unit tests; should not escalate in generic mode.",
    },
    {
        "dir": "dogfood_codex_env_setup_low_concern",
        "slug": "vercel-workflow-2238",
        "expected_posture": "LOW_CONCERN",
        "required": ["ui_copy_changed"],
        "forbidden": ["implementation_without_tests", "persistence_schema_changed"],
        "allow_unlisted": True,
        "rationale": "Real Codex environment bootstrap PR; config-only with advisory copy noise.",
    },
    {
        "dir": "dogfood_agent_policy_markdown_low_concern",
        "slug": "officebeats-beats-pm-kit-15",
        "expected_posture": "LOW_CONCERN",
        "required": ["ui_copy_changed"],
        "forbidden": ["implementation_without_tests", "deleted_tests"],
        "allow_unlisted": True,
        "rationale": "Real Codex browser-first policy docs with tests in PR body; posture should stay low.",
    },
    {
        "dir": "dogfood_docs_task_script_scope_review",
        "slug": "hyperflow-5",
        "expected_posture": "REVIEW",
        "required": [
            "implementation_without_tests",
            "scope_auditor_task_scope_expansion",
            "test_skeptic_missing_behavior_coverage",
        ],
        "forbidden": ["deleted_tests"],
        "allow_unlisted": True,
        "rationale": "Real Codex docs clarification PR that also touches validation scripts; reviewers should fire.",
        "required_reviewer_finding_ids": [
            "scope_auditor_task_scope_expansion",
            "test_skeptic_missing_behavior_coverage",
        ],
    },
    {
        "dir": "dogfood_codex_metrics_tests_low_concern",
        "slug": "bourdon-113",
        "expected_posture": "LOW_CONCERN",
        "required": [],
        "forbidden": ["implementation_without_tests", "persistence_schema_changed"],
        "allow_unlisted": False,
        "rationale": "Real Codex L5 publisher freshness PR with regression tests; no static escalation.",
    },
    {
        "dir": "dogfood_cursor_ipc_refactor_low_concern",
        "slug": "t3code-2973-cursor",
        "expected_posture": "LOW_CONCERN",
        "required": ["ui_copy_changed"],
        "forbidden": ["implementation_without_tests", "deleted_tests", "persistence_schema_changed"],
        "allow_unlisted": True,
        "rationale": "Real Cursor Bugbot-reviewed Electron fetch refactor with tests; low concern in generic mode.",
    },
    {
        "dir": "dogfood_effect_refactor_broad_review",
        "slug": "t3code-2968-effect",
        "expected_posture": "REVIEW",
        "required": ["dependency_surface_changed", "broad_file_surface"],
        "forbidden": ["deleted_tests"],
        "allow_unlisted": True,
        "rationale": "Real broad Effect refactor; dependency + surface signals should review even if persistence heuristic misfires.",
    },
    {
        "dir": "dogfood_codex_autocomplete_broad_review",
        "slug": "t3code-2955-codex",
        "expected_posture": "REVIEW",
        "required": ["broad_file_surface"],
        "forbidden": ["deleted_tests", "forbidden_pattern_added"],
        "allow_unlisted": True,
        "rationale": "Real Codex workspace skill autocomplete fix across many files; broad surface REVIEW is appropriate.",
    },
    {
        "dir": "dogfood_rust_codex_routing_review",
        "slug": "tsumi233-cc-switch-1",
        "expected_posture": "REVIEW",
        "required": ["broad_file_surface"],
        "forbidden": ["deleted_tests"],
        "allow_unlisted": True,
        "rationale": "Real Codex chat tool-name fallback in Rust; broad surface REVIEW, persistence heuristic may misfire.",
    },
]


def main() -> int:
    for spec in CASES:
        slug = str(spec["slug"])
        case_dir = GOLDEN_ROOT / str(spec["dir"])
        src = RUN_ROOT / slug
        case_dir.mkdir(parents=True, exist_ok=True)
        for name in ("patch.diff", "task.md"):
            shutil.copy2(src / name, case_dir / name)
        expected = {
            "case_name": spec["dir"],
            "run_checks": False,
            "expected_posture": spec["expected_posture"],
            "required_finding_ids": spec["required"],
            "allowed_extra_finding_ids": [],
            "forbidden_finding_ids": spec["forbidden"],
            "allow_unlisted_findings": spec["allow_unlisted"],
            "rationale": spec["rationale"],
        }
        if spec.get("required_reviewer_finding_ids"):
            expected["required_reviewer_finding_ids"] = spec["required_reviewer_finding_ids"]
        (case_dir / "expected.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
        (case_dir / "rationale.md").write_text(f"# Rationale\n\n{spec['rationale']}\n", encoding="utf-8")
        print(f"Wrote {case_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())