from __future__ import annotations

from forgebench.adversaries.models import ReviewerContext, SCOPE_AUDITOR
from forgebench.models import Confidence, EvidenceType, Finding, Severity, SpecializedReviewerResult, SpecializedReviewerStatus


REVIEWER_NAME = "Scope Auditor"

DOCS_TASK_TERMS = ("docs", "documentation", "readme", "typo", "wording", "comment only", "comments only")
DEPENDENCY_TASK_TERMS = ("dependency", "dependencies", "package", "lockfile", "install", "library", "upgrade", "version")
CONFIG_TASK_TERMS = ("build", "config", "configuration", "ci", "workflow", "docker", "typescript", "compiler")
NARROW_TASK_TERMS = ("fix", "update", "adjust", "clarify", "rename", "typo", "wording")


def review(context: ReviewerContext) -> SpecializedReviewerResult:
    findings: list[Finding] = []
    referenced: list[str] = []
    existing_ids = {finding.id for finding in context.findings}
    task = context.task_text.lower()

    source_files = _list_signal(context, "source_files_changed")
    dependency_files = _list_signal(context, "dependency_files_changed")
    config_files = _list_signal(context, "build_or_config_files_changed")
    persistence_files = _list_signal(context, "persistence_or_schema_files_changed")
    generated_files = _list_signal(context, "generated_or_unrelated_files_changed")

    task_looks_docs_only = _mentions(task, DOCS_TASK_TERMS)
    non_docs_scope_files = sorted(set(source_files + dependency_files + config_files + persistence_files) - set(generated_files))
    if task_looks_docs_only and non_docs_scope_files:
        supporting = _supporting_ids(existing_ids, ["implementation_without_tests", "dependency_surface_changed", "build_config_changed", "persistence_schema_changed"])
        referenced.extend(supporting)
        findings.append(
            Finding(
                id="scope_auditor_task_scope_expansion",
                title="Patch changes files outside the apparent task scope",
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=non_docs_scope_files,
                evidence=[
                    "Task text appears documentation/copy-only.",
                    "Patch also changes implementation, dependency, configuration, or persistence files.",
                ]
                + [f"Out-of-scope file changed: {path}" for path in non_docs_scope_files[:8]],
                explanation=(
                    "The task appears limited to documentation, copy, typo, or comment changes, but the patch also "
                    "changes files that can affect runtime, build, dependency, or data behavior."
                ),
                suggested_fix=(
                    "Confirm these changes were intentionally requested or split unrelated changes into a separate patch."
                ),
                reviewer=SCOPE_AUDITOR,
                supporting_finding_ids=supporting,
            )
        )

    scoped_files: list[str] = []
    if dependency_files and not _mentions(task, DEPENDENCY_TASK_TERMS):
        scoped_files.extend(dependency_files)
    if config_files and not _mentions(task, CONFIG_TASK_TERMS):
        scoped_files.extend(config_files)
    if scoped_files and not findings:
        supporting = _supporting_ids(existing_ids, ["dependency_surface_changed", "build_config_changed"])
        referenced.extend(supporting)
        findings.append(
            Finding(
                id="scope_auditor_task_scope_expansion",
                title="Patch changes files outside the apparent task scope",
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=sorted(set(scoped_files)),
                evidence=[
                    "Task text does not mention dependency, build, configuration, or CI work.",
                    "Patch changes dependency or configuration files.",
                ]
                + [f"Scope-sensitive file changed: {path}" for path in sorted(set(scoped_files))[:8]],
                explanation=(
                    "The patch changes dependency or configuration surfaces without the task text making that scope explicit. "
                    "That can indicate unrelated agent changes or hidden setup drift."
                ),
                suggested_fix=(
                    "Confirm the dependency or configuration change is required for the task, or split it into a separate patch."
                ),
                reviewer=SCOPE_AUDITOR,
                supporting_finding_ids=supporting,
            )
        )

    if "broad_file_surface" in existing_ids and _mentions(task, NARROW_TASK_TERMS):
        referenced.append("broad_file_surface")

    if findings:
        summary = "Found task-scope drift that should be reviewed before merge."
    elif referenced:
        summary = "Broad or scope-sensitive static evidence is already present; no additional scope finding added."
    else:
        summary = "No additional scope concern found from task text and changed files."
    return SpecializedReviewerResult(
        reviewer_id=SCOPE_AUDITOR,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.COMPLETED,
        summary=summary,
        findings=findings,
        referenced_finding_ids=sorted(set(referenced)),
    )


def _list_signal(context: ReviewerContext, key: str) -> list[str]:
    value = context.static_signals.get(key) or []
    return [str(item) for item in value] if isinstance(value, list) else []


def _mentions(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _supporting_ids(existing_ids: set[str], candidates: list[str]) -> list[str]:
    return [finding_id for finding_id in candidates if finding_id in existing_ids]
