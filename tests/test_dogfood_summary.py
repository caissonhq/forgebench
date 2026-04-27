from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.dogfood_summary import generate_markdown_summary


class DogfoodSummaryTests(unittest.TestCase):
    def test_empty_file(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            path.write_text("", encoding="utf-8")

            markdown = generate_markdown_summary([path])

        self.assertIn("# ForgeBench Dogfood Feedback Summary", markdown)
        self.assertIn("- Total feedback entries: 0", markdown)
        self.assertIn("- Accepted: 0 (0.0%)", markdown)

    def test_multiple_statuses(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            _write_entries(
                path,
                [
                    {"uid": "fnd_1", "status": "accepted", "kind": "tests_failed", "fb_version": 1},
                    {"uid": "fnd_2", "status": "dismissed", "kind": "ui_copy_changed", "fb_version": 1},
                    {"uid": "fnd_3", "status": "wrong", "kind": "broad_file_surface", "fb_version": 1},
                ],
            )

            markdown = generate_markdown_summary([path])

        self.assertIn("- Total feedback entries: 3", markdown)
        self.assertIn("- Accepted: 1 (33.3%)", markdown)
        self.assertIn("- Dismissed: 1 (33.3%)", markdown)
        self.assertIn("- Wrong: 1 (33.3%)", markdown)

    def test_kind_aggregation(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            _write_entries(
                path,
                [
                    {"uid": "fnd_1", "status": "accepted", "kind": "tests_failed", "fb_version": 1},
                    {"uid": "fnd_2", "status": "accepted", "kind": "tests_failed", "fb_version": 1},
                    {"uid": "fnd_3", "status": "dismissed", "kind": "ui_copy_changed", "fb_version": 1},
                ],
            )

            markdown = generate_markdown_summary([path])

        self.assertIn("## Top Useful Kinds", markdown)
        self.assertIn("- tests_failed: 2", markdown)
        self.assertIn("## Top Noisy Kinds", markdown)
        self.assertIn("- ui_copy_changed: 1", markdown)

    def test_multiple_input_files(self) -> None:
        with TemporaryDirectory() as tmp:
            first = Path(tmp) / "one.jsonl"
            second = Path(tmp) / "two.jsonl"
            _write_entries(first, [{"uid": "fnd_1", "status": "accepted", "kind": "tests_failed", "fb_version": 1}])
            _write_entries(second, [{"uid": "fnd_2", "status": "wrong", "kind": "ui_copy_changed", "fb_version": 1}])

            markdown = generate_markdown_summary([first, second])

        self.assertIn("- Total feedback entries: 2", markdown)
        self.assertIn("- Accepted: 1 (50.0%)", markdown)
        self.assertIn("- Wrong: 1 (50.0%)", markdown)

    def test_malformed_json_line_is_reported(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            path.write_text('{"uid": "fnd_1", "status": "accepted", "kind": "tests_failed"}\nnot json\n', encoding="utf-8")

            markdown = generate_markdown_summary([path])

        self.assertIn("- Total feedback entries: 1", markdown)
        self.assertIn("- Malformed lines skipped: 1", markdown)

    def test_markdown_output_is_stable(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            _write_entries(path, [{"uid": "fnd_1", "status": "accepted", "kind": "tests_failed", "fb_version": 1}])

            markdown = generate_markdown_summary([path])

        expected = "\n".join(
            [
                "# ForgeBench Dogfood Feedback Summary",
                "",
                "- Total feedback entries: 1",
                "- Accepted: 1 (100.0%)",
                "- Dismissed: 0 (0.0%)",
                "- Wrong: 0 (0.0%)",
                "- Entries missing kind: 0",
                "- Malformed lines skipped: 0",
                "",
                "## Top Useful Kinds",
                "",
                "- tests_failed: 1",
                "",
                "## Top Noisy Kinds",
                "",
                "- None.",
                "",
                "## Top Wrong Kinds",
                "",
                "- None.",
                "",
            ]
        )
        self.assertEqual(markdown, expected)


def _write_entries(path: Path, entries: list[dict[str, object]]) -> None:
    path.write_text("\n".join(json.dumps(entry, sort_keys=True) for entry in entries) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
