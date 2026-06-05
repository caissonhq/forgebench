from __future__ import annotations

import re

from forgebench.adversaries.models import REPO_CONVENTION_REVIEWER, ReviewerContext
from forgebench.models import Confidence, EvidenceType, Finding, Severity, SpecializedReviewerResult, SpecializedReviewerStatus


REVIEWER_NAME = "Repo Convention Reviewer"

DEBUG_MARKERS: tuple[tuple[str, str], ...] = (
    ("console_log", r"\bconsole\.log\s*\("),
    ("debugger_statement", r"\bdebugger\b"),
    ("pdb_trace", r"\bpdb\.set_trace\s*\("),
    ("breakpoint_call", r"\bbreakpoint\s*\("),
    ("print_debug", r"\bprint\s*\(\s*['\"]debug"),
)

TODO_MARKERS = (
    "todo",
    "fixme",
    "hack",
    "xxx",
)


def review(context: ReviewerContext) -> SpecializedReviewerResult:
    findings: list[Finding] = []
    debug_hits = _scan_added_lines(context, DEBUG_MARKERS)
    todo_hits = _scan_todo_markers(context)

    if debug_hits:
        files = sorted({hit["file"] for hit in debug_hits})
        findings.append(
            Finding(
                id="repo_convention_debug_marker_added",
                title="Debug or console logging added in implementation code",
                severity=Severity.LOW,
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=files,
                evidence=[hit["evidence"] for hit in debug_hits[:12]],
                explanation=(
                    "Added lines include debug logging, debugger statements, or breakpoint helpers in likely "
                    "implementation files. These are often accidental in agent-generated patches."
                ),
                suggested_fix="Remove debug logging and breakpoint helpers before merge, or gate them behind explicit debug flags.",
                reviewer=REPO_CONVENTION_REVIEWER,
            )
        )

    if todo_hits:
        files = sorted({hit["file"] for hit in todo_hits})
        findings.append(
            Finding(
                id="repo_convention_todo_marker_added",
                title="TODO or FIXME marker added in implementation code",
                severity=Severity.ADVISORY,
                confidence=Confidence.LOW,
                evidence_type=EvidenceType.REVIEWER,
                files=files,
                evidence=[hit["evidence"] for hit in todo_hits[:12]],
                explanation=(
                    "Added lines include TODO/FIXME-style markers in likely implementation files. This may indicate "
                    "unfinished agent work."
                ),
                suggested_fix="Resolve the TODO/FIXME or convert it into a tracked issue before merge.",
                reviewer=REPO_CONVENTION_REVIEWER,
            )
        )

    summary = "No repo convention concerns detected."
    if findings:
        summary = f"Repo Convention Reviewer flagged {len(findings)} concern(s) in added lines."
    return SpecializedReviewerResult(
        reviewer_id=REPO_CONVENTION_REVIEWER,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.COMPLETED,
        summary=summary,
        findings=findings,
        referenced_finding_ids=[],
    )


def _scan_added_lines(context: ReviewerContext, patterns: tuple[tuple[str, str], ...]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for changed_file in context.diff.files:
        if changed_file.is_binary or changed_file.is_deleted or changed_file.is_test:
            continue
        line_number = 0
        for hunk in changed_file.hunks:
            line_number = _line_number_from_hunk_header(hunk.header)
            for raw_line in hunk.lines:
                if raw_line.startswith("+"):
                    content = raw_line[1:]
                    for marker_id, expression in patterns:
                        if re.search(expression, content):
                            snippet = content.strip()
                            if len(snippet) > 100:
                                snippet = snippet[:97].rstrip() + "..."
                            hits.append(
                                {
                                    "file": changed_file.path,
                                    "evidence": (
                                        f"Convention marker '{marker_id}' in {changed_file.path}:{line_number}: "
                                        f"{snippet}"
                                    ),
                                }
                            )
                    line_number += 1
                elif raw_line.startswith(" "):
                    line_number += 1
    return hits


def _scan_todo_markers(context: ReviewerContext) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for changed_file in context.diff.files:
        if changed_file.is_binary or changed_file.is_deleted or changed_file.is_test:
            continue
        for line in changed_file.added_lines:
            lower = line.lower()
            if any(marker in lower for marker in TODO_MARKERS):
                snippet = line.strip()
                if len(snippet) > 100:
                    snippet = snippet[:97].rstrip() + "..."
                hits.append(
                    {
                        "file": changed_file.path,
                        "evidence": f"TODO/FIXME marker in {changed_file.path}: {snippet}",
                    }
                )
    return hits


def _line_number_from_hunk_header(header: str) -> int:
    match = re.search(r"\+(\d+)", header)
    if not match:
        return 1
    return int(match.group(1))