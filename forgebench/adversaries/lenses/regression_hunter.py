from __future__ import annotations

import json
from pathlib import Path

from forgebench.adversaries.models import REGRESSION_HUNTER, ReviewerContext
from forgebench.adversaries.test_skeptic import ASSERTION_TOKENS
from forgebench.llm_review import LLMJSONResult, run_llm_json
from forgebench.models import Confidence, EvidenceType, Finding, LLMReviewerConfig, LLMReviewStatus, Severity, SpecializedReviewerResult, SpecializedReviewerStatus


LENS_ID = REGRESSION_HUNTER
REVIEWER_NAME = "Regression Hunter"
FINDING_ID = "regression_hunter_load_bearing_assertion_removed"
MAX_TEST_CHARS = 5000
MAX_SOURCE_CHARS = 7000
MAX_RATIONALE_CHARS = 500


def trigger(context: ReviewerContext) -> bool:
    return bool(_source_files(context) and _test_files_with_removed_assertions_without_replacement(context))


def skip_reason(context: ReviewerContext) -> str:
    if not _source_files(context):
        return "No source file changed alongside removed test assertions."
    if not _test_files_with_removed_assertions(context):
        return "No removed test assertion lines were present."
    if not _test_files_with_removed_assertions_without_replacement(context):
        return "Removed test assertions had an obvious assertion replacement in the same file."
    return "Regression Hunter trigger did not fire."


def run(
    context: ReviewerContext,
    config: LLMReviewerConfig | None = None,
    *,
    allow_llm_call: bool = True,
) -> tuple[SpecializedReviewerResult, bool]:
    if not trigger(context):
        return _skipped(skip_reason(context)), False

    referenced = _referenced_findings(context)
    if _can_use_llm(config) and allow_llm_call:
        raw_result = run_llm_json(config, _build_bundle(context))
        if raw_result.status == LLMReviewStatus.COMPLETED:
            return _result_from_payload(raw_result, context, referenced), True
        return (
            SpecializedReviewerResult(
                reviewer_id=LENS_ID,
                reviewer_name=REVIEWER_NAME,
                status=SpecializedReviewerStatus.FAILED if raw_result.status == LLMReviewStatus.FAILED else SpecializedReviewerStatus.SKIPPED,
                summary=raw_result.error_message or "Regression Hunter LLM review did not complete.",
                findings=[],
                referenced_finding_ids=referenced,
                error_message=raw_result.error_message if raw_result.status == LLMReviewStatus.FAILED else None,
            ),
            raw_result.status != LLMReviewStatus.SKIPPED,
        )

    return _deterministic_result(context, referenced), False


def _result_from_payload(
    raw_result: LLMJSONResult,
    context: ReviewerContext,
    referenced: list[str],
) -> SpecializedReviewerResult:
    payload = raw_result.payload or {}
    verdict = str(payload.get("verdict") or "uncertain").strip().lower()
    rationale = _truncate_single_line(str(payload.get("rationale") or ""), MAX_RATIONALE_CHARS)
    evidence_lines = _string_list(payload.get("evidence_lines"))[:8]

    if verdict not in {"load_bearing", "weak", "removed"}:
        if verdict in {"replaced", "adequate"}:
            summary = "Regression Hunter found an obvious replacement for the removed assertion."
        else:
            summary = "Regression Hunter was uncertain and did not add a finding."
        if rationale:
            summary = f"{summary} {rationale}"
        return SpecializedReviewerResult(
            reviewer_id=LENS_ID,
            reviewer_name=REVIEWER_NAME,
            status=SpecializedReviewerStatus.COMPLETED,
            summary=summary,
            findings=[],
            referenced_finding_ids=referenced,
        )

    finding = _finding(
        context,
        evidence_type=EvidenceType.LLM,
        evidence=[
            f"LLM provider: {raw_result.provider or 'unknown'}",
            f"Verdict: {verdict}",
            "Severity and confidence are hard-capped by ForgeBench, not selected by the LLM.",
            "Regression Hunter findings cannot block merge by themselves.",
        ]
        + [f"Evidence line: {_truncate_single_line(line, 180)}" for line in evidence_lines],
        referenced=referenced,
    )
    summary = "Regression Hunter found a potentially load-bearing removed assertion."
    if rationale:
        summary = f"{summary} {rationale}"
    return SpecializedReviewerResult(
        reviewer_id=LENS_ID,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.COMPLETED,
        summary=summary,
        findings=[finding],
        referenced_finding_ids=referenced,
    )


def _deterministic_result(context: ReviewerContext, referenced: list[str]) -> SpecializedReviewerResult:
    finding = _finding(
        context,
        evidence_type=EvidenceType.REVIEWER,
        evidence=[
            "Source files changed in the same patch.",
            "A test file removed assertion lines without an obvious replacement assertion in that file.",
            "This is a narrow regression heuristic, not broad regression prediction.",
        ]
        + [f"Removed assertion without obvious replacement: {path}" for path in _test_files_with_removed_assertions_without_replacement(context)],
        referenced=referenced,
    )
    return SpecializedReviewerResult(
        reviewer_id=LENS_ID,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.COMPLETED,
        summary="Potentially load-bearing assertion removal found in a patch that also changes source files.",
        findings=[finding],
        referenced_finding_ids=referenced,
    )


def _finding(
    context: ReviewerContext,
    *,
    evidence_type: EvidenceType,
    evidence: list[str],
    referenced: list[str],
) -> Finding:
    return Finding(
        id=FINDING_ID,
        title="Potential load-bearing assertion removed",
        severity=Severity.HIGH,
        confidence=Confidence.MEDIUM,
        evidence_type=evidence_type,
        files=_test_files_with_removed_assertions_without_replacement(context),
        evidence=evidence,
        explanation=(
            "The patch changes source files and removes a test assertion without an obvious replacement. "
            "That assertion may have been load-bearing regression coverage."
        ),
        suggested_fix="Restore the assertion or add an equivalent test that covers the same behavior.",
        reviewer=REGRESSION_HUNTER,
        supporting_finding_ids=referenced,
    )


def _build_bundle(context: ReviewerContext) -> str:
    payload = {
        "original_task": _truncate(context.task_text, 4000),
        "changed_test_lines": _truncate(_format_changed_lines(_test_files_with_removed_assertions(context), context), MAX_TEST_CHARS),
        "changed_source_lines": _truncate(_format_changed_lines(_most_changed_source_files(context), context), MAX_SOURCE_CHARS),
        "existing_static_finding_titles": [
            finding.title
            for finding in context.findings
            if finding.evidence_type in {EvidenceType.STATIC, EvidenceType.DETERMINISTIC}
        ],
    }
    return _prompt_text() + "\n\nEvidence bundle:\n" + json.dumps(payload, indent=2, sort_keys=True)


def _prompt_text() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "regression_hunter.md"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except OSError:
        return (
            "You are Regression Hunter. Review only whether removed test assertions appear load-bearing "
            "or replaced by equivalent assertions. Return only JSON."
        )


def _format_changed_lines(paths: list[str], context: ReviewerContext) -> str:
    selected = []
    path_set = set(paths)
    for changed_file in context.diff.files:
        if changed_file.path not in path_set:
            continue
        lines = [f"File: {changed_file.path}", "Deleted lines:"]
        lines.extend(f"- {line}" for line in changed_file.deleted_lines)
        lines.append("Added lines:")
        lines.extend(f"+ {line}" for line in changed_file.added_lines)
        selected.append("\n".join(lines))
    return "\n\n".join(selected)


def _source_files(context: ReviewerContext) -> list[str]:
    value = context.static_signals.get("source_files_changed") or []
    return [str(item) for item in value] if isinstance(value, list) else []


def _most_changed_source_files(context: ReviewerContext) -> list[str]:
    source_paths = set(_source_files(context))
    changed = [changed_file for changed_file in context.diff.files if changed_file.path in source_paths]
    changed.sort(key=lambda item: item.added_line_count + item.deleted_line_count, reverse=True)
    return [changed_file.path for changed_file in changed[:3]]


def _test_files_with_removed_assertions(context: ReviewerContext) -> list[str]:
    return sorted(
        {
            changed_file.path
            for changed_file in context.diff.files
            if changed_file.is_test and _assertion_lines(changed_file.deleted_lines)
        }
    )


def _test_files_with_removed_assertions_without_replacement(context: ReviewerContext) -> list[str]:
    paths: list[str] = []
    for changed_file in context.diff.files:
        if not changed_file.is_test:
            continue
        deleted_assertions = _assertion_lines(changed_file.deleted_lines)
        if not deleted_assertions:
            continue
        added_assertions = _assertion_lines(changed_file.added_lines)
        if len(added_assertions) < len(deleted_assertions):
            paths.append(changed_file.path)
    return sorted(set(paths))


def _assertion_lines(lines: list[str]) -> list[str]:
    matched: list[str] = []
    for line in lines:
        lower = line.strip().lower()
        if any(token in lower for token in ASSERTION_TOKENS):
            matched.append(line)
    return matched


def _referenced_findings(context: ReviewerContext) -> list[str]:
    ids = []
    for finding_id in ["tests_assertions_removed_without_replacement", "test_skeptic_weak_test_signal"]:
        if any(finding.id == finding_id for finding in context.findings):
            ids.append(finding_id)
    return ids


def _can_use_llm(config: LLMReviewerConfig | None) -> bool:
    return bool(config and config.enabled and (config.provider or config.command))


def _skipped(reason: str) -> SpecializedReviewerResult:
    return SpecializedReviewerResult(
        reviewer_id=LENS_ID,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.SKIPPED,
        summary=reason,
        findings=[],
        referenced_finding_ids=[],
    )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def _truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[:max_chars].rstrip() + "\n[truncated]"


def _truncate_single_line(value: str, max_chars: int) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= max_chars:
        return collapsed
    return collapsed[: max_chars - 3].rstrip() + "..."
