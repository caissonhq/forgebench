from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from forgebench.adversaries.models import ReviewerContext, TEST_SKEPTIC
from forgebench.adversaries.test_skeptic import ASSERTION_TOKENS
from forgebench.llm_review import LLMJSONResult, run_llm_json
from forgebench.models import Confidence, EvidenceType, Finding, LLMReviewerConfig, LLMReviewStatus, Severity, SpecializedReviewerResult, SpecializedReviewerStatus


LENS_ID = "test_skeptic_v2"
REVIEWER_NAME = "Test Skeptic v2"
FINDING_ID = "test_skeptic_v2_weak_assertion_semantics"
MAX_TEST_CHARS = 4000
MAX_SOURCE_CHARS = 8000
MAX_RATIONALE_CHARS = 500


def trigger(context: ReviewerContext) -> bool:
    return bool(_source_files(context) and _test_files_with_added_lines(context) and _added_test_lines_lack_assertions(context))


def skip_reason(context: ReviewerContext) -> str:
    if not _test_files_with_added_lines(context):
        return "No test files with added lines were present."
    if not _added_test_lines_lack_assertions(context):
        return "Added test lines already include common assertion tokens."
    if not _source_files(context):
        return "No source file changed alongside the test changes."
    return "Test Skeptic v2 trigger did not fire."


def run(context: ReviewerContext, config: LLMReviewerConfig) -> tuple[SpecializedReviewerResult, bool]:
    bundle = _build_bundle(context)
    raw_result = run_llm_json(config, bundle)
    if raw_result.status != LLMReviewStatus.COMPLETED:
        return (
            SpecializedReviewerResult(
                reviewer_id=LENS_ID,
                reviewer_name=REVIEWER_NAME,
                status=SpecializedReviewerStatus.SKIPPED if raw_result.status == LLMReviewStatus.SKIPPED else SpecializedReviewerStatus.FAILED,
                summary=raw_result.error_message or "Test Skeptic v2 LLM review did not complete.",
                findings=[],
                referenced_finding_ids=["test_skeptic_weak_test_signal"] if _has_finding(context, "test_skeptic_weak_test_signal") else [],
                error_message=raw_result.error_message if raw_result.status == LLMReviewStatus.FAILED else None,
            ),
            raw_result.status != LLMReviewStatus.SKIPPED,
        )

    result = _result_from_payload(raw_result, context)
    return result, True


def _result_from_payload(raw_result: LLMJSONResult, context: ReviewerContext) -> SpecializedReviewerResult:
    payload = raw_result.payload or {}
    verdict = str(payload.get("verdict") or "uncertain").strip().lower()
    rationale = _truncate_single_line(str(payload.get("rationale") or ""), MAX_RATIONALE_CHARS)
    evidence_lines = _string_list(payload.get("evidence_lines"))[:8]
    referenced = ["test_skeptic_weak_test_signal"] if _has_finding(context, "test_skeptic_weak_test_signal") else []

    if verdict != "weak":
        if verdict == "adequate":
            summary = "Test Skeptic v2 did not find weak assertion semantics beyond the existing evidence."
        else:
            summary = "Test Skeptic v2 was uncertain and did not add a finding."
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

    test_files = _test_files_with_added_lines(context)
    finding = Finding(
        id=FINDING_ID,
        title="Test Skeptic v2 flagged weak test semantics",
        severity=Severity.MEDIUM,
        confidence=Confidence.MEDIUM,
        evidence_type=EvidenceType.LLM,
        files=test_files,
        evidence=[
            f"LLM provider: {raw_result.provider or 'unknown'}",
            "Verdict: weak",
            "Severity and confidence are hard-capped by ForgeBench, not selected by the LLM.",
            "LLM lens findings are advisory and cannot block merge by themselves.",
        ]
        + [f"Evidence line: {_truncate_single_line(line, 180)}" for line in evidence_lines],
        explanation=(
            "Test Skeptic v2 reviewed the changed tests and found that they may not meaningfully assert "
            "the changed behavior. Treat this as a review task, not proof."
        ),
        suggested_fix=(
            "Review the changed tests and add explicit assertions that prove the changed behavior and nearby regression cases."
        ),
        reviewer=TEST_SKEPTIC,
        supporting_finding_ids=referenced,
    )
    summary = "LLM-assisted lens found weak test assertion semantics."
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


def _build_bundle(context: ReviewerContext) -> str:
    payload = {
        "original_task": _truncate(context.task_text, 4000),
        "changed_test_lines": _truncate(_format_changed_lines(_test_files_with_added_lines(context), context), MAX_TEST_CHARS),
        "changed_source_lines": _truncate(_format_changed_lines(_most_changed_source_files(context), context), MAX_SOURCE_CHARS),
        "existing_static_finding_titles": [
            finding.title
            for finding in context.findings
            if finding.evidence_type in {EvidenceType.STATIC, EvidenceType.DETERMINISTIC}
        ],
    }
    return _prompt_text() + "\n\nEvidence bundle:\n" + json.dumps(payload, indent=2, sort_keys=True)


def _prompt_text() -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "test_skeptic_v2.md"
    try:
        return prompt_path.read_text(encoding="utf-8")
    except OSError:
        return (
            "You are Test Skeptic v2. Review only whether changed tests meaningfully assert changed behavior. "
            "Return only JSON with verdict, rationale, and evidence_lines."
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


def _most_changed_source_files(context: ReviewerContext) -> list[str]:
    source_paths = set(_source_files(context))
    changed = [changed_file for changed_file in context.diff.files if changed_file.path in source_paths]
    changed.sort(key=lambda item: item.added_line_count + item.deleted_line_count, reverse=True)
    return [changed_file.path for changed_file in changed[:3]]


def _source_files(context: ReviewerContext) -> list[str]:
    value = context.static_signals.get("source_files_changed") or []
    return [str(item) for item in value] if isinstance(value, list) else []


def _test_files_with_added_lines(context: ReviewerContext) -> list[str]:
    return sorted({changed_file.path for changed_file in context.diff.files if changed_file.is_test and changed_file.added_lines})


def _added_test_lines_lack_assertions(context: ReviewerContext) -> bool:
    added = "\n".join(
        line
        for changed_file in context.diff.files
        if changed_file.is_test
        for line in changed_file.added_lines
    ).lower()
    return bool(added.strip()) and not any(token in added for token in ASSERTION_TOKENS)


def _has_finding(context: ReviewerContext, finding_id: str) -> bool:
    return any(finding.id == finding_id for finding in context.findings)


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
