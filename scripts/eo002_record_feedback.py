#!/usr/bin/env python3
"""Record EO-002 dogfood finding feedback using stable UIDs from review artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from forgebench.feedback import append_feedback


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "dogfood_runs" / "eo002-2026-06-05"
FEEDBACK_LOG = RUN_ROOT / "feedback.jsonl"

# slug -> kind -> (status, note)
LABELS: dict[str, dict[str, tuple[str, str]]] = {
    "caissonhq-forgebench-1": {
        "ui_copy_changed": ("dismissed", "README-only PR; markdown copy finding is generic-mode noise."),
    },
    "vercel-workflow-2238": {
        "ui_copy_changed": ("dismissed", "Codex environment TOML + changeset; not merge-risk UI copy."),
    },
    "officebeats-beats-pm-kit-15": {
        "ui_copy_changed": ("dismissed", "Agent policy markdown only; advisory copy signal expected."),
    },
    "hyperflow-5": {
        "implementation_without_tests": (
            "dismissed",
            "Patch includes validation/tests; static heuristic missed test paths.",
        ),
        "ui_copy_changed": ("dismissed", "Documentation-only hyperflow plugin copy."),
        "scope_auditor_task_scope_expansion": (
            "accepted",
            "Docs-focused task with script/validation path changes; useful scope drift.",
        ),
        "test_skeptic_missing_behavior_coverage": (
            "accepted",
            "Good human review framing even though tests were updated.",
        ),
    },
    "t3code-2973-cursor": {
        "ui_copy_changed": ("dismissed", "Small TS IPC refactor; copy heuristic not useful here."),
    },
    "t3code-2968-effect": {
        "dependency_surface_changed": ("accepted", "Monorepo lockfile/package changes are real merge risk."),
        "build_config_changed": ("accepted", "TS/Bun workspace config edits need review."),
        "persistence_schema_changed": ("wrong", "TS config edits are not persistence/schema."),
        "broad_file_surface": ("accepted", "42-file mechanical refactor needs unrelated-change scan."),
        "test_skeptic_weak_test_signal": (
            "dismissed",
            "PR updates tests; weak assertion token heuristic false positive.",
        ),
    },
    "t3code-2955-codex": {
        "broad_file_surface": ("accepted", "22-file provider cwd threading warrants REVIEW."),
        "ui_copy_changed": ("dismissed", "PR body/markdown churn; not product UI risk."),
        "test_skeptic_weak_test_signal": (
            "dismissed",
            "Substantial regression tests added; weak-token heuristic misfired.",
        ),
    },
    "tsumi233-cc-switch-1": {
        "persistence_schema_changed": ("wrong", "Rust Codex chat transform; not database schema."),
        "broad_file_surface": ("accepted", "22-file routing/build change set is broad."),
        "ui_copy_changed": ("dismissed", "Rust/logging changes; copy heuristic noise."),
    },
}


def main() -> int:
    FEEDBACK_LOG.parent.mkdir(parents=True, exist_ok=True)
    if FEEDBACK_LOG.exists():
        FEEDBACK_LOG.unlink()

    count = 0
    for slug, kinds in LABELS.items():
        report_path = RUN_ROOT / slug / "forgebench-output" / "forgebench-report.json"
        if not report_path.exists():
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        for finding in report.get("findings", []):
            kind = str(finding.get("kind") or finding.get("id"))
            uid = finding.get("uid")
            if not uid or kind not in kinds:
                continue
            status, note = kinds[kind]
            append_feedback(
                uid,
                status=status,
                kind=kind,
                note=note,
                repo_name=slug,
                source="eo002-dogfood",
                feedback_log=FEEDBACK_LOG,
            )
            count += 1

    print(f"Recorded {count} feedback entries to {FEEDBACK_LOG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())