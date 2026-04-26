from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.guardrails import GuardrailsParseError, load_guardrails, parse_guardrails


ROOT = Path(__file__).resolve().parents[1]


class GuardrailsYamlTests(unittest.TestCase):
    def test_valid_file_loads(self) -> None:
        guardrails = parse_guardrails(
            """
project: Quarterly
protected_behavior:
  - Federal + California only
risk_files:
  high:
    - "**/TaxEngine/**"
checks:
  test: "python -m unittest discover -s tests"
  custom:
    docs: null
policy:
  path_categories:
    docs:
      patterns:
        - "README.md"
      default_severity: advisory
"""
        )

        self.assertEqual(guardrails.project, "Quarterly")
        self.assertEqual(guardrails.risk_files_high, ["**/TaxEngine/**"])
        self.assertEqual(guardrails.checks["test"], "python -m unittest discover -s tests")
        self.assertIn("docs", guardrails.custom_checks)
        self.assertIn("docs", guardrails.policy.path_categories)

    def test_malformed_yaml_has_clear_error(self) -> None:
        with self.assertRaises(GuardrailsParseError) as raised:
            parse_guardrails("project: [unterminated\n")

        message = str(raised.exception)
        self.assertIn("Malformed forgebench.yml", message)
        self.assertIn("line", message)

    def test_unknown_top_level_key_is_warning(self) -> None:
        guardrails = parse_guardrails(
            """
project: Example
surprise: true
"""
        )

        self.assertEqual(guardrails.project, "Example")
        self.assertEqual(len(guardrails.warnings), 1)
        self.assertIn("surprise", guardrails.warnings[0])

    def test_empty_file_loads_empty_config(self) -> None:
        guardrails = parse_guardrails("")

        self.assertIsNone(guardrails.project)
        self.assertEqual(guardrails.protected_behavior, [])

    def test_comments_only_file_loads_empty_config(self) -> None:
        guardrails = parse_guardrails("# comment only\n# another comment\n")

        self.assertIsNone(guardrails.project)
        self.assertEqual(guardrails.forbidden_patterns, [])

    def test_null_policy_loads_empty_policy(self) -> None:
        guardrails = parse_guardrails("policy: null\n")

        self.assertEqual(guardrails.policy.path_categories, {})

    def test_non_mapping_shape_fails_clearly(self) -> None:
        with self.assertRaises(GuardrailsParseError) as raised:
            parse_guardrails("checks:\n  - python -m unittest\n")

        self.assertIn("checks", str(raised.exception))
        self.assertIn("mapping", str(raised.exception))

    def test_every_example_and_fixture_yml_loads(self) -> None:
        paths = sorted((ROOT / "examples").rglob("forgebench.yml"))
        paths += sorted((ROOT / "tests" / "fixtures").glob("*.yml"))
        self.assertTrue(paths)

        for path in paths:
            with self.subTest(path=path):
                self.assertIsNotNone(load_guardrails(path))

    def test_load_guardrails_accepts_empty_file(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "forgebench.yml"
            path.write_text("# no config yet\n", encoding="utf-8")

            guardrails = load_guardrails(path)

        self.assertIsNone(guardrails.project)
