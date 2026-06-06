from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_OUTCOMES_PATH = Path("examples/benchmark_outcomes/eo002-pr-outcomes.json")
VALID_PR_OUTCOMES = {"merged", "reverted", "incident", "open", "unknown"}
VALID_HUMAN_AGREEMENT = {"agree", "disagree", "partial"}


class BenchmarkOutcomesError(ValueError):
    pass


@dataclass(frozen=True)
class PrOutcome:
    case_slug: str
    forgebench_posture: str
    human_posture_agreement: str
    pr_outcome: str
    finding_count: int = 0
    reviewer_fired: bool = False


@dataclass(frozen=True)
class PrOutcomesBundle:
    schema_version: str
    source: str
    description: str
    privacy_note: str
    outcomes: list[PrOutcome]
    summary: dict[str, Any]


@dataclass(frozen=True)
class PrOutcomesSummary:
    total_prs: int
    human_posture_agreement_rate: float
    posture_distribution: dict[str, int]
    pr_outcome_distribution: dict[str, int]
    reviewer_fire_rate: float
    labeled_false_positive_rate: float | None


def load_pr_outcomes(path: str | Path) -> PrOutcomesBundle:
    file_path = Path(path)
    if not file_path.exists():
        raise BenchmarkOutcomesError(f"PR outcomes file not found: {file_path}")
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BenchmarkOutcomesError(f"Invalid PR outcomes JSON: {file_path}") from exc
    if not isinstance(payload, dict):
        raise BenchmarkOutcomesError("PR outcomes root must be a JSON object.")

    raw_outcomes = payload.get("outcomes")
    if not isinstance(raw_outcomes, list):
        raise BenchmarkOutcomesError("PR outcomes must include an outcomes array.")

    outcomes: list[PrOutcome] = []
    for index, item in enumerate(raw_outcomes):
        if not isinstance(item, dict):
            raise BenchmarkOutcomesError(f"Outcome entry {index} must be an object.")
        case_slug = str(item.get("case_slug") or "").strip()
        if not case_slug:
            raise BenchmarkOutcomesError(f"Outcome entry {index} is missing case_slug.")
        posture = str(item.get("forgebench_posture") or "").strip()
        agreement = str(item.get("human_posture_agreement") or "").strip()
        pr_outcome = str(item.get("pr_outcome") or "").strip()
        if agreement not in VALID_HUMAN_AGREEMENT:
            raise BenchmarkOutcomesError(f"Invalid human_posture_agreement for {case_slug}: {agreement}")
        if pr_outcome not in VALID_PR_OUTCOMES:
            raise BenchmarkOutcomesError(f"Invalid pr_outcome for {case_slug}: {pr_outcome}")
        outcomes.append(
            PrOutcome(
                case_slug=case_slug,
                forgebench_posture=posture,
                human_posture_agreement=agreement,
                pr_outcome=pr_outcome,
                finding_count=int(item.get("finding_count") or 0),
                reviewer_fired=bool(item.get("reviewer_fired")),
            )
        )

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        summary = {}

    return PrOutcomesBundle(
        schema_version=str(payload.get("schema_version") or "0.1.0"),
        source=str(payload.get("source") or "unknown"),
        description=str(payload.get("description") or ""),
        privacy_note=str(payload.get("privacy_note") or ""),
        outcomes=outcomes,
        summary=summary,
    )


def summarize_pr_outcomes(bundle: PrOutcomesBundle) -> PrOutcomesSummary:
    total = len(bundle.outcomes)
    if total == 0:
        return PrOutcomesSummary(
            total_prs=0,
            human_posture_agreement_rate=0.0,
            posture_distribution={},
            pr_outcome_distribution={},
            reviewer_fire_rate=0.0,
            labeled_false_positive_rate=None,
        )

    agree_count = sum(1 for item in bundle.outcomes if item.human_posture_agreement == "agree")
    posture_distribution: dict[str, int] = {}
    pr_outcome_distribution: dict[str, int] = {}
    reviewer_fired_count = 0
    false_positive_findings = 0
    total_findings = 0

    for item in bundle.outcomes:
        posture_distribution[item.forgebench_posture] = posture_distribution.get(item.forgebench_posture, 0) + 1
        pr_outcome_distribution[item.pr_outcome] = pr_outcome_distribution.get(item.pr_outcome, 0) + 1
        if item.reviewer_fired:
            reviewer_fired_count += 1
        total_findings += item.finding_count
        if item.forgebench_posture == "LOW_CONCERN" and item.finding_count > 0:
            false_positive_findings += item.finding_count

    labeled_fpr: float | None = None
    if total_findings > 0:
        labeled_fpr = false_positive_findings / total_findings
    elif isinstance(bundle.summary.get("labeled_false_positive_rate"), (int, float)):
        labeled_fpr = float(bundle.summary["labeled_false_positive_rate"])

    return PrOutcomesSummary(
        total_prs=total,
        human_posture_agreement_rate=agree_count / total,
        posture_distribution=posture_distribution,
        pr_outcome_distribution=pr_outcome_distribution,
        reviewer_fire_rate=reviewer_fired_count / total,
        labeled_false_positive_rate=labeled_fpr,
    )


def outcomes_to_manifest(bundle: PrOutcomesBundle, summary: PrOutcomesSummary) -> dict[str, Any]:
    return {
        "schema_version": bundle.schema_version,
        "source": bundle.source,
        "description": bundle.description,
        "privacy_note": bundle.privacy_note,
        "summary": {
            "total_prs": summary.total_prs,
            "human_posture_agreement_rate": round(summary.human_posture_agreement_rate, 4),
            "posture_distribution": summary.posture_distribution,
            "pr_outcome_distribution": summary.pr_outcome_distribution,
            "reviewer_fire_rate": round(summary.reviewer_fire_rate, 4),
            "labeled_false_positive_rate": (
                round(summary.labeled_false_positive_rate, 4)
                if summary.labeled_false_positive_rate is not None
                else None
            ),
        },
        "outcomes": [
            {
                "case_slug": item.case_slug,
                "forgebench_posture": item.forgebench_posture,
                "human_posture_agreement": item.human_posture_agreement,
                "pr_outcome": item.pr_outcome,
                "finding_count": item.finding_count,
                "reviewer_fired": item.reviewer_fired,
            }
            for item in bundle.outcomes
        ],
    }