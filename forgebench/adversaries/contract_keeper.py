from __future__ import annotations

import re
from pathlib import PurePosixPath

from forgebench.adversaries.models import CONTRACT_KEEPER, ReviewerContext
from forgebench.models import Confidence, EvidenceType, Finding, Severity, SpecializedReviewerResult, SpecializedReviewerStatus


REVIEWER_NAME = "Contract Keeper"

CONTRACT_PATH_MARKERS = (
    "schema",
    "migrations",
    "migration",
    "openapi",
    "graphql",
    "prisma",
    "drizzle",
    "alembic",
    "routes",
    "api",
    "endpoints",
    "contract",
    "interface",
    "protocol",
    "types",
    "database",
    "db",
    "swiftdata",
    "coredata",
)

PUBLIC_INTERFACE_PATTERNS = (
    "public struct",
    "public class",
    "public protocol",
    "interface ",
    "type ",
    "export ",
    "export interface",
    "export type",
    "route(",
    "app.get",
    "app.post",
    "@route",
    "@entity",
    "@model",
)

CONTRACT_LINE_PATTERNS = (
    "required",
    "optional",
    "nullable",
    "not null",
    "add column",
    "drop column",
    "rename",
    "migration",
)


def review(context: ReviewerContext) -> SpecializedReviewerResult:
    findings: list[Finding] = []
    referenced: list[str] = []
    existing_ids = {finding.id for finding in context.findings}
    tests_changed = bool(context.static_signals.get("tests_changed"))

    if "persistence_schema_changed" in existing_ids:
        referenced.append("persistence_schema_changed")

    read_model_files = _read_model_public_interface_files(context)
    if read_model_files and not tests_changed:
        supporting = ["implementation_without_tests"] if "implementation_without_tests" in existing_ids else []
        findings.append(
            Finding(
                id="contract_keeper_read_model_contract_changed",
                title="Read-model contract changed without clear coverage",
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=read_model_files,
                evidence=[
                    "Changed lines in a read/view model include public shape or type-like tokens.",
                    "No likely test file changed with the read-model contract change.",
                ]
                + [f"Read-model contract signal in: {path}" for path in read_model_files[:8]],
                explanation=(
                    "The patch changes a read-model or view-model surface that callers may depend on. "
                    "ForgeBench is treating this as contract risk, not persistence/schema risk."
                ),
                suggested_fix=(
                    "Add focused coverage for the changed read-model shape or confirm the affected callers tolerate the change."
                ),
                reviewer=CONTRACT_KEEPER,
                supporting_finding_ids=supporting,
            )
        )
        referenced.extend(supporting)

    public_files = _public_interface_files(context)
    if public_files and not tests_changed:
        supporting = ["implementation_without_tests"] if "implementation_without_tests" in existing_ids else []
        findings.append(
            Finding(
                id="contract_keeper_public_interface_changed",
                title="Public interface changed without clear regression coverage",
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=public_files,
                evidence=[
                    "Changed lines include public interface, type, route, export, or model tokens.",
                    "No likely test file changed with the contract-like change.",
                ]
                + [f"Public interface signal in: {path}" for path in public_files[:8]],
                explanation=(
                    "The patch changes a public interface or type-like surface without a corresponding test update. "
                    "That can silently change callers, serialization, UI contracts, or API expectations."
                ),
                suggested_fix="Add or update tests that exercise the changed public contract, or document why existing coverage is sufficient.",
                reviewer=CONTRACT_KEEPER,
                supporting_finding_ids=supporting,
            )
        )
        referenced.extend(supporting)
    else:
        contract_files = _contract_like_files(context)
        static_persistence_files = set(_list_signal(context, "persistence_or_schema_files_changed"))
        contract_files = [path for path in contract_files if path not in static_persistence_files]
        if contract_files and not tests_changed:
            supporting = _supporting_ids(existing_ids, ["persistence_schema_changed", "build_config_changed", "dependency_surface_changed"])
            findings.append(
                Finding(
                    id="contract_keeper_contract_changed_without_tests",
                    title="Contract-like surface changed without clear test coverage",
                    severity=Severity.MEDIUM,
                    confidence=Confidence.MEDIUM,
                    evidence_type=EvidenceType.REVIEWER,
                    files=contract_files,
                    evidence=[
                        "Patch touches files or lines that look like schema, API, route, type, or persistence contracts.",
                        "No likely test file changed with the contract-like surface.",
                    ]
                    + [f"Contract-like file changed: {path}" for path in contract_files[:8]],
                    explanation=(
                        "The patch changes a contract-like surface without a corresponding test update. "
                        "This can break consumers even when implementation code appears locally correct."
                    ),
                    suggested_fix="Add tests or compatibility checks for the changed contract before merge.",
                    reviewer=CONTRACT_KEEPER,
                    supporting_finding_ids=supporting,
                )
            )
            referenced.extend(supporting)

    if findings:
        summary = "Found contract-like surface changes that need review."
    elif referenced:
        summary = "Contract risk is already represented by existing static findings."
    else:
        summary = "No additional contract-surface concern found."
    return SpecializedReviewerResult(
        reviewer_id=CONTRACT_KEEPER,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.COMPLETED,
        summary=summary,
        findings=findings,
        referenced_finding_ids=sorted(set(referenced)),
    )


def _public_interface_files(context: ReviewerContext) -> list[str]:
    files: list[str] = []
    for changed_file in context.diff.files:
        if _is_docs_or_asset(changed_file.path):
            continue
        if _is_read_or_view_model(changed_file.path) and not _explicitly_high_risk(changed_file.path, context):
            continue
        changed_lines = "\n".join(changed_file.added_lines + changed_file.deleted_lines).lower()
        if any(pattern in changed_lines for pattern in PUBLIC_INTERFACE_PATTERNS):
            files.append(changed_file.path)
    return sorted(set(files))


def _read_model_public_interface_files(context: ReviewerContext) -> list[str]:
    files: list[str] = []
    for changed_file in context.diff.files:
        if not _is_read_or_view_model(changed_file.path):
            continue
        changed_lines = changed_file.added_lines + changed_file.deleted_lines
        joined = "\n".join(changed_lines).lower()
        if any(pattern in joined for pattern in PUBLIC_INTERFACE_PATTERNS) or any(
            _looks_like_read_model_shape_line(line) for line in changed_lines
        ):
            files.append(changed_file.path)
    return sorted(set(files))


def _contract_like_files(context: ReviewerContext) -> list[str]:
    files = set(_list_signal(context, "persistence_or_schema_files_changed"))
    for changed_file in context.diff.files:
        if _is_docs_or_asset(changed_file.path):
            continue
        if _is_read_or_view_model(changed_file.path) and not _explicitly_high_risk(changed_file.path, context):
            continue
        lower_path = changed_file.path.replace("\\", "/").lower()
        path_tokens = [token for token in re.split(r"[^a-z0-9]+", lower_path) if token]
        if any(marker in lower_path for marker in CONTRACT_PATH_MARKERS) or "api" in path_tokens or "db" in path_tokens:
            files.add(changed_file.path)
            continue
        changed_lines = "\n".join(changed_file.added_lines + changed_file.deleted_lines).lower()
        if any(pattern in changed_lines for pattern in CONTRACT_LINE_PATTERNS):
            files.add(changed_file.path)
    return sorted(files)


def _is_read_or_view_model(path: str) -> bool:
    lower = PurePosixPath(path.replace("\\", "/")).name.lower()
    full = path.replace("\\", "/").lower()
    return any(marker in lower or marker in full for marker in ("read_model", "view_model", "readmodel", "viewmodel"))


def _looks_like_read_model_shape_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return False
    if re.match(r"[A-Za-z_][A-Za-z0-9_]*\s*:", stripped):
        return True
    return bool(re.match(r"[\"'][A-Za-z_][A-Za-z0-9_ -]*[\"']\s*:", stripped))


def _is_docs_or_asset(path: str) -> bool:
    lower = path.replace("\\", "/").lower()
    suffix = PurePosixPath(lower).suffix
    return suffix in {
        ".md",
        ".markdown",
        ".rst",
        ".txt",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".ico",
        ".icns",
    }


def _explicitly_high_risk(path: str, context: ReviewerContext) -> bool:
    for finding in context.findings:
        if finding.id == "high_risk_guardrail_file" and path in finding.files:
            return True
    return False


def _list_signal(context: ReviewerContext, key: str) -> list[str]:
    value = context.static_signals.get(key) or []
    return [str(item) for item in value] if isinstance(value, list) else []


def _supporting_ids(existing_ids: set[str], candidates: list[str]) -> list[str]:
    return [finding_id for finding_id in candidates if finding_id in existing_ids]
