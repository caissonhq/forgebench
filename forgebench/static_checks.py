from __future__ import annotations

from pathlib import PurePosixPath
import re
from typing import Any

from forgebench.models import Confidence, DiffSummary, EvidenceType, Finding, Severity


SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".dart",
    ".go",
    ".h",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".m",
    ".mm",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".svelte",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
}

DEPENDENCY_FILES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pyproject.toml",
    "requirements.txt",
    "poetry.lock",
    "package.resolved",
    "gemfile.lock",
    "cargo.toml",
    "cargo.lock",
}

CONFIG_MARKERS = (
    ".github/",
    "dockerfile",
    "docker-compose",
    "makefile",
    "vite.config",
    "next.config",
    "tsconfig",
    "xcodeproj",
    "xcconfig",
    "info.plist",
    "package.swift",
)

GENERATED_MARKERS = (
    "dist/",
    "build/",
    "deriveddata/",
    "node_modules/",
    ".coverage",
    ".pyc",
    ".ds_store",
)

UI_COPY_MARKERS = (
    ".strings",
    "localizable",
    "view.swift",
    ".tsx",
    ".jsx",
    ".html",
    ".md",
)


def run_static_checks(diff: DiffSummary) -> tuple[list[Finding], dict[str, Any]]:
    findings: list[Finding] = []
    changed_files = diff.changed_files
    test_files = [changed_file.path for changed_file in diff.files if changed_file.is_test]
    generated_files = [path for path in changed_files if _is_generated_file(path)]
    source_files = [
        changed_file.path
        for changed_file in diff.files
        if _is_likely_source_file(changed_file.path, changed_file.is_test)
        and changed_file.path not in generated_files
        and not changed_file.is_binary
    ]
    deleted_test_files = [changed_file.path for changed_file in diff.files if changed_file.is_test and changed_file.is_deleted]
    modified_test_files_with_deletions = [
        changed_file.path
        for changed_file in diff.files
        if changed_file.is_test and changed_file.deleted_line_count > 0 and not changed_file.is_deleted
    ]
    dependency_files = [path for path in changed_files if _is_dependency_file(path)]
    config_files = [path for path in changed_files if _is_config_file(path)]
    persistence_files = [path for path in changed_files if _is_persistence_file(path)]
    ui_copy_files = [path for path in changed_files if _is_ui_or_copy_file(path)]
    binary_files = [changed_file.path for changed_file in diff.files if changed_file.is_binary]

    if source_files and not test_files:
        findings.append(
            Finding(
                id="implementation_without_tests",
                title="Implementation changed without corresponding test updates",
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.STATIC,
                files=source_files,
                evidence=[f"Implementation file changed without a likely test file: {path}" for path in source_files],
                explanation=(
                    "The patch changes likely implementation files, but no likely test files were changed. "
                    "This increases the risk that the agent produced behavior that is not covered by regression tests."
                ),
                suggested_fix=(
                    "Add or update tests that prove the changed behavior works and does not regress nearby behavior."
                ),
            )
        )

    test_risk_files = sorted(set(deleted_test_files + modified_test_files_with_deletions))
    if test_risk_files:
        file_deleted = bool(deleted_test_files)
        findings.append(
            Finding(
                id="deleted_tests" if file_deleted else "tests_weakened",
                title="Tests were deleted or substantially modified",
                severity=Severity.HIGH,
                confidence=Confidence.HIGH if file_deleted else Confidence.MEDIUM,
                evidence_type=EvidenceType.STATIC,
                files=test_risk_files,
                evidence=[f"Test file deleted: {path}" for path in deleted_test_files]
                + [f"Deleted lines in test file: {path}" for path in modified_test_files_with_deletions],
                explanation=(
                    "The patch deletes a test file or removes lines from tests. This can weaken regression "
                    "coverage exactly where reviewer confidence is needed."
                ),
                suggested_fix=(
                    "Restore the deleted coverage or replace it with tests that prove the changed behavior still holds."
                ),
            )
        )

    if dependency_files:
        dependency_evidence = [f"Dependency manifest or lockfile changed: {path}" for path in sorted(set(dependency_files))]
        if not test_files:
            dependency_evidence.append("No likely test file changed in this patch.")
        findings.append(
            Finding(
                id="dependency_surface_changed",
                title="Dependency surface changed",
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                evidence_type=EvidenceType.STATIC,
                files=sorted(set(dependency_files)),
                evidence=dependency_evidence,
                explanation=(
                    "The patch changes dependency manifests or lockfiles. "
                    "Dependency changes can affect install behavior, runtime behavior, and supply-chain exposure."
                ),
                suggested_fix=(
                    "Confirm the dependency change is required, review the lockfile impact, and run the relevant build and tests."
                ),
            )
        )

    if config_files:
        findings.append(
            Finding(
                id="build_config_changed",
                title="Build or configuration surface changed",
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.STATIC,
                files=sorted(set(config_files)),
                evidence=[f"Build or configuration file changed: {path}" for path in sorted(set(config_files))],
                explanation=(
                    "The patch changes build, CI, package, or platform configuration. "
                    "These files can change behavior outside the code paths touched by the task."
                ),
                suggested_fix=(
                    "Review the configuration change separately and run the build or CI path it affects."
                ),
            )
        )

    if persistence_files:
        persistence_evidence = [
            f"Persistence, schema, model, or migration file changed: {path}"
            for path in sorted(set(persistence_files))
        ]
        if not test_files:
            persistence_evidence.append("No likely test file changed in this patch.")
        findings.append(
            Finding(
                id="persistence_schema_changed",
                title="Persistence or schema behavior may have changed",
                severity=Severity.HIGH,
                confidence=Confidence.HIGH if not test_files else Confidence.MEDIUM,
                evidence_type=EvidenceType.STATIC,
                files=sorted(set(persistence_files)),
                evidence=persistence_evidence,
                explanation=(
                    "The patch changes a likely persistence, schema, model, or migration file. If no "
                    "corresponding test file changed, data behavior may have changed without regression coverage."
                ),
                suggested_fix=(
                    "Review the data model impact, verify migration behavior, and add tests around persistence compatibility."
                ),
            )
        )

    if len(changed_files) > 10:
        findings.append(
            Finding(
                id="broad_file_surface",
                title="Patch touches a broad file surface",
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                evidence_type=EvidenceType.STATIC,
                files=changed_files,
                evidence=[f"{len(changed_files)} files changed"],
                explanation=(
                    "The patch changes more than 10 files. Broad patches are harder to review and more likely "
                    "to contain unrelated changes."
                ),
                suggested_fix=(
                    "Split unrelated changes, reduce the patch scope, or provide a clear review map for the touched areas."
                ),
            )
        )

    if generated_files:
        findings.append(
            Finding(
                id="generated_files_changed",
                title="Generated or unrelated files changed",
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                evidence_type=EvidenceType.STATIC,
                files=sorted(set(generated_files)),
                evidence=[f"Generated, build output, cache, or local file changed: {path}" for path in sorted(set(generated_files))],
                explanation=(
                    "The patch includes common generated, build output, cache, or local machine files. "
                    "These changes are often accidental and add review noise."
                ),
                suggested_fix=(
                    "Remove generated or local-only files from the patch unless they are intentionally versioned."
                ),
            )
        )

    if ui_copy_files:
        findings.append(
            Finding(
                id="ui_copy_changed",
                title="User-facing copy or UI surface changed",
                severity=Severity.ADVISORY,
                confidence=Confidence.LOW,
                evidence_type=EvidenceType.STATIC,
                files=sorted(set(ui_copy_files)),
                evidence=[f"Likely user-facing, documentation, or UI file changed: {path}" for path in sorted(set(ui_copy_files))],
                explanation=(
                    "The patch touches files that often affect user-facing copy, documentation, or UI. "
                    "This is not automatically a defect, but it deserves product review when relevant."
                ),
                suggested_fix=(
                    "Review the changed UI or copy for accuracy, tone, and unintended product behavior."
                ),
            )
        )

    static_signals = {
        "changed_file_count": len(changed_files),
        "added_line_count": diff.total_added_lines,
        "deleted_line_count": diff.total_deleted_lines,
        "source_files_changed": sorted(set(source_files)),
        "test_files_changed": sorted(set(test_files)),
        "tests_changed": bool(test_files),
        "deleted_test_files": sorted(set(deleted_test_files)),
        "dependency_files_changed": sorted(set(dependency_files)),
        "build_or_config_files_changed": sorted(set(config_files)),
        "persistence_or_schema_files_changed": sorted(set(persistence_files)),
        "generated_or_unrelated_files_changed": sorted(set(generated_files)),
        "ui_or_copy_files_changed": sorted(set(ui_copy_files)),
        "binary_files_changed": sorted(set(binary_files)),
    }
    return _dedupe_findings(findings), static_signals


def _is_likely_source_file(path: str, is_test: bool) -> bool:
    if is_test:
        return False
    return PurePosixPath(path.replace("\\", "/")).suffix.lower() in SOURCE_EXTENSIONS


def _is_dependency_file(path: str) -> bool:
    return PurePosixPath(path.replace("\\", "/")).name.lower() in DEPENDENCY_FILES


def _is_config_file(path: str) -> bool:
    lower = path.replace("\\", "/").lower()
    basename = PurePosixPath(lower).name
    return lower.startswith(".github/") or basename in CONFIG_MARKERS or any(marker in lower for marker in CONFIG_MARKERS)


def _is_persistence_file(path: str) -> bool:
    lower = path.replace("\\", "/").lower()
    parsed = PurePosixPath(lower)
    if parsed.suffix in {".md", ".markdown", ".txt", ".rst"}:
        return False
    basename = parsed.name
    if any(marker in lower for marker in ("read_model", "view_model", "readmodel", "viewmodel")):
        return False
    if any(marker in lower for marker in ("dto", "response_model", "presentation_model")):
        return False

    long_markers = {
        "schema",
        "migration",
        "migrations",
        "database",
        "persistence",
        "swiftdata",
        "coredata",
        "prisma",
        "drizzle",
        "sequelize",
        "alembic",
    }
    if any(marker in lower for marker in long_markers):
        return True

    tokens = [token for token in re.split(r"[^a-z0-9]+", lower) if token]
    if "db" in tokens or "entity" in tokens or "entities" in tokens or "store" in tokens:
        return True
    return basename.endswith("entity" + parsed.suffix) or basename.endswith("store" + parsed.suffix)


def _is_generated_file(path: str) -> bool:
    lower = path.replace("\\", "/").lower()
    return lower.endswith(".pyc") or any(marker in lower for marker in GENERATED_MARKERS)


def _is_ui_or_copy_file(path: str) -> bool:
    lower = path.replace("\\", "/").lower()
    return any(marker in lower for marker in UI_COPY_MARKERS)


def _dedupe_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[tuple[str, tuple[str, ...]]] = set()
    deduped: list[Finding] = []
    for finding in findings:
        key = (finding.id, tuple(sorted(finding.files)))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(finding)
    return deduped
