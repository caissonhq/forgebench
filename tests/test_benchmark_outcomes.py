from __future__ import annotations

from pathlib import Path
import unittest

from forgebench.benchmark import build_benchmark_snapshot, format_benchmark_markdown
from forgebench.benchmark_outcomes import BenchmarkOutcomesError, load_pr_outcomes, summarize_pr_outcomes


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "examples" / "golden_cases"
OUTCOMES = ROOT / "examples" / "benchmark_outcomes" / "eo002-pr-outcomes.json"


class BenchmarkOutcomesTests(unittest.TestCase):
    def test_load_default_outcomes_bundle(self) -> None:
        bundle = load_pr_outcomes(OUTCOMES)
        summary = summarize_pr_outcomes(bundle)

        self.assertEqual(summary.total_prs, 10)
        self.assertEqual(summary.human_posture_agreement_rate, 1.0)
        self.assertIn("merged", summary.pr_outcome_distribution)

    def test_snapshot_includes_pr_outcomes(self) -> None:
        snapshot = build_benchmark_snapshot(GOLDEN, repo_path=ROOT, outcomes_path=OUTCOMES)
        self.assertIsNotNone(snapshot.pr_outcomes)
        assert snapshot.pr_outcomes is not None
        self.assertEqual(snapshot.pr_outcomes.total_prs, 10)

    def test_markdown_includes_real_pr_outcomes_section(self) -> None:
        snapshot = build_benchmark_snapshot(GOLDEN, repo_path=ROOT, outcomes_path=OUTCOMES)
        markdown = format_benchmark_markdown(snapshot, cases_dir=GOLDEN)
        self.assertIn("## Real PR outcomes", markdown)
        self.assertIn("Human posture agreement", markdown)

    def test_invalid_outcomes_file_raises(self) -> None:
        with self.assertRaises(BenchmarkOutcomesError):
            load_pr_outcomes(ROOT / "missing-outcomes.json")


if __name__ == "__main__":
    unittest.main()