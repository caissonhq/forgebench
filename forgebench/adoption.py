from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ADOPTION_STATE_PATH = Path("forgebench-output") / "adoption-state.json"

MILESTONES = (
    "first_install",
    "quickstart_completed",
    "first_review",
    "first_demo",
    "first_guardrails",
    "first_team_init",
    "first_preset_installed",
    "first_share_report",
    "first_paid_feature",
)


@dataclass(frozen=True)
class AdoptionState:
    milestones: dict[str, str] = field(default_factory=dict)
    review_count: int = 0


def load_adoption_state(path: str | Path | None = None) -> AdoptionState:
    target = Path(path) if path else ADOPTION_STATE_PATH
    if not target.exists():
        return AdoptionState()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AdoptionState()
    if not isinstance(payload, dict):
        return AdoptionState()
    milestones = payload.get("milestones") if isinstance(payload.get("milestones"), dict) else {}
    return AdoptionState(
        milestones={str(k): str(v) for k, v in milestones.items()},
        review_count=int(payload.get("review_count") or 0),
    )


def save_adoption_state(state: AdoptionState, path: str | Path | None = None) -> Path:
    target = Path(path) if path else ADOPTION_STATE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0.0",
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "milestones": state.milestones,
        "review_count": state.review_count,
    }
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def record_milestone(name: str, *, path: str | Path | None = None) -> bool:
    normalized = name.strip()
    if normalized not in MILESTONES:
        return False
    state = load_adoption_state(path)
    if normalized in state.milestones:
        return False
    updated = AdoptionState(
        milestones={**state.milestones, normalized: datetime.now(timezone.utc).isoformat(timespec="seconds")},
        review_count=state.review_count,
    )
    save_adoption_state(updated, path=path)
    _emit_product_event(normalized)
    return True


def increment_review_count(*, path: str | Path | None = None) -> AdoptionState:
    state = load_adoption_state(path)
    updated = AdoptionState(milestones=dict(state.milestones), review_count=state.review_count + 1)
    save_adoption_state(updated, path=path)
    if updated.review_count == 1:
        record_milestone("first_review", path=path)
    return updated


def next_actions_after_review(*, posture: str, config_mode: str, finding_count: int) -> list[str]:
    actions: list[str] = []
    if config_mode == "generic":
        actions.append("Run `forgebench init` to add repo-specific guardrails.")
        actions.append("Try `forgebench presets list` for a curated starter policy.")
    if finding_count:
        actions.append("Run `forgebench repair --out forgebench-output` and paste into your coding agent.")
        actions.append("Share results: `forgebench share-report --out forgebench-output`")
    if posture in {"BLOCK", "REVIEW"}:
        actions.append("Re-run review after repairs: `forgebench review --repo . --diff patch.diff --task task.md`")
    else:
        actions.append("Nice first pass — try `forgebench review-pr PR_URL` on a real PR.")
    actions.append("Track progress: `forgebench doctor --checklist`")
    return actions


def format_next_actions(actions: list[str]) -> str:
    lines = ["Suggested next steps:"]
    for item in actions:
        lines.append(f"  → {item}")
    return "\n".join(lines)


@dataclass(frozen=True)
class ChecklistItem:
    label: str
    done: bool
    next_command: str | None = None


def build_success_checklist(*, repo_path: str | Path = ".", state_path: str | Path | None = None) -> list[ChecklistItem]:
    repo = Path(repo_path).resolve()
    state = load_adoption_state(state_path)
    return [
        ChecklistItem("Install verified (doctor passes)", _doctor_core_ok(repo), "forgebench doctor"),
        ChecklistItem("First demo completed", "first_demo" in state.milestones or "quickstart_completed" in state.milestones, "forgebench demo"),
        ChecklistItem("Guardrails configured", (repo / "forgebench.yml").exists() or (repo / ".github" / "forgebench.yml").exists(), "forgebench init"),
        ChecklistItem("First review run", "first_review" in state.milestones, "forgebench review --repo . --diff patch.diff --task task.md"),
        ChecklistItem("Preset or team kit applied", "first_preset_installed" in state.milestones or "first_team_init" in state.milestones, "forgebench presets list"),
        ChecklistItem("Shared a report", "first_share_report" in state.milestones, "forgebench share-report"),
        ChecklistItem("Team license activated", "first_paid_feature" in state.milestones, "forgebench license activate <KEY>"),
    ]


def format_success_checklist(items: list[ChecklistItem]) -> str:
    lines = ["Adoption success checklist:"]
    for item in items:
        mark = "x" if item.done else " "
        lines.append(f"  [{mark}] {item.label}")
        if not item.done and item.next_command:
            lines.append(f"      → {item.next_command}")
    completed = sum(1 for item in items if item.done)
    lines.append("")
    lines.append(f"Progress: {completed}/{len(items)} complete")
    return "\n".join(lines)


def doctor_next_steps(*, repo_path: str | Path = ".", doctor_ready: bool, has_warnings: bool) -> list[str]:
    repo = Path(repo_path).resolve()
    state = load_adoption_state()
    steps: list[str] = []
    if not doctor_ready:
        steps.append("Fix failed doctor checks above, then re-run: forgebench doctor")
        return steps
    if "quickstart_completed" not in state.milestones and "first_demo" not in state.milestones:
        steps.append("New here? Run: forgebench quickstart")
    elif not (repo / "forgebench.yml").exists():
        steps.append("Add guardrails: forgebench init  (or forgebench presets install python)")
    if "first_review" not in state.milestones:
        steps.append("Run your first review: forgebench demo  (or forgebench review-pr PR_URL)")
    if has_warnings:
        steps.append("Address warnings: forgebench status --explain")
    if "first_team_init" not in state.milestones and (repo / "org-policy").exists():
        steps.append("Team kit detected — share onboarding: docs/forgebench-onboarding.md")
    steps.append("Track milestones: forgebench doctor --checklist")
    return steps


FEATURE_DISCUSSION_HINT = "github.com/caissonhq/forgebench/discussions/new?category=ideas"


def format_feature_suggestion(
    *,
    title: str = "",
    description: str = "",
    use_case: str = "",
) -> str:
    heading = title.strip() or "ForgeBench feature idea"
    body = description.strip() or "Describe the problem ForgeBench should solve."
    context = use_case.strip() or "Solo developer / team workflow context."
    return "\n".join(
        [
            "ForgeBench feature suggestion",
            "",
            "Copy the template below into GitHub Discussions (Ideas category):",
            FEATURE_DISCUSSION_HINT,
            "",
            "---",
            "",
            f"## {heading}",
            "",
            "### Problem",
            body,
            "",
            "### Proposed solution",
            "(What would ForgeBench do differently?)",
            "",
            "### Use case",
            context,
            "",
            "### Alternatives considered",
            "(Optional)",
            "",
            "---",
            "",
            "Local-only — no data is uploaded automatically.",
        ]
    ) + "\n"


def _doctor_core_ok(repo: Path) -> bool:
    try:
        from forgebench.doctor import run_doctor

        return run_doctor(repo_path=repo).ready
    except Exception:
        return False


def _emit_product_event(milestone: str) -> None:
    try:
        from forgebench.product_analytics import record_product_event

        record_product_event("milestone_reached", {"milestone": milestone})
    except Exception:
        pass