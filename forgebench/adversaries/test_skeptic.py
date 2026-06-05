from __future__ import annotations

from pathlib import PurePosixPath

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
    "mock(",
    "patch(",
    "raises(",
)

SETUP_ONLY_TOKENS = (
    "import ",
    "from ",
    "@pytest",
    "@mock",
    "fixture",
    "setup",
    "teardown",
    "#",
)


def review(context: ReviewerContext) -> SpecializedReviewerResult:
    findings: list[Finding] = []
    referenced: list[str] = []
    existing_ids = {finding.id for finding in context.findings}
    source_files = _list_signal(context, "source_files_changed")
    test_files = _list_signal(context, "test_files_changed")
    generic_mode = context.static_signals.get("config_mode") == "generic"

    if "implementation_without_tests" in existing_ids:
        referenced.append("implementation_without_tests")
        uncovered = _source_files_without_paired_tests(context, source_files, test_files)
        findings.append(
            Finding(
                id="test_skeptic_missing_behavior_coverage",
                title=(
                    "Changed implementation files need coverage review"
                    if generic_mode
                    else "Changed behavior lacks corresponding test coverage"
                ),
                severity=Severity.MEDIUM,
                confidence=Confidence.LOW if generic_mode else Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=uncovered or source_files,
                evidence=[
                    "Static finding implementation_without_tests is present.",
                    "No likely test file changed with the source behavior change.",
                ]
                + [f"Source file changed without test coverage: {path}" for path in (uncovered or source_files)[:8]]
                + _paired_test_hints(uncovered or source_files),
                explanation=(
                    "The patch changes likely implementation files without a corresponding test update. "
                    "In generic mode this is a coverage-review prompt, not proof that behavior lacks tests."
                    if generic_mode
                    else (
                        "The patch changes likely behavior without a corresponding test update. A serious reviewer should ask "
                        "what regression would catch this if the agent got the behavior wrong."
                    )
                ),
                suggested_fix=(
                    "Review whether the changed behavior needs tests, or configure repo-specific checks/guardrails if this signal is noisy."
                    if generic_mode
                    else "Add tests covering the changed behavior and nearby regression cases."
                ),
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

    setup_only_tests = _setup_only_test_files(context, test_files)
    if source_files and setup_only_tests:
        findings.append(
            Finding(
                id="test_skeptic_setup_only_test_changes",
                title="Test files changed with setup-only lines",
                severity=Severity.ADVISORY,
                confidence=Confidence.LOW,
                evidence_type=EvidenceType.REVIEWER,
                files=setup_only_tests,
                evidence=[
                    "Test file added lines appear to be imports, fixtures, or comments without assertion tokens.",
                ]
                + [f"Setup-only test change: {path}" for path in setup_only_tests[:8]],
                explanation=(
                    "Test files changed alongside source files, but added lines look like scaffolding rather than behavior assertions."
                ),
                suggested_fix="Add assertions that prove the changed source behavior, not just test scaffolding.",
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


def _source_files_without_paired_tests(context: ReviewerContext, source_files: list[str], test_files: list[str]) -> list[str]:
    if not source_files:
        return []
    test_set = {path.replace("\\", "/") for path in test_files}
    uncovered: list[str] = []
    for source in source_files:
        candidates = _likely_test_paths_for_source(source)
        if not test_set.intersection(candidates):
            uncovered.append(source)
    return sorted(uncovered)


def _likely_test_paths_for_source(source_path: str) -> set[str]:
    normalized = source_path.replace("\\", "/")
    path = PurePosixPath(normalized)
    stem = path.stem
    parent = str(path.parent)
    candidates = {
        f"{parent}/test_{stem}.py",
        f"{parent}/tests/test_{stem}.py",
        f"{parent}/{stem}_test.py",
        f"{parent}/{stem}.test.ts",
        f"{parent}/{stem}.test.tsx",
        f"{parent}/{stem}.spec.ts",
        f"{parent}/{stem}.spec.tsx",
        f"{parent}/__tests__/{stem}.ts",
        f"{parent}/__tests__/{stem}.tsx",
    }
    if parent != ".":
        candidates.add(f"tests/test_{stem}.py")
        candidates.add(f"test/test_{stem}.py")
    return candidates


def _paired_test_hints(source_files: list[str]) -> list[str]:
    hints: list[str] = []
    for source in source_files[:4]:
        likely = sorted(_likely_test_paths_for_source(source))[:2]
        if likely:
            hints.append(f"Likely test paths for {source}: {', '.join(likely)}")
    return hints


def _weak_test_files(context: ReviewerContext) -> list[str]:
    weak: list[str] = []
    for changed_file in context.diff.files:
        if not changed_file.is_test or not changed_file.added_lines:
            continue
        added = "\n".join(changed_file.added_lines).lower()
        if not any(token in added for token in ASSERTION_TOKENS):
            weak.append(changed_file.path)
    return sorted(set(weak))


def _setup_only_test_files(context: ReviewerContext, test_files: list[str]) -> list[str]:
    if not test_files:
        return []
    setup_only: list[str] = []
    for changed_file in context.diff.files:
        if changed_file.path not in test_files or not changed_file.is_test or not changed_file.added_lines:
            continue
        added = "\n".join(changed_file.added_lines).lower()
        if any(token in added for token in ASSERTION_TOKENS):
            continue
        if all(any(marker in line.lower() for marker in SETUP_ONLY_TOKENS) or not line.strip() for line in changed_file.added_lines):
            setup_only.append(changed_file.path)
    return sorted(set(setup_only))


def _list_signal(context: ReviewerContext, key: str) -> list[str]:
    value = context.static_signals.get(key) or []
    return [str(item) for item in value] if isinstance(value, list) else []