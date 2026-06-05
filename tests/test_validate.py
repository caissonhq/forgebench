from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.cli import main
from forgebench.validate import validate_guardrails_file


class ValidateTests(unittest.TestCase):
    def test_valid_guardrails_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "forgebench.yml"
            path.write_text(
                """
project: Example
checks:
  test: python -m unittest discover -s tests
""".strip()
                + "\n",
                encoding="utf-8",
            )
            report = validate_guardrails_file(path)

        self.assertTrue(report.valid)
        self.assertEqual(report.exit_code, 0)

    def test_malformed_yaml_fails(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "forgebench.yml"
            path.write_text("project: [unterminated\n", encoding="utf-8")
            report = validate_guardrails_file(path)

        self.assertFalse(report.valid)
        self.assertEqual(report.exit_code, 2)

    def test_unknown_key_warns_by_default(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "forgebench.yml"
            path.write_text("project: Example\nsurprise: true\n", encoding="utf-8")
            report = validate_guardrails_file(path)

        self.assertTrue(report.valid)
        self.assertEqual(report.exit_code, 1)
        self.assertTrue(any("surprise" in issue.message for issue in report.issues))

    def test_strict_mode_errors_on_unknown_key(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "forgebench.yml"
            path.write_text("project: Example\nsurprise: true\n", encoding="utf-8")
            report = validate_guardrails_file(path, strict=True)

        self.assertFalse(report.valid)
        self.assertEqual(report.exit_code, 2)

    def test_cli_validate_command(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "forgebench.yml"
            path.write_text("project: Example\n", encoding="utf-8")
            result = main(["validate", "--repo", tmp, "--file", "forgebench.yml"])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()