from __future__ import annotations

import json
from pathlib import Path

from forgebench.models import CheckResult, CheckStatus, Confidence, ForgeBenchReport, Guardrails
from forgebench.repair_prompt import build_repair_prompt


REPORT_MD = "forgebench-report.md"
REPORT_JSON = "forgebench-report.json"
REPAIR_PROMPT = "repair-prompt.md"


def write_reports(
    out_dir: str | Path,
    report: ForgeBenchReport,
    guardrails: Guardrails,
    task_text: str,
    inputs: dict[str, str],
) -> dict[str, Path]:
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = output_dir / REPORT_MD
    json_path = output_dir / REPORT_JSON
    repair_prompt_path = output_dir / REPAIR_PROMPT

    markdown_path.write_text(build_markdown_report(report, guardrails, inputs), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    repair_prompt_path.write_text(build_repair_prompt(task_text, report, guardrails), encoding="utf-8")

    return {
        "markdown": markdown_path,
        "json": json_path,
        "repair_prompt": repair_prompt_path,
    }


def build_markdown_report(report: ForgeBenchReport, guardrails: Guardrails, inputs: dict[str, str]) -> str:
    high_confidence = [finding for finding in report.findings if finding.confidence == Confidence.HIGH]
    other_findings = [finding for finding in report.findings if finding.confidence != Confidence.HIGH]

    lines: list[str] = [
        "# ForgeBench Merge Risk Report",
        "",
        "## Merge Posture",
        "",
        _posture_heading(report.posture.value),
        "",
        "## Summary",
        "",
        report.summary,
        "",
        "## Suggested Next Action",
        "",
        _suggested_next_action(report),
        "",
        "## Inputs",
        "",
        f"- Repo: {inputs.get('repo', '')}",
        f"- Diff: {inputs.get('diff', '')}",
        f"- Task: {inputs.get('task', '')}",
        f"- Guardrails: {inputs.get('guardrails', 'none')}",
        "",
        "## Deterministic Checks",
        "",
        *_format_deterministic_checks(report),
        "",
        "## Static Signals",
        "",
        f"- Changed file count: {report.static_signals.get('changed_file_count', len(report.changed_files))}",
        f"- Added lines: {report.static_signals.get('added_line_count', 0)}",
        f"- Deleted lines: {report.static_signals.get('deleted_line_count', 0)}",
        f"- Tests changed: {'yes' if report.static_signals.get('tests_changed') else 'no'}",
        f"- Finding counts by severity: {_severity_counts(report)}",
        "",
        "## Changed Files",
        "",
    ]

    if report.changed_files:
        lines.extend(f"- {path}" for path in report.changed_files)
    else:
        lines.append("- No changed files detected.")

    lines.extend(["", "## High-Confidence Issues", ""])
    lines.extend(_format_findings(high_confidence, "No high-confidence issues found."))

    lines.extend(["", "## Medium / Low Confidence Risks", ""])
    lines.extend(_format_findings(other_findings, "No medium, low, or advisory findings found."))

    lines.extend(["", "## Guardrail Review", "", "Protected behavior:"])
    if guardrails.protected_behavior:
        lines.extend(f"- {item}" for item in guardrails.protected_behavior)
    else:
        lines.append("- None provided.")

    lines.extend(["", "Guardrail hits:"])
    if report.guardrail_hits:
        lines.extend(f"- {hit}" for hit in report.guardrail_hits)
    else:
        lines.append("- None.")

    lines.extend(["", "## Guardrails Policy", ""])
    lines.extend(_format_policy_decision(report))

    lines.extend(["", "## Repair Prompt", "", "See repair-prompt.md.", ""])
    return "\n".join(lines)


def _format_findings(findings, empty_message: str) -> list[str]:
    if not findings:
        return [empty_message]

    lines: list[str] = []
    for finding in findings:
        files = ", ".join(finding.files) if finding.files else "unknown"
        lines.extend(
            [
                f"### {finding.title}",
                "",
                f"- Severity: {finding.severity.value}",
                f"- Confidence: {finding.confidence.value}",
                f"- Evidence: {finding.evidence_type.value}",
                f"- Files: {files}",
                *_format_evidence_snippets(finding.evidence),
                f"- Explanation: {finding.explanation}",
                f"- Suggested fix: {finding.suggested_fix}",
                "",
            ]
        )
    return lines


def _posture_heading(posture: str) -> str:
    if posture == "BLOCK":
        return "BLOCK MERGE"
    if posture == "REVIEW":
        return "REVIEW BEFORE MERGE"
    return "LOW CONCERN"


def _suggested_next_action(report: ForgeBenchReport) -> str:
    posture = report.posture.value
    checks = report.deterministic_checks
    if posture == "BLOCK" and _has_failed_blocking_check(report):
        return "Do not merge. Fix the failing deterministic checks, regenerate the diff if needed, and rerun ForgeBench."
    if posture == "REVIEW" and _has_lint_failure(report):
        return "Review before merge. The patch has no build/test blocker, but at least one configured quality check failed."
    if posture == "REVIEW" and _has_timed_out_check(report):
        return "Review before merge. Investigate the timed out deterministic checks, rerun them locally, and rerun ForgeBench."
    if posture == "LOW_CONCERN" and checks.run_requested and checks.results and _configured_checks_passed(checks.results):
        return "Proceed with normal human review. Configured deterministic checks passed and ForgeBench found no high-confidence blockers."
    if posture == "LOW_CONCERN" and not checks.run_requested:
        return "Proceed cautiously with normal human review. Deterministic checks were not run."
    if posture == "BLOCK":
        return "Do not merge yet. Run the repair prompt, regenerate the diff, and rerun ForgeBench."
    if posture == "REVIEW":
        return "Review the listed risks before merge. If the patch was agent-generated, paste repair-prompt.md back into your coding agent."
    return "Proceed with normal human review. No required repair was identified."


def _severity_counts(report: ForgeBenchReport) -> str:
    counts: dict[str, int] = {}
    for finding in report.findings:
        counts[finding.severity.value] = counts.get(finding.severity.value, 0) + 1
    if not counts:
        return "none"
    order = ["BLOCKER", "HIGH", "MEDIUM", "LOW", "ADVISORY"]
    return ", ".join(f"{severity}={counts[severity]}" for severity in order if severity in counts)


def _format_evidence_snippets(evidence: list[str]) -> list[str]:
    if not evidence:
        return []
    lines = ["- Evidence snippets:"]
    lines.extend(f"  - {snippet}" for snippet in evidence)
    return lines


def _format_deterministic_checks(report: ForgeBenchReport) -> list[str]:
    checks = report.deterministic_checks
    if not checks.run_requested:
        return ["Not run. Re-run with --run-checks to execute configured local verification commands."]
    if not checks.results:
        return ["No checks configured. Add a checks section to forgebench.yml to enable build/test/lint/typecheck evidence."]

    lines = [_deterministic_summary_line(report)]
    for result in checks.results:
        lines.extend(
            [
                "",
                f"### {result.name}",
                "",
                f"- Status: {result.status.value}",
                f"- Command: {result.command or '(not configured)'}",
                f"- Exit code: {result.exit_code if result.exit_code is not None else 'none'}",
                f"- Duration: {result.duration_seconds:.2f}s",
            ]
        )
        if result.error_message and result.status != CheckStatus.NOT_CONFIGURED:
            lines.append(f"- Error: {result.error_message}")
        excerpt = _combined_output_excerpt(result)
        if excerpt and result.status in {CheckStatus.FAILED, CheckStatus.ERROR, CheckStatus.TIMED_OUT}:
            lines.extend(["", "Output excerpt:", "", "```text", excerpt, "```"])
    return lines


def _deterministic_summary_line(report: ForgeBenchReport) -> str:
    summary = report.deterministic_checks.summary
    return (
        f"Summary: passed={summary['passed']}, failed={summary['failed']}, "
        f"timed_out={summary['timed_out']}, skipped={summary['skipped']}, "
        f"not_configured={summary['not_configured']}, errors={summary['errors']}"
    )


def _combined_output_excerpt(result: CheckResult) -> str:
    parts: list[str] = []
    if result.stdout_excerpt:
        parts.extend(["stdout:", result.stdout_excerpt.strip()])
    if result.stderr_excerpt:
        parts.extend(["stderr:", result.stderr_excerpt.strip()])
    return "\n".join(parts).strip()


def _has_failed_blocking_check(report: ForgeBenchReport) -> bool:
    blocking_ids = {"build_failed", "tests_failed", "typecheck_failed"}
    return any(finding.id in blocking_ids for finding in report.findings)


def _has_lint_failure(report: ForgeBenchReport) -> bool:
    return any(finding.id == "lint_failed" for finding in report.findings)


def _has_timed_out_check(report: ForgeBenchReport) -> bool:
    return any(result.status == CheckStatus.TIMED_OUT for result in report.deterministic_checks.results)


def _configured_checks_passed(results: list[CheckResult]) -> bool:
    configured = [result for result in results if result.status != CheckStatus.NOT_CONFIGURED]
    return bool(configured) and all(result.status == CheckStatus.PASSED for result in configured)


def _format_policy_decision(report: ForgeBenchReport) -> list[str]:
    policy = report.policy
    lines: list[str] = ["Active categories:"]
    if policy.active_categories:
        for category in policy.active_categories:
            files = ", ".join(category.files)
            severity = category.default_severity.value if category.default_severity else "none"
            lines.append(f"- {category.name}: {files} (default severity: {severity})")
    else:
        lines.append("- None.")

    lines.extend(["", "Suppressed findings:"])
    if policy.suppressed_findings:
        for finding in policy.suppressed_findings:
            files = ", ".join(finding.files) if finding.files else "unknown"
            lines.append(f"- {finding.finding_id} suppressed by {finding.matched_rule} for {files}. Reason: {finding.reason}")
    else:
        lines.append("- None.")

    lines.extend(["", "Severity/confidence overrides:"])
    overrides = [adjustment for adjustment in policy.finding_adjustments if adjustment.action != "suppress"]
    if overrides:
        for adjustment in overrides:
            severity = _format_adjusted_value(adjustment.original_severity, adjustment.new_severity)
            confidence = _format_adjusted_value(adjustment.original_confidence, adjustment.new_confidence)
            lines.append(
                f"- {adjustment.finding_id} changed by {adjustment.matched_rule}: "
                f"severity {severity}, confidence {confidence}. Reason: {adjustment.reason or 'No reason provided.'}"
            )
    else:
        lines.append("- None.")

    lines.extend(["", "Posture ceiling:"])
    if policy.posture_ceiling:
        reason = policy.posture_ceiling_reason or "No reason provided."
        rule = policy.posture_ceiling_rule or "policy"
        lines.append(f"- {policy.posture_ceiling.value} by {rule}. Reason: {reason}")
    else:
        lines.append("- None.")
    return lines


def _format_adjusted_value(original, new) -> str:
    original_value = original.value if original else "none"
    new_value = new.value if new else original_value
    return f"{original_value} -> {new_value}"
