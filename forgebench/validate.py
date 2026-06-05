from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from forgebench.guardrails import KNOWN_TOP_LEVEL_KEYS, GuardrailsParseError, parse_guardrails


@dataclass
class ValidationIssue:
    level: str
    message: str
    path: str = ""

    def format(self) -> str:
        location = f" ({self.path})" if self.path else ""
        return f"{self.level.upper()}{location}: {self.message}"


@dataclass
class ValidationReport:
    path: Path
    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.level == "warning")

    @property
    def exit_code(self) -> int:
        if self.error_count:
            return 2
        if self.warning_count:
            return 1
        return 0


def validate_guardrails_file(path: str | Path, *, strict: bool = False) -> ValidationReport:
    guardrails_path = Path(path)
    report = ValidationReport(path=guardrails_path, valid=True)
    if not guardrails_path.exists():
        report.valid = False
        report.issues.append(ValidationIssue("error", f"file does not exist: {guardrails_path}"))
        return report
    if not guardrails_path.is_file():
        report.valid = False
        report.issues.append(ValidationIssue("error", f"not a file: {guardrails_path}"))
        return report

    text = guardrails_path.read_text(encoding="utf-8", errors="replace")
    try:
        guardrails = parse_guardrails(text)
    except GuardrailsParseError as exc:
        report.valid = False
        report.issues.append(ValidationIssue("error", str(exc)))
        return report

    _lint_parsed_guardrails(guardrails, report, strict=strict)
    report.valid = report.error_count == 0
    return report


def format_validation_report(report: ValidationReport) -> str:
    lines = [f"ForgeBench guardrails validation: {report.path}"]
    if report.valid and not report.issues:
        lines.append("Valid. No issues found.")
        return "\n".join(lines)
    if report.valid:
        lines.append(f"Valid with {report.warning_count} warning(s).")
    else:
        lines.append(f"Invalid: {report.error_count} error(s), {report.warning_count} warning(s).")
    lines.append("")
    for issue in report.issues:
        lines.append(f"- {issue.format()}")
    return "\n".join(lines)


def _lint_parsed_guardrails(guardrails, report: ValidationReport, *, strict: bool) -> None:
    for warning in guardrails.warnings:
        level = "error" if strict else "warning"
        report.issues.append(ValidationIssue(level, warning, "top-level"))

    if guardrails.checks_present and not any(guardrails.checks.values()) and not guardrails.custom_checks:
        report.issues.append(
            ValidationIssue(
                "warning",
                "checks section is present but every command is null or missing.",
                "checks",
            )
        )

    for key, command in guardrails.checks.items():
        if command is not None and not str(command).strip():
            report.issues.append(ValidationIssue("warning", f"check '{key}' is blank.", f"checks.{key}"))

    for name, command in guardrails.custom_checks.items():
        if command is not None and not str(command).strip():
            report.issues.append(ValidationIssue("warning", f"custom check '{name}' is blank.", f"checks.custom.{name}"))

    for finding_id, override in guardrails.policy.finding_overrides.items():
        if override.severity is None and override.confidence is None and not override.suppress_paths:
            report.issues.append(
                ValidationIssue(
                    "warning",
                    f"finding override '{finding_id}' does not change severity, confidence, or suppress paths.",
                    f"policy.finding_overrides.{finding_id}",
                )
            )

    for index, rule in enumerate(guardrails.policy.suppress_findings):
        if not rule.paths and not rule.when_all_changed_files_match:
            report.issues.append(
                ValidationIssue(
                    "warning",
                    f"suppress_findings[{index}] for '{rule.finding_id}' has no path selectors.",
                    f"policy.suppress_findings[{index}]",
                )
            )

    for category_name, category in guardrails.policy.path_categories.items():
        if not category.patterns:
            report.issues.append(
                ValidationIssue(
                    "warning",
                    f"path category '{category_name}' has no patterns.",
                    f"policy.path_categories.{category_name}",
                )
            )

    if guardrails.review_scope_include_paths and guardrails.review_scope_exclude_paths:
        report.issues.append(
            ValidationIssue(
                "warning",
                "review_scope sets both include_paths and exclude_paths; include_paths is applied before exclude_paths.",
                "review_scope",
            )
        )

    if strict:
        _lint_raw_shape(guardrails_path=report.path, report=report)


def _lint_raw_shape(*, guardrails_path: Path, report: ValidationReport) -> None:
    import yaml

    payload = yaml.safe_load(guardrails_path.read_text(encoding="utf-8", errors="replace")) or {}
    if not isinstance(payload, dict):
        return

    unknown = sorted(set(payload) - KNOWN_TOP_LEVEL_KEYS)
    for key in unknown:
        report.issues.append(ValidationIssue("error", f"unknown top-level key '{key}'", "top-level"))

    risk_files = payload.get("risk_files")
    if risk_files is not None:
        if not isinstance(risk_files, dict):
            report.issues.append(ValidationIssue("error", "risk_files must be a mapping.", "risk_files"))
        else:
            for child in ("high", "medium"):
                value = risk_files.get(child)
                if value is not None and not isinstance(value, list):
                    report.issues.append(
                        ValidationIssue("error", f"risk_files.{child} must be a list.", f"risk_files.{child}")
                    )

    review_scope = payload.get("review_scope")
    if review_scope is not None and isinstance(review_scope, dict):
        for child in ("include_paths", "exclude_paths"):
            value = review_scope.get(child)
            if value is not None and not isinstance(value, list):
                report.issues.append(
                    ValidationIssue("error", f"review_scope.{child} must be a list.", f"review_scope.{child}")
                )

    checks = payload.get("checks")
    if checks is not None and isinstance(checks, dict):
        for key, value in checks.items():
            if key == "custom":
                if value is not None and not isinstance(value, dict):
                    report.issues.append(ValidationIssue("error", "checks.custom must be a mapping.", "checks.custom"))
                continue
            if value is not None and not isinstance(value, str):
                report.issues.append(
                    ValidationIssue("error", f"checks.{key} must be a string or null.", f"checks.{key}")
                )