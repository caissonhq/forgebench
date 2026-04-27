from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import subprocess
import sys
import unittest

import forgebench
from forgebench.cli import main


class VersionTests(unittest.TestCase):
    def test_package_version_is_non_empty(self) -> None:
        self.assertEqual(forgebench.__version__, "0.9.0")

    def test_cli_version_exits_successfully(self) -> None:
        stdout = StringIO()
        with self.assertRaises(SystemExit) as raised, redirect_stdout(stdout):
            main(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("forgebench 0.9.0", stdout.getvalue())

    def test_python_module_help_exits_successfully(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "forgebench", "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("usage: forgebench", result.stdout)
