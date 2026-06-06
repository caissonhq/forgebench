from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_OUTCOME_LABELS = {
    "false_positive",
    "true_positive",
    "missed_concern",
    "noise",
    "calibration_gap",
    "other",
}
GOLDEN_CASE_STATUSES = {"accepted", "dismissed", "wrong"}


class GoldenCaseGeneratorError(ValueError):
    pass


@dataclass(frozen=True)
class GoldenCaseCandidate:
    case_slug: str
    source_uid: str
    feedback_status: str
    kind: str
    expected_posture: str | None
    outcome_label: str | None
    rationale: str
    expected_json: dict[str, Any]
    review_gate: str


@dataclass(frozen=True)
class GoldenCaseGenerationResult:
    output_dir: Path
    candidates: list[GoldenCaseCandidate]
    manifest_path: Path
    skipped_count: int


def generate_golden_case_candidates(
    feedback_logs: list[str | Path],
    *,
    output_dir: str | Path,
    min_statuses: set[str] | None = None,
) -> GoldenCaseGenerationResult:
    statuses = min_statuses or {"dismissed", "wrong"}
    entries, malformed_count, _missing = _load_feedback_entries(feedback_logs)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    candidates: list[GoldenCaseCandidate] = []
    skipped = malformed_count
    seen_slugs: set[str] = set()

    for entry in entries:
        status = str(entry.get("status") or "")
        if status not in statuses:
            skipped += 1
            continue
        kind = str(entry.get("kind") or "").strip()
        if not kind:
            skipped += 1
            continue
        uid = str(entry.get("uid") or "").strip()
        if not uid:
            skipped += 1
            continue

        case_slug = _suggest_case_slug(entry, kind, seen_slugs)
        seen_slugs.add(case_slug)
        expected_posture = _optional_str(entry.get("expected_posture"))
        outcome_label = _optional_str(entry.get("outcome_label"))
        rationale = _build_rationale(entry, kind, status, outcome_label)
        expected_json = _build_expected_json(case_slug, kind, status, entry, expected_posture, rationale)
        review_gate = _review_gate_message(case_slug)

        candidate = GoldenCaseCandidate(
            case_slug=case_slug,
            source_uid=uid,
            feedback_status=status,
            kind=kind,
            expected_posture=expected_posture,
            outcome_label=outcome_label,
            rationale=rationale,
            expected_json=expected_json,
            review_gate=review_gate,
        )
        candidates.append(candidate)
        case_dir = output / case_slug
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "expected.json").write_text(json.dumps(expected_json, indent=2) + "\n", encoding="utf-8")
        (case_dir / "rationale.md").write_text(f"# Rationale\n\n{rationale}\n\n{review_gate}\n", encoding="utf-8")
        (case_dir / "REVIEW_GATE.md").write_text(review_gate + "\n", encoding="utf-8")
        _write_placeholder_artifacts(case_dir, entry)

    manifest = {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidate_count": len(candidates),
        "skipped_count": skipped,
        "human_review_required": True,
        "candidates": [
            {
                "case_slug": item.case_slug,
                "source_uid": item.source_uid,
                "feedback_status": item.feedback_status,
                "kind": item.kind,
                "expected_posture": item.expected_posture,
                "outcome_label": item.outcome_label,
            }
            for item in candidates
        ],
        "instructions": (
            "These are draft golden cases generated from local feedback. "
            "Add anonymized patch.diff and task.md, verify expected.json, then move approved cases to examples/golden_cases/."
        ),
    }
    manifest_path = output / "candidates-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return GoldenCaseGenerationResult(
        output_dir=output,
        candidates=candidates,
        manifest_path=manifest_path,
        skipped_count=skipped,
    )


def _load_feedback_entries(feedback_logs: list[str | Path]) -> tuple[list[dict[str, Any]], int, list[str]]:
    from forgebench.feedback import _load_feedback_entries as load_entries

    return load_entries(feedback_logs)


def _suggest_case_slug(entry: dict[str, Any], kind: str, seen: set[str]) -> str:
    explicit = str(entry.get("case_slug") or "").strip()
    if explicit:
        base = _slugify(explicit)
    else:
        status = str(entry.get("status") or "feedback")
        base = _slugify(f"feedback_{status}_{kind}")
    slug = base
    suffix = 2
    while slug in seen:
        slug = f"{base}_{suffix}"
        suffix += 1
    return slug


def _slugify(value: str) -> str:
    lowered = value.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    return slug[:80] or "feedback_case"


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _build_rationale(
    entry: dict[str, Any],
    kind: str,
    status: str,
    outcome_label: str | None,
) -> str:
    note = str(entry.get("note") or "").strip()
    parts = [
        f"Generated from local feedback ({status}) on finding kind `{kind}`.",
    ]
    if outcome_label:
        parts.append(f"Outcome label: {outcome_label}.")
    posture = _optional_str(entry.get("posture"))
    if posture:
        parts.append(f"Observed review posture: {posture}.")
    agent = _optional_str(entry.get("agent_tool"))
    if agent:
        parts.append(f"Agent tool: {agent}.")
    if note:
        parts.append(f"Reviewer note: {note}")
    return " ".join(parts)


def _build_expected_json(
    case_slug: str,
    kind: str,
    status: str,
    entry: dict[str, Any],
    expected_posture: str | None,
    rationale: str,
) -> dict[str, Any]:
    posture = expected_posture or _default_posture_for_status(status)
    payload: dict[str, Any] = {
        "case_name": case_slug,
        "run_checks": False,
        "expected_posture": posture,
        "required_finding_ids": [],
        "allowed_extra_finding_ids": [],
        "forbidden_finding_ids": [],
        "allow_unlisted_findings": True,
        "rationale": rationale,
        "generated_from_feedback": {
            "uid": entry.get("uid"),
            "status": status,
            "kind": kind,
            "fb_version": entry.get("fb_version"),
        },
    }
    if status in {"dismissed", "wrong"}:
        payload["forbidden_finding_ids"] = [kind]
    elif status == "accepted":
        payload["required_finding_ids"] = [kind]
    reviewer_lens = _optional_str(entry.get("reviewer_lens"))
    if reviewer_lens:
        payload["required_reviewer_finding_ids"] = [kind]
    return payload


def _default_posture_for_status(status: str) -> str:
    if status == "wrong":
        return "REVIEW"
    if status == "dismissed":
        return "LOW_CONCERN"
    return "REVIEW"


def _review_gate_message(case_slug: str) -> str:
    return (
        "## Human review required\n\n"
        f"Draft case `{case_slug}` was generated automatically from local feedback.\n"
        "Before promoting to `examples/golden_cases/`:\n"
        "1. Add anonymized `patch.diff` and `task.md`.\n"
        "2. Run `forgebench calibrate --cases <this-dir>` and adjust `expected.json`.\n"
        "3. Open a golden case proposal issue for maintainer review.\n"
    )


def _write_placeholder_artifacts(case_dir: Path, entry: dict[str, Any]) -> None:
    patch_placeholder = case_dir / "patch.diff.PLACEHOLDER"
    task_placeholder = case_dir / "task.md.PLACEHOLDER"
    if not patch_placeholder.exists():
        patch_placeholder.write_text(
            "# Add anonymized unified diff here, then rename to patch.diff\n",
            encoding="utf-8",
        )
    if not task_placeholder.exists():
        note = str(entry.get("note") or "Add original task prompt.").strip()
        task_placeholder.write_text(f"# Add task prompt here, then rename to task.md\n\n{note}\n", encoding="utf-8")