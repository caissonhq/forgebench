from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from forgebench.github_pr import GitHubPRMetadata, generate_pr_comment
from forgebench.review import run_review


SAMPLE_ROOT = Path("examples") / "sample_report"


class SampleReportTests(unittest.TestCase):
    def test_sample_cases_are_reproducible(self) -> None:
        for case_name, expected_posture in [("block_case", "BLOCK"), ("low_concern_case", "LOW_CONCERN")]:
            with self.subTest(case=case_name), TemporaryDirectory() as tmp:
                case = SAMPLE_ROOT / case_name
                result = run_review(
                    repo_path=".",
                    diff_path=case / "patch.diff",
                    task_path=case / "task.md",
                    guardrails_path=case / "forgebench.yml",
                    output_dir=tmp,
                )
                generated_payload = json.loads((Path(tmp) / "forgebench-report.json").read_text(encoding="utf-8"))
                committed_payload = json.loads((case / "forgebench-report.json").read_text(encoding="utf-8"))

                self.assertEqual(result.report.posture.value, expected_posture)
                self.assertEqual(committed_payload["posture"], expected_posture)
                self.assertEqual(generated_payload["schema_version"], "1.0.0")
                self.assertEqual(committed_payload["schema_version"], "1.0.0")
                self.assertEqual(_normalize_report_json(generated_payload), _normalize_report_json(committed_payload))

    def test_sample_markdown_contains_important_sections(self) -> None:
        required_sections = [
            "# ForgeBench Merge Risk Report",
            "## Merge Posture",
            "## Deterministic Checks",
            "## Heuristic Review Lenses",
            "## Guardrail Review",
            "## Repair Prompt",
        ]
        for case in [SAMPLE_ROOT / "block_case", SAMPLE_ROOT / "low_concern_case"]:
            markdown = (case / "forgebench-report.md").read_text(encoding="utf-8")
            for section in required_sections:
                self.assertIn(section, markdown)

    def test_sample_pr_comments_are_concise_and_labeled(self) -> None:
        for case in [SAMPLE_ROOT / "block_case", SAMPLE_ROOT / "low_concern_case"]:
            readme = (case / "README.md").read_text(encoding="utf-8")
            comment = (case / "pr-comment.md").read_text(encoding="utf-8")

            self.assertIn("This is a synthetic ForgeBench sample case.", readme)
            self.assertIn("## ForgeBench Merge Risk Report", comment)
            self.assertIn("ForgeBench does not prove code is safe.", comment)
            self.assertLess(len(comment), 3000)

    def test_block_sample_repair_prompt_includes_diff_hunk(self) -> None:
        prompt = (SAMPLE_ROOT / "block_case" / "repair-prompt.md").read_text(encoding="utf-8")

        self.assertIn("Diff hunk context:", prompt)
        self.assertIn("```diff", prompt)
        self.assertIn("CREATE TABLE payment_receipts", prompt)

    def test_sample_reports_have_no_private_paths(self) -> None:
        for path in SAMPLE_ROOT.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("/Users/", text)
            self.assertNotIn("davidhorton", text)

    def test_generated_pr_comment_shape_matches_committed_comment(self) -> None:
        case = SAMPLE_ROOT / "low_concern_case"
        with TemporaryDirectory() as tmp:
            result = run_review(
                repo_path=".",
                diff_path=case / "patch.diff",
                task_path=case / "task.md",
                guardrails_path=case / "forgebench.yml",
                output_dir=tmp,
            )
            metadata = GitHubPRMetadata(
                owner="synthetic",
                repo="sample",
                number=2,
                title="Synthetic LOW_CONCERN sample",
                body="Synthetic, human-approved sample used to demonstrate ForgeBench output shape.",
                author="forgebench-example",
                base_ref="main",
                head_ref="low_concern_case",
                changed_files=1,
                additions=3,
                deletions=1,
                url="https://github.com/synthetic/sample/pull/2",
            )
            generated = generate_pr_comment(result.report, metadata)
            committed = (case / "pr-comment.md").read_text(encoding="utf-8")

            self.assertEqual(generated, committed)


def _normalize_report_json(payload: dict[str, object]) -> dict[str, object]:
    normalized = dict(payload)
    normalized["generated_at"] = "<generated>"
    return normalized


if __name__ == "__main__":
    unittest.main()
