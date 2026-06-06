from __future__ import annotations

import unittest

from forgebench.github_app.attestation import sign_attestation
from forgebench.github_app.enforcement import enforce_org_policy, load_org_enforcement_config
from forgebench.github_app.manifest import export_github_app_manifest
from forgebench.github_app.webhook import handle_github_webhook, verify_github_signature


ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
ORG_CONFIG = ROOT / "examples" / "github-app" / "org-enforcement.json"


class GitHubAppTests(unittest.TestCase):
    def test_manifest_exports_required_permissions(self) -> None:
        manifest = export_github_app_manifest()
        self.assertIn("default_permissions", manifest)
        self.assertIn("pull_request", manifest["default_events"])
        self.assertIn("org_policy_enforcement", manifest)

    def test_block_posture_fails_enforcement(self) -> None:
        config = load_org_enforcement_config(ORG_CONFIG)
        result = enforce_org_policy(posture="BLOCK", config=config)
        self.assertFalse(result.allowed)
        self.assertEqual(result.check_conclusion, "failure")

    def test_low_concern_passes_enforcement(self) -> None:
        config = load_org_enforcement_config(ORG_CONFIG)
        result = enforce_org_policy(
            posture="LOW_CONCERN",
            config=config,
            policy_fingerprint="sha256:example-fingerprint",
        )
        self.assertTrue(result.allowed)

    def test_webhook_signature_round_trip(self) -> None:
        payload = b'{"action":"opened"}'
        import hashlib
        import hmac

        secret = "test-secret-12345678"
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        self.assertTrue(verify_github_signature(payload, f"sha256={digest}", secret))

    def test_webhook_handles_check_run_payload(self) -> None:
        result = handle_github_webhook(
            {
                "_event_type": "check_run",
                "check_run": {
                    "name": "ForgeBench",
                    "conclusion": "neutral",
                    "output": {"title": "ForgeBench posture: REVIEW"},
                },
            },
            config_path=ORG_CONFIG,
            webhook_secret="secret",
            policy_fingerprint="fp",
        )
        self.assertTrue(result.handled)
        assert result.enforcement is not None
        self.assertEqual(result.enforcement.posture, "REVIEW")

    def test_webhook_auto_configures_installation(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            result = handle_github_webhook(
                {
                    "_event_type": "installation",
                    "action": "created",
                    "installation": {
                        "id": 4242,
                        "app_id": 1,
                        "target_type": "Organization",
                        "account": {"login": "acme-corp"},
                    },
                },
                install_output_dir=tmp,
            )
            self.assertTrue(result.handled)
            self.assertIn("4242", result.message)
            enforcement = __import__("pathlib").Path(tmp) / "installation-4242" / "org-enforcement.json"
            self.assertTrue(enforcement.exists())

    def test_webhook_handles_signed_attestation(self) -> None:
        secret = "webhook-secret-12345678"
        signature = sign_attestation(
            secret=secret,
            org_id="acme-platform",
            pr_number=1,
            head_sha="deadbeef",
            posture="REVIEW",
            policy_fingerprint="sha256:example-fingerprint",
        )
        result = handle_github_webhook(
            {
                "_event_type": "pull_request",
                "forgebench_attestation": {
                    "org_id": "acme-platform",
                    "pr_number": 1,
                    "head_sha": "deadbeef",
                    "posture": "REVIEW",
                    "policy_fingerprint": "sha256:example-fingerprint",
                },
            },
            config_path=ORG_CONFIG,
            webhook_secret=secret,
            attestation_signature=signature,
            policy_fingerprint="sha256:example-fingerprint",
        )
        self.assertTrue(result.handled)


if __name__ == "__main__":
    unittest.main()