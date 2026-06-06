from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from forgebench.diff_parser import parse_diff_file
from forgebench.guardrails import evaluate_guardrails, load_guardrails
from forgebench.models import MergePosture, PolicyDecision
from forgebench.policy import apply_guardrails_policy
from forgebench.posture import determine_posture
from forgebench.static_checks import run_static_checks


@dataclass(frozen=True)
class PolicySimulationResult:
    posture: MergePosture
    findings: list[str]
    suppressed_findings: list[str]
    active_categories: list[str]
    posture_ceiling: str | None
    policy_decision: PolicyDecision
    policy_version: str | None = None
    policy_fingerprint: str | None = None
    formal_obligations: list[str] = field(default_factory=list)
    formal_violations: list[str] = field(default_factory=list)


def simulate_policy(
    *,
    repo_path: str | Path,
    diff_path: str | Path,
    guardrails_path: str | Path,
    task_path: str | Path | None = None,
    run_checks: bool = False,
    run_formal_hooks: bool = True,
) -> PolicySimulationResult:
    del task_path
    repo = Path(repo_path)
    diff = parse_diff_file(Path(diff_path))
    guardrails = load_guardrails(guardrails_path)
    static_findings, signals = run_static_checks(diff)
    guardrail_findings, _ = evaluate_guardrails(diff, guardrails)
    findings, adjusted_signals, decision = apply_guardrails_policy(
        diff,
        static_findings + guardrail_findings,
        signals,
        guardrails,
    )
    reviewer_findings = []
    posture, _ = determine_posture(findings, adjusted_signals, reviewer_findings, policy_decision=decision)

    formal_obligations: list[str] = []
    formal_violations: list[str] = []
    if run_formal_hooks:
        from forgebench.formal_hooks import run_formal_verification_hooks

        formal = run_formal_verification_hooks(
            posture=posture,
            findings=findings,
            policy_decision=decision,
            changed_files=diff.changed_files,
        )
        formal_obligations = formal.obligations
        formal_violations = formal.violations

    from forgebench.policy_versioning import load_policy_text_fingerprint, resolve_policy_version

    policy_text = Path(guardrails_path).read_text(encoding="utf-8", errors="replace")
    policy_fingerprint = load_policy_text_fingerprint(policy_text)
    policy_version, _ = resolve_policy_version(
        {
            "project": guardrails.project,
            "policy_version": guardrails.policy_version or guardrails.fpl_version,
            "fpl_name": guardrails.fpl_name,
        },
        source_path=guardrails_path,
    )

    if run_checks:
        del repo

    return PolicySimulationResult(
        posture=posture,
        findings=[finding.id for finding in findings],
        suppressed_findings=[item.finding_id for item in decision.suppressed_findings],
        active_categories=[category.name for category in decision.active_categories],
        posture_ceiling=decision.posture_ceiling.value if decision.posture_ceiling else None,
        policy_decision=decision,
        policy_version=policy_version,
        policy_fingerprint=policy_fingerprint,
        formal_obligations=formal_obligations,
        formal_violations=formal_violations,
    )