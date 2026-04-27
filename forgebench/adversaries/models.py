from __future__ import annotations

from dataclasses import dataclass

from forgebench.models import (
    DeterministicChecks,
    DiffSummary,
    Finding,
    Guardrails,
    PolicyDecision,
    SpecializedReviewerResult,
    SpecializedReviewerStatus,
    SpecializedReviewReport,
)


SCOPE_AUDITOR = "scope_auditor"
TEST_SKEPTIC = "test_skeptic"
CONTRACT_KEEPER = "contract_keeper"
PRODUCT_GUARDRAIL_REVIEWER = "product_guardrail_reviewer"
REGRESSION_HUNTER = "regression_hunter"


@dataclass(frozen=True)
class ReviewerContext:
    task_text: str
    diff: DiffSummary
    static_signals: dict[str, object]
    findings: list[Finding]
    guardrails: Guardrails
    guardrail_hits: list[str]
    policy: PolicyDecision
    deterministic_checks: DeterministicChecks


__all__ = [
    "CONTRACT_KEEPER",
    "PRODUCT_GUARDRAIL_REVIEWER",
    "REGRESSION_HUNTER",
    "ReviewerContext",
    "SCOPE_AUDITOR",
    "TEST_SKEPTIC",
    "SpecializedReviewerResult",
    "SpecializedReviewerStatus",
    "SpecializedReviewReport",
]
