from __future__ import annotations

from forgebench.adversaries.models import PRODUCT_GUARDRAIL_REVIEWER, ReviewerContext
from forgebench.models import Confidence, EvidenceType, Finding, Severity, SpecializedReviewerResult, SpecializedReviewerStatus


REVIEWER_NAME = "Product / Guardrail Reviewer"


def review(context: ReviewerContext) -> SpecializedReviewerResult:
    findings: list[Finding] = []
    referenced: list[str] = []
    existing_by_id = {finding.id: finding for finding in context.findings}

    forbidden = existing_by_id.get("forbidden_pattern_added")
    if forbidden:
        referenced.append("forbidden_pattern_added")
        findings.append(
            Finding(
                id="product_guardrail_forbidden_pattern",
                title="Patch introduces a forbidden product or architecture pattern",
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                evidence_type=EvidenceType.REVIEWER,
                files=list(forbidden.files),
                evidence=[
                    "Existing guardrail finding forbidden_pattern_added is present.",
                    *forbidden.evidence[:6],
                ],
                explanation=(
                    "Project guardrails explicitly forbid this product or architecture pattern. This is not a semantic guess; "
                    "it is grounded in configured forbidden-pattern evidence from added lines."
                ),
                suggested_fix="Remove the forbidden pattern or update the guardrail intentionally before merging.",
                reviewer=PRODUCT_GUARDRAIL_REVIEWER,
                supporting_finding_ids=["forbidden_pattern_added"],
            )
        )

    protected_area_files: list[str] = []
    protected_supporting: list[str] = []
    for finding_id in ("high_risk_guardrail_file", "medium_risk_guardrail_file"):
        finding = existing_by_id.get(finding_id)
        if finding:
            protected_area_files.extend(finding.files)
            protected_supporting.append(finding_id)
    if context.guardrails.protected_behavior and protected_area_files:
        referenced.extend(protected_supporting)
        findings.append(
            Finding(
                id="product_guardrail_protected_area_changed",
                title="Patch touches protected product or architecture behavior",
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH if "high_risk_guardrail_file" in protected_supporting else Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=sorted(set(protected_area_files)),
                evidence=[
                    "Project protected_behavior is configured.",
                    "Patch hit configured high- or medium-risk guardrail paths.",
                ]
                + [f"Protected behavior: {item}" for item in context.guardrails.protected_behavior[:6]],
                explanation=(
                    "The patch touches files that this repo marks as tied to protected product or architecture behavior. "
                    "This needs review against the guardrails; it is not automatically a violation."
                ),
                suggested_fix="Review the changed files against the protected behavior list and add focused tests or reduce scope if needed.",
                reviewer=PRODUCT_GUARDRAIL_REVIEWER,
                supporting_finding_ids=protected_supporting,
            )
        )

    ui_copy = existing_by_id.get("ui_copy_changed")
    if ui_copy and context.guardrails.protected_behavior:
        referenced.append("ui_copy_changed")
        findings.append(
            Finding(
                id="product_guardrail_copy_needs_review",
                title="User-facing copy should be checked against product guardrails",
                severity=Severity.ADVISORY,
                confidence=Confidence.LOW,
                evidence_type=EvidenceType.REVIEWER,
                files=list(ui_copy.files),
                evidence=[
                    "User-facing copy or UI changed while protected product behavior is configured.",
                ],
                explanation=(
                    "The patch changes UI or copy in a repo with explicit protected behavior. This should be checked for "
                    "tone, scope, and product intent, but ForgeBench is not claiming a violation unless a forbidden pattern matched."
                ),
                suggested_fix="Review the copy against the protected behavior list and adjust wording if it changes product intent.",
                reviewer=PRODUCT_GUARDRAIL_REVIEWER,
                supporting_finding_ids=["ui_copy_changed"],
            )
        )

    if findings:
        summary = "Found guardrail-related review concerns grounded in configured project policy."
    else:
        summary = "No additional product or guardrail concern found."
    return SpecializedReviewerResult(
        reviewer_id=PRODUCT_GUARDRAIL_REVIEWER,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.COMPLETED,
        summary=summary,
        findings=findings,
        referenced_finding_ids=sorted(set(referenced)),
    )
