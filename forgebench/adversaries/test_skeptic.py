from __future__ import annotations

from forgebench.adversaries.models import ReviewerContext, TEST_SKEPTIC
from forgebench.models import Confidence, EvidenceType, Finding, Severity, SpecializedReviewerResult, SpecializedReviewerStatus


REVIEWER_NAME = "Test Skeptic"

ASSERTION_TOKENS = (
    "assert",
    "xctassert",
    "expect(",
    "should",
    "toequal",
    "tobe",
    "pytest",
    "unittest",
    "assertequal",
    "asserttrue",
    "assertfalse",
)


def review(context: ReviewerContext) -> SpecializedReviewerResult:
    findings: list[Finding] = []
    referenced: list[str] = []
    existing_ids = {finding.id for finding in context.findings}
    source_files = _list_signal(context, "source_files_changed")
    test_files = _list_signal(context, "test_files_changed")

    if "implementation_without_tests" in existing_ids:
        referenced.append("implementation_without_tests")
        findings.append(
            Finding(
                id="test_skeptic_missing_behavior_coverage",
                title="Changed behavior lacks corresponding test coverage",
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=source_files,
                evidence=[
                    "Static finding implementation_without_tests is present.",
                    "No likely test file changed with the source behavior change.",
                ]
                + [f"Source file changed without test coverage: {path}" for path in source_files[:8]],
                explanation=(
                    "The patch changes likely behavior without a corresponding test update. A serious reviewer should ask "
                    "what regression would catch this if the agent got the behavior wrong."
                ),
                suggested_fix="Add tests covering the changed behavior and nearby regression cases.",
                reviewer=TEST_SKEPTIC,
                supporting_finding_ids=["implementation_without_tests"],
            )
        )

    weak_test_files = _weak_test_files(context)
    if source_files and test_files and weak_test_files:
        findings.append(
            Finding(
                id="test_skeptic_weak_test_signal",
                title="Test changes do not show a clear assertion signal",
                severity=Severity.LOW,
                confidence=Confidence.LOW,
                evidence_type=EvidenceType.REVIEWER,
                files=weak_test_files,
                evidence=[
                    "Test files changed, but added test lines do not include common assertion tokens.",
                ]
                + [f"Weak assertion signal in test file: {path}" for path in weak_test_files[:8]],
                explanation=(
                    "The patch changes tests, but the added lines do not show obvious assertion or expectation tokens. "
                    "That may be fine, but it is a weak static signal for behavior coverage."
                ),
                suggested_fix="Review the tests for real assertions, or add focused assertions for the changed behavior.",
                reviewer=TEST_SKEPTIC,
            )
        )

    if "deleted_tests" in existing_ids:
        referenced.append("deleted_tests")
    if "tests_assertions_removed_without_replacement" in existing_ids:
        referenced.append("tests_assertions_removed_without_replacement")

    if findings:
        summary = "Found test coverage concerns for the changed behavior."
    elif "deleted_tests" in referenced:
        summary = "Deleted tests are already captured as high-confidence static evidence."
    elif "tests_assertions_removed_without_replacement" in referenced:
        summary = "Removed test assertions are already captured as static evidence."
    elif test_files and not source_files:
        summary = "Test-only changes did not show a separate behavior coverage concern."
    else:
        summary = "No additional test coverage concern found."
    return SpecializedReviewerResult(
        reviewer_id=TEST_SKEPTIC,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.COMPLETED,
        summary=summary,
        findings=findings,
        referenced_finding_ids=sorted(set(referenced)),
    )


def _weak_test_files(context: ReviewerContext) -> list[str]:
    weak: list[str] = []
    for changed_file in context.diff.files:
        if not changed_file.is_test or not changed_file.added_lines:
            continue
        added = "\n".join(changed_file.added_lines).lower()
        if not any(token in added for token in ASSERTION_TOKENS):
            weak.append(changed_file.path)
    return sorted(set(weak))


def _list_signal(context: ReviewerContext, key: str) -> list[str]:
    value = context.static_signals.get(key) or []
    return [str(item) for item in value] if isinstance(value, list) else []
