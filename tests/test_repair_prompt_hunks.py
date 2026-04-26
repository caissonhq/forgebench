from __future__ import annotations

import unittest

from forgebench.diff_parser import parse_unified_diff
from forgebench.models import (
    CheckResult,
    CheckStatus,
    Confidence,
    DeterministicChecks,
    EvidenceType,
    Finding,
    ForgeBenchReport,
    Guardrails,
    MergePosture,
    Severity,
)
from forgebench.repair_prompt import build_repair_prompt


class RepairPromptHunkTests(unittest.TestCase):
    def test_one_file_finding_includes_matching_hunk(self) -> None:
        diff = parse_unified_diff(_diff_for("app.py", ["-    return 1", "+    return 2"]))
        finding = _finding("implementation_without_tests", "Implementation changed", ["app.py"])
        prompt = build_repair_prompt("Change behavior.", _report([finding], diff), Guardrails())

        self.assertIn("Diff hunk context:", prompt)
        self.assertIn("```diff", prompt)
        self.assertIn("@@ -1,3 +1,3 @@", prompt)
        self.assertIn("+    return 2", prompt)

    def test_multi_file_finding_includes_matching_hunks(self) -> None:
        diff = parse_unified_diff(
            _diff_for("app/a.py", ["-A = 1", "+A = 2"])
            + "\n"
            + _diff_for("app/b.py", ["-B = 1", "+B = 2"])
        )
        finding = _finding("broad_file_surface", "Broad surface", ["app/a.py", "app/b.py"])
        prompt = build_repair_prompt("Update constants.", _report([finding], diff), Guardrails())

        self.assertIn("diff -- app/a.py", prompt)
        self.assertIn("diff -- app/b.py", prompt)

    def test_fifty_line_hunk_truncates_to_forty_lines(self) -> None:
        hunk_lines = [f"+line {index}" for index in range(50)]
        diff = parse_unified_diff(_diff_for("app.py", hunk_lines))
        finding = _finding("implementation_without_tests", "Implementation changed", ["app.py"])
        prompt = build_repair_prompt("Change behavior.", _report([finding], diff), Guardrails())

        self.assertIn("... (truncated, see patch.diff for full context)", prompt)
        self.assertIn("+line 0", prompt)
        self.assertNotIn("+line 49", prompt)

    def test_large_prompt_drops_low_findings_first(self) -> None:
        diff = parse_unified_diff(_diff_for("app.py", [f"+line {index}" for index in range(80)]))
        blocker = _deterministic_blocker()
        low = _finding("ui_copy_changed", "Low copy note", ["app.py"], severity=Severity.LOW)
        report = _report([blocker, low], diff, deterministic_checks=_failed_build_checks())

        prompt = build_repair_prompt("Change behavior.", report, Guardrails(), max_prompt_chars=1800)

        self.assertIn("Build failed", prompt)
        self.assertNotIn("Low copy note", prompt)
        self.assertIn("findings omitted to fit prompt size cap", prompt)

    def test_deterministic_blocker_is_not_dropped(self) -> None:
        diff = parse_unified_diff(_diff_for("app.py", [f"+line {index}" for index in range(80)]))
        blocker = _deterministic_blocker()
        low = _finding("ui_copy_changed", "Low copy note", ["app.py"], severity=Severity.ADVISORY)
        report = _report([blocker, low], diff, deterministic_checks=_failed_build_checks())

        prompt = build_repair_prompt("Change behavior.", report, Guardrails(), max_prompt_chars=1200)

        self.assertIn("BLOCKER: Build failed", prompt)
        self.assertIn("Command to rerun: python -m compileall app", prompt)

    def test_no_matching_hunk_gets_fallback_text(self) -> None:
        diff = parse_unified_diff(_diff_for("app.py", ["-A = 1", "+A = 2"]))
        finding = _finding("implementation_without_tests", "Implementation changed", ["missing.py"])
        prompt = build_repair_prompt("Change behavior.", _report([finding], diff), Guardrails())

        self.assertIn("No matching diff hunk was available for this finding.", prompt)

    def test_prompt_has_balanced_code_fences(self) -> None:
        diff = parse_unified_diff(_diff_for("app.py", ["-A = 1", "+A = 2"]))
        finding = _finding("implementation_without_tests", "Implementation changed", ["app.py"])
        prompt = build_repair_prompt("Change behavior.", _report([finding], diff), Guardrails())

        self.assertEqual(prompt.count("```") % 2, 0)


def _diff_for(path: str, hunk_lines: list[str]) -> str:
    body = "\n".join([" line before", *hunk_lines, " line after"])
    return (
        f"diff --git a/{path} b/{path}\n"
        f"--- a/{path}\n"
        f"+++ b/{path}\n"
        "@@ -1,3 +1,3 @@\n"
        f"{body}\n"
    )


def _finding(
    finding_id: str,
    title: str,
    files: list[str],
    severity: Severity = Severity.MEDIUM,
    evidence_type: EvidenceType = EvidenceType.STATIC,
) -> Finding:
    return Finding(
        id=finding_id,
        title=title,
        severity=severity,
        confidence=Confidence.MEDIUM,
        evidence_type=evidence_type,
        files=files,
        explanation="The changed lines need review.",
        suggested_fix="Review the changed behavior and add coverage where needed.",
    )


def _deterministic_blocker() -> Finding:
    return Finding(
        id="build_failed",
        title="Build failed",
        severity=Severity.BLOCKER,
        confidence=Confidence.HIGH,
        evidence_type=EvidenceType.DETERMINISTIC,
        files=[],
        evidence=["Check: build"],
        explanation="The configured build command failed.",
        suggested_fix="Fix the build and rerun ForgeBench.",
    )


def _failed_build_checks() -> DeterministicChecks:
    return DeterministicChecks(
        run_requested=True,
        results=[
            CheckResult(
                name="build",
                command="python -m compileall app",
                status=CheckStatus.FAILED,
                exit_code=1,
                duration_seconds=0.1,
            )
        ],
    )


def _report(
    findings: list[Finding],
    diff_summary,
    deterministic_checks: DeterministicChecks | None = None,
) -> ForgeBenchReport:
    return ForgeBenchReport(
        posture=MergePosture.REVIEW,
        summary="Review before merge.",
        task_summary="Change behavior.",
        changed_files=diff_summary.changed_files,
        findings=findings,
        static_signals={"changed_file_count": len(diff_summary.changed_files)},
        guardrail_hits=[],
        deterministic_checks=deterministic_checks or DeterministicChecks(),
        generated_at="2026-04-26T00:00:00+00:00",
        diff_summary=diff_summary,
    )


if __name__ == "__main__":
    unittest.main()
