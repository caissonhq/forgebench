from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.cli import main
from forgebench.feedback import append_feedback, export_feedback_bundle
from forgebench.feedback_digest import build_feedback_digest, format_feedback_digest, parse_period
from forgebench.feedback_import import import_feedback
from forgebench.feedback_promote import promote_feedback_to_golden_cases
from forgebench.feedback_triage import compute_feedback_health, infer_priority
from forgebench.roadmap_sync import suggest_roadmap_items, update_roadmap
from forgebench.weekly_review import run_weekly_review


ROOT = Path(__file__).resolve().parents[1]


class FeedbackIterationTests(unittest.TestCase):
    def test_feedback_v4_fields_and_auto_triage(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "feedback.jsonl"
            append_feedback(
                "fnd_fp",
                status="dismissed",
                feedback_log=path,
                kind="ui_copy_changed",
                outcome_label="false_positive",
                category="false_positive",
                context="docs-only PR",
                nps=8,
            )
            entry = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(entry["fb_version"], 4)
            self.assertIn("triage", entry)
            self.assertEqual(entry["category"], "false_positive")

    def test_infer_priority_missed_concern_is_critical(self) -> None:
        triage = infer_priority({"outcome_label": "missed_concern", "status": "wrong"})
        self.assertEqual(triage.priority, "critical")

    def test_parse_period_formats(self) -> None:
        self.assertEqual(parse_period("7d"), 7)
        self.assertEqual(parse_period("2w"), 14)
        self.assertEqual(parse_period("1m"), 30)

    def test_import_json_bundle(self) -> None:
        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "bundle.json"
            log = Path(tmp) / "feedback.jsonl"
            src.write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "uid": "fnd_imp",
                                "status": "dismissed",
                                "kind": "ui_copy_changed",
                                "note": "imported",
                                "source": "json",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = import_feedback(src, feedback_log=log)
            self.assertEqual(result.imported, 1)
            self.assertTrue(log.exists())

    def test_import_discussion_markdown(self) -> None:
        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "post.md"
            log = Path(tmp) / "feedback.jsonl"
            src.write_text(
                "# False positive on docs\n\nkind: ui_copy_changed\nposture: LOW_CONCERN\n",
                encoding="utf-8",
            )
            result = import_feedback(src, format_hint="discussion", feedback_log=log)
            self.assertEqual(result.imported, 1)
            self.assertEqual(result.source_format, "discussion")

    def test_import_email(self) -> None:
        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "mail.eml"
            log = Path(tmp) / "feedback.jsonl"
            src.write_text(
                "From: user@example.com\nSubject: ForgeBench feature idea\n\nPlease add Slack export.\n",
                encoding="utf-8",
            )
            result = import_feedback(src, format_hint="email", feedback_log=log)
            self.assertEqual(result.imported, 1)

    def test_digest_prioritized_insights(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            for i in range(3):
                append_feedback(
                    f"fnd_{i}",
                    status="dismissed",
                    feedback_log=log,
                    kind="ui_copy_changed",
                    outcome_label="false_positive",
                )
            digest = build_feedback_digest([log], period="7d")
            self.assertGreaterEqual(digest.total_entries, 3)
            self.assertTrue(digest.prioritized_insights)
            text = format_feedback_digest(digest)
            self.assertIn("Prioritized insights", text)
            self.assertIn("false_positive_rate", text)

    def test_feedback_health_metrics(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            append_feedback("fnd_a", status="accepted", feedback_log=log, kind="tests_failed", nps=9)
            append_feedback("fnd_b", status="dismissed", feedback_log=log, kind="ui_copy_changed", nps=7)
            entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            health = compute_feedback_health(entries)
            self.assertEqual(health["volume"], 2)
            self.assertIn("false_positive_rate", health)

    def test_promote_feedback_to_golden_cases(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            out = Path(tmp) / "candidates"
            append_feedback(
                "fnd_promote",
                status="dismissed",
                feedback_log=log,
                kind="ui_copy_changed",
                outcome_label="false_positive",
            )
            result = promote_feedback_to_golden_cases(feedback_log=log, uid="fnd_promote", output_dir=out)
            self.assertEqual(result.promoted_count, 1)
            self.assertTrue((out / result.candidate_slugs[0] / "expected.json").exists())

    def test_roadmap_suggest_items(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            append_feedback(
                "fnd_rm",
                status="wrong",
                feedback_log=log,
                kind="broad_file_surface",
                outcome_label="missed_concern",
            )
            items = suggest_roadmap_items(feedback_logs=[log], period="7d")
            self.assertTrue(items)

    def test_roadmap_update_apply(self) -> None:
        with TemporaryDirectory() as tmp:
            roadmap = Path(tmp) / "ROADMAP.md"
            log = Path(tmp) / "feedback.jsonl"
            roadmap.write_text(
                "# Roadmap\n\n### User-requested improvements (tracked from early feedback)\n\n"
                "| Priority | Request | Status | Notes |\n"
                "|----------|---------|--------|-------|\n"
                "| P1 | Existing item | Planned | test |\n\n## Next\n",
                encoding="utf-8",
            )
            for i in range(4):
                append_feedback(
                    f"fnd_{i}",
                    status="dismissed",
                    feedback_log=log,
                    kind="ui_copy_changed",
                )
            result = update_roadmap(roadmap_path=roadmap, feedback_logs=[log], period="7d", apply=True)
            updated = roadmap.read_text(encoding="utf-8")
            self.assertTrue(result.applied)
            self.assertIn("ui_copy_changed", updated)

    def test_weekly_review_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            out = Path(tmp) / "weekly"
            append_feedback("fnd_w", status="dismissed", feedback_log=log, kind="ui_copy_changed")
            result = run_weekly_review(feedback_log=log, period="7d", output_dir=out)
            self.assertTrue(result.digest_path and result.digest_path.exists())
            self.assertTrue(result.roadmap_path and result.roadmap_path.exists())
            self.assertTrue(result.whats_new_path and result.whats_new_path.exists())

    def test_cli_feedback_import(self) -> None:
        with TemporaryDirectory() as tmp:
            src = Path(tmp) / "data.json"
            log = Path(tmp) / "feedback.jsonl"
            src.write_text(
                json.dumps([{"uid": "fnd_cli", "status": "accepted", "kind": "tests_failed"}]),
                encoding="utf-8",
            )
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["feedback", "import", str(src), "--feedback-log", str(log)])
            self.assertEqual(code, 0)
            self.assertIn("Imported: 1", stdout.getvalue())

    def test_cli_feedback_digest_period(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            append_feedback("fnd_d", status="dismissed", feedback_log=log, kind="ui_copy_changed")
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["feedback", "digest", "--period", "7d", "--feedback-log", str(log)])
            self.assertEqual(code, 0)
            self.assertIn("feedback digest", stdout.getvalue().lower())

    def test_cli_feedback_promote(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            out = Path(tmp) / "out"
            append_feedback("fnd_p", status="dismissed", feedback_log=log, kind="ui_copy_changed")
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["feedback", "promote", "--uid", "fnd_p", "--feedback-log", str(log), "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertIn("Candidates: 1", stdout.getvalue())

    def test_cli_roadmap_update(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            append_feedback("fnd_r", status="dismissed", feedback_log=log, kind="ui_copy_changed")
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["roadmap", "update", "--feedback-log", str(log), "--period", "7d"])
            self.assertEqual(code, 0)
            self.assertIn("roadmap update", stdout.getvalue().lower())

    def test_cli_weekly_review(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            out = Path(tmp) / "weekly"
            append_feedback("fnd_wr", status="dismissed", feedback_log=log, kind="ui_copy_changed")
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["weekly-review", "--feedback-log", str(log), "--out", str(out)])
            self.assertEqual(code, 0)
            self.assertIn("weekly review complete", stdout.getvalue().lower())

    def test_cli_feedback_thank(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["feedback", "thank", "--name", "Alex"])
        self.assertEqual(code, 0)
        self.assertIn("Thank you", stdout.getvalue())

    def test_export_v4_schema(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            append_feedback("fnd_v4", status="dismissed", feedback_log=log, category="bug", triage="high")
            bundle = export_feedback_bundle([log])
            self.assertEqual(bundle["schema_version"], "4.0.0")
            self.assertEqual(bundle["export_version"], 3)

    def test_iteration_docs_exist(self) -> None:
        self.assertTrue((ROOT / "docs" / "iteration" / "how-we-iterate.md").exists())
        self.assertTrue((ROOT / "docs" / "iteration" / "WEEKLY_ITERATION_PLAYBOOK.md").exists())
        self.assertTrue((ROOT / "docs" / "iteration" / "FEEDBACK_HEALTH_SCORECARD.md").exists())


if __name__ == "__main__":
    unittest.main()