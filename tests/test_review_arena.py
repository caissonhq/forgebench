from __future__ import annotations

from pathlib import Path
import unittest

from forgebench.benchmark import build_benchmark_snapshot
from forgebench.benchmark_outcomes import load_pr_outcomes
from forgebench.review_arena import build_review_arena_leaderboard, leaderboard_to_manifest


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "examples" / "golden_cases"
OUTCOMES = ROOT / "examples" / "benchmark_outcomes" / "eo002-pr-outcomes.json"


class ReviewArenaTests(unittest.TestCase):
    def test_leaderboard_ranks_entries(self) -> None:
        snapshot = build_benchmark_snapshot(GOLDEN, repo_path=ROOT)
        leaderboard = build_review_arena_leaderboard(snapshot)
        self.assertGreater(len(leaderboard.entries), 0)
        self.assertEqual(leaderboard.entries[0].rank, 1)
        self.assertEqual(leaderboard.entries[0].contender_id, "forgebench_core")

    def test_leaderboard_includes_pr_outcomes_contenders(self) -> None:
        snapshot = build_benchmark_snapshot(GOLDEN, repo_path=ROOT, outcomes_path=OUTCOMES)
        bundle = load_pr_outcomes(OUTCOMES)
        leaderboard = build_review_arena_leaderboard(snapshot, outcomes_bundle=bundle)
        manifest = leaderboard_to_manifest(leaderboard)
        contender_ids = {entry["contender_id"] for entry in manifest["entries"]}
        self.assertIn("human_calibration", contender_ids)
        self.assertIn("pr_outcomes", leaderboard.generated_from)


if __name__ == "__main__":
    unittest.main()