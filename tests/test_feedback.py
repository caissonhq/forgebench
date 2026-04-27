from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import socket
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from forgebench.cli import main
from forgebench.feedback import FeedbackError, append_feedback, summarize_feedback


class FeedbackTests(unittest.TestCase):
    def test_append_one_entry(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            append_feedback("fnd_test123", status="accepted", feedback_log=path)
            entries = _read_entries(path)

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["uid"], "fnd_test123")
        self.assertEqual(entries[0]["status"], "accepted")
        self.assertEqual(entries[0]["fb_version"], 1)
        self.assertIn("ts", entries[0])

    def test_append_two_entries(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            append_feedback("fnd_one", status="accepted", feedback_log=path, kind="implementation_without_tests")
            append_feedback("fnd_two", status="dismissed", feedback_log=path, kind="ui_copy_changed")

            summary = summarize_feedback([path])

        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.status_counts["accepted"], 1)
        self.assertEqual(summary.status_counts["dismissed"], 1)
        self.assertEqual(summary.kind_counts["accepted"]["implementation_without_tests"], 1)

    def test_invalid_status_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaises(FeedbackError):
                append_feedback("fnd_test123", status="maybe", feedback_log=Path(tmp) / "feedback.jsonl")

    def test_note_is_preserved(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            append_feedback("fnd_test123", status="dismissed", note="false positive", feedback_log=path)

            self.assertEqual(_read_entries(path)[0]["note"], "false positive")

    def test_custom_feedback_log_path(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "custom" / "feedback.jsonl"
            returned = append_feedback("fnd_test123", status="wrong", feedback_log=path)

            self.assertEqual(returned, path)
            self.assertTrue(path.exists())

    def test_summarize_counts(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            append_feedback("fnd_one", status="accepted", feedback_log=path, kind="tests_failed")
            append_feedback("fnd_two", status="accepted", feedback_log=path, kind="tests_failed")
            append_feedback("fnd_three", status="wrong", feedback_log=path, kind="ui_copy_changed")

            summary = summarize_feedback([path])

        self.assertEqual(summary.total, 3)
        self.assertEqual(summary.status_counts["accepted"], 2)
        self.assertEqual(summary.status_counts["wrong"], 1)
        self.assertEqual(summary.kind_counts["accepted"]["tests_failed"], 2)

    def test_summarize_missing_file_is_empty(self) -> None:
        with TemporaryDirectory() as tmp:
            summary = summarize_feedback([Path(tmp) / "missing.jsonl"])

        self.assertEqual(summary.total, 0)
        self.assertEqual(summary.status_counts["accepted"], 0)

    def test_cli_append_and_summarize(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(
                    [
                        "feedback",
                        "fnd_test123",
                        "--status",
                        "accepted",
                        "--note",
                        "useful finding",
                        "--kind",
                        "implementation_without_tests",
                        "--feedback-log",
                        str(path),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertIn("ForgeBench feedback recorded.", stdout.getvalue())

            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["feedback", "--summarize", "--feedback-log", str(path)])
            self.assertEqual(code, 0)
            self.assertIn("accepted: 1", stdout.getvalue())
            self.assertIn("implementation_without_tests", stdout.getvalue())

    def test_cli_invalid_status_exits_nonzero(self) -> None:
        stderr = StringIO()
        with self.assertRaises(SystemExit) as raised, redirect_stderr(stderr):
            main(["feedback", "fnd_test123", "--status", "invalid"])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("status must be one of", stderr.getvalue())

    def test_cli_summarize_missing_file_is_friendly_success(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing.jsonl"
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["feedback", "--summarize", "--feedback-log", str(path)])

        self.assertEqual(code, 0)
        self.assertIn("No feedback entries found", stdout.getvalue())

    def test_no_network_calls_are_needed(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            with patch.object(socket, "socket", side_effect=AssertionError("network call attempted")):
                append_feedback("fnd_test123", status="accepted", feedback_log=path)
                summary = summarize_feedback([path])

        self.assertEqual(summary.total, 1)


def _read_entries(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    unittest.main()
