from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.cli import main
from forgebench.presets import PresetError, format_preset_list, install_preset, list_presets


class PresetsTests(unittest.TestCase):
    def test_list_presets_includes_bundled(self) -> None:
        presets = list_presets()
        names = {item.name for item in presets}
        self.assertTrue({"python", "node", "nextjs"} <= names)

    def test_install_python_preset(self) -> None:
        with TemporaryDirectory() as tmp:
            path = install_preset("python", repo_path=tmp)
            self.assertEqual(path.resolve(), (Path(tmp) / "forgebench.yml").resolve())
            self.assertIn("# Preset: python.", path.read_text(encoding="utf-8"))

    def test_install_unknown_preset_raises(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaises(PresetError):
                install_preset("missing", repo_path=tmp)

    def test_cli_presets_list(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = main(["presets", "list"])
        self.assertEqual(result, 0)
        self.assertIn("python", stdout.getvalue())

    def test_format_preset_list_empty_message(self) -> None:
        text = format_preset_list([])
        self.assertIn("No presets found", text)