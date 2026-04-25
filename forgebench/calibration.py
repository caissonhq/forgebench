from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from forgebench.models import ForgeBenchReport
from forgebench.review import ReviewInputError, ReviewResult, run_review


@dataclass(frozen=True)
class ExpectedCase:
    case_name: str
    run_checks: bool
    expected_posture: str
    required_finding_ids: set[str] = field(default_factory=set)
    allowed_extra_finding_ids: set[str] = field(default_factory=set)
    forbidden_finding_ids: set[str] = field(default_factory=set)
    allow_unlisted_findings: bool = False
    rationale: str = ""


@dataclass(frozen=True)
class GoldenCase:
    name: str
    directory: Path
    patch_path: Path
    task_path: Path
    guardrails_path: Path | None
    expected: ExpectedCase


@dataclass
class CaseResult:
    case_name: str
    passed: bool
    expected_posture: str
    actual_posture: str | None = None
    missing_required_findings: list[str] = field(default_factory=list)
    forbidden_findings_present: list[str] = field(default_factory=list)
    unexpected_findings: list[str] = field(default_factory=list)
    artifact_errors: list[str] = field(default_factory=list)
    error_message: str | None = None
    report_path: Path | None = None


@dataclass(frozen=True)
class CalibrationResult:
    cases: list[CaseResult]

    @property
    def passed_count(self) -> int:
        return sum(1 for case in self.cases if case.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for case in self.cases if not case.passed)


def discover_cases(cases_dir: str | Path) -> list[GoldenCase]:
    root = Path(cases_dir)
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"cases directory does not exist: {root}")

    cases: list[GoldenCase] = []
    for case_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        cases.append(load_case(case_dir))
    return cases


def load_case(case_dir: str | Path) -> GoldenCase:
    directory = Path(case_dir)
    expected_path = directory / "expected.json"
    patch_path = directory / "patch.diff"
    task_path = directory / "task.md"
    guardrails_path = directory / "forgebench.yml"

    for required_path in [expected_path, patch_path, task_path]:
        if not required_path.exists():
            raise FileNotFoundError(f"golden case missing required file: {required_path}")

    expected = _load_expected(expected_path)
    name = expected.case_name or directory.name
    return GoldenCase(
        name=name,
        directory=directory,
        patch_path=patch_path,
        task_path=task_path,
        guardrails_path=guardrails_path if guardrails_path.exists() else None,
        expected=expected,
    )


def run_calibration(
    cases_dir: str | Path,
    output_dir: str | Path = "forgebench-calibration-output",
    repo_path: str | Path = ".",
) -> CalibrationResult:
    cases = discover_cases(cases_dir)
    output_root = Path(output_dir)
    results = [_run_case(case, repo_path=Path(repo_path), output_root=output_root) for case in cases]
    return CalibrationResult(cases=results)


def compare_expected(report: ForgeBenchReport, expected: ExpectedCase) -> CaseResult:
    actual_ids = {finding.id for finding in report.findings}
    missing = sorted(expected.required_finding_ids - actual_ids)
    forbidden_present = sorted(expected.forbidden_finding_ids & actual_ids)
    expected_ids = expected.required_finding_ids | expected.allowed_extra_finding_ids
    unexpected = [] if expected.allow_unlisted_findings else sorted(actual_ids - expected_ids)
    posture_matches = report.posture.value == expected.expected_posture

    return CaseResult(
        case_name=expected.case_name,
        passed=posture_matches and not missing and not forbidden_present and not unexpected,
        expected_posture=expected.expected_posture,
        actual_posture=report.posture.value,
        missing_required_findings=missing,
        forbidden_findings_present=forbidden_present,
        unexpected_findings=unexpected,
    )


def validate_markdown_report(path: str | Path) -> list[str]:
    report_path = Path(path)
    if not report_path.exists():
        return [f"Markdown report missing: {report_path}"]
    text = report_path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    for required in [
        "# ForgeBench Merge Risk Report",
        "## Merge Posture",
        "## Deterministic Checks",
        "## Suggested Next Action",
    ]:
        if required not in text:
            errors.append(f"Markdown report missing section: {required}")
    if _unclosed_code_fence(text):
        errors.append("Markdown report has unbalanced code fences.")
    return errors


def validate_json_report(path: str | Path) -> list[str]:
    report_path = Path(path)
    if not report_path.exists():
        return [f"JSON report missing: {report_path}"]
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"JSON report is invalid: {exc}"]
    errors: list[str] = []
    for key in ["posture", "findings", "deterministic_checks"]:
        if key not in payload:
            errors.append(f"JSON report missing key: {key}")
    return errors


def validate_repair_prompt(path: str | Path, task_text: str, report: ForgeBenchReport) -> list[str]:
    prompt_path = Path(path)
    if not prompt_path.exists():
        return [f"Repair prompt missing: {prompt_path}"]
    text = prompt_path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    if task_text.strip() and task_text.strip() not in text:
        errors.append("Repair prompt missing original task text.")
    if report.posture.value not in text:
        errors.append("Repair prompt missing merge posture.")
    for instruction in ["Do not broaden the scope.", "Do not add unrelated refactors."]:
        if instruction not in text:
            errors.append(f"Repair prompt missing scope-control instruction: {instruction}")
    if report.findings:
        missing_titles = [finding.title for finding in report.findings if finding.title not in text]
        if missing_titles:
            errors.append("Repair prompt missing finding titles: " + ", ".join(missing_titles))
    return errors


def validate_report_artifacts(review_result: ReviewResult) -> list[str]:
    paths = review_result.written_paths
    errors: list[str] = []
    errors.extend(validate_markdown_report(paths["markdown"]))
    errors.extend(validate_json_report(paths["json"]))
    errors.extend(validate_repair_prompt(paths["repair_prompt"], review_result.task_text, review_result.report))
    return errors


def format_calibration_result(result: CalibrationResult) -> str:
    lines = [
        "ForgeBench calibration complete.",
        "",
        f"Cases: {len(result.cases)}",
        f"Passed: {result.passed_count}",
        f"Failed: {result.failed_count}",
        "",
    ]
    for case in result.cases:
        lines.append(("PASS " if case.passed else "FAIL ") + case.case_name)
        if not case.passed:
            lines.extend(_format_case_failure(case))
    return "\n".join(lines)


def _run_case(case: GoldenCase, repo_path: Path, output_root: Path) -> CaseResult:
    try:
        review_result = run_review(
            repo_path=repo_path,
            diff_path=case.patch_path,
            task_path=case.task_path,
            guardrails_path=case.guardrails_path,
            output_dir=output_root / case.name,
            run_checks=case.expected.run_checks,
        )
    except (ReviewInputError, OSError) as exc:
        return CaseResult(
            case_name=case.name,
            passed=False,
            expected_posture=case.expected.expected_posture,
            error_message=str(exc),
            report_path=output_root / case.name / "forgebench-report.md",
        )

    comparison = compare_expected(review_result.report, case.expected)
    artifact_errors = validate_report_artifacts(review_result)
    comparison.case_name = case.name
    comparison.artifact_errors = artifact_errors
    comparison.report_path = review_result.written_paths["markdown"]
    comparison.passed = comparison.passed and not artifact_errors
    return comparison


def _load_expected(path: Path) -> ExpectedCase:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ExpectedCase(
        case_name=str(payload.get("case_name") or path.parent.name),
        run_checks=bool(payload.get("run_checks", False)),
        expected_posture=str(payload["expected_posture"]),
        required_finding_ids=set(payload.get("required_finding_ids", [])),
        allowed_extra_finding_ids=set(payload.get("allowed_extra_finding_ids", [])),
        forbidden_finding_ids=set(payload.get("forbidden_finding_ids", [])),
        allow_unlisted_findings=bool(payload.get("allow_unlisted_findings", False)),
        rationale=str(payload.get("rationale", "")),
    )


def _format_case_failure(case: CaseResult) -> list[str]:
    lines = [
        "",
        "Expected posture:",
        case.expected_posture,
        "",
        "Actual posture:",
        case.actual_posture or "not available",
    ]
    if case.missing_required_findings:
        lines.extend(["", "Missing required findings:"])
        lines.extend(f"- {finding_id}" for finding_id in case.missing_required_findings)
    if case.forbidden_findings_present:
        lines.extend(["", "Forbidden findings present:"])
        lines.extend(f"- {finding_id}" for finding_id in case.forbidden_findings_present)
    if case.unexpected_findings:
        lines.extend(["", "Unexpected findings:"])
        lines.extend(f"- {finding_id}" for finding_id in case.unexpected_findings)
    if case.artifact_errors:
        lines.extend(["", "Artifact errors:"])
        lines.extend(f"- {error}" for error in case.artifact_errors)
    if case.error_message:
        lines.extend(["", "Error:", case.error_message])
    if case.report_path:
        lines.extend(["", "Report path:", str(case.report_path)])
    lines.append("")
    return lines


def _unclosed_code_fence(text: str) -> bool:
    fence_count = 0
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fence_count += 1
    return fence_count % 2 != 0
