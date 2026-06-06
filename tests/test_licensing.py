from __future__ import annotations

import json
import os
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.licensing.keys import LicenseError, activate_license_key, generate_license_key, verify_license_key
from forgebench.licensing.quotas import LicenseRequired, check_quota, consume_quota, require_feature
from forgebench.licensing.store import activate_and_store, load_license, machine_id
from forgebench.licensing.tiers import LicenseTier
from forgebench.cli import main


class LicensingTests(unittest.TestCase):
    def test_generate_and_verify_team_key(self) -> None:
        key = generate_license_key(tier="team", organization="Acme", seats=5)
        payload = verify_license_key(key)
        self.assertEqual(payload.tier, LicenseTier.TEAM)
        self.assertEqual(payload.organization, "Acme")
        self.assertEqual(payload.seats, 5)

    def test_invalid_signature_rejected(self) -> None:
        key = generate_license_key(tier="team", organization="Acme")
        with self.assertRaises(LicenseError):
            verify_license_key(key + "x")

    def test_activate_and_load_license(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "license.json"
            key = generate_license_key(tier="team", organization="TestCo", seats=3)
            record = activate_and_store(key, path=path)
            self.assertTrue(record.valid)
            self.assertEqual(record.tier, LicenseTier.TEAM)
            self.assertEqual(record.organization, "TestCo")

    def test_require_feature_blocks_enterprise_without_license(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "license.json"
            with _license_path(path):
                with self.assertRaises(LicenseRequired):
                    require_feature("policy_serve")

    def test_team_license_allows_init_enterprise_feature_check(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "license.json"
            key = generate_license_key(tier="team", organization="TeamCo", seats=2)
            activate_and_store(key, path=path)
            with _license_path(path):
                require_feature("init_enterprise")

    def test_quota_consumption_for_grok(self) -> None:
        with TemporaryDirectory() as tmp:
            license_path = Path(tmp) / "license.json"
            quota_path = Path(tmp) / "quota.json"
            key = generate_license_key(tier="team", organization="QuotaCo", seats=1)
            with _license_path(license_path), _quota_path(quota_path):
                activate_and_store(key, path=license_path)
                record = load_license(path=license_path)
                self.assertTrue(record.valid)
                self.assertEqual(record.tier, LicenseTier.TEAM)
                status = consume_quota("grok_verify")
                self.assertEqual(status.used, 1)

    def test_cli_license_status_free_by_default(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "license.json"
            with _license_path(path):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    result = main(["license", "status"])
                self.assertEqual(result, 0)
                self.assertIn("free", stdout.getvalue().lower())

    def test_cli_license_activate(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "license.json"
            key = generate_license_key(tier="enterprise", organization="EntCo", seats=10)
            with _license_path(path):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    result = main(["license", "activate", key, "--path", str(path)])
                self.assertEqual(result, 0)
                self.assertIn("enterprise", stdout.getvalue().lower())

    def test_cli_license_check_feature_denied(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "license.json"
            with _license_path(path):
                stdout = StringIO()
                with redirect_stdout(stdout):
                    result = main(["license", "check", "--feature", "policy_serve"])
                self.assertEqual(result, 2)
                self.assertIn("policy_serve", stdout.getvalue())

    def test_activate_license_key_includes_machine(self) -> None:
        key = generate_license_key(tier="team", organization="M", seats=1)
        payload = activate_license_key(key, machine_id="abc123")
        self.assertEqual(payload["machine_id"], "abc123")
        self.assertIn("abc123", payload["activations"])

    def test_machine_id_is_stable_length(self) -> None:
        self.assertEqual(len(machine_id()), 16)

    def test_cli_license_verify(self) -> None:
        key = generate_license_key(tier="team", organization="VerifyCLI", seats=1)
        stdout = StringIO()
        with redirect_stdout(stdout):
            result = main(["license", "verify", key, "--json"])
        self.assertEqual(result, 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["valid"])

    def test_upgrade_prompt_on_license_required(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "license.json"
            with _license_path(path):
                try:
                    require_feature("policy_serve")
                except LicenseRequired as exc:
                    self.assertIn("forgebench subscribe", str(exc))
                    self.assertEqual(exc.feature, "policy_serve")
                else:
                    self.fail("expected LicenseRequired")


class _PathPatch:
    def __init__(self, module, attr: str, value: Path, *, set_license_env: bool = False) -> None:
        self.module = module
        self.attr = attr
        self.value = value
        self.set_license_env = set_license_env
        self.original = getattr(module, attr)

    def __enter__(self) -> None:
        setattr(self.module, self.attr, self.value)
        if self.set_license_env:
            os.environ["FORGEBENCH_LICENSE_PATH"] = str(self.value)

    def __exit__(self, exc_type, exc, tb) -> None:
        setattr(self.module, self.attr, self.original)
        if self.set_license_env:
            os.environ.pop("FORGEBENCH_LICENSE_PATH", None)


def _license_path(path: Path):
    import forgebench.licensing.store as store

    return _PathPatch(store, "DEFAULT_LICENSE_PATH", path, set_license_env=True)


def _quota_path(path: Path):
    import forgebench.licensing.quotas as quotas

    return _PathPatch(quotas, "QUOTA_PATH", path)


if __name__ == "__main__":
    unittest.main()