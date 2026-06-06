from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.cli import main
from forgebench.quickstart import run_quickstart


class QuickstartTests(unittest.TestCase):
    def test_run_quickstart_skip_init_when_guardrails_exist(self) -> None:
        with TemporaryDirectory() as tmp:
            (Path(tmp) / "forgebench.yml").write_text("project: test\n", encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = run_quickstart(repo_path=tmp, skip_demo=True)
            self.assertEqual(result.doctor_exit_code, 0)
            self.assertIn("Skipped init", stdout.getvalue())

    def test_cli_quickstart(self) -> None:
        with TemporaryDirectory() as tmp:
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(["quickstart", "--repo", tmp, "--skip-demo", "--skip-init"])
            self.assertEqual(result, 0)
            self.assertIn("Quickstart", stdout.getvalue())