from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp
import unittest

from forgebench.llm_review import CommandLLMProvider, MockLLMProvider
from forgebench.models import EvidenceType, LLMReviewStatus, MergePosture, Severity
from forgebench.review import run_review


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class LLMReviewTests(unittest.TestCase):
    def test_llm_review_disabled_by_default(self) -> None:
        result = _run_review("docs_only.patch")

        self.assertFalse(result.report.llm_review.enabled)
        self.assertEqual(result.report.llm_review.status, LLMReviewStatus.SKIPPED)
        self.assertEqual(result.report.pre_llm_posture, result.report.posture)

    def test_llm_review_section_says_not_run_when_disabled(self) -> None:
        result = _run_review("docs_only.patch")
        markdown = result.written_paths["markdown"].read_text(encoding="utf-8")

        self.assertIn("## LLM Review", markdown)
        self.assertIn("LLM review was not run.", markdown)

    def test_mock_provider_returns_deterministic_finding(self) -> None:
        provider = MockLLMProvider(response=_llm_payload())
        result = provider.review("bundle", existing_findings=[])

        self.assertEqual(result.status, LLMReviewStatus.COMPLETED)
        self.assertEqual(result.findings[0].id, "llm_missing_test_case")
        self.assertEqual(result.findings[0].evidence_type, EvidenceType.LLM)

    def test_llm_provider_cannot_create_blocker_finding(self) -> None:
        payload = _llm_payload()
        payload["findings"][0]["severity"] = "blocker"
        result = MockLLMProvider(response=payload).review("bundle", existing_findings=[])

        self.assertEqual(result.findings[0].severity, Severity.MEDIUM)

    def test_command_provider_parses_json_output(self) -> None:
        with TemporaryDirectory() as tmp:
            script = _write_script(Path(tmp), "import json\nprint(json.dumps(" + repr(_llm_payload()) + "))\n")
            result = CommandLLMProvider(_python_command(script), timeout_seconds=5).review("bundle", [])

        self.assertEqual(result.status, LLMReviewStatus.COMPLETED)
        self.assertEqual(result.findings[0].id, "llm_missing_test_case")

    def test_command_provider_handles_invalid_json(self) -> None:
        with TemporaryDirectory() as tmp:
            script = _write_script(Path(tmp), "print('not json')\n")
            result = CommandLLMProvider(_python_command(script), timeout_seconds=5).review("bundle", [])

        self.assertEqual(result.status, LLMReviewStatus.FAILED)
        self.assertIn("invalid JSON", result.error_message or "")

    def test_command_provider_handles_timeout(self) -> None:
        with TemporaryDirectory() as tmp:
            script = _write_script(Path(tmp), "import time\ntime.sleep(2)\n")
            result = CommandLLMProvider(_python_command(script), timeout_seconds=1).review("bundle", [])

        self.assertEqual(result.status, LLMReviewStatus.FAILED)
        self.assertIn("timed out", result.error_message or "")

    def test_llm_findings_appear_in_markdown_report(self) -> None:
        result = _run_review_with_mock("docs_only.patch")
        markdown = result.written_paths["markdown"].read_text(encoding="utf-8")

        self.assertIn("## LLM Review", markdown)
        self.assertIn("LLM reviewer suggests a missing usage example", markdown)

    def test_llm_findings_appear_in_json_report(self) -> None:
        result = _run_review_with_mock("docs_only.patch")
        payload = json.loads(result.written_paths["json"].read_text(encoding="utf-8"))

        self.assertEqual(payload["pre_llm_posture"], "LOW_CONCERN")
        self.assertEqual(payload["final_posture"], "REVIEW")
        self.assertEqual(payload["llm_review"]["findings"][0]["id"], "llm_missing_test_case")

    def test_repair_prompt_includes_llm_findings(self) -> None:
        result = _run_review_with_mock("docs_only.patch")
        prompt = result.written_paths["repair_prompt"].read_text(encoding="utf-8")

        self.assertIn("LLM reviewer notes:", prompt)
        self.assertIn("LLM reviewer suggests a missing usage example", prompt)
        self.assertIn("LLM findings are advisory", prompt)

    def test_llm_finding_can_escalate_low_concern_to_review(self) -> None:
        result = _run_review_with_mock("docs_only.patch")

        self.assertEqual(result.report.pre_llm_posture, MergePosture.LOW_CONCERN)
        self.assertEqual(result.report.posture, MergePosture.REVIEW)

    def test_llm_finding_cannot_downgrade_review_to_low_concern(self) -> None:
        result = _run_review_with_mock("simple.patch", payload=_no_findings_payload())

        self.assertEqual(result.report.pre_llm_posture, MergePosture.REVIEW)
        self.assertEqual(result.report.posture, MergePosture.REVIEW)

    def test_llm_finding_cannot_downgrade_block(self) -> None:
        result = _run_review_with_mock("risky.patch", payload=_no_findings_payload())

        self.assertEqual(result.report.pre_llm_posture, MergePosture.BLOCK)
        self.assertEqual(result.report.posture, MergePosture.BLOCK)

    def test_deterministic_failure_remains_block_with_llm_review(self) -> None:
        result = _run_review_with_mock("docs_only.patch", guardrails="checks_test_fail.yml", run_checks=True)

        self.assertEqual(result.report.pre_llm_posture, MergePosture.BLOCK)
        self.assertEqual(result.report.posture, MergePosture.BLOCK)
        self.assertIn("tests_failed", {finding.id for finding in result.report.findings})


def _run_review(diff_name: str, guardrails: str | None = None, run_checks: bool = False):
    return run_review(
        repo_path=ROOT,
        diff_path=FIXTURES / diff_name,
        task_path=FIXTURES / "task.md",
        guardrails_path=FIXTURES / guardrails if guardrails else None,
        output_dir=Path(mkdtemp()) / "out",
        run_checks=run_checks,
    )


def _run_review_with_mock(
    diff_name: str,
    payload: dict[str, object] | None = None,
    guardrails: str | None = None,
    run_checks: bool = False,
):
    return run_review(
        repo_path=ROOT,
        diff_path=FIXTURES / diff_name,
        task_path=FIXTURES / "task.md",
        guardrails_path=FIXTURES / guardrails if guardrails else None,
        output_dir=Path(mkdtemp()) / "out",
        run_checks=run_checks,
        llm_review=True,
        llm_provider="mock",
        llm_mock_response=payload or _llm_payload(),
    )


def _write_script(directory: Path, body: str) -> Path:
    script = directory / "reviewer.py"
    script.write_text(body, encoding="utf-8")
    return script


def _python_command(script: Path) -> str:
    return f"{shlex.quote(sys.executable)} {shlex.quote(str(script))}"


def _llm_payload() -> dict[str, object]:
    return {
        "reviewer_name": "Mock LLM Reviewer",
        "summary": "The docs-only change could still use a small example.",
        "findings": [
            {
                "id": "llm_missing_test_case",
                "title": "LLM reviewer suggests a missing usage example",
                "severity": "medium",
                "confidence": "medium",
                "files": ["README.md"],
                "explanation": "The diff changes documentation but does not show an example of the documented command.",
                "suggested_fix": "Add a focused example or confirm existing examples cover the command.",
            }
        ],
    }


def _no_findings_payload() -> dict[str, object]:
    return {
        "reviewer_name": "Mock LLM Reviewer",
        "summary": "No additional LLM findings beyond existing deterministic/static evidence.",
        "findings": [],
    }


if __name__ == "__main__":
    unittest.main()
