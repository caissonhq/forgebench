from __future__ import annotations

from collections.abc import Callable

from forgebench.adversaries.contract_keeper import review as contract_keeper_review
from forgebench.adversaries.lenses import test_skeptic_v2
from forgebench.adversaries.models import ReviewerContext
from forgebench.adversaries.product_guardrail_reviewer import review as product_guardrail_review
from forgebench.adversaries.scope_auditor import review as scope_auditor_review
from forgebench.adversaries.test_skeptic import review as test_skeptic_review
from forgebench.models import (
    LLMReviewerConfig,
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


def run_specialized_reviewers(
    context: ReviewerContext,
    llm_config: LLMReviewerConfig | None = None,
) -> SpecializedReviewReport:
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
    skipped_lenses: list[dict[str, str]] = []
    llm_call_used = False
    lens_result, lens_used_call, skip_reason = _run_test_skeptic_v2(context, llm_config)
    if lens_result is not None:
        results.append(lens_result)
    if skip_reason:
        skipped_lenses.append({"lens_id": test_skeptic_v2.LENS_ID, "reason": skip_reason})
    llm_call_used = llm_call_used or lens_used_call
    findings = [finding for result in results for finding in result.findings]
    return SpecializedReviewReport(
        enabled=True,
        results=results,
        findings=findings,
        metadata={
            "skipped_lenses": skipped_lenses,
            "llm_call_used": llm_call_used,
        },
    )


def specialized_reviewers_not_run() -> SpecializedReviewReport:
    return SpecializedReviewReport(enabled=False, results=[], findings=[])


def _run_test_skeptic_v2(
    context: ReviewerContext,
    llm_config: LLMReviewerConfig | None,
) -> tuple[SpecializedReviewerResult | None, bool, str | None]:
    if not test_skeptic_v2.trigger(context):
        reason = test_skeptic_v2.skip_reason(context)
        return _skipped_lens(reason), False, reason
    if llm_config is None or not llm_config.enabled:
        reason = "LLM review is disabled; Test Skeptic v2 is opt-in."
        return _skipped_lens(reason), False, reason
    if not (llm_config.provider or llm_config.command):
        reason = "LLM review is enabled but no usable provider is configured."
        return _skipped_lens(reason), False, reason
    try:
        result, used_call = test_skeptic_v2.run(context, llm_config)
    except Exception as exc:  # pragma: no cover - defensive boundary
        return (
            SpecializedReviewerResult(
                reviewer_id=test_skeptic_v2.LENS_ID,
                reviewer_name=test_skeptic_v2.REVIEWER_NAME,
                status=SpecializedReviewerStatus.FAILED,
                summary="Test Skeptic v2 failed before producing findings.",
                findings=[],
                referenced_finding_ids=[],
                error_message=str(exc),
            ),
            False,
            None,
        )
    skip_reason = result.summary if result.status == SpecializedReviewerStatus.SKIPPED else None
    return result, used_call, skip_reason


def _skipped_lens(reason: str) -> SpecializedReviewerResult:
    return SpecializedReviewerResult(
        reviewer_id=test_skeptic_v2.LENS_ID,
        reviewer_name=test_skeptic_v2.REVIEWER_NAME,
        status=SpecializedReviewerStatus.SKIPPED,
        summary=reason,
        findings=[],
        referenced_finding_ids=[],
    )
