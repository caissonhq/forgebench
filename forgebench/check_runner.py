from __future__ import annotations

import subprocess
import time
from pathlib import Path

from forgebench.models import (
    CheckCommand,
    CheckResult,
    CheckStatus,
    Confidence,
    DeterministicChecks,
    EvidenceType,
    Finding,
    Guardrails,
    Severity,
)


STANDARD_CHECKS = ("build", "test", "lint", "typecheck")
MAX_EXCERPT_LENGTH = 4000


def build_check_commands(guardrails: Guardrails) -> list[CheckCommand]:
    if not guardrails.checks_present:
        return []

    commands = [
        CheckCommand(name=name, command=guardrails.checks.get(name), timeout_seconds=guardrails.check_timeout_seconds)
        for name in STANDARD_CHECKS
        if name in guardrails.checks or guardrails.checks_present
    ]
    commands.extend(
        CheckCommand(
            name=f"custom.{name}",
            command=command,
            timeout_seconds=guardrails.check_timeout_seconds,
        )
        for name, command in sorted(guardrails.custom_checks.items())
    )
    return commands


def run_configured_checks(repo_path: str | Path, guardrails: Guardrails) -> DeterministicChecks:
    repo = Path(repo_path)
    if not repo.exists() or not repo.is_dir():
        return DeterministicChecks(
            run_requested=True,
            results=[
                CheckResult(
                    name="repo",
                    command=None,
                    status=CheckStatus.ERROR,
                    error_message=f"Repo path does not exist or is not a directory: {repo}",
                )
            ],
        )

    results = [run_check_command(command, repo) for command in build_check_commands(guardrails)]
    return DeterministicChecks(run_requested=True, results=results)


def checks_not_run() -> DeterministicChecks:
    return DeterministicChecks(run_requested=False, results=[])


def run_check_command(check: CheckCommand, repo_path: str | Path) -> CheckResult:
    command = (check.command or "").strip() if check.command else ""
    if not command:
        return CheckResult(
            name=check.name,
            command=check.command,
            status=CheckStatus.NOT_CONFIGURED,
            skipped=True,
            error_message="No command configured for this check.",
        )

    start = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=Path(repo_path),
            shell=True,
            text=True,
            capture_output=True,
            timeout=check.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        return CheckResult(
            name=check.name,
            command=command,
            status=CheckStatus.TIMED_OUT,
            duration_seconds=_duration(duration),
            stdout_excerpt=_truncate(_coerce_output(exc.stdout)),
            stderr_excerpt=_truncate(_coerce_output(exc.stderr)),
            timed_out=True,
            error_message=f"Command timed out after {check.timeout_seconds} seconds.",
        )
    except OSError as exc:
        duration = time.monotonic() - start
        return CheckResult(
            name=check.name,
            command=command,
            status=CheckStatus.ERROR,
            duration_seconds=_duration(duration),
            error_message=str(exc),
        )

    duration = time.monotonic() - start
    stdout_excerpt = _truncate(completed.stdout)
    stderr_excerpt = _truncate(completed.stderr)
    status = _status_for_exit_code(completed.returncode, stderr_excerpt)
    return CheckResult(
        name=check.name,
        command=command,
        status=status,
        exit_code=completed.returncode,
        duration_seconds=_duration(duration),
        stdout_excerpt=stdout_excerpt,
        stderr_excerpt=stderr_excerpt,
        error_message=_error_message(status, completed.returncode, stderr_excerpt),
    )


def findings_from_check_results(results: list[CheckResult]) -> list[Finding]:
    findings: list[Finding] = []
    for result in results:
        if result.status in {CheckStatus.PASSED, CheckStatus.NOT_CONFIGURED, CheckStatus.SKIPPED}:
            continue
        if result.status == CheckStatus.TIMED_OUT:
            findings.append(_timeout_finding(result))
        elif result.status in {CheckStatus.FAILED, CheckStatus.ERROR}:
            findings.append(_failed_finding(result))
    return findings


def _failed_finding(result: CheckResult) -> Finding:
    check_kind = _check_kind(result.name)
    finding_id = _failed_id(check_kind)
    severity = Severity.MEDIUM if check_kind == "lint" else Severity.BLOCKER
    if check_kind == "custom":
        severity = Severity.HIGH
    title = _failed_title(check_kind, result.name)
    explanation = _failed_explanation(result)
    return Finding(
        id=finding_id,
        title=title,
        severity=severity,
        confidence=Confidence.HIGH,
        evidence_type=EvidenceType.DETERMINISTIC,
        files=[],
        evidence=_result_evidence(result),
        explanation=explanation,
        suggested_fix=_suggested_fix(check_kind, timed_out=False),
    )


def _timeout_finding(result: CheckResult) -> Finding:
    check_kind = _check_kind(result.name)
    finding_id = _timeout_id(check_kind)
    severity = Severity.MEDIUM if check_kind in {"lint", "custom"} else Severity.HIGH
    title = _timeout_title(check_kind, result.name)
    return Finding(
        id=finding_id,
        title=title,
        severity=severity,
        confidence=Confidence.MEDIUM,
        evidence_type=EvidenceType.DETERMINISTIC,
        files=[],
        evidence=_result_evidence(result),
        explanation=(
            f"The configured {result.name} command timed out after running for "
            f"{result.duration_seconds:.2f}s. This leaves the local verification result incomplete."
        ),
        suggested_fix=_suggested_fix(check_kind, timed_out=True),
    )


def _status_for_exit_code(exit_code: int, stderr_excerpt: str) -> CheckStatus:
    if exit_code == 0:
        return CheckStatus.PASSED
    if exit_code in {126, 127} and ("not found" in stderr_excerpt.lower() or "not recognized" in stderr_excerpt.lower()):
        return CheckStatus.ERROR
    return CheckStatus.FAILED


def _error_message(status: CheckStatus, exit_code: int, stderr_excerpt: str) -> str | None:
    if status == CheckStatus.ERROR:
        return stderr_excerpt.strip() or f"Command could not be executed; exit code {exit_code}."
    if status == CheckStatus.FAILED:
        return f"Command exited with code {exit_code}."
    return None


def _check_kind(name: str) -> str:
    if name.startswith("custom."):
        return "custom"
    if name in STANDARD_CHECKS:
        return name
    return "custom"


def _failed_id(check_kind: str) -> str:
    if check_kind == "build":
        return "build_failed"
    if check_kind == "test":
        return "tests_failed"
    if check_kind == "lint":
        return "lint_failed"
    if check_kind == "typecheck":
        return "typecheck_failed"
    return "custom_check_failed"


def _timeout_id(check_kind: str) -> str:
    if check_kind == "build":
        return "build_timed_out"
    if check_kind == "test":
        return "tests_timed_out"
    if check_kind == "lint":
        return "lint_timed_out"
    if check_kind == "typecheck":
        return "typecheck_timed_out"
    return "custom_check_timed_out"


def _failed_title(check_kind: str, name: str) -> str:
    if check_kind == "build":
        return "Configured build command failed"
    if check_kind == "test":
        return "Configured test command failed"
    if check_kind == "lint":
        return "Configured lint command failed"
    if check_kind == "typecheck":
        return "Configured typecheck command failed"
    return f"Configured custom check failed: {name}"


def _timeout_title(check_kind: str, name: str) -> str:
    if check_kind == "build":
        return "Configured build command timed out"
    if check_kind == "test":
        return "Configured test command timed out"
    if check_kind == "lint":
        return "Configured lint command timed out"
    if check_kind == "typecheck":
        return "Configured typecheck command timed out"
    return f"Configured custom check timed out: {name}"


def _failed_explanation(result: CheckResult) -> str:
    if result.status == CheckStatus.ERROR:
        return (
            f"The configured {result.name} command could not be executed cleanly. "
            "This is deterministic evidence that local verification is not currently usable."
        )
    return (
        f"The configured {result.name} command failed with exit code {result.exit_code}. "
        "This is deterministic evidence that the current repo state does not pass that local verification step."
    )


def _suggested_fix(check_kind: str, timed_out: bool) -> str:
    if timed_out:
        return "Investigate why the configured command timed out, rerun it locally, and rerun ForgeBench."
    if check_kind == "build":
        return "Fix the build failure so the configured build command passes, then rerun ForgeBench."
    if check_kind == "test":
        return "Fix the failing tests or update the implementation so the configured test command passes, then rerun ForgeBench."
    if check_kind == "typecheck":
        return "Fix the type errors so the configured typecheck command passes, then rerun ForgeBench."
    if check_kind == "lint":
        return "Fix the lint failure or explain why the configured lint rule is not applicable, then rerun ForgeBench."
    return "Fix the custom check failure or explain why the custom check is no longer applicable, then rerun ForgeBench."


def _result_evidence(result: CheckResult) -> list[str]:
    evidence = [
        f"Check: {result.name}",
        f"Command: {result.command or '(not configured)'}",
        f"Status: {result.status.value}",
        f"Duration: {result.duration_seconds:.2f}s",
    ]
    if result.exit_code is not None:
        evidence.append(f"Exit code: {result.exit_code}")
    if result.error_message:
        evidence.append(f"Error: {result.error_message}")
    if result.stdout_excerpt:
        evidence.append("stdout excerpt: " + _single_line(result.stdout_excerpt))
    if result.stderr_excerpt:
        evidence.append("stderr excerpt: " + _single_line(result.stderr_excerpt))
    return evidence


def _truncate(output: str) -> str:
    if len(output) <= MAX_EXCERPT_LENGTH:
        return output
    return output[:MAX_EXCERPT_LENGTH].rstrip() + "\n[truncated]"


def _coerce_output(output: object) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return str(output)


def _duration(duration: float) -> float:
    return round(duration, 2)


def _single_line(value: str) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= 500:
        return collapsed
    return collapsed[:497].rstrip() + "..."
