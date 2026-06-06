from __future__ import annotations

from forgebench.adversaries.models import BEHAVIORAL_SKEPTIC, ReviewerContext
from forgebench.models import Confidence, EvidenceType, Finding, Severity, SpecializedReviewerResult, SpecializedReviewerStatus


REVIEWER_NAME = "Behavioral Skeptic"


def review(context: ReviewerContext) -> SpecializedReviewerResult:
    changed_symbols = _list_signal_dicts(context, "changed_symbols")
    uncovered = _list_signal(context, "symbols_without_test_reference")
    edges = _list_signal_dicts(context, "cross_file_behavior_edges")

    if not changed_symbols:
        return SpecializedReviewerResult(
            reviewer_id=BEHAVIORAL_SKEPTIC,
            reviewer_name=REVIEWER_NAME,
            status=SpecializedReviewerStatus.COMPLETED,
            summary="No semantic symbol changes detected in supported languages.",
            findings=[],
            referenced_finding_ids=[],
        )

    findings: list[Finding] = []
    referenced: list[str] = []
    existing_ids = {finding.id for finding in context.findings}
    if "implementation_without_tests" in existing_ids:
        referenced.append("implementation_without_tests")

    source_changed = bool(_list_signal(context, "source_files_changed"))
    tests_changed = bool(context.static_signals.get("tests_changed"))
    should_flag = uncovered and source_changed and (not tests_changed or "implementation_without_tests" in existing_ids)

    if should_flag:
        files = sorted({item["file_path"] for item in changed_symbols if item.get("name") in uncovered})
        findings.append(
            Finding(
                id="behavioral_skeptic_uncovered_symbols",
                title="Changed behavior symbols lack cross-file test references",
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=files,
                evidence=[
                    "Semantic diff identified changed symbols without matching references in changed test files.",
                    f"Uncovered symbols: {', '.join(uncovered[:12])}",
                ]
                + [f"Changed symbol: {item['name']} ({item['kind']}) in {item['file_path']}" for item in changed_symbols[:8]],
                explanation=(
                    "Cross-file behavioral analysis found implementation symbols that changed without a corresponding "
                    "reference in the patch's test-file changes. This is not proof tests are missing, but a serious "
                    "reviewer should ask what would catch a behavioral regression."
                ),
                suggested_fix=(
                    "Add or extend tests that exercise the changed symbols, or document why existing coverage is sufficient."
                ),
                reviewer=BEHAVIORAL_SKEPTIC,
            )
        )

    if edges and not uncovered:
        summary = (
            f"Semantic analysis found {len(changed_symbols)} changed symbol(s) with "
            f"{len(edges)} cross-file test reference(s)."
        )
    elif uncovered:
        summary = (
            f"Semantic analysis found {len(uncovered)} changed symbol(s) without cross-file test references."
        )
    else:
        summary = f"Semantic analysis found {len(changed_symbols)} changed symbol(s)."

    return SpecializedReviewerResult(
        reviewer_id=BEHAVIORAL_SKEPTIC,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.COMPLETED,
        summary=summary,
        findings=findings,
        referenced_finding_ids=referenced,
    )


def _list_signal(context: ReviewerContext, key: str) -> list[str]:
    value = context.static_signals.get(key, [])
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _list_signal_dicts(context: ReviewerContext, key: str) -> list[dict[str, object]]:
    value = context.static_signals.get(key, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]