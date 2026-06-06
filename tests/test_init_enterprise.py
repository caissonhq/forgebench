from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import unittest

from forgebench.cli import main
from forgebench.init_enterprise import EnterpriseInitOptions, run_enterprise_init
from forgebench.licensing.keys import generate_license_key
from forgebench.licensing.store import activate_and_store


class EnterpriseInitTests(unittest.TestCase):
    def _activate_team_license(self, tmp: str) -> Path:
        license_path = Path(tmp) / "license.json"
        key = generate_license_key(tier="team", organization="Test Org", seats=5)
        activate_and_store(key, path=license_path)
        os.environ["FORGEBENCH_LICENSE_PATH"] = str(license_path)
        return license_path

    def tearDown(self) -> None:
        os.environ.pop("FORGEBENCH_LICENSE_PATH", None)

    def test_run_enterprise_init_generates_starter_kit(self) -> None:
        with TemporaryDirectory() as tmp:
            self._activate_team_license(tmp)
            root = Path(tmp)
            result = run_enterprise_init(
                root,
                options=EnterpriseInitOptions(
                    org_name="Test Org",
                    team_slug="eng",
                    force=True,
                    non_interactive=True,
                ),
            )
            self.assertTrue(result.guardrails_path.exists())
            self.assertTrue(result.org_policy_path.exists())
            self.assertTrue(result.ci_guardrails_path and result.ci_guardrails_path.exists())
            self.assertTrue(result.workflow_path and result.workflow_path.exists())
            self.assertTrue(result.onboarding_doc_path.exists())
            guardrails = result.guardrails_path.read_text(encoding="utf-8")
            self.assertIn("extends:", guardrails)
            self.assertIn("Test Org", result.org_policy_path.read_text(encoding="utf-8"))

    def test_cli_init_enterprise_non_interactive(self) -> None:
        with TemporaryDirectory() as tmp:
            self._activate_team_license(tmp)
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "init",
                        "--enterprise",
                        "--yes",
                        "--repo",
                        tmp,
                        "--org-name",
                        "CLI Org",
                        "--manifest",
                        str(Path(tmp) / "manifest.json"),
                    ]
                )
            self.assertEqual(result, 0)
            self.assertIn("enterprise init complete", stdout.getvalue().lower())
            manifest = json.loads((Path(tmp) / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                Path(manifest["org_policy_path"]).resolve(),
                (Path(tmp) / "org-policy" / "forgebench-org.yml").resolve(),
            )

    def test_cli_init_team_alias(self) -> None:
        with TemporaryDirectory() as tmp:
            self._activate_team_license(tmp)
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "init",
                        "--team",
                        "--yes",
                        "--repo",
                        tmp,
                        "--org-name",
                        "Team Alias Org",
                    ]
                )
            self.assertEqual(result, 0)
            self.assertTrue((Path(tmp) / "org-policy" / "forgebench-org.yml").exists())

    def test_enterprise_init_refuses_overwrite_without_force(self) -> None:
        with TemporaryDirectory() as tmp:
            self._activate_team_license(tmp)
            root = Path(tmp)
            run_enterprise_init(root, options=EnterpriseInitOptions(force=True, non_interactive=True))
            with self.assertRaises(SystemExit) as raised:
                main(["init", "--enterprise", "--yes", "--repo", str(root)])
            self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()