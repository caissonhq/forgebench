from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.dashboard import DashboardExportError, export_policy_dashboard


class DashboardExportTests(unittest.TestCase):
    def test_export_writes_html_and_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "forgebench.yml").write_text(
                """
team:
  name: Platform
project: Payments
protected_behavior:
  - Preserve ledger invariants
checks:
  test: pytest -q
""",
                encoding="utf-8",
            )
            out_dir = root / "dashboard-out"
            result = export_policy_dashboard(root, output_dir=out_dir)

            self.assertTrue(result.index_path.exists())
            self.assertTrue(result.manifest_path.exists())
            html = result.index_path.read_text(encoding="utf-8")
            self.assertIn("Platform", html)
            self.assertIn("Preserve ledger invariants", html)
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["team"], "Platform")
            self.assertEqual(manifest["project"], "Payments")

    def test_missing_guardrails_raises(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaises(DashboardExportError):
                export_policy_dashboard(tmp)


if __name__ == "__main__":
    unittest.main()