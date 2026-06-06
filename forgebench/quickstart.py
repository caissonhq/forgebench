from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from forgebench.adoption import format_next_actions, next_actions_after_review, record_milestone
from forgebench.demo import run_demo
from forgebench.doctor import format_doctor_report, run_doctor
from forgebench.init import write_starter_guardrails
from forgebench.status import build_status_report, format_status_report
from forgebench.ux.output import heading, info, progress, success, write_kv


@dataclass(frozen=True)
class QuickstartResult:
    doctor_exit_code: int
    demo_posture: str
    guardrails_path: Path | None
    skipped_init: bool


def run_quickstart(
    *,
    repo_path: str | Path = ".",
    skip_init: bool = False,
    skip_demo: bool = False,
) -> QuickstartResult:
    repo = Path(repo_path).resolve()
    heading("ForgeBench Quickstart")
    info("Solo developer path — ~2 minutes to your first merge-risk review.")
    write_kv("Repository", str(repo))

    progress("Step 1/4 — Verify install")
    doctor = run_doctor(repo_path=repo)
    print(format_doctor_report(doctor))

    demo_posture = "skipped"
    if not skip_demo:
        progress("Step 2/4 — Run guided demo")
        demo = run_demo(repo_path=repo)
        demo_posture = demo.posture
        record_milestone("first_demo")
        success(f"Demo posture: {demo_posture}")

    progress("Step 3/4 — Health summary")
    status = build_status_report(repo_path=repo)
    print(format_status_report(status))

    guardrails_path: Path | None = None
    if not skip_init and not (repo / "forgebench.yml").exists():
        progress("Step 4/4 — Create starter guardrails")
        result = write_starter_guardrails(repo_path=repo)
        guardrails_path = result.path
        record_milestone("first_guardrails")
        success(f"Created {guardrails_path}")
    else:
        info("Step 4/4 — Skipped init (guardrails already exist or --skip-init)")
        if (repo / "forgebench.yml").exists():
            guardrails_path = repo / "forgebench.yml"

    record_milestone("first_install")
    record_milestone("quickstart_completed")
    actions = next_actions_after_review(
        posture=demo_posture if demo_posture != "skipped" else "REVIEW",
        config_mode="configured" if guardrails_path else "generic",
        finding_count=1 if demo_posture not in {"skipped", "LOW_CONCERN"} else 0,
    )
    print()
    print(format_next_actions(actions))
    return QuickstartResult(
        doctor_exit_code=doctor.exit_code,
        demo_posture=demo_posture,
        guardrails_path=guardrails_path,
        skipped_init=skip_init or guardrails_path is None,
    )