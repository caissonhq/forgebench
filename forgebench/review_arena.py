from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from forgebench.benchmark import BenchmarkSnapshot
from forgebench.benchmark_outcomes import PrOutcomesBundle, PrOutcomesSummary, summarize_pr_outcomes


@dataclass(frozen=True)
class ArenaEntry:
    contender_id: str
    contender_type: str
    display_name: str
    score: float
    metrics: dict[str, Any]
    rank: int = 0


@dataclass(frozen=True)
class ReviewArenaLeaderboard:
    schema_version: str
    generated_from: list[str]
    entries: list[ArenaEntry]


def build_review_arena_leaderboard(
    snapshot: BenchmarkSnapshot,
    *,
    outcomes_bundle: PrOutcomesBundle | None = None,
) -> ReviewArenaLeaderboard:
    generated_from = ["merge_risk_benchmark"]
    entries: list[ArenaEntry] = []

    calibration_score = _calibration_score(snapshot)
    entries.append(
        ArenaEntry(
            contender_id="forgebench_core",
            contender_type="pipeline",
            display_name="ForgeBench Core",
            score=calibration_score,
            metrics={
                "calibration_pass_rate": _pass_rate(snapshot),
                "case_count": snapshot.case_count,
                "failed_count": snapshot.failed_count,
            },
        )
    )

    for lens, fire_count in snapshot.review_lens_fire_rate.items():
        lens_score = _lens_score(fire_count, snapshot.case_count)
        entries.append(
            ArenaEntry(
                contender_id=f"lens:{lens}",
                contender_type="review_lens",
                display_name=lens,
                score=lens_score,
                metrics={
                    "fire_count": fire_count,
                    "fire_rate": round(fire_count / max(snapshot.case_count, 1), 4),
                },
            )
        )

    if outcomes_bundle is not None:
        generated_from.append("pr_outcomes")
        outcome_summary = summarize_pr_outcomes(outcomes_bundle)
        entries.append(
            ArenaEntry(
                contender_id="human_calibration",
                contender_type="ground_truth",
                display_name="Human Posture Agreement",
                score=outcome_summary.human_posture_agreement_rate * 100.0,
                metrics={
                    "agreement_rate": round(outcome_summary.human_posture_agreement_rate, 4),
                    "total_prs": outcome_summary.total_prs,
                    "reviewer_fire_rate": round(outcome_summary.reviewer_fire_rate, 4),
                },
            )
        )
        entries.extend(_agent_entries(outcomes_bundle, outcome_summary))

    ranked = sorted(entries, key=lambda item: (-item.score, item.display_name))
    ranked_entries = [
        ArenaEntry(
            contender_id=entry.contender_id,
            contender_type=entry.contender_type,
            display_name=entry.display_name,
            score=round(entry.score, 2),
            metrics=entry.metrics,
            rank=index + 1,
        )
        for index, entry in enumerate(ranked)
    ]
    return ReviewArenaLeaderboard(
        schema_version="0.1.0",
        generated_from=generated_from,
        entries=ranked_entries,
    )


def leaderboard_to_manifest(leaderboard: ReviewArenaLeaderboard) -> dict[str, Any]:
    return {
        "schema_version": leaderboard.schema_version,
        "generated_from": leaderboard.generated_from,
        "entries": [
            {
                "rank": entry.rank,
                "contender_id": entry.contender_id,
                "contender_type": entry.contender_type,
                "display_name": entry.display_name,
                "score": entry.score,
                "metrics": entry.metrics,
            }
            for entry in leaderboard.entries
        ],
    }


def _calibration_score(snapshot: BenchmarkSnapshot) -> float:
    return _pass_rate(snapshot) * 100.0


def _pass_rate(snapshot: BenchmarkSnapshot) -> float:
    if snapshot.case_count == 0:
        return 0.0
    return snapshot.passed_count / snapshot.case_count


def _lens_score(fire_count: int, case_count: int) -> float:
    if case_count == 0:
        return 0.0
    fire_rate = fire_count / case_count
    return min(100.0, fire_rate * 100.0 + fire_count)


def _agent_entries(bundle: PrOutcomesBundle, summary: PrOutcomesSummary) -> list[ArenaEntry]:
    del summary
    by_agent: dict[str, list[Any]] = {}
    for outcome in bundle.outcomes:
        if not outcome.case_slug.startswith("dogfood_"):
            continue
        agent = _infer_agent_from_slug(outcome.case_slug)
        by_agent.setdefault(agent, []).append(outcome)

    entries: list[ArenaEntry] = []
    for agent, outcomes in sorted(by_agent.items()):
        agree = sum(1 for item in outcomes if item.human_posture_agreement == "agree")
        score = (agree / len(outcomes)) * 100.0 if outcomes else 0.0
        entries.append(
            ArenaEntry(
                contender_id=f"agent:{agent}",
                contender_type="coding_agent",
                display_name=agent.title(),
                score=score,
                metrics={
                    "pr_count": len(outcomes),
                    "agreement_rate": round(agree / max(len(outcomes), 1), 4),
                    "merged_count": sum(1 for item in outcomes if item.pr_outcome == "merged"),
                },
            )
        )
    return entries


def _infer_agent_from_slug(case_slug: str) -> str:
    markers = ("cursor", "codex", "claude", "copilot")
    lowered = case_slug.lower()
    for marker in markers:
        if marker in lowered:
            return marker
    return "mixed"