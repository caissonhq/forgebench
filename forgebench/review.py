from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from forgebench.check_runner import checks_not_run, findings_from_check_results, run_configured_checks
from forgebench.diff_parser import parse_diff_file
from forgebench.guardrails import evaluate_guardrails, load_guardrails
from forgebench.llm_review import apply_llm_posture, build_review_bundle, llm_review_not_run, run_llm_review
from forgebench.models import Finding, ForgeBenchReport, Guardrails, LLMReviewerConfig
from forgebench.policy import apply_guardrails_policy
from forgebench.posture import determine_posture
from forgebench.report_writer import write_reports
from forgebench.static_checks import run_static_checks


class ReviewInputError(ValueError):
    pass


@dataclass(frozen=True)
class ReviewResult:
    report: ForgeBenchReport
    written_paths: dict[str, Path]
    task_text: str
    guardrails: Guardrails
    output_dir: Path


def run_review(
    repo_path: str | Path,
    diff_path: str | Path,
    task_path: str | Path,
    guardrails_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    run_checks: bool = False,
    llm_review: bool = False,
    llm_provider: str | None = None,
    llm_command: str | None = None,
    llm_timeout: int = 60,
    llm_max_diff_chars: int = 20000,
    llm_mock_response: dict | None = None,
    input_notes: list[str] | None = None,
) -> ReviewResult:
    repo = Path(repo_path)
    diff = _resolve_input_path(Path(diff_path), repo)
    task = _resolve_input_path(Path(task_path), repo)
    guardrails_file = _resolve_input_path(Path(guardrails_path), repo) if guardrails_path else None
    out_dir = Path(output_dir) if output_dir else Path("forgebench-output")

    _validate_inputs(repo, diff, task, guardrails_file)

    task_text = task.read_text(encoding="utf-8", errors="replace")
    diff_text = diff.read_text(encoding="utf-8", errors="replace")
    diff_summary = parse_diff_file(diff)
    guardrails = load_guardrails(guardrails_file)
    deterministic_checks = run_configured_checks(repo, guardrails) if run_checks else checks_not_run()

    deterministic_findings = findings_from_check_results(deterministic_checks.results)
    static_findings, static_signals = run_static_checks(diff_summary)
    guardrail_findings, guardrail_hits = evaluate_guardrails(diff_summary, guardrails)
    findings = _dedupe_findings(deterministic_findings + static_findings + guardrail_findings)
    findings, static_signals, policy_decision = apply_guardrails_policy(diff_summary, findings, static_signals, guardrails)
    pre_llm_posture, pre_llm_summary = determine_posture(findings, static_signals, guardrail_hits, deterministic_checks, policy_decision)

    llm_config = LLMReviewerConfig(
        enabled=llm_review,
        provider=llm_provider,
        command=llm_command,
        timeout_seconds=llm_timeout,
        max_diff_chars=llm_max_diff_chars,
        mock_response=llm_mock_response,
    )
    if llm_review:
        bundle = build_review_bundle(
            task_text=task_text,
            diff_text=diff_text,
            diff_summary=diff_summary,
            guardrails=guardrails,
            findings=findings,
            pre_llm_posture=pre_llm_posture,
            pre_llm_summary=pre_llm_summary,
            deterministic_checks=deterministic_checks,
            policy=policy_decision,
            config=llm_config,
        )
        llm_result = run_llm_review(llm_config, bundle, findings)
    else:
        llm_result = llm_review_not_run()

    findings = _dedupe_findings(findings + llm_result.findings)
    posture, summary = apply_llm_posture(pre_llm_posture, pre_llm_summary, llm_result)

    report = ForgeBenchReport(
        posture=posture,
        summary=summary,
        task_summary=_task_summary(task_text),
        changed_files=diff_summary.changed_files,
        findings=findings,
        static_signals=static_signals,
        guardrail_hits=guardrail_hits,
        deterministic_checks=deterministic_checks,
        policy=policy_decision,
        llm_review=llm_result,
        pre_llm_posture=pre_llm_posture,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    written = write_reports(
        out_dir,
        report,
        guardrails,
        task_text,
        inputs={
            "repo": str(repo),
            "diff": str(diff),
            "task": str(task),
            "guardrails": str(guardrails_file) if guardrails_file else "none",
            "notes": list(input_notes or []),
        },
    )
    return ReviewResult(
        report=report,
        written_paths=written,
        task_text=task_text,
        guardrails=guardrails,
        output_dir=out_dir,
    )


def _validate_inputs(repo_path: Path, diff_path: Path, task_path: Path, guardrails_path: Path | None) -> None:
    if not repo_path.exists() or not repo_path.is_dir():
        raise ReviewInputError(f"repo path does not exist or is not a directory: {repo_path}")
    if not diff_path.exists() or not diff_path.is_file():
        raise ReviewInputError(f"diff file does not exist: {diff_path}")
    if not task_path.exists() or not task_path.is_file():
        raise ReviewInputError(f"task file does not exist: {task_path}")
    if guardrails_path is not None and (not guardrails_path.exists() or not guardrails_path.is_file()):
        raise ReviewInputError(f"guardrails file does not exist: {guardrails_path}")


def _resolve_input_path(path: Path, repo_path: Path) -> Path:
    if path.exists() or path.is_absolute():
        return path
    repo_relative = repo_path / path
    if repo_relative.exists():
        return repo_relative
    return path


def _task_summary(task_text: str) -> str:
    collapsed = " ".join(task_text.split())
    if len(collapsed) <= 220:
        return collapsed
    return collapsed[:217].rstrip() + "..."


def _dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    deduped: list[Finding] = []
    for finding in findings:
        key = (finding.id, tuple(sorted(finding.files)))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped
