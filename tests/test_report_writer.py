from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from forgebench.check_runner import findings_from_check_results, run_configured_checks
from forgebench.diff_parser import parse_diff_file
from forgebench.guardrails import Guardrails, evaluate_guardrails, load_guardrails
from forgebench.models import ForgeBenchReport
from forgebench.posture import determine_posture
from forgebench.report_writer import write_reports
from forgebench.static_checks import run_static_checks


FIXTURES = Path(__file__).parent / "fixtures"


class ReportWriterTests(unittest.TestCase):
    def test_reports_are_written_to_disk(self) -> None:
        report, guardrails, task_text = _sample_report()

        with TemporaryDirectory() as tmp:
            written = write_reports(
                tmp,
                report,
                guardrails,
                task_text,
                inputs={"repo": ".", "diff": "patch.diff", "task": "task.md", "guardrails": "none"},
            )

            self.assertTrue(written["markdown"].exists())
            self.assertTrue(written["json"].exists())
            self.assertTrue(written["repair_prompt"].exists())

    def test_repair_prompt_includes_original_task_and_findings(self) -> None:
        report, guardrails, task_text = _sample_report()

        with TemporaryDirectory() as tmp:
            written = write_reports(
                tmp,
                report,
                guardrails,
                task_text,
                inputs={"repo": ".", "diff": "patch.diff", "task": "task.md", "guardrails": "none"},
            )
            prompt = written["repair_prompt"].read_text(encoding="utf-8")

            self.assertIn(task_text.strip(), prompt)
            self.assertIn("Implementation changed without corresponding test updates", prompt)

    def test_json_report_is_valid_json(self) -> None:
        report, guardrails, task_text = _sample_report()

        with TemporaryDirectory() as tmp:
            written = write_reports(
                tmp,
                report,
                guardrails,
                task_text,
                inputs={"repo": ".", "diff": "patch.diff", "task": "task.md", "guardrails": "none"},
            )

            payload = json.loads(written["json"].read_text(encoding="utf-8"))

            self.assertEqual(payload["posture"], report.posture.value)
            self.assertIn("findings", payload)
            self.assertIn("deterministic_checks", payload)

    def test_markdown_report_includes_suggested_next_action(self) -> None:
        report, guardrails, task_text = _sample_report()

        with TemporaryDirectory() as tmp:
            written = write_reports(
                tmp,
                report,
                guardrails,
                task_text,
                inputs={"repo": ".", "diff": "patch.diff", "task": "task.md", "guardrails": "none"},
            )
            markdown = written["markdown"].read_text(encoding="utf-8")

            self.assertIn("## Suggested Next Action", markdown)
            self.assertIn("## Deterministic Checks", markdown)
            self.assertIn("Finding counts by severity", markdown)

    def test_repair_prompt_includes_guardrails(self) -> None:
        report, guardrails, task_text = _guardrail_report()

        with TemporaryDirectory() as tmp:
            written = write_reports(
                tmp,
                report,
                guardrails,
                task_text,
                inputs={
                    "repo": ".",
                    "diff": "risky.patch",
                    "task": "task.md",
                    "guardrails": "forgebench.yml",
                },
            )
            prompt = written["repair_prompt"].read_text(encoding="utf-8")

            self.assertIn("Federal + California only", prompt)
            self.assertIn("Forbidden product or architecture pattern introduced", prompt)

    def test_report_includes_failed_deterministic_check_output(self) -> None:
        report, guardrails, task_text = _checks_report("checks_test_fail.yml")

        with TemporaryDirectory() as tmp:
            written = write_reports(
                tmp,
                report,
                guardrails,
                task_text,
                inputs={"repo": ".", "diff": "docs_only.patch", "task": "task.md", "guardrails": "checks_test_fail.yml"},
            )
            markdown = written["markdown"].read_text(encoding="utf-8")

            self.assertIn("## Deterministic Checks", markdown)
            self.assertIn("### test", markdown)
            self.assertIn("Status: FAILED", markdown)
            self.assertIn("bad test", markdown)

    def test_repair_prompt_includes_failing_command_and_rerun_instruction(self) -> None:
        report, guardrails, task_text = _checks_report("checks_test_fail.yml")

        with TemporaryDirectory() as tmp:
            written = write_reports(
                tmp,
                report,
                guardrails,
                task_text,
                inputs={"repo": ".", "diff": "docs_only.patch", "task": "task.md", "guardrails": "checks_test_fail.yml"},
            )
            prompt = written["repair_prompt"].read_text(encoding="utf-8")

            self.assertIn("Deterministic check failures:", prompt)
            self.assertIn("Command to rerun:", prompt)
            self.assertIn("bad test", prompt)
            self.assertIn("Before returning the repair, run the configured checks that failed", prompt)


def _sample_report():
    diff = parse_diff_file(FIXTURES / "simple.patch")
    findings, signals = run_static_checks(diff)
    posture, summary = determine_posture(findings, signals, [])
    task_text = (FIXTURES / "task.md").read_text(encoding="utf-8")
    report = ForgeBenchReport(
        posture=posture,
        summary=summary,
        task_summary=task_text.strip(),
        changed_files=diff.changed_files,
        findings=findings,
        static_signals=signals,
        guardrail_hits=[],
        generated_at="2026-04-25T00:00:00+00:00",
    )
    return report, Guardrails(), task_text


def _guardrail_report():
    diff = parse_diff_file(FIXTURES / "risky.patch")
    static_findings, signals = run_static_checks(diff)
    guardrails = load_guardrails(FIXTURES / "guardrails.yml")
    guardrail_findings, guardrail_hits = evaluate_guardrails(diff, guardrails)
    findings = static_findings + guardrail_findings
    posture, summary = determine_posture(findings, signals, guardrail_hits)
    task_text = (FIXTURES / "task.md").read_text(encoding="utf-8")
    report = ForgeBenchReport(
        posture=posture,
        summary=summary,
        task_summary=task_text.strip(),
        changed_files=diff.changed_files,
        findings=findings,
        static_signals=signals,
        guardrail_hits=guardrail_hits,
        generated_at="2026-04-25T00:00:00+00:00",
    )
    return report, guardrails, task_text


def _checks_report(guardrails_name: str):
    diff = parse_diff_file(FIXTURES / "docs_only.patch")
    static_findings, signals = run_static_checks(diff)
    guardrails = load_guardrails(FIXTURES / guardrails_name)
    deterministic_checks = run_configured_checks(Path.cwd(), guardrails)
    deterministic_findings = findings_from_check_results(deterministic_checks.results)
    findings = deterministic_findings + static_findings
    posture, summary = determine_posture(findings, signals, [], deterministic_checks)
    task_text = (FIXTURES / "task.md").read_text(encoding="utf-8")
    report = ForgeBenchReport(
        posture=posture,
        summary=summary,
        task_summary=task_text.strip(),
        changed_files=diff.changed_files,
        findings=findings,
        static_signals=signals,
        guardrail_hits=[],
        deterministic_checks=deterministic_checks,
        generated_at="2026-04-25T00:00:00+00:00",
    )
    return report, guardrails, task_text


if __name__ == "__main__":
    unittest.main()
