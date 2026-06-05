from __future__ import annotations

from pathlib import Path
import unittest

from forgebench.benchmark import build_benchmark_snapshot, format_benchmark_markdown


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "examples" / "golden_cases"


class BenchmarkTests(unittest.TestCase):
    def test_build_benchmark_snapshot_passes_golden_corpus(self) -> None:
        snapshot = build_benchmark_snapshot(GOLDEN, repo_path=ROOT)

        self.assertEqual(snapshot.case_count, 47)
        self.assertEqual(snapshot.failed_count, 0)
        self.assertEqual(snapshot.passed_count, 47)
        self.assertGreater(snapshot.posture_distribution["BLOCK"], 0)
        self.assertGreater(snapshot.posture_distribution["REVIEW"], 0)
        self.assertGreater(snapshot.posture_distribution["LOW_CONCERN"], 0)

    def test_format_benchmark_markdown_includes_key_sections(self) -> None:
        snapshot = build_benchmark_snapshot(GOLDEN, repo_path=ROOT)
        markdown = format_benchmark_markdown(snapshot, cases_dir=GOLDEN)

        self.assertIn("# Merge Risk Benchmark", markdown)
        self.assertIn("SWE-Bench asks whether an agent solved the task", markdown)
        self.assertIn("## Posture distribution", markdown)
        self.assertIn("## Methodology", markdown)
        self.assertIn("Golden cases: **47**", markdown)


if __name__ == "__main__":
    unittest.main()