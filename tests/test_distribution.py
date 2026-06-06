from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import unittest

from forgebench.cli import main
from forgebench.distribution import (
    InstallMethod,
    detect_environment,
    format_install_guide,
    format_methods_table,
    recommend_install_method,
    render_shell_completion,
    upgrade_instructions,
)


class DistributionTests(unittest.TestCase):
    def test_detect_environment_returns_profile(self) -> None:
        env = detect_environment()
        self.assertTrue(env.python_version)
        self.assertIn(env.os_name, {"darwin", "linux", "windows", "other"})

    def test_format_install_guide(self) -> None:
        text = format_install_guide()
        self.assertIn("ForgeBench Install Guide", text)
        self.assertIn("forgebench quickstart", text)

    def test_format_methods_table_lists_all_methods(self) -> None:
        text = format_methods_table()
        for method in ("pip", "pipx", "homebrew", "binary", "source"):
            self.assertIn(method, text)

    def test_upgrade_instructions_for_pipx(self) -> None:
        lines = upgrade_instructions(InstallMethod.PIPX)
        self.assertTrue(any("pipx upgrade" in line for line in lines))

    def test_render_bash_completion(self) -> None:
        script = render_shell_completion("bash")
        self.assertIn("_forgebench_completions", script)
        self.assertIn("quickstart", script)

    def test_render_unsupported_shell_raises(self) -> None:
        with self.assertRaises(ValueError):
            render_shell_completion("powershell")

    def test_recommend_install_method(self) -> None:
        info = recommend_install_method()
        self.assertTrue(info.command)

    def test_cli_install_guide(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = main(["install"])
        self.assertEqual(result, 0)
        self.assertIn("Install Guide", stdout.getvalue())

    def test_cli_install_methods(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = main(["install", "methods"])
        self.assertEqual(result, 0)
        self.assertIn("pipx", stdout.getvalue())

    def test_cli_install_completions(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = main(["install", "completions", "--shell", "zsh"])
        self.assertEqual(result, 0)
        self.assertIn("compdef", stdout.getvalue())

    def test_cli_install_upgrade(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = main(["install", "upgrade"])
        self.assertEqual(result, 0)
        self.assertIn("upgrade", stdout.getvalue().lower())