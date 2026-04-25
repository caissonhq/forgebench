from __future__ import annotations

from dataclasses import replace
from typing import Any

from forgebench.guardrails import matches_path_pattern
from forgebench.models import (
    ActivePathCategory,
    Confidence,
    DiffSummary,
    EvidenceType,
    Finding,
    FindingAdjustment,
    Guardrails,
    MergePosture,
    PolicyDecision,
    Severity,
    SuppressedFinding,
)


DEFAULT_DOC_PATTERNS = [
    "README.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "docs/**",
    "**/*.md",
    "**/*.markdown",
    "**/*.rst",
]

DEFAULT_ASSET_PATTERNS = [
    "**/*.png",
    "**/*.jpg",
    "**/*.jpeg",
    "**/*.gif",
    "**/*.webp",
    "**/*.svg",
    "**/*.ico",
    "**/*.icns",
    "**/Assets.xcassets/**",
]

DEFAULT_GENERATED_PATTERNS = [
    "dist/**",
    "build/**",
    "DerivedData/**",
    "node_modules/**",
    "**/.coverage",
    "**/*.pyc",
    "**/.DS_Store",
]


def apply_guardrails_policy(
    diff: DiffSummary,
    findings: list[Finding],
    static_signals: dict[str, Any],
    guardrails: Guardrails,
) -> tuple[list[Finding], dict[str, Any], PolicyDecision]:
    active_categories = _classify_paths(diff.changed_files, guardrails)
    adjusted_signals = dict(static_signals)
    kept_findings: list[Finding] = []
    suppressed: list[SuppressedFinding] = []
    adjustments: list[FindingAdjustment] = []

    for finding in findings:
        suppression = _suppression_for_finding(finding, diff.changed_files, guardrails, active_categories)
        if suppression:
            suppressed.append(suppression)
            adjustments.append(
                FindingAdjustment(
                    finding_id=finding.id,
                    action="suppress",
                    original_severity=finding.severity,
                    original_confidence=finding.confidence,
                    matched_rule=suppression.matched_rule,
                    reason=suppression.reason,
                    files=finding.files,
                )
            )
            _remove_suppressed_signal(adjusted_signals, finding)
            continue

        adjusted = _apply_finding_override(finding, guardrails)
        if adjusted != finding:
            adjustments.append(
                FindingAdjustment(
                    finding_id=finding.id,
                    action="severity_confidence_override",
                    original_severity=finding.severity,
                    new_severity=adjusted.severity,
                    original_confidence=finding.confidence,
                    new_confidence=adjusted.confidence,
                    matched_rule=f"policy.finding_overrides.{finding.id}",
                    reason=guardrails.policy.finding_overrides[finding.id].reason,
                    files=finding.files,
                )
            )
        kept_findings.append(adjusted)

    ceiling, ceiling_reason, ceiling_rule = _posture_ceiling(diff.changed_files, guardrails, active_categories)
    decision = PolicyDecision(
        active_categories=active_categories,
        finding_adjustments=adjustments,
        suppressed_findings=suppressed,
        posture_ceiling=ceiling,
        posture_ceiling_reason=ceiling_reason,
        posture_ceiling_rule=ceiling_rule,
    )
    return kept_findings, adjusted_signals, decision


def _classify_paths(files: list[str], guardrails: Guardrails) -> list[ActivePathCategory]:
    categories: list[ActivePathCategory] = []
    for name, category in sorted(guardrails.policy.path_categories.items()):
        matched_files = sorted(file_path for file_path in files if _matches_any(file_path, category.patterns))
        if matched_files:
            categories.append(
                ActivePathCategory(
                    name=name,
                    files=matched_files,
                    patterns=list(category.patterns),
                    default_severity=category.default_severity,
                )
            )
    return categories


def _suppression_for_finding(
    finding: Finding,
    changed_files: list[str],
    guardrails: Guardrails,
    active_categories: list[ActivePathCategory],
) -> SuppressedFinding | None:
    if finding.evidence_type == EvidenceType.DETERMINISTIC:
        return None

    override = guardrails.policy.finding_overrides.get(finding.id)
    if override:
        if override.suppress_if_all_files_match and _all_match(changed_files, override.suppress_if_all_files_match):
            return _suppressed(finding, f"policy.finding_overrides.{finding.id}.suppress_if_all_files_match", override.reason)
        if override.suppress_paths and _finding_files_all_match(finding, override.suppress_paths):
            return _suppressed(finding, f"policy.finding_overrides.{finding.id}.suppress_paths", override.reason)

    for index, rule in enumerate(guardrails.policy.suppress_findings):
        if rule.finding_id != finding.id:
            continue
        if rule.when_all_changed_files_match and _all_match(changed_files, rule.when_all_changed_files_match):
            return _suppressed(finding, f"policy.suppress_findings[{index}].when_all_changed_files_match", rule.reason)
        if rule.paths and _finding_files_all_match(finding, rule.paths):
            return _suppressed(finding, f"policy.suppress_findings[{index}].paths", rule.reason)
    if finding.id == "broad_file_surface" and _all_docs_assets_or_generated(changed_files, active_categories):
        return _suppressed(
            finding,
            "default.broad_file_surface_non_code",
            "Broad file surface was suppressed because all changed files are docs, assets, or generated output.",
        )
    return None


def _apply_finding_override(finding: Finding, guardrails: Guardrails) -> Finding:
    override = guardrails.policy.finding_overrides.get(finding.id)
    if not override:
        return finding
    if override.applies_to and not _finding_files_all_match(finding, override.applies_to):
        return finding
    severity = override.severity or finding.severity
    confidence = override.confidence or finding.confidence
    if severity == finding.severity and confidence == finding.confidence:
        return finding
    evidence = list(finding.evidence)
    reason = override.reason or "Guardrails policy adjusted this finding."
    evidence.append(f"Policy override applied: {reason}")
    return replace(finding, severity=severity, confidence=confidence, evidence=evidence)


def _posture_ceiling(
    changed_files: list[str],
    guardrails: Guardrails,
    active_categories: list[ActivePathCategory],
) -> tuple[MergePosture | None, str | None, str | None]:
    if not changed_files:
        return None, None, None

    docs_override = guardrails.policy.posture_overrides.get("docs_only_changes")
    docs_patterns = guardrails.policy.advisory_only or _category_patterns("docs", active_categories) or DEFAULT_DOC_PATTERNS
    if _all_match(changed_files, docs_patterns):
        ceiling = docs_override.posture_ceiling if docs_override else MergePosture.LOW_CONCERN
        reason = docs_override.reason if docs_override and docs_override.reason else "All changed files matched docs or advisory-only paths."
        rule = "policy.posture_overrides.docs_only_changes" if docs_override else "default.docs_only_changes"
        return ceiling, reason, rule

    asset_override = guardrails.policy.posture_overrides.get("asset_only_changes")
    asset_patterns = _category_patterns("assets", active_categories) or DEFAULT_ASSET_PATTERNS
    if _all_match(changed_files, asset_patterns):
        ceiling = asset_override.posture_ceiling if asset_override else MergePosture.LOW_CONCERN
        reason = asset_override.reason if asset_override and asset_override.reason else "All changed files matched asset paths."
        rule = "policy.posture_overrides.asset_only_changes" if asset_override else "default.asset_only_changes"
        return ceiling, reason, rule

    return None, None, None


def _category_patterns(name: str, active_categories: list[ActivePathCategory]) -> list[str]:
    for category in active_categories:
        if category.name == name:
            return list(category.patterns)
    return []


def _all_docs_assets_or_generated(files: list[str], active_categories: list[ActivePathCategory]) -> bool:
    if not files:
        return False
    docs_patterns = _category_patterns("docs", active_categories) or DEFAULT_DOC_PATTERNS
    asset_patterns = _category_patterns("assets", active_categories) or DEFAULT_ASSET_PATTERNS
    all_patterns = docs_patterns + asset_patterns + DEFAULT_GENERATED_PATTERNS
    return _all_match(files, all_patterns)


def _suppressed(finding: Finding, matched_rule: str, reason: str) -> SuppressedFinding:
    return SuppressedFinding(
        finding_id=finding.id,
        title=finding.title,
        original_severity=finding.severity,
        original_confidence=finding.confidence,
        reason=reason or "Guardrails policy suppressed this finding.",
        matched_rule=matched_rule,
        files=list(finding.files),
    )


def _remove_suppressed_signal(static_signals: dict[str, Any], finding: Finding) -> None:
    signal_keys = {
        "dependency_surface_changed": "dependency_files_changed",
        "persistence_schema_changed": "persistence_or_schema_files_changed",
        "deleted_tests": "deleted_test_files",
        "generated_files_changed": "generated_or_unrelated_files_changed",
        "ui_copy_changed": "ui_or_copy_files_changed",
    }
    key = signal_keys.get(finding.id)
    if key:
        static_signals[key] = []


def _finding_files_all_match(finding: Finding, patterns: list[str]) -> bool:
    return bool(finding.files) and _all_match(finding.files, patterns)


def _all_match(files: list[str], patterns: list[str]) -> bool:
    return bool(files) and bool(patterns) and all(_matches_any(file_path, patterns) for file_path in files)


def _matches_any(file_path: str, patterns: list[str]) -> bool:
    normalized = file_path.replace("\\", "/")
    return any(matches_path_pattern(normalized, pattern) for pattern in patterns)
