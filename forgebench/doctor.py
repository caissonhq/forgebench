from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

from forgebench import __version__


class DoctorStatus(str, Enum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: DoctorStatus
    message: str
    fix_hint: str | None = None


@dataclass(frozen=True)
class DoctorReport:
    checks: list[DoctorCheck]

    @property
    def exit_code(self) -> int:
        if any(check.status == DoctorStatus.FAIL for check in self.checks):
            return 2
        return 0

    @property
    def ready(self) -> bool:
        return not any(check.status == DoctorStatus.FAIL for check in self.checks)

    @property
    def has_warnings(self) -> bool:
        return any(check.status == DoctorStatus.WARN for check in self.checks)


def run_doctor(repo_path: str | Path | None = None) -> DoctorReport:
    repo = Path(repo_path or ".").resolve()
    checks = [
        _check_python_version(),
        _check_forgebench_import(),
        _check_pyyaml(),
        _check_git(),
        _check_gh(),
        _check_gh_auth(),
        _check_writable_output(repo),
        _check_repo_path(repo),
        _check_telemetry_opt_in(),
        _check_guardrails(repo),
        _check_ci_workflow(repo),
        _check_demo_available(),
        _check_onboarding_docs(repo),
    ]
    return DoctorReport(checks=checks)


def format_doctor_report(report: DoctorReport, *, repo_path: str | Path | None = None, include_checklist: bool = False) -> str:
    repo = Path(repo_path or ".").resolve()
    lines = [
        "ForgeBench doctor",
        f"Version: {__version__}",
        "",
    ]
    for check in report.checks:
        label = check.status.value.upper()
        lines.append(f"[{label}] {check.name}: {check.message}")
        if check.fix_hint and check.status != DoctorStatus.OK:
            lines.append(f"       fix: {check.fix_hint}")
    lines.append("")
    if include_checklist:
        from forgebench.adoption import build_success_checklist, format_success_checklist

        lines.append(format_success_checklist(build_success_checklist(repo_path=repo)))
        lines.append("")
    from forgebench.adoption import doctor_next_steps

    for step in doctor_next_steps(repo_path=repo, doctor_ready=report.ready, has_warnings=report.has_warnings):
        lines.append(step)
    return "\n".join(lines)


def _check_python_version() -> DoctorCheck:
    version = sys.version_info
    if (version.major, version.minor) >= (3, 10):
        return DoctorCheck(
            name="python",
            status=DoctorStatus.OK,
            message=f"{version.major}.{version.minor}.{version.micro}",
        )
    return DoctorCheck(
        name="python",
        status=DoctorStatus.FAIL,
        message=f"{version.major}.{version.minor}.{version.micro} (requires >= 3.10)",
        fix_hint="Install Python 3.10 or newer.",
    )


def _check_forgebench_import() -> DoctorCheck:
    try:
        import forgebench  # noqa: F401
    except ImportError as exc:
        return DoctorCheck(
            name="forgebench",
            status=DoctorStatus.FAIL,
            message=f"package import failed: {exc}",
            fix_hint="Run: pip install forgebench",
        )
    return DoctorCheck(
        name="forgebench",
        status=DoctorStatus.OK,
        message=f"import ok ({__version__})",
    )


def _check_pyyaml() -> DoctorCheck:
    if importlib.util.find_spec("yaml") is None:
        return DoctorCheck(
            name="pyyaml",
            status=DoctorStatus.FAIL,
            message="PyYAML is not installed",
            fix_hint="Run: pip install forgebench",
        )
    return DoctorCheck(name="pyyaml", status=DoctorStatus.OK, message="installed")


def _check_git() -> DoctorCheck:
    git_path = shutil.which("git")
    if not git_path:
        return DoctorCheck(
            name="git",
            status=DoctorStatus.FAIL,
            message="git not found on PATH",
            fix_hint="Install git. PR worktree checkout requires it.",
        )
    completed = _run_quiet([git_path, "--version"])
    if completed is None or completed.returncode != 0:
        detail = _command_detail(completed)
        return DoctorCheck(
            name="git",
            status=DoctorStatus.FAIL,
            message=f"git is present but not runnable ({detail})",
            fix_hint="Repair your git installation.",
        )
    version = (completed.stdout or completed.stderr or "").strip().splitlines()[0]
    return DoctorCheck(name="git", status=DoctorStatus.OK, message=version or "available")


def _check_gh() -> DoctorCheck:
    gh_path = shutil.which("gh")
    if not gh_path:
        return DoctorCheck(
            name="github_cli",
            status=DoctorStatus.WARN,
            message="gh not found on PATH",
            fix_hint="Install GitHub CLI for review-pr: https://cli.github.com/",
        )
    completed = _run_quiet([gh_path, "--version"])
    if completed is None or completed.returncode != 0:
        detail = _command_detail(completed)
        return DoctorCheck(
            name="github_cli",
            status=DoctorStatus.WARN,
            message=f"gh is present but not runnable ({detail})",
            fix_hint="Repair your GitHub CLI installation.",
        )
    version = (completed.stdout or completed.stderr or "").strip().splitlines()[0]
    return DoctorCheck(name="github_cli", status=DoctorStatus.OK, message=version or "available")


def _check_gh_auth() -> DoctorCheck:
    gh_path = shutil.which("gh")
    if not gh_path:
        return DoctorCheck(
            name="github_auth",
            status=DoctorStatus.WARN,
            message="skipped because gh is not installed",
            fix_hint="Install gh, then run: gh auth login",
        )
    completed = _run_quiet([gh_path, "auth", "status"])
    if completed is None:
        return DoctorCheck(
            name="github_auth",
            status=DoctorStatus.WARN,
            message="could not verify gh auth",
            fix_hint="Run: gh auth login",
        )
    if completed.returncode == 0:
        return DoctorCheck(name="github_auth", status=DoctorStatus.OK, message="authenticated")
    detail = _command_detail(completed)
    return DoctorCheck(
        name="github_auth",
        status=DoctorStatus.WARN,
        message=f"not authenticated ({detail})",
        fix_hint="Run: gh auth login",
    )


def _check_writable_output(repo: Path) -> DoctorCheck:
    candidates = [repo / "forgebench-output", Path.cwd() / "forgebench-output"]
    seen: set[Path] = set()
    errors: list[str] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".doctor-write-test"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
        except OSError as exc:
            errors.append(f"{candidate}: {exc}")
            continue
        return DoctorCheck(
            name="output_dir",
            status=DoctorStatus.OK,
            message=f"writable at {candidate}",
        )
    return DoctorCheck(
        name="output_dir",
        status=DoctorStatus.FAIL,
        message="; ".join(errors) or "no writable forgebench-output directory",
        fix_hint="Choose a repo path with write permission or run from a writable directory.",
    )


def _check_telemetry_opt_in() -> DoctorCheck:
    try:
        from forgebench.telemetry import is_telemetry_enabled

        if is_telemetry_enabled():
            return DoctorCheck(
                name="telemetry",
                status=DoctorStatus.OK,
                message="opt-in telemetry enabled (local-only, anonymized)",
            )
    except Exception:
        pass
    return DoctorCheck(
        name="telemetry",
        status=DoctorStatus.OK,
        message="disabled by default; enable with forgebench telemetry enable",
    )


def _check_guardrails(repo: Path) -> DoctorCheck:
    root_guardrails = repo / "forgebench.yml"
    ci_guardrails = repo / ".github" / "forgebench.yml"
    if root_guardrails.exists() or ci_guardrails.exists():
        found = root_guardrails if root_guardrails.exists() else ci_guardrails
        return DoctorCheck(
            name="guardrails",
            status=DoctorStatus.OK,
            message=f"found at {found}",
        )
    return DoctorCheck(
        name="guardrails",
        status=DoctorStatus.WARN,
        message="no forgebench.yml found",
        fix_hint="Run: forgebench init --repo . --out forgebench.yml (or forgebench init --enterprise)",
    )


def _check_ci_workflow(repo: Path) -> DoctorCheck:
    workflow = repo / ".github" / "workflows" / "forgebench.yml"
    if workflow.exists():
        return DoctorCheck(
            name="ci_workflow",
            status=DoctorStatus.OK,
            message=f"ForgeBench workflow at {workflow}",
        )
    return DoctorCheck(
        name="ci_workflow",
        status=DoctorStatus.WARN,
        message="no .github/workflows/forgebench.yml",
        fix_hint="Run: forgebench init --enterprise to generate CI workflow and trusted guardrails",
    )


def _check_demo_available() -> DoctorCheck:
    demo_case = Path(__file__).resolve().parents[1] / "examples" / "golden_cases" / "generic_dependency_without_tests_review"
    if demo_case.is_dir() and (demo_case / "patch.diff").exists():
        return DoctorCheck(
            name="demo",
            status=DoctorStatus.OK,
            message="demo case bundled; run forgebench demo",
        )
    return DoctorCheck(
        name="demo",
        status=DoctorStatus.WARN,
        message="demo case not found in package",
        fix_hint="Reinstall forgebench or run from the source repository",
    )


def _check_onboarding_docs(repo: Path) -> DoctorCheck:
    onboarding = repo / "docs" / "forgebench-onboarding.md"
    if onboarding.exists():
        return DoctorCheck(
            name="onboarding",
            status=DoctorStatus.OK,
            message=f"team guide at {onboarding}",
        )
    return DoctorCheck(
        name="onboarding",
        status=DoctorStatus.WARN,
        message="no docs/forgebench-onboarding.md",
        fix_hint="Run: forgebench init --enterprise for team onboarding docs",
    )


def _check_repo_path(repo: Path) -> DoctorCheck:
    if not repo.exists():
        return DoctorCheck(
            name="repo",
            status=DoctorStatus.FAIL,
            message=f"path does not exist: {repo}",
            fix_hint="Pass --repo . from inside your repository.",
        )
    if not repo.is_dir():
        return DoctorCheck(
            name="repo",
            status=DoctorStatus.FAIL,
            message=f"path is not a directory: {repo}",
            fix_hint="Pass a directory path with --repo.",
        )
    git_dir = repo / ".git"
    if git_dir.exists():
        return DoctorCheck(name="repo", status=DoctorStatus.OK, message=f"git repo at {repo}")
    return DoctorCheck(
        name="repo",
        status=DoctorStatus.WARN,
        message=f"directory exists but is not a git repo: {repo}",
        fix_hint="review-pr still works with gh, but worktree checkout needs a git repository.",
    )


def _run_quiet(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _command_detail(completed: subprocess.CompletedProcess[str] | None) -> str:
    if completed is None:
        return "command failed"
    detail = (completed.stderr or completed.stdout or "").strip()
    if not detail:
        return f"exit code {completed.returncode}"
    return " ".join(detail.split())