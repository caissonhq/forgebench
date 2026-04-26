from __future__ import annotations

from forgebench.models import CheckResult, CheckStatus, EvidenceType, ForgeBenchReport, Guardrails, MergePosture


def build_repair_prompt(task_text: str, report: ForgeBenchReport, guardrails: Guardrails) -> str:
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
    ]

    lines.extend(["Deterministic check failures:"])
    lines.extend(_format_check_failures(report))

    lines.extend(["", "Static and guardrail findings:"])
    static_findings = [
        finding
        for finding in report.findings
        if finding.evidence_type not in {EvidenceType.DETERMINISTIC, EvidenceType.REVIEWER, EvidenceType.LLM}
    ]
    if static_findings:
        lines.extend(_format_findings(static_findings))
    else:
        lines.append("- No static or guardrail findings.")

    lines.extend(["", "Specialized reviewer findings:"])
    lines.extend(_format_specialized_reviewer_findings(report))

    lines.extend(["", "LLM reviewer notes:"])
    lines.extend(_format_llm_notes(report))

    lines.extend(["", "Suppressed or policy-calibrated findings:"])
    lines.extend(_format_policy_notes(report))

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
            "- Treat specialized reviewer findings as review tasks, not as automatic approval or rejection.",
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


def _format_findings(findings) -> list[str]:
    lines: list[str] = []
    for finding in findings:
        files = ", ".join(finding.files) if finding.files else "unknown"
        lines.extend(
            [
                f"- {finding.severity.value}: {finding.title}",
                f"  Confidence: {finding.confidence.value}",
                f"  Evidence: {finding.evidence_type.value}",
                f"  Files: {files}",
                *_format_evidence(finding.evidence),
                f"  Explanation: {finding.explanation}",
                f"  Suggested fix: {finding.suggested_fix}",
            ]
        )
    return lines


def _format_check_failures(report: ForgeBenchReport) -> list[str]:
    failing_results = [
        result
        for result in report.deterministic_checks.results
        if result.status in {CheckStatus.FAILED, CheckStatus.ERROR, CheckStatus.TIMED_OUT}
    ]
    if failing_results:
        lines: list[str] = []
        for result in failing_results:
            lines.extend(_format_check_result(result, report))
        return lines
    if not report.deterministic_checks.run_requested:
        return ["- Deterministic checks were not run."]
    if not report.deterministic_checks.results:
        return ["- No deterministic checks were configured."]
    return ["- No deterministic check failures were reported."]


def _format_check_result(result: CheckResult, report: ForgeBenchReport) -> list[str]:
    finding = _deterministic_finding_for_result(result, report)
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
                f"  Explanation: {finding.explanation}",
                f"  Suggested fix: {finding.suggested_fix}",
            ]
        )
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


def _format_specialized_reviewer_findings(report: ForgeBenchReport) -> list[str]:
    reviewers = report.specialized_reviewers
    if not reviewers.enabled:
        return ["- Specialized reviewers were not run."]
    lines: list[str] = []
    for result in reviewers.results:
        if not result.findings:
            continue
        lines.append(f"- {result.reviewer_name}:")
        for finding in result.findings:
            files = ", ".join(finding.files) if finding.files else "unknown"
            lines.extend(
                [
                    f"  - {finding.severity.value}: {finding.title}",
                    f"    Confidence: {finding.confidence.value}",
                    f"    Files: {files}",
                    *_format_nested_evidence(finding.evidence),
                    f"    Explanation: {finding.explanation}",
                    f"    Suggested fix: {finding.suggested_fix}",
                ]
            )
    return lines or ["- No specialized reviewer findings."]


def _format_nested_evidence(evidence: list[str]) -> list[str]:
    if not evidence:
        return []
    lines = ["    Evidence snippets:"]
    lines.extend(f"    - {snippet}" for snippet in evidence)
    return lines


def _format_llm_notes(report: ForgeBenchReport) -> list[str]:
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
    lines = [
        "- LLM findings are advisory. Address them where useful, but do not treat low-confidence LLM notes as mandatory repairs."
    ]
    lines.extend(_format_findings(review.findings))
    return lines
