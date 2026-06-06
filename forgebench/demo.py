from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from forgebench.review import ReviewInputError, run_review
from forgebench.ux.output import heading, info, progress, success, write_kv


DEFAULT_DEMO_CASE = "generic_dependency_without_tests_review"


@dataclass(frozen=True)
class DemoResult:
    case_name: str
    case_dir: Path
    output_dir: Path
    posture: str
    finding_count: int
    report_markdown: Path
    report_json: Path
    repair_prompt: Path


def resolve_demo_case_dir(case_name: str = DEFAULT_DEMO_CASE) -> Path:
    root = Path(__file__).resolve().parents[1]
    case_dir = root / "examples" / "golden_cases" / case_name
    if not case_dir.is_dir():
        raise ReviewInputError(f"demo case not found: {case_name}")
    for name in ("patch.diff", "task.md"):
        if not (case_dir / name).exists():
            raise ReviewInputError(f"demo case missing {name}: {case_dir}")
    return case_dir


def run_demo(
    *,
    repo_path: str | Path = ".",
    output_dir: str | Path | None = None,
    case_name: str = DEFAULT_DEMO_CASE,
) -> DemoResult:
    repo = Path(repo_path).resolve()
    case_dir = resolve_demo_case_dir(case_name)
    out = Path(output_dir) if output_dir else repo / "forgebench-output" / "demo"
    out.mkdir(parents=True, exist_ok=True)

    from forgebench.ux.output import is_rich_output_enabled

    if is_rich_output_enabled():
        heading("ForgeBench Demo")
        info("Running a realistic merge-risk review using a curated golden case.")
        write_kv("Case", case_name)
        write_kv("Repository", str(repo))
        write_kv("Output", str(out))
        progress("Copying demo inputs")
    diff_copy = out / "demo.patch.diff"
    task_copy = out / "demo.task.md"
    shutil.copy2(case_dir / "patch.diff", diff_copy)
    shutil.copy2(case_dir / "task.md", task_copy)

    if is_rich_output_enabled():
        progress("Reviewing diff (generic mode — no guardrails required)")
    result = run_review(
        repo_path=repo,
        diff_path=diff_copy,
        task_path=task_copy,
        guardrails_path=None,
        output_dir=out,
        run_checks=False,
        reviewers_enabled=True,
        semantic_analysis=False,
    )
    report = result.report
    if is_rich_output_enabled():
        success(f"Demo complete — posture: {report.posture.value}")
        write_kv("Findings", str(len(report.findings)))
        info("Open forgebench-output/demo/forgebench-report.md or run `forgebench repair --out forgebench-output/demo`")

    return DemoResult(
        case_name=case_name,
        case_dir=case_dir,
        output_dir=out,
        posture=report.posture.value,
        finding_count=len(report.findings),
        report_markdown=result.written_paths["markdown"],
        report_json=result.written_paths["json"],
        repair_prompt=result.written_paths["repair_prompt"],
    )


def format_demo_result(result: DemoResult) -> str:
    return "\n".join(
        [
            "ForgeBench demo complete.",
            f"Case: {result.case_name}",
            f"Posture: {result.posture}",
            f"Findings: {result.finding_count}",
            f"Report: {result.report_markdown}",
            f"Repair prompt: {result.repair_prompt}",
            "",
            "Next: forgebench init --enterprise   # team starter kit",
            "      forgebench doctor              # onboarding checklist",
        ]
    ) + "\n"