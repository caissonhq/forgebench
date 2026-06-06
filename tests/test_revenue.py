from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.cli import main
from forgebench.crm.pipeline import PIPELINE_PATH
from forgebench.licensing.keys import generate_license_key
from forgebench.licensing.server import LicenseServerState
from forgebench.licensing.validation import validate_license_offline


ROOT = Path(__file__).resolve().parents[1]


class RevenueCliTests(unittest.TestCase):
    def test_cli_subscribe_team(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["subscribe", "team", "--seats", "2"])
        self.assertEqual(code, 0)
        self.assertIn("team", stdout.getvalue().lower())

    def test_cli_upgrade_shows_tiers(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["upgrade"])
        self.assertEqual(code, 0)
        self.assertIn("ForgeBench tiers", stdout.getvalue())

    def test_cli_portal_export(self) -> None:
        with TemporaryDirectory() as tmp:
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["portal", "--out", tmp])
            self.assertEqual(code, 0)
            self.assertTrue((Path(tmp) / "index.html").exists())

    def test_cli_crm_add_and_list(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "crm.json"
            with _pipeline_path(path):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    code = main(["crm", "add", "Acme Corp", "--stage", "design_partner", "--seats", "8"])
                self.assertEqual(code, 0)
                with redirect_stdout(stdout := StringIO()):
                    code = main(["crm", "list"])
                self.assertEqual(code, 0)
                self.assertIn("Acme Corp", stdout.getvalue())

    def test_cli_license_verify_offline(self) -> None:
        key = generate_license_key(tier="team", organization="VerifyCo", seats=2)
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["license", "verify", key])
        self.assertEqual(code, 0)
        self.assertIn("valid", stdout.getvalue().lower())

    def test_license_server_state_seat_enforcement(self) -> None:
        key = generate_license_key(tier="team", organization="SeatCo", seats=1)
        state = LicenseServerState()
        first = state.validate_activation(key, "machine-a")
        self.assertTrue(first["valid"])
        second = state.validate_activation(key, "machine-b")
        self.assertFalse(second["valid"])

    def test_revenue_docs_exist(self) -> None:
        self.assertTrue((ROOT / "docs" / "revenue" / "REVENUE_READINESS_SCORECARD.md").exists())
        self.assertTrue((ROOT / "docs" / "customer-onboarding-playbook.md").exists())

    def test_offline_validation_round_trip(self) -> None:
        key = generate_license_key(tier="enterprise", organization="Ent", seats=25)
        result = validate_license_offline(key)
        self.assertTrue(result.valid)
        self.assertEqual(result.payload.tier.name, "ENTERPRISE")


class _PathPatch:
    def __init__(self, module, attr: str, value: Path) -> None:
        self.module = module
        self.attr = attr
        self.value = value
        self.original = getattr(module, attr)

    def __enter__(self) -> None:
        setattr(self.module, self.attr, self.value)

    def __exit__(self, exc_type, exc, tb) -> None:
        setattr(self.module, self.attr, self.original)


def _pipeline_path(path: Path):
    import forgebench.crm.pipeline as pipeline

    return _PathPatch(pipeline, "PIPELINE_PATH", path)


if __name__ == "__main__":
    unittest.main()