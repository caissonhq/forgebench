from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


REPORT_SCHEMA_VERSION = "1.0.0"


class EvidenceType(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    STATIC = "STATIC"
    REVIEWER = "REVIEWER"
    LLM = "LLM"
    INFERRED = "INFERRED"
    SPECULATIVE = "SPECULATIVE"


class Severity(str, Enum):
    BLOCKER = "BLOCKER"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    ADVISORY = "ADVISORY"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MergePosture(str, Enum):
    BLOCK = "BLOCK"
    REVIEW = "REVIEW"
    LOW_CONCERN = "LOW_CONCERN"


class CheckStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    SKIPPED = "SKIPPED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    ERROR = "ERROR"


class LLMReviewStatus(str, Enum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class SpecializedReviewerStatus(str, Enum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class PRCheckoutInfo:
    requested: bool = False
    status: str = "not_requested"
    worktree_path: str | None = None
    checks_target: str = "not_run"
    error_message: str | None = None
    kept: bool = False
    cleanup_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested": self.requested,
            "status": self.status,
            "worktree_path": self.worktree_path,
            "checks_target": self.checks_target,
            "error_message": self.error_message,
            "kept": self.kept,
            "cleanup_error": self.cleanup_error,
        }


@dataclass(frozen=True)
class Finding:
    id: str
    title: str
    severity: Severity
    confidence: Confidence
    evidence_type: EvidenceType
    files: list[str]
    explanation: str
    suggested_fix: str
    evidence: list[str] = field(default_factory=list)
    reviewer: str | None = None
    supporting_finding_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity.value,
            "confidence": self.confidence.value,
            "evidence_type": self.evidence_type.value,
            "files": list(self.files),
            "evidence": list(self.evidence),
            "reviewer": self.reviewer,
            "supporting_finding_ids": list(self.supporting_finding_ids),
            "explanation": self.explanation,
            "suggested_fix": self.suggested_fix,
        }


@dataclass
class ChangedHunk:
    header: str
    lines: list[str] = field(default_factory=list)
    added_lines: list[str] = field(default_factory=list)
    deleted_lines: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "header": self.header,
            "lines": list(self.lines),
            "added_lines": list(self.added_lines),
            "deleted_lines": list(self.deleted_lines),
        }


@dataclass
class ChangedFile:
    path: str
    old_path: str | None = None
    added_line_count: int = 0
    deleted_line_count: int = 0
    is_added: bool = False
    is_deleted: bool = False
    is_renamed: bool = False
    is_binary: bool = False
    is_test: bool = False
    added_lines: list[str] = field(default_factory=list)
    deleted_lines: list[str] = field(default_factory=list)
    hunks: list[ChangedHunk] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "old_path": self.old_path,
            "added_line_count": self.added_line_count,
            "deleted_line_count": self.deleted_line_count,
            "is_added": self.is_added,
            "is_deleted": self.is_deleted,
            "is_renamed": self.is_renamed,
            "is_binary": self.is_binary,
            "is_test": self.is_test,
            "added_lines": list(self.added_lines),
            "deleted_lines": list(self.deleted_lines),
            "hunks": [hunk.to_dict() for hunk in self.hunks],
        }


@dataclass
class DiffSummary:
    files: list[ChangedFile]

    @property
    def changed_files(self) -> list[str]:
        return [changed_file.path for changed_file in self.files]

    @property
    def total_added_lines(self) -> int:
        return sum(changed_file.added_line_count for changed_file in self.files)

    @property
    def total_deleted_lines(self) -> int:
        return sum(changed_file.deleted_line_count for changed_file in self.files)

    @property
    def tests_changed(self) -> bool:
        return any(changed_file.is_test for changed_file in self.files)

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_files": self.changed_files,
            "total_added_lines": self.total_added_lines,
            "total_deleted_lines": self.total_deleted_lines,
            "files": [changed_file.to_dict() for changed_file in self.files],
        }


@dataclass(frozen=True)
class Guardrails:
    project: str | None = None
    protected_behavior: list[str] = field(default_factory=list)
    risk_files_high: list[str] = field(default_factory=list)
    risk_files_medium: list[str] = field(default_factory=list)
    forbidden_patterns: list[str] = field(default_factory=list)
    checks: dict[str, str | None] = field(default_factory=dict)
    custom_checks: dict[str, str | None] = field(default_factory=dict)
    checks_present: bool = False
    check_timeout_seconds: int = 120
    policy: "GuardrailsPolicy" = field(default_factory=lambda: GuardrailsPolicy())
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FindingOverride:
    finding_id: str
    severity: Severity | None = None
    confidence: Confidence | None = None
    applies_to: list[str] = field(default_factory=list)
    suppress_paths: list[str] = field(default_factory=list)
    suppress_if_all_files_match: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True)
class PathCategory:
    name: str
    patterns: list[str] = field(default_factory=list)
    default_severity: Severity | None = None


@dataclass(frozen=True)
class SuppressFindingRule:
    finding_id: str
    paths: list[str] = field(default_factory=list)
    when_all_changed_files_match: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True)
class PostureOverride:
    name: str
    posture_ceiling: MergePosture | None = None
    reason: str = ""


@dataclass(frozen=True)
class GuardrailsPolicy:
    finding_overrides: dict[str, FindingOverride] = field(default_factory=dict)
    path_categories: dict[str, PathCategory] = field(default_factory=dict)
    advisory_only: list[str] = field(default_factory=list)
    suppress_findings: list[SuppressFindingRule] = field(default_factory=list)
    posture_overrides: dict[str, PostureOverride] = field(default_factory=dict)


@dataclass(frozen=True)
class ActivePathCategory:
    name: str
    files: list[str]
    patterns: list[str]
    default_severity: Severity | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "files": list(self.files),
            "patterns": list(self.patterns),
            "default_severity": self.default_severity.value if self.default_severity else None,
        }


@dataclass(frozen=True)
class FindingAdjustment:
    finding_id: str
    action: str
    original_severity: Severity | None = None
    new_severity: Severity | None = None
    original_confidence: Confidence | None = None
    new_confidence: Confidence | None = None
    matched_rule: str = ""
    reason: str = ""
    files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "action": self.action,
            "original_severity": self.original_severity.value if self.original_severity else None,
            "new_severity": self.new_severity.value if self.new_severity else None,
            "original_confidence": self.original_confidence.value if self.original_confidence else None,
            "new_confidence": self.new_confidence.value if self.new_confidence else None,
            "matched_rule": self.matched_rule,
            "reason": self.reason,
            "files": list(self.files),
        }


@dataclass(frozen=True)
class SuppressedFinding:
    finding_id: str
    title: str
    original_severity: Severity
    original_confidence: Confidence
    reason: str
    matched_rule: str
    files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "title": self.title,
            "original_severity": self.original_severity.value,
            "original_confidence": self.original_confidence.value,
            "reason": self.reason,
            "matched_rule": self.matched_rule,
            "files": list(self.files),
        }


@dataclass(frozen=True)
class PolicyDecision:
    active_categories: list[ActivePathCategory] = field(default_factory=list)
    finding_adjustments: list[FindingAdjustment] = field(default_factory=list)
    suppressed_findings: list[SuppressedFinding] = field(default_factory=list)
    posture_ceiling: MergePosture | None = None
    posture_ceiling_reason: str | None = None
    posture_ceiling_rule: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_categories": [category.to_dict() for category in self.active_categories],
            "finding_adjustments": [adjustment.to_dict() for adjustment in self.finding_adjustments],
            "suppressed_findings": [finding.to_dict() for finding in self.suppressed_findings],
            "posture_ceiling": self.posture_ceiling.value if self.posture_ceiling else None,
            "posture_ceiling_reason": self.posture_ceiling_reason,
            "posture_ceiling_rule": self.posture_ceiling_rule,
        }


@dataclass(frozen=True)
class CheckCommand:
    name: str
    command: str | None
    timeout_seconds: int


@dataclass(frozen=True)
class CheckResult:
    name: str
    command: str | None
    status: CheckStatus
    exit_code: int | None = None
    duration_seconds: float = 0.0
    stdout_excerpt: str = ""
    stderr_excerpt: str = ""
    timed_out: bool = False
    skipped: bool = False
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "command": self.command,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "stdout_excerpt": self.stdout_excerpt,
            "stderr_excerpt": self.stderr_excerpt,
            "timed_out": self.timed_out,
            "skipped": self.skipped,
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class DeterministicChecks:
    run_requested: bool = False
    results: list[CheckResult] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        counts = {
            "passed": 0,
            "failed": 0,
            "timed_out": 0,
            "skipped": 0,
            "not_configured": 0,
            "errors": 0,
        }
        for result in self.results:
            if result.status == CheckStatus.PASSED:
                counts["passed"] += 1
            elif result.status == CheckStatus.FAILED:
                counts["failed"] += 1
            elif result.status == CheckStatus.TIMED_OUT:
                counts["timed_out"] += 1
            elif result.status == CheckStatus.SKIPPED:
                counts["skipped"] += 1
            elif result.status == CheckStatus.NOT_CONFIGURED:
                counts["not_configured"] += 1
            elif result.status == CheckStatus.ERROR:
                counts["errors"] += 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_requested": self.run_requested,
            "results": [result.to_dict() for result in self.results],
            "summary": self.summary,
        }


@dataclass(frozen=True)
class LLMReviewerConfig:
    enabled: bool = False
    provider: str | None = None
    reviewer_name: str = "General LLM Reviewer"
    command: str | None = None
    timeout_seconds: int = 60
    max_diff_chars: int = 20000
    max_task_chars: int = 4000
    max_report_chars: int = 8000
    mock_response: dict[str, Any] | None = None


@dataclass(frozen=True)
class LLMReviewResult:
    enabled: bool = False
    provider: str | None = None
    reviewer_name: str | None = None
    status: LLMReviewStatus = LLMReviewStatus.SKIPPED
    findings: list[Finding] = field(default_factory=list)
    raw_summary: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "status": self.status.value,
            "reviewer_name": self.reviewer_name,
            "summary": self.raw_summary,
            "findings": [finding.to_dict() for finding in self.findings],
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class SpecializedReviewerResult:
    reviewer_id: str
    reviewer_name: str
    status: SpecializedReviewerStatus
    summary: str
    findings: list[Finding] = field(default_factory=list)
    referenced_finding_ids: list[str] = field(default_factory=list)
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviewer_id": self.reviewer_id,
            "reviewer_name": self.reviewer_name,
            "status": self.status.value,
            "summary": self.summary,
            "findings": [finding.to_dict() for finding in self.findings],
            "referenced_finding_ids": list(self.referenced_finding_ids),
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class SpecializedReviewReport:
    enabled: bool = False
    results: list[SpecializedReviewerResult] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "results": [result.to_dict() for result in self.results],
            "findings": [finding.to_dict() for finding in self.findings],
        }


@dataclass
class ForgeBenchReport:
    posture: MergePosture
    summary: str
    task_summary: str
    changed_files: list[str]
    findings: list[Finding]
    static_signals: dict[str, Any]
    guardrail_hits: list[str]
    generated_at: str
    deterministic_checks: DeterministicChecks = field(default_factory=DeterministicChecks)
    policy: PolicyDecision = field(default_factory=PolicyDecision)
    llm_review: LLMReviewResult = field(default_factory=LLMReviewResult)
    specialized_reviewers: SpecializedReviewReport = field(default_factory=SpecializedReviewReport)
    pre_llm_posture: MergePosture | None = None
    pr_checkout: PRCheckoutInfo = field(default_factory=PRCheckoutInfo)
    diff_summary: DiffSummary | None = None

    def to_dict(self) -> dict[str, Any]:
        pre_llm_posture = self.pre_llm_posture or self.posture
        return {
            "schema_version": REPORT_SCHEMA_VERSION,
            "posture": self.posture.value,
            "pre_llm_posture": pre_llm_posture.value,
            "final_posture": self.posture.value,
            "summary": self.summary,
            "task_summary": self.task_summary,
            "changed_files": list(self.changed_files),
            "findings": [finding.to_dict() for finding in self.findings],
            "static_signals": self.static_signals,
            "guardrail_hits": list(self.guardrail_hits),
            "deterministic_checks": self.deterministic_checks.to_dict(),
            "policy": self.policy.to_dict(),
            "specialized_reviewers": self.specialized_reviewers.to_dict(),
            "llm_review": self.llm_review.to_dict(),
            "pr_checkout": self.pr_checkout.to_dict(),
            "generated_at": self.generated_at,
        }
