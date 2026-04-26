from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from forgebench.calibration import (
    ExpectedCase,
    compare_expected,
    discover_cases,
    load_case,
    run_calibration,
    validate_json_report,
    validate_markdown_report,
    validate_repair_prompt,
)
from forgebench.cli import main
from forgebench.models import Confidence, EvidenceType, Finding, ForgeBenchReport, MergePosture, Severity


ROOT = Path(__file__).resolve().parents[1]
GOLDEN_CASES = ROOT / "examples" / "golden_cases"


class CalibrationTests(unittest.TestCase):
    def test_calibration_case_loading(self) -> None:
        case = load_case(GOLDEN_CASES / "docs_only_low_concern")

        self.assertEqual(case.name, "docs_only_low_concern")
        self.assertEqual(case.expected.expected_posture, "LOW_CONCERN")
        self.assertIn("ui_copy_changed", case.expected.required_finding_ids)

    def test_expected_posture_comparison_passes(self) -> None:
        report = _report(MergePosture.LOW_CONCERN, ["ui_copy_changed"])
        expected = ExpectedCase(
            case_name="sample",
            run_checks=False,
            expected_posture="LOW_CONCERN",
            required_finding_ids={"ui_copy_changed"},
        )

        result = compare_expected(report, expected)

        self.assertTrue(result.passed)

    def test_expected_posture_comparison_fails(self) -> None:
        report = _report(MergePosture.REVIEW, ["ui_copy_changed"])
        expected = ExpectedCase(
            case_name="sample",
            run_checks=False,
            expected_posture="LOW_CONCERN",
            required_finding_ids={"ui_copy_changed"},
        )

        result = compare_expected(report, expected)

        self.assertFalse(result.passed)
        self.assertEqual(result.actual_posture, "REVIEW")

    def test_required_finding_ids_are_enforced(self) -> None:
        report = _report(MergePosture.LOW_CONCERN, ["ui_copy_changed"])
        expected = ExpectedCase(
            case_name="sample",
            run_checks=False,
            expected_posture="LOW_CONCERN",
            required_finding_ids={"implementation_without_tests"},
            allowed_extra_finding_ids={"ui_copy_changed"},
        )

        result = compare_expected(report, expected)

        self.assertFalse(result.passed)
        self.assertEqual(result.missing_required_findings, ["implementation_without_tests"])

    def test_forbidden_finding_ids_are_enforced(self) -> None:
        report = _report(MergePosture.LOW_CONCERN, ["ui_copy_changed"])
        expected = ExpectedCase(
            case_name="sample",
            run_checks=False,
            expected_posture="LOW_CONCERN",
            required_finding_ids={"ui_copy_changed"},
            forbidden_finding_ids={"ui_copy_changed"},
        )

        result = compare_expected(report, expected)

        self.assertFalse(result.passed)
        self.assertEqual(result.forbidden_findings_present, ["ui_copy_changed"])

    def test_unexpected_findings_fail_unless_allowed(self) -> None:
        report = _report(MergePosture.LOW_CONCERN, ["ui_copy_changed", "generated_files_changed"])
        strict = ExpectedCase(
            case_name="sample",
            run_checks=False,
            expected_posture="LOW_CONCERN",
            required_finding_ids={"ui_copy_changed"},
        )
        permissive = ExpectedCase(
            case_name="sample",
            run_checks=False,
            expected_posture="LOW_CONCERN",
            required_finding_ids={"ui_copy_changed"},
            allow_unlisted_findings=True,
        )

        self.assertFalse(compare_expected(report, strict).passed)
        self.assertEqual(compare_expected(report, strict).unexpected_findings, ["generated_files_changed"])
        self.assertTrue(compare_expected(report, permissive).passed)

    def test_markdown_code_fence_validation_catches_unbalanced_fences(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "forgebench-report.md"
            path.write_text(
                "# ForgeBench Merge Risk Report\n\n"
                "## Merge Posture\n\n"
                "## Deterministic Checks\n\n"
                "## LLM Review\n\n"
                "## Suggested Next Action\n\n"
                "```text\nunclosed\n",
                encoding="utf-8",
            )

            errors = validate_markdown_report(path)

            self.assertTrue(any("code fences" in error for error in errors))

    def test_json_artifact_validation_catches_invalid_json(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "forgebench-report.json"
            path.write_text("{not json", encoding="utf-8")

            errors = validate_json_report(path)

            self.assertTrue(any("invalid" in error for error in errors))

    def test_repair_prompt_validation_catches_missing_task_and_posture(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "repair-prompt.md"
            path.write_text("Do not broaden the scope.\nDo not add unrelated refactors.\n", encoding="utf-8")

            errors = validate_repair_prompt(path, "Original task text", _report(MergePosture.REVIEW, []))

            self.assertTrue(any("task" in error for error in errors))
            self.assertTrue(any("posture" in error for error in errors))

    def test_calibration_runner_passes_included_golden_corpus(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_calibration(GOLDEN_CASES, output_dir=Path(tmp) / "out", repo_path=ROOT)

        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.passed_count, 29)

    def test_cli_calibrate_command_works(self) -> None:
        with TemporaryDirectory() as tmp:
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "calibrate",
                        "--cases",
                        str(GOLDEN_CASES),
                        "--repo",
                        str(ROOT),
                        "--out",
                        str(Path(tmp) / "out"),
                    ]
            )

            self.assertEqual(result, 0)
            self.assertIn("Cases: 29", stdout.getvalue())
            self.assertIn("Failed: 0", stdout.getvalue())

    def test_cli_calibrate_returns_nonzero_when_case_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            cases_dir = Path(tmp) / "cases"
            case_dir = cases_dir / "bad_case"
            case_dir.mkdir(parents=True)
            (case_dir / "patch.diff").write_text((GOLDEN_CASES / "docs_only_low_concern" / "patch.diff").read_text(), encoding="utf-8")
            (case_dir / "task.md").write_text("Clarify docs.\n", encoding="utf-8")
            (case_dir / "expected.json").write_text(
                json.dumps(
                    {
                        "case_name": "bad_case",
                        "run_checks": False,
                        "expected_posture": "BLOCK",
                        "required_finding_ids": ["deleted_tests"],
                        "allowed_extra_finding_ids": [],
                        "forbidden_finding_ids": [],
                    }
                ),
                encoding="utf-8",
            )
            stdout = StringIO()

            with redirect_stdout(stdout):
                result = main(
                    [
                        "calibrate",
                        "--cases",
                        str(cases_dir),
                        "--repo",
                        str(ROOT),
                        "--out",
                        str(Path(tmp) / "out"),
                    ]
                )

            self.assertEqual(result, 1)
            self.assertIn("FAIL bad_case", stdout.getvalue())


def _report(posture: MergePosture, finding_ids: list[str]) -> ForgeBenchReport:
    findings = [
        Finding(
            id=finding_id,
            title=finding_id.replace("_", " ").title(),
            severity=Severity.ADVISORY,
            confidence=Confidence.LOW,
            evidence_type=EvidenceType.STATIC,
            files=[],
            explanation="Test finding.",
            suggested_fix="Review the finding.",
        )
        for finding_id in finding_ids
    ]
    return ForgeBenchReport(
        posture=posture,
        summary="Test summary.",
        task_summary="Test task.",
        changed_files=[],
        findings=findings,
        static_signals={},
        guardrail_hits=[],
        generated_at="2026-04-25T00:00:00+00:00",
    )


if __name__ == "__main__":
    unittest.main()
