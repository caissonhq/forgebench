from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.feedback import append_feedback
from forgebench.golden_case_generator import generate_golden_case_candidates


class GoldenCaseGeneratorTests(unittest.TestCase):
    def test_generates_candidate_from_dismissed_feedback(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            out = Path(tmp) / "candidates"
            append_feedback(
                "fnd_ui_copy",
                status="dismissed",
                kind="ui_copy_changed",
                feedback_log=log,
                outcome_label="false_positive",
                expected_posture="LOW_CONCERN",
                files=["docs/README.md"],
            )
            result = generate_golden_case_candidates([log], output_dir=out)

            self.assertEqual(len(result.candidates), 1)
            case_dir = out / result.candidates[0].case_slug
            expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
            self.assertEqual(expected["expected_posture"], "LOW_CONCERN")
            self.assertEqual(expected["forbidden_finding_ids"], ["ui_copy_changed"])
            self.assertTrue((case_dir / "REVIEW_GATE.md").exists())
            self.assertTrue(result.manifest_path.exists())

    def test_skips_accepted_without_generate_filter(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            out = Path(tmp) / "candidates"
            append_feedback("fnd_ok", status="accepted", kind="tests_failed", feedback_log=log)
            result = generate_golden_case_candidates([log], output_dir=out)
            self.assertEqual(len(result.candidates), 0)
            self.assertEqual(result.skipped_count, 1)


if __name__ == "__main__":
    unittest.main()