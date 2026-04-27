from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath

from forgebench.adversaries import run_specialized_reviewers, specialized_reviewers_not_run
from forgebench.adversaries.models import ReviewerContext
from forgebench.check_runner import checks_not_run, findings_from_check_results, run_configured_checks
from forgebench.diff_parser import parse_diff_file
from forgebench.guardrails import GuardrailsParseError, evaluate_guardrails, load_guardrails
from forgebench.llm_review import apply_llm_posture, build_review_bundle, llm_review_not_run, llm_review_skipped, run_llm_review
from forgebench.models import Finding, ForgeBenchReport, Guardrails, LLMReviewerConfig, PRCheckoutInfo
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
    pr_checkout: PRCheckoutInfo | None = None,
    reviewers_enabled: bool = True,
) -> ReviewResult:
    repo = Path(repo_path)
    diff = _resolve_input_path(Path(diff_path), repo)
    task = _resolve_input_path(Path(task_path), repo)
    guardrails_file = _resolve_guardrails_path(repo, guardrails_path)
    config_mode = "configured" if guardrails_file else "generic"
    first_run_guidance = config_mode == "generic"
    out_dir = Path(output_dir) if output_dir else Path("forgebench-output")

    _validate_inputs(repo, diff, task, guardrails_file)

    task_text = task.read_text(encoding="utf-8", errors="replace")
    diff_text = diff.read_text(encoding="utf-8", errors="replace")
    diff_summary = parse_diff_file(diff)
    try:
        guardrails = load_guardrails(guardrails_file)
    except GuardrailsParseError as exc:
        raise ReviewInputError(str(exc)) from exc
    deterministic_checks = run_configured_checks(repo, guardrails) if run_checks else checks_not_run()

    deterministic_findings = findings_from_check_results(deterministic_checks.results)
    static_findings, static_signals = run_static_checks(diff_summary)
    guardrail_findings, guardrail_hits = evaluate_guardrails(diff_summary, guardrails)
    findings = _dedupe_findings(deterministic_findings + static_findings + guardrail_findings)
    findings, static_signals, policy_decision = apply_guardrails_policy(diff_summary, findings, static_signals, guardrails)
    static_signals["config_mode"] = config_mode
    findings = _apply_generic_mode_calibration(findings, diff_summary) if config_mode == "generic" else findings

    llm_config = LLMReviewerConfig(
        enabled=llm_review,
        provider=llm_provider,
        command=llm_command,
        timeout_seconds=llm_timeout,
        max_diff_chars=llm_max_diff_chars,
        mock_response=llm_mock_response,
    )
    if reviewers_enabled:
        specialized_reviewers = run_specialized_reviewers(
            ReviewerContext(
                task_text=task_text,
                diff=diff_summary,
                static_signals=static_signals,
                findings=findings,
                guardrails=guardrails,
                guardrail_hits=guardrail_hits,
                policy=policy_decision,
                deterministic_checks=deterministic_checks,
            ),
            llm_config=llm_config,
        )
    else:
        specialized_reviewers = specialized_reviewers_not_run()
    findings = _dedupe_findings(findings + specialized_reviewers.findings)

    pre_llm_posture, pre_llm_summary = determine_posture(
        findings,
        static_signals,
        guardrail_hits,
        deterministic_checks,
        policy_decision,
        config_mode=config_mode,
    )

    if llm_review and specialized_reviewers.metadata.get("llm_call_used"):
        llm_result = llm_review_skipped(
            "LLM call was used by a trigger-gated review lens; general LLM review was skipped to keep one LLM call per review.",
            provider=llm_provider or ("command" if llm_command else None),
        )
    elif llm_review:
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
        specialized_reviewers=specialized_reviewers,
        pre_llm_posture=pre_llm_posture,
        pr_checkout=pr_checkout or PRCheckoutInfo(),
        diff_summary=diff_summary,
        config_mode=config_mode,
        guardrails_source=str(guardrails_file) if guardrails_file else None,
        first_run_guidance=first_run_guidance,
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
            "notes": list(input_notes or []) + list(guardrails.warnings),
        },
    )
    return ReviewResult(
        report=report,
        written_paths=written,
        task_text=task_text,
        guardrails=guardrails,
        output_dir=out_dir,
    )


def _resolve_guardrails_path(repo: Path, guardrails_path: str | Path | None) -> Path | None:
    if guardrails_path:
        return _resolve_input_path(Path(guardrails_path), repo)
    candidate = repo / "forgebench.yml"
    return candidate if candidate.exists() else None


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


def _apply_generic_mode_calibration(findings: list[Finding], diff_summary) -> list[Finding]:
    calibrated: list[Finding] = []
    for finding in findings:
        if finding.id == "broad_file_surface" and _all_generic_low_noise_paths(diff_summary.changed_files):
            continue
        if finding.id == "implementation_without_tests":
            calibrated.append(
                replace(
                    finding,
                    title="Changed implementation files without test changes",
                    confidence=finding.confidence,
                    evidence=[
                        *finding.evidence,
                        "Generic mode: this signal may be noisy when tests live outside the changed paths or were not required by the task.",
                    ],
                    explanation=(
                        "The patch changes likely implementation files, but no likely test files changed. "
                        "In generic mode this is a review signal, not proof that coverage is missing; "
                        "some repos organize tests separately or rely on configured checks."
                    ),
                    suggested_fix=(
                        "Review whether the changed behavior needs tests. If the signal is noisy for this repo, "
                        "run forgebench init and tune guardrails or checks."
                    ),
                )
            )
            continue
        calibrated.append(finding)
    return calibrated


def _all_generic_low_noise_paths(paths: list[str]) -> bool:
    return bool(paths) and all(_is_generic_low_noise_path(path) for path in paths)


def _is_generic_low_noise_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    suffix = PurePosixPath(normalized).suffix
    if normalized.startswith(("docs/", "examples/golden_cases/", "examples/sample_report/")):
        return True
    if PurePosixPath(normalized).name in {"readme.md", "changelog.md", "contributing.md", "security.md"}:
        return True
    if suffix in {".md", ".markdown", ".rst", ".txt"}:
        return True
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".icns"}:
        return True
    if "assets.xcassets/" in normalized:
        return True
    return any(marker in normalized for marker in ("dist/", "build/", "deriveddata/", "node_modules/", ".pyc", ".ds_store"))


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
