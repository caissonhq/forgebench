from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.adoption import (
    AdoptionState,
    build_conversion_funnel,
    build_success_checklist,
    format_conversion_funnel,
    format_success_checklist,
    increment_review_count,
    is_first_review_pending,
    load_adoption_state,
    record_milestone,
    save_adoption_state,
)


class AdoptionTests(unittest.TestCase):
    def test_record_milestone_once(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "adoption-state.json"
            self.assertTrue(record_milestone("first_demo", path=path))
            self.assertFalse(record_milestone("first_demo", path=path))
            state = load_adoption_state(path)
            self.assertIn("first_demo", state.milestones)

    def test_increment_review_count_triggers_first_review(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "adoption-state.json"
            state = increment_review_count(path=path)
            self.assertEqual(state.review_count, 1)
            loaded = load_adoption_state(path)
            self.assertIn("first_review", loaded.milestones)

    def test_success_checklist_format(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "adoption-state.json"
            save_adoption_state(AdoptionState(milestones={"first_demo": "2026-01-01"}, review_count=0), path=path)
            items = build_success_checklist(repo_path=tmp, state_path=path)
            text = format_success_checklist(items)
            self.assertIn("Adoption success checklist", text)
            self.assertIn("[x] First demo completed", text)

    def test_conversion_funnel_format(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "adoption-state.json"
            record_milestone("first_review", path=path)
            text = format_conversion_funnel(path=path)
            self.assertIn("first_review", text)
            funnel = build_conversion_funnel(path=path)
            self.assertTrue(funnel["first_review"])

    def test_is_first_review_pending_false_after_review(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "adoption-state.json"
            increment_review_count(path=path)
            self.assertFalse(is_first_review_pending(path=path))

    def test_adoption_state_round_trip(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            save_adoption_state(AdoptionState(milestones={"quickstart_completed": "t"}, review_count=2), path=path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["review_count"], 2)
            self.assertEqual(payload["schema_version"], "1.0.0")