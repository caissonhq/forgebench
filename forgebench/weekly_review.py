from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forgebench.feedback_digest import build_feedback_digest, format_feedback_digest, parse_period
from forgebench.iteration.changelog import generate_whats_new_from_feedback
from forgebench.iteration.thanks import format_thank_you_response
from forgebench.roadmap_sync import format_roadmap_suggestions, update_roadmap


@dataclass(frozen=True)
class WeeklyReviewResult:
    digest_path: Path | None
    roadmap_path: Path | None
    whats_new_path: Path | None
    period: str


def run_weekly_review(
    *,
    feedback_log: str | Path = "forgebench-output/feedback.jsonl",
    period: str = "7d",
    output_dir: str | Path = "forgebench-output/weekly-review",
    apply_roadmap: bool = False,
    roadmap_path: str | Path | None = None,
) -> WeeklyReviewResult:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    logs = [Path(feedback_log)]

    digest = build_feedback_digest(logs, period=period)
    digest_text = format_feedback_digest(digest)
    digest_file = out / f"digest-{period}.txt"
    digest_file.write_text(digest_text + "\n", encoding="utf-8")

    roadmap_result = update_roadmap(
        roadmap_path=roadmap_path,
        feedback_logs=logs,
        period=period,
        apply=apply_roadmap,
    )
    roadmap_file = out / f"roadmap-suggestions-{period}.txt"
    roadmap_file.write_text(format_roadmap_suggestions(roadmap_result) + "\n", encoding="utf-8")

    whats_new = generate_whats_new_from_feedback(logs, period=period)
    whats_new_file = out / f"whats-new-{period}.md"
    whats_new_file.write_text(whats_new + "\n", encoding="utf-8")

    summary = out / "WEEKLY_REVIEW.md"
    summary.write_text(
        "\n".join(
            [
                "# ForgeBench Weekly Review",
                "",
                f"Period: {period}",
                "",
                "## Digest",
                f"See `{digest_file.name}`",
                "",
                "## Roadmap suggestions",
                f"See `{roadmap_file.name}`",
                "Apply: `forgebench roadmap update --apply --period " + period + "`",
                "",
                "## What's New draft",
                f"See `{whats_new_file.name}`",
                "",
                "## Thank-you template",
                format_thank_you_response(),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return WeeklyReviewResult(
        digest_path=digest_file,
        roadmap_path=roadmap_file,
        whats_new_path=whats_new_file,
        period=period,
    )


def format_weekly_review_result(result: WeeklyReviewResult) -> str:
    return "\n".join(
        [
            "ForgeBench weekly review complete",
            f"Period: {result.period}",
            f"Digest: {result.digest_path}",
            f"Roadmap suggestions: {result.roadmap_path}",
            f"What's New draft: {result.whats_new_path}",
        ]
    )