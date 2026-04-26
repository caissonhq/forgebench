from __future__ import annotations

from collections.abc import Callable

from forgebench.adversaries.contract_keeper import review as contract_keeper_review
from forgebench.adversaries.models import ReviewerContext
from forgebench.adversaries.product_guardrail_reviewer import review as product_guardrail_review
from forgebench.adversaries.scope_auditor import review as scope_auditor_review
from forgebench.adversaries.test_skeptic import review as test_skeptic_review
from forgebench.models import (
    SpecializedReviewerResult,
    SpecializedReviewerStatus,
    SpecializedReviewReport,
)


Reviewer = Callable[[ReviewerContext], SpecializedReviewerResult]


REVIEWERS: tuple[Reviewer, ...] = (
    scope_auditor_review,
    test_skeptic_review,
    contract_keeper_review,
    product_guardrail_review,
)


def run_specialized_reviewers(context: ReviewerContext) -> SpecializedReviewReport:
    results: list[SpecializedReviewerResult] = []
    for reviewer in REVIEWERS:
        try:
            results.append(reviewer(context))
        except Exception as exc:  # pragma: no cover - defensive boundary
            results.append(
                SpecializedReviewerResult(
                    reviewer_id=getattr(reviewer, "__name__", "unknown_reviewer"),
                    reviewer_name="Unknown Reviewer",
                    status=SpecializedReviewerStatus.FAILED,
                    summary="Reviewer failed before producing findings.",
                    findings=[],
                    referenced_finding_ids=[],
                    error_message=str(exc),
                )
            )
    findings = [finding for result in results for finding in result.findings]
    return SpecializedReviewReport(enabled=True, results=results, findings=findings)


def specialized_reviewers_not_run() -> SpecializedReviewReport:
    return SpecializedReviewReport(enabled=False, results=[], findings=[])
