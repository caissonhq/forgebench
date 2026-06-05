from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forgebench.calibration import CalibrationResult, run_calibration


@dataclass(frozen=True)
class BenchmarkSnapshot:
    case_count: int
    passed_count: int
    failed_count: int
    posture_distribution: dict[str, int]
    top_finding_kinds: dict[str, int]
    review_lens_fire_rate: dict[str, int]


def build_benchmark_snapshot(
    cases_dir: str | Path,
    *,
    repo_path: str | Path = ".",
    output_dir: str | Path | None = None,
) -> BenchmarkSnapshot:
    result = run_calibration(
        cases_dir=cases_dir,
        output_dir=output_dir or Path("forgebench-benchmark-output"),
        repo_path=repo_path,
    )
    return snapshot_from_calibration(result)


def snapshot_from_calibration(result: CalibrationResult) -> BenchmarkSnapshot:
    return BenchmarkSnapshot(
        case_count=len(result.cases),
        passed_count=result.passed_count,
        failed_count=result.failed_count,
        posture_distribution=dict(result.posture_distribution),
        top_finding_kinds=dict(result.finding_kind_counts),
        review_lens_fire_rate=dict(result.review_lens_counts),
    )


def format_benchmark_markdown(snapshot: BenchmarkSnapshot, *, cases_dir: str | Path) -> str:
    cases_path = Path(cases_dir)
    lines = [
        "# Merge Risk Benchmark",
        "",
        "ForgeBench's Merge Risk Benchmark measures whether a serious engineer would merge an AI-generated diff.",
        "",
        "SWE-Bench asks whether an agent solved the task. This benchmark asks whether the resulting patch is safe to merge.",
        "",
        "## Snapshot",
        "",
        f"- Golden cases: **{snapshot.case_count}**",
        f"- Calibration pass rate: **{snapshot.passed_count}/{snapshot.case_count}** ({_pass_rate(snapshot)}%)",
        f"- Corpus path: `{cases_path}`",
        "",
        "## Posture distribution",
        "",
        "Each case expects a merge posture (`BLOCK`, `REVIEW`, or `LOW_CONCERN`). Distribution across the corpus:",
        "",
        f"- BLOCK: {snapshot.posture_distribution.get('BLOCK', 0)}",
        f"- REVIEW: {snapshot.posture_distribution.get('REVIEW', 0)}",
        f"- LOW_CONCERN: {snapshot.posture_distribution.get('LOW_CONCERN', 0)}",
        "",
        "## Top finding kinds",
        "",
        "Most common finding kinds surfaced across the corpus:",
        "",
    ]
    if snapshot.top_finding_kinds:
        for kind, count in list(snapshot.top_finding_kinds.items())[:15]:
            lines.append(f"- `{kind}`: {count}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Review lens fire-rate",
            "",
            "Heuristic lenses that produced at least one finding:",
            "",
        ]
    )
    if snapshot.review_lens_fire_rate:
        for lens, count in snapshot.review_lens_fire_rate.items():
            lines.append(f"- {lens}: {count}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Methodology",
            "",
            "1. Each golden case includes a realistic unified diff, original task prompt, and expected merge posture.",
            "2. ForgeBench runs the full local review pipeline: static signals, guardrails, heuristic lenses, and optional LLM cases.",
            "3. Calibration passes when posture, required findings, and artifact shape match the case contract.",
            "4. This is a product-quality regression suite, not a leaderboard. It guards merge-judgment drift as reviewers evolve.",
            "",
            "## Reproduce locally",
            "",
            "```bash",
            "pip install forgebench",
            f"forgebench benchmark --cases {cases_path}",
            "forgebench calibrate --cases examples/golden_cases --repo .",
            "```",
            "",
            "## What this is not",
            "",
            "- Not a hosted leaderboard or public submission portal.",
            "- Not a proof that ForgeBench certifies code as safe.",
            "- Not a replacement for repo-specific guardrails or human review.",
            "",
            "ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.",
        ]
    )
    return "\n".join(lines) + "\n"


def _pass_rate(snapshot: BenchmarkSnapshot) -> str:
    if snapshot.case_count == 0:
        return "0.0"
    rate = 100.0 * snapshot.passed_count / snapshot.case_count
    return f"{rate:.1f}"