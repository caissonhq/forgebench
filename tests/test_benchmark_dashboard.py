from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.benchmark_dashboard import export_benchmark_dashboard


ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "examples" / "golden_cases"
OUTCOMES = ROOT / "examples" / "benchmark_outcomes" / "eo002-pr-outcomes.json"


class BenchmarkDashboardTests(unittest.TestCase):
    def test_export_writes_html_and_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / "dashboard"
            result = export_benchmark_dashboard(
                cases_dir=GOLDEN,
                repo_path=ROOT,
                outcomes_path=OUTCOMES,
                output_dir=out,
                include_telemetry=True,
            )
            self.assertTrue(result.index_path.exists())
            self.assertTrue(result.manifest_path.exists())
            html = result.index_path.read_text(encoding="utf-8")
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertIn("Merge Risk Benchmark", html)
            self.assertIn("Review Arena leaderboard", html)
            self.assertIn("benchmark", manifest)
            self.assertIn("review_arena", manifest)
            self.assertIn("pr_outcomes", manifest)


if __name__ == "__main__":
    unittest.main()