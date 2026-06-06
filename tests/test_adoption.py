from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.adoption import (
    build_success_checklist,
    format_success_checklist,
    increment_review_count,
    load_adoption_state,
    record_milestone,
    save_adoption_state,
    AdoptionState,
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

    def test_adoption_state_round_trip(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            save_adoption_state(AdoptionState(milestones={"quickstart_completed": "t"}, review_count=2), path=path)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["review_count"], 2)
            self.assertEqual(payload["schema_version"], "1.0.0")