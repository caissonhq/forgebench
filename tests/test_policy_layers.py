from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.guardrails import GuardrailsParseError, load_guardrails
from forgebench.policy_layers import ORG_POLICY_ENV, load_layered_guardrails, resolve_guardrails_path


class PolicyLayerTests(unittest.TestCase):
    def test_extends_merges_base_and_overlay(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yml").write_text(
                """
project: Base
protected_behavior:
  - Keep billing stable
risk_files:
  high:
    - "**/billing/**"
""",
                encoding="utf-8",
            )
            (root / "forgebench.yml").write_text(
                """
extends: base.yml
project: Overlay
forbidden_patterns:
  - eval(
""",
                encoding="utf-8",
            )

            guardrails = load_guardrails(root / "forgebench.yml")

            self.assertEqual(guardrails.project, "Overlay")
            self.assertEqual(guardrails.protected_behavior, ["Keep billing stable"])
            self.assertEqual(guardrails.risk_files_high, ["**/billing/**"])
            self.assertEqual(guardrails.forbidden_patterns, ["eval("])
            self.assertEqual(len(guardrails.sources), 2)

    def test_include_merges_multiple_layers(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "security.yml").write_text(
                """
forbidden_patterns:
  - subprocess.run
""",
                encoding="utf-8",
            )
            (root / "tests.yml").write_text(
                """
checks:
  test: pytest -q
""",
                encoding="utf-8",
            )
            (root / "forgebench.yml").write_text(
                """
include:
  - security.yml
  - tests.yml
project: Monorepo
""",
                encoding="utf-8",
            )

            guardrails = load_guardrails(root / "forgebench.yml")

            self.assertEqual(guardrails.project, "Monorepo")
            self.assertEqual(guardrails.forbidden_patterns, ["subprocess.run"])
            self.assertEqual(guardrails.checks["test"], "pytest -q")

    def test_org_policy_env_layers_on_top_of_repo(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            org = root / "org"
            org.mkdir()
            (org / "forgebench-org.yml").write_text(
                """
team:
  name: Acme Platform
protected_behavior:
  - No direct prod DB writes
""",
                encoding="utf-8",
            )
            (root / "forgebench.yml").write_text(
                """
project: Service A
forbidden_patterns:
  - DROP TABLE
""",
                encoding="utf-8",
            )

            previous = os.environ.get(ORG_POLICY_ENV)
            os.environ[ORG_POLICY_ENV] = str(org / "forgebench-org.yml")
            try:
                guardrails = load_layered_guardrails(root / "forgebench.yml")
            finally:
                if previous is None:
                    os.environ.pop(ORG_POLICY_ENV, None)
                else:
                    os.environ[ORG_POLICY_ENV] = previous

            self.assertEqual(guardrails.team, "Acme Platform")
            self.assertEqual(guardrails.project, "Service A")
            self.assertIn("No direct prod DB writes", guardrails.protected_behavior)
            self.assertEqual(guardrails.forbidden_patterns, ["DROP TABLE"])

    def test_cycle_detection_raises(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.yml").write_text("extends: b.yml\n", encoding="utf-8")
            (root / "b.yml").write_text("extends: a.yml\n", encoding="utf-8")

            with self.assertRaises(GuardrailsParseError) as raised:
                load_guardrails(root / "a.yml")

            self.assertIn("cycle", str(raised.exception).lower())

    def test_resolve_guardrails_path_defaults_to_repo_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(resolve_guardrails_path(root, None))
            (root / "forgebench.yml").write_text("project: Example\n", encoding="utf-8")
            resolved = resolve_guardrails_path(root, None)
            self.assertEqual(resolved, root / "forgebench.yml")


if __name__ == "__main__":
    unittest.main()