from __future__ import annotations

from forgebench.models import CheckResult, CheckStatus, EvidenceType, Finding, ForgeBenchReport, Guardrails, MergePosture, Severity


MAX_REPAIR_PROMPT_CHARS = 30000
MAX_FINDING_HUNK_LINES = 40


def build_repair_prompt(
    task_text: str,
    report: ForgeBenchReport,
    guardrails: Guardrails,
    max_prompt_chars: int = MAX_REPAIR_PROMPT_CHARS,
) -> str:
    omitted_keys: set[tuple[str, tuple[str, ...], str | None]] = set()
    prompt = _render_repair_prompt(task_text, report, guardrails, omitted_keys)
    if len(prompt) <= max_prompt_chars:
        return prompt

    for key in _droppable_finding_keys(report):
        omitted_keys.add(key)
        prompt = _render_repair_prompt(task_text, report, guardrails, omitted_keys)
        if len(prompt) <= max_prompt_chars:
            return prompt

    if len(prompt) <= max_prompt_chars:
        return prompt
    suffix = "\n\n(Prompt truncated to fit prompt size cap. See patch.diff and forgebench-report.md for full context.)\n"
    return prompt[: max(0, max_prompt_chars - len(suffix))].rstrip() + suffix


def _render_repair_prompt(
    task_text: str,
    report: ForgeBenchReport,
    guardrails: Guardrails,
    omitted_keys: set[tuple[str, tuple[str, ...], str | None]],
) -> str:
    omitted_count = len(omitted_keys)
    lines: list[str] = [
        "You are repairing an AI-generated code change after ForgeBench review.",
        "",
        "Original task:",
        task_text.strip() or "(No task text provided.)",
        "",
        "ForgeBench merge posture:",
        report.posture.value,
        "",
        _posture_instruction(report),
        "",
        "Review context:",
        *_format_review_context(report),
        "",
        "Repair priority:",
        *_format_repair_priority(report, omitted_keys),
        "",
    ]
    if report.config_mode == "generic":
        lines.extend(
            [
                "Configuration note:",
                "This review ran with generic heuristics. Do not broaden scope based on low-confidence generic findings.",
                "",
            ]
        )
    if omitted_count:
        lines.extend([f"({omitted_count} findings omitted to fit prompt size cap.)", ""])

    lines.extend(["Deterministic check failures:"])
    lines.extend(_format_check_failures(report, omitted_keys))

    lines.extend(["", "Static and guardrail findings:"])
    static_findings = [
        finding
        for finding in report.findings
        if finding.evidence_type not in {EvidenceType.DETERMINISTIC, EvidenceType.REVIEWER, EvidenceType.LLM}
        and _finding_key(finding) not in omitted_keys
    ]
    if static_findings:
        lines.extend(_format_findings(static_findings, report))
    else:
        lines.append("- No static or guardrail findings.")

    lines.extend(["", "Heuristic review lens findings:"])
    lines.extend(_format_specialized_reviewer_findings(report, omitted_keys))

    lines.extend(["", "LLM reviewer notes:"])
    lines.extend(_format_llm_notes(report, omitted_keys))

    lines.extend(["", "Suppressed or policy-calibrated findings:"])
    lines.extend(_format_policy_notes(report))

    lines.extend(["", "Reviewer summaries:"])
    lines.extend(_format_reviewer_summaries(report))

    if guardrails.forbidden_patterns:
        lines.extend(["", "Forbidden patterns (do not introduce):"])
        lines.extend(f"- {pattern}" for pattern in guardrails.forbidden_patterns[:12])

    lines.extend(
        [
            "",
            "Instructions:",
            "- Fix only the issues listed above.",
            "- For each issue, either make the smallest necessary repair or clearly explain why the issue is acceptable.",
            "- Do not broaden the scope.",
            "- Do not add unrelated refactors.",
            "- Do not introduce new dependencies unless explicitly necessary.",
            "- Preserve the original product and architecture guardrails.",
            "- Treat heuristic review lens findings as review tasks, not as automatic approval or rejection.",
            "- Add or update tests where ForgeBench identified missing coverage.",
            "- Before returning the repair, run the configured checks that failed if they are available locally. If you cannot run them, explain why.",
            "- After making changes, summarize exactly what changed and why.",
            "",
            "Project guardrails:",
        ]
    )

    if guardrails.protected_behavior:
        lines.extend(f"- {item}" for item in guardrails.protected_behavior)
    else:
        lines.append("- No project-specific protected behavior was provided.")

    lines.append("")
    return "\n".join(lines)


def _format_review_context(report: ForgeBenchReport) -> list[str]:
    signals = report.static_signals
    lines = [
        f"- Changed files in scope: {len(report.changed_files)}",
        f"- Finding count: {len(report.findings)} ({_severity_counts(report)})",
    ]
    if signals.get("path_filter_active"):
        excluded = signals.get("path_filter_excluded_count", 0)
        lines.append(f"- Path filter active: {signals.get('path_filter_included_count', 0)} included, {excluded} excluded.")
        excluded_paths = signals.get("path_filter_excluded_paths") or []
        if excluded_paths:
            lines.append("- Excluded paths: " + ", ".join(excluded_paths[:8]))
    monorepo_hint = signals.get("monorepo_hint")
    if monorepo_hint:
        lines.append(f"- Monorepo note: {monorepo_hint}")
    if report.changed_files:
        lines.append("- Top changed files: " + ", ".join(report.changed_files[:12]))
    return lines


def _format_repair_priority(
    report: ForgeBenchReport,
    omitted_keys: set[tuple[str, tuple[str, ...], str | None]],
) -> list[str]:
    ordered = [
        finding
        for finding in report.findings
        if _finding_key(finding) not in omitted_keys
    ]
    severity_order = {
        Severity.BLOCKER: 0,
        Severity.HIGH: 1,
        Severity.MEDIUM: 2,
        Severity.LOW: 3,
        Severity.ADVISORY: 4,
    }
    ordered.sort(key=lambda finding: (severity_order.get(finding.severity, 99), finding.id))
    if not ordered:
        return ["- No required repairs identified."]
    lines: list[str] = []
    for index, finding in enumerate(ordered[:12], start=1):
        files = ", ".join(finding.files[:2]) if finding.files else "unknown"
        lines.append(f"{index}. {finding.severity.value}: {finding.title} ({files})")
    if len(ordered) > 12:
        lines.append(f"- ...and {len(ordered) - 12} more findings.")
    return lines


def _severity_counts(report: ForgeBenchReport) -> str:
    counts: dict[str, int] = {}
    for finding in report.findings:
        counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
    if not counts:
        return "none"
    order = ["BLOCKER", "HIGH", "MEDIUM", "LOW", "ADVISORY"]
    return ", ".join(f"{severity}={counts[severity]}" for severity in order if severity in counts)


def _format_reviewer_summaries(report: ForgeBenchReport) -> list[str]:
    reviewers = report.specialized_reviewers
    if not reviewers.enabled or not reviewers.results:
        return ["- Heuristic review lenses were not run."]
    lines: list[str] = []
    for result in reviewers.results:
        finding_count = len(result.findings)
        if finding_count:
            lines.append(f"- {result.reviewer_name}: {result.summary} ({finding_count} finding(s))")
        else:
            lines.append(f"- {result.reviewer_name}: {result.summary}")
    return lines


def _posture_instruction(report: ForgeBenchReport) -> str:
    if report.posture == MergePosture.BLOCK and _has_failed_blocking_check(report):
        return "Do not proceed to merge until the failing deterministic checks pass."
    if report.posture == MergePosture.BLOCK:
        return "Do not proceed to merge until these issues are addressed."
    if report.posture == MergePosture.REVIEW:
        return "Address the issues below or explain why each is acceptable."
    return "No required repair was identified. Use this only to tighten tests or advisory concerns."


def _format_evidence(evidence: list[str]) -> list[str]:
    if not evidence:
        return []
    lines = ["  Evidence snippets:"]
    lines.extend(f"  - {snippet}" for snippet in evidence)
    return lines


def _format_findings(findings: list[Finding], report: ForgeBenchReport) -> list[str]:
    lines: list[str] = []
    for finding in findings:
        files = ", ".join(finding.files) if finding.files else "unknown"
        lines.extend(
            [
                f"- {finding.severity.value}: {finding.title}",
                f"  UID: {finding.uid}",
                f"  Kind: {finding.kind}",
                f"  Confidence: {finding.confidence.value}",
                f"  Evidence: {finding.evidence_type.value}",
                f"  Files: {files}",
                *_format_evidence(finding.evidence),
                f"  Explanation: {finding.explanation}",
                f"  Suggested fix: {finding.suggested_fix}",
                *_format_hunk_context(finding, report, indent="  "),
            ]
        )
    return lines


def _format_check_failures(
    report: ForgeBenchReport,
    omitted_keys: set[tuple[str, tuple[str, ...], str | None]],
) -> list[str]:
    failing_results = [
        result
        for result in report.deterministic_checks.results
        if result.status in {CheckStatus.FAILED, CheckStatus.ERROR, CheckStatus.TIMED_OUT}
    ]
    if failing_results:
        lines: list[str] = []
        for result in failing_results:
            lines.extend(_format_check_result(result, report, omitted_keys))
        return lines
    if not report.deterministic_checks.run_requested:
        return ["- Deterministic checks were not run."]
    if not report.deterministic_checks.results:
        return ["- No deterministic checks were configured."]
    return ["- No deterministic check failures were reported."]


def _format_check_result(
    result: CheckResult,
    report: ForgeBenchReport,
    omitted_keys: set[tuple[str, tuple[str, ...], str | None]],
) -> list[str]:
    finding = _deterministic_finding_for_result(result, report)
    if finding and _finding_key(finding) in omitted_keys:
        finding = None
    prefix = f"- {finding.severity.value}: {finding.title}" if finding else f"- {result.name}: {result.status.value}"
    lines = [
        prefix,
        f"  Check status: {result.name}: {result.status.value}",
        f"  Command to rerun: {result.command or '(not configured)'}",
        f"  Exit code: {result.exit_code if result.exit_code is not None else 'none'}",
        f"  Duration: {result.duration_seconds:.2f}s",
    ]
    if finding:
        lines.extend(
            [
                f"  UID: {finding.uid}",
                f"  Kind: {finding.kind}",
                f"  Explanation: {finding.explanation}",
                f"  Suggested fix: {finding.suggested_fix}",
            ]
        )
        lines.extend(_format_hunk_context(finding, report, indent="  "))
    if result.error_message:
        lines.append(f"  Error: {result.error_message}")
    if result.stdout_excerpt:
        lines.append(f"  stdout excerpt: {_single_line(result.stdout_excerpt)}")
    if result.stderr_excerpt:
        lines.append(f"  stderr excerpt: {_single_line(result.stderr_excerpt)}")
    return lines


def _deterministic_finding_for_result(result: CheckResult, report: ForgeBenchReport):
    check_marker = f"Check: {result.name}"
    for finding in report.findings:
        if finding.evidence_type == EvidenceType.DETERMINISTIC and check_marker in finding.evidence:
            return finding
    return None


def _has_failed_blocking_check(report: ForgeBenchReport) -> bool:
    return any(finding.id in {"build_failed", "tests_failed", "typecheck_failed"} for finding in report.findings)


def _single_line(value: str) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= 500:
        return collapsed
    return collapsed[:497].rstrip() + "..."


def _format_policy_notes(report: ForgeBenchReport) -> list[str]:
    notes: list[str] = []
    for finding in report.policy.suppressed_findings:
        notes.append(
            f"- {finding.finding_id} was suppressed by {finding.matched_rule}: {finding.reason} "
            "Do not repair this unless the policy is wrong."
        )
    for adjustment in report.policy.finding_adjustments:
        if adjustment.action == "suppress":
            continue
        notes.append(
            f"- {adjustment.finding_id} was calibrated by {adjustment.matched_rule}: "
            f"{adjustment.reason or 'No reason provided.'}"
        )
    if report.policy.posture_ceiling:
        notes.append(
            f"- Merge posture was capped at {report.policy.posture_ceiling.value}: "
            f"{report.policy.posture_ceiling_reason or 'No reason provided.'}"
        )
    return notes or ["- None."]


def _format_specialized_reviewer_findings(
    report: ForgeBenchReport,
    omitted_keys: set[tuple[str, tuple[str, ...], str | None]],
) -> list[str]:
    reviewers = report.specialized_reviewers
    if not reviewers.enabled:
        return ["- Heuristic review lenses were not run."]
    lines: list[str] = []
    for result in reviewers.results:
        findings = [finding for finding in result.findings if _finding_key(finding) not in omitted_keys]
        if not findings:
            continue
        lines.append(f"- {result.reviewer_name}:")
        for finding in findings:
            files = ", ".join(finding.files) if finding.files else "unknown"
            lines.extend(
                [
                    f"  - {finding.severity.value}: {finding.title}",
                    f"    UID: {finding.uid}",
                    f"    Kind: {finding.kind}",
                    f"    Confidence: {finding.confidence.value}",
                    f"    Files: {files}",
                    *_format_nested_evidence(finding.evidence),
                    f"    Explanation: {finding.explanation}",
                    f"    Suggested fix: {finding.suggested_fix}",
                    *_format_llm_lens_note(finding),
                    *_format_hunk_context(finding, report, indent="    "),
                ]
            )
    return lines or ["- No heuristic review lens findings."]


def _format_nested_evidence(evidence: list[str]) -> list[str]:
    if not evidence:
        return []
    lines = ["    Evidence snippets:"]
    lines.extend(f"    - {snippet}" for snippet in evidence)
    return lines


def _format_llm_lens_note(finding: Finding) -> list[str]:
    if finding.evidence_type != EvidenceType.LLM:
        return []
    return ["    Note: Test Skeptic v2 flagged weak test semantics. Treat this as a review task, not proof."]


def _format_llm_notes(
    report: ForgeBenchReport,
    omitted_keys: set[tuple[str, tuple[str, ...], str | None]],
) -> list[str]:
    review = report.llm_review
    if not review.enabled:
        return ["- LLM review was not run."]
    if review.status.value == "failed":
        return [f"- LLM review failed: {review.error_message or 'unknown error'}"]
    if review.status.value != "completed":
        return [f"- LLM review status: {review.status.value}"]
    if not review.findings:
        summary = review.raw_summary or "No additional LLM findings beyond existing deterministic/static evidence."
        return [f"- {summary}"]
    findings = [finding for finding in review.findings if _finding_key(finding) not in omitted_keys]
    if not findings:
        return ["- LLM findings were omitted to fit the prompt size cap."]
    lines = [
        "- LLM findings are advisory. Address them where useful, but do not treat low-confidence LLM notes as mandatory repairs."
    ]
    lines.extend(_format_findings(findings, report))
    return lines


def _format_hunk_context(finding: Finding, report: ForgeBenchReport, indent: str) -> list[str]:
    hunk_lines, truncated = _hunk_lines_for_finding(finding, report)
    lines = [f"{indent}Diff hunk context:"]
    if not hunk_lines:
        lines.append(f"{indent}No matching diff hunk was available for this finding.")
        return lines
    lines.append(f"{indent}```diff")
    lines.extend(f"{indent}{line}" for line in hunk_lines)
    lines.append(f"{indent}```")
    if truncated:
        lines.append(f"{indent}... (truncated, see patch.diff for full context)")
    return lines


def _hunk_lines_for_finding(finding: Finding, report: ForgeBenchReport) -> tuple[list[str], bool]:
    diff = report.diff_summary
    if diff is None or not finding.files:
        return [], False

    targets = {path.replace("\\", "/") for path in finding.files}
    lines: list[str] = []
    truncated = False
    for changed_file in diff.files:
        path_candidates = {changed_file.path.replace("\\", "/")}
        if changed_file.old_path:
            path_candidates.add(changed_file.old_path.replace("\\", "/"))
        if not targets.intersection(path_candidates):
            continue
        for hunk in changed_file.hunks:
            candidate = [f"diff -- {changed_file.path}", hunk.header, *hunk.lines]
            for line in candidate:
                if len(lines) >= MAX_FINDING_HUNK_LINES:
                    return lines, True
                lines.append(line)
    return lines, truncated


def _droppable_finding_keys(report: ForgeBenchReport) -> list[tuple[str, tuple[str, ...], str | None]]:
    findings = list(report.findings)
    ordered: list[Finding] = []
    ordered.extend(
        finding
        for finding in findings
        if finding.severity in {Severity.LOW, Severity.ADVISORY}
        and not (finding.evidence_type == EvidenceType.DETERMINISTIC and finding.severity == Severity.BLOCKER)
    )
    ordered.extend(
        finding
        for finding in findings
        if finding.severity == Severity.MEDIUM
        and not (finding.evidence_type == EvidenceType.DETERMINISTIC and finding.severity == Severity.BLOCKER)
    )
    ordered.extend(
        finding
        for finding in findings
        if finding.severity == Severity.HIGH and finding.evidence_type in {EvidenceType.REVIEWER, EvidenceType.LLM}
    )
    seen: set[tuple[str, tuple[str, ...], str | None]] = set()
    keys: list[tuple[str, tuple[str, ...], str | None]] = []
    for finding in ordered:
        key = _finding_key(finding)
        if key in seen:
            continue
        seen.add(key)
        keys.append(key)
    return keys


def _finding_key(finding: Finding) -> tuple[str, tuple[str, ...], str | None]:
    return finding.id, tuple(sorted(finding.files)), finding.reviewer
