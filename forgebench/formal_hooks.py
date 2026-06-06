from __future__ import annotations

from dataclasses import dataclass, field

from forgebench.models import EvidenceType, Finding, MergePosture, PolicyDecision, Severity


@dataclass(frozen=True)
class FormalVerificationResult:
    obligations: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    passed: bool = True


def run_formal_verification_hooks(
    *,
    posture: MergePosture,
    findings: list[Finding],
    policy_decision: PolicyDecision,
    changed_files: list[str],
) -> FormalVerificationResult:
    obligations = [
        "block_finding_implies_block_posture",
        "posture_respects_policy_ceiling",
        "suppressed_findings_must_not_reappear",
        "deterministic_failures_are_not_suppressed",
    ]
    violations: list[str] = []

    if any(
        finding.evidence_type == EvidenceType.DETERMINISTIC and finding.severity == Severity.HIGH
        for finding in findings
    ):
        if posture != MergePosture.BLOCK:
            violations.append("Deterministic failure present but posture is not BLOCK.")

    if policy_decision.posture_ceiling and _posture_rank(posture) > _posture_rank(policy_decision.posture_ceiling):
        violations.append(
            f"Posture {posture.value} exceeds policy ceiling {policy_decision.posture_ceiling.value}."
        )

    suppressed_ids = {item.finding_id for item in policy_decision.suppressed_findings}
    for finding in findings:
        if finding.id in suppressed_ids:
            violations.append(f"Suppressed finding '{finding.id}' is still present in active findings.")

    if posture == MergePosture.BLOCK and not findings:
        violations.append("BLOCK posture requires at least one active finding.")

    if posture == MergePosture.LOW_CONCERN and any(finding.severity == Severity.HIGH for finding in findings):
        high_ids = [finding.id for finding in findings if finding.severity == Severity.HIGH]
        violations.append(f"HIGH severity findings present under LOW_CONCERN posture: {', '.join(high_ids)}")

    if not changed_files and posture != MergePosture.LOW_CONCERN:
        violations.append("Empty diff should not escalate beyond LOW_CONCERN.")

    return FormalVerificationResult(
        obligations=obligations,
        violations=violations,
        passed=not violations,
    )


def _posture_rank(posture: MergePosture) -> int:
    return {
        MergePosture.LOW_CONCERN: 0,
        MergePosture.REVIEW: 1,
        MergePosture.BLOCK: 2,
    }[posture]