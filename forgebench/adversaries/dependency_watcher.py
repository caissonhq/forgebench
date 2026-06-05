from __future__ import annotations

import re
from pathlib import PurePosixPath

from forgebench.adversaries.models import DEPENDENCY_WATCHER, ReviewerContext
from forgebench.models import Confidence, EvidenceType, Finding, Severity, SpecializedReviewerResult, SpecializedReviewerStatus


REVIEWER_NAME = "Dependency Watcher"

DEPENDENCY_MANIFESTS = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "pyproject.toml",
    "requirements.txt",
    "poetry.lock",
    "cargo.toml",
    "cargo.lock",
}

RUNTIME_DEP_PATTERNS = (
    (r'"dependencies"\s*:\s*\{[^}]*"([^"]+)"\s*:', "package.json dependency"),
    (r'"devDependencies"\s*:\s*\{[^}]*"([^"]+)"\s*:', "package.json devDependency"),
    (r"^\s*([a-zA-Z0-9_.-]+)\s*=\s*[\"']", "pyproject/requirements dependency"),
)


def review(context: ReviewerContext) -> SpecializedReviewerResult:
    findings: list[Finding] = []
    referenced: list[str] = []
    existing_ids = {finding.id for finding in context.findings}
    dependency_files = _list_signal(context, "dependency_files_changed")
    test_files = _list_signal(context, "test_files_changed")

    if not dependency_files:
        return _completed("No dependency manifest changes detected.", findings, referenced)

    if "dependency_surface_changed" in existing_ids:
        referenced.append("dependency_surface_changed")

    if not test_files:
        findings.append(
            Finding(
                id="dependency_watcher_manifest_without_tests",
                title="Dependency manifest changed without test updates",
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=dependency_files,
                evidence=[
                    "Dependency or lockfile changed in this patch.",
                    "No likely test file changed alongside the manifest update.",
                ]
                + [f"Dependency file changed: {path}" for path in dependency_files[:8]],
                explanation=(
                    "Dependency manifest or lockfile changes can alter install behavior, runtime APIs, or supply-chain "
                    "exposure. Without corresponding test updates, regressions may slip through."
                ),
                suggested_fix=(
                    "Run the relevant install/build/test path and add regression coverage for behavior affected by the dependency change."
                ),
                reviewer=DEPENDENCY_WATCHER,
                supporting_finding_ids=referenced,
            )
        )

    major_bumps = _major_version_bumps(context)
    if major_bumps:
        files = sorted({item["file"] for item in major_bumps})
        findings.append(
            Finding(
                id="dependency_watcher_major_version_bump",
                title="Major dependency version bump detected",
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                evidence_type=EvidenceType.REVIEWER,
                files=files,
                evidence=[item["evidence"] for item in major_bumps[:10]],
                explanation=(
                    "The patch includes major-version dependency changes. Major bumps are a common source of breaking "
                    "API changes and deserve explicit review."
                ),
                suggested_fix="Review release notes/changelogs for the bumped packages and run targeted regression tests.",
                reviewer=DEPENDENCY_WATCHER,
                supporting_finding_ids=referenced,
            )
        )

    new_runtime_deps = _new_runtime_dependencies(context)
    if new_runtime_deps:
        files = sorted({item["file"] for item in new_runtime_deps})
        findings.append(
            Finding(
                id="dependency_watcher_new_runtime_dependency",
                title="New runtime dependency introduced",
                severity=Severity.LOW,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=files,
                evidence=[item["evidence"] for item in new_runtime_deps[:10]],
                explanation=(
                    "Added lines introduce new package names in dependency manifests. New dependencies increase "
                    "supply-chain and maintenance surface."
                ),
                suggested_fix="Confirm the dependency is required, vetted, and covered by install/build checks.",
                reviewer=DEPENDENCY_WATCHER,
                supporting_finding_ids=referenced,
            )
        )

    if findings:
        summary = f"Dependency Watcher flagged {len(findings)} concern(s) in manifest changes."
    else:
        summary = "Dependency manifest changes were detected, but no additional watcher concerns were found."
    return _completed(summary, findings, referenced)


def _major_version_bumps(context: ReviewerContext) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    pattern = re.compile(r'"([^"]+)"\s*:\s*"\^?(\d+)\.')
    for changed_file in context.diff.files:
        if PurePosixPath(changed_file.path).name.lower() not in DEPENDENCY_MANIFESTS:
            continue
        for line in changed_file.added_lines:
            match = pattern.search(line)
            if not match:
                continue
            package = match.group(1)
            major = match.group(2)
            if major.isdigit() and int(major) >= 1:
                hits.append(
                    {
                        "file": changed_file.path,
                        "evidence": f"Major-range dependency added/updated in {changed_file.path}: {package} -> {major}.x",
                    }
                )
    return hits


def _new_runtime_dependencies(context: ReviewerContext) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for changed_file in context.diff.files:
        basename = PurePosixPath(changed_file.path).name.lower()
        if basename not in {"package.json", "pyproject.toml", "requirements.txt"}:
            continue
        for line in changed_file.added_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("#"):
                continue
            if basename == "package.json":
                match = re.search(r'"([^"]+)"\s*:\s*"[^"]+"', stripped)
                if match and match.group(1) not in {"name", "version", "private", "type", "scripts"}:
                    hits.append(
                        {
                            "file": changed_file.path,
                            "evidence": f"New dependency entry in {changed_file.path}: {stripped[:100]}",
                        }
                    )
            elif basename in {"pyproject.toml", "requirements.txt"} and "=" in stripped:
                name = stripped.split("=", 1)[0].strip()
                if name and not name.startswith("["):
                    hits.append(
                        {
                            "file": changed_file.path,
                            "evidence": f"New dependency entry in {changed_file.path}: {stripped[:100]}",
                        }
                    )
    return hits


def _list_signal(context: ReviewerContext, key: str) -> list[str]:
    value = context.static_signals.get(key) or []
    return [str(item) for item in value] if isinstance(value, list) else []


def _completed(summary: str, findings: list[Finding], referenced: list[str]) -> SpecializedReviewerResult:
    return SpecializedReviewerResult(
        reviewer_id=DEPENDENCY_WATCHER,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.COMPLETED,
        summary=summary,
        findings=findings,
        referenced_finding_ids=sorted(set(referenced)),
    )