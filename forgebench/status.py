from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from forgebench import __version__
from forgebench.doctor import DoctorReport, run_doctor
from forgebench.telemetry import is_telemetry_enabled, telemetry_status
from forgebench.ux.output import heading, success, warn, write_kv


@dataclass(frozen=True)
class StatusReport:
    version: str
    doctor: DoctorReport
    guardrails_path: Path | None
    ci_guardrails_path: Path | None
    policy_tests_present: bool
    telemetry_enabled: bool
    telemetry_events: int
    recommendations: list[str] = field(default_factory=list)


def build_status_report(repo_path: str | Path = ".") -> StatusReport:
    repo = Path(repo_path).resolve()
    doctor = run_doctor(repo_path=repo)
    guardrails = repo / "forgebench.yml"
    ci_guardrails = repo / ".github" / "forgebench.yml"
    policy_tests = (repo / "examples" / "policy_tests").exists() or any(repo.glob("**/policy_test.json"))
    telemetry = telemetry_status()
    recommendations: list[str] = []
    if not guardrails.exists() and not ci_guardrails.exists():
        recommendations.append("Run `forgebench init` or `forgebench init --enterprise` to add guardrails.")
    if not doctor.ready:
        recommendations.append("Run `forgebench doctor` and fix failed checks.")
    elif doctor.has_warnings and not (repo / ".git").exists():
        recommendations.append("Initialize git for PR worktree checkout: `git init`")
    if not policy_tests:
        recommendations.append("Add policy tests under examples/policy_tests/ for team policy regression.")
    recommendations.append("Try `forgebench demo` for a guided first review.")
    return StatusReport(
        version=__version__,
        doctor=doctor,
        guardrails_path=guardrails if guardrails.exists() else None,
        ci_guardrails_path=ci_guardrails if ci_guardrails.exists() else None,
        policy_tests_present=policy_tests,
        telemetry_enabled=is_telemetry_enabled(),
        telemetry_events=telemetry.event_count,
        recommendations=recommendations,
    )


def format_status_report(report: StatusReport) -> str:
    lines: list[str] = []
    lines.append("ForgeBench status")
    lines.append(f"Version: {report.version}")
    lines.append("")
    lines.append("Health")
    for check in report.doctor.checks:
        prefix = check.status.value.upper()
        lines.append(f"  [{prefix}] {check.name}: {check.message}")
    lines.append("")
    lines.append("Configuration")
    lines.append(f"  guardrails: {report.guardrails_path or 'not found'}")
    lines.append(f"  ci guardrails: {report.ci_guardrails_path or 'not found'}")
    lines.append(f"  policy tests: {'yes' if report.policy_tests_present else 'no'}")
    lines.append(f"  telemetry: {'enabled' if report.telemetry_enabled else 'disabled'} ({report.telemetry_events} events)")
    lines.append("")
    lines.append("Next steps")
    for item in report.recommendations:
        lines.append(f"  - {item}")
    return "\n".join(lines) + "\n"


def print_status_report(report: StatusReport) -> None:
    heading(f"ForgeBench {report.version}")
    heading("Health")
    for check in report.doctor.checks:
        if check.status.value == "ok":
            success(f"{check.name}: {check.message}")
        elif check.status.value == "warn":
            warn(f"{check.name}: {check.message}")
        else:
            from forgebench.ux.output import error

            error(f"{check.name}: {check.message}")
    heading("Configuration")
    write_kv("guardrails", str(report.guardrails_path or "not found"))
    write_kv("ci guardrails", str(report.ci_guardrails_path or "not found"))
    write_kv("policy tests", "yes" if report.policy_tests_present else "no")
    write_kv("telemetry", f"{'enabled' if report.telemetry_enabled else 'disabled'} ({report.telemetry_events} events)")
    heading("Next steps")
    for item in report.recommendations:
        info(f"• {item}")


def info(text: str) -> None:
    from forgebench.ux.output import info as _info

    _info(text)