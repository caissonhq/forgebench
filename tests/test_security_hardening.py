from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from forgebench.audit_chain import record_tamper_evident_event, verify_audit_chain
from forgebench.fpl.parser import FPLParseError, parse_fpl
from forgebench.github_app.attestation import posture_from_check_run_payload, sign_attestation
from forgebench.github_app.webhook import handle_github_webhook, verify_github_signature
from forgebench.guardrails import GuardrailsParseError, load_guardrails
from forgebench.policy_layers import load_layered_guardrails
from forgebench.security.command_exec import CommandParseError, parse_command_argv
from forgebench.security.http_limits import HTTPBodyTooLargeError, parse_content_length
from forgebench.security.path_confinement import PathConfinementError, resolve_confined_path
from forgebench.security.rbac import PolicyAuthorizationError, authorize_policy_request
from forgebench.security.secrets import SecretValidationError, require_webhook_secret


ROOT = Path(__file__).resolve().parents[1]
ORG_CONFIG = ROOT / "examples" / "github-app" / "org-enforcement.json"


class SecurityHardeningTests(unittest.TestCase):
    def test_extends_cannot_escape_trusted_root(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root.parent / "outside-policy.yml"
            outside.write_text("project: Outside\n", encoding="utf-8")
            (root / "forgebench.yml").write_text(
                "extends: ../outside-policy.yml\n",
                encoding="utf-8",
            )
            with self.assertRaises(GuardrailsParseError):
                load_guardrails(root / "forgebench.yml")

    def test_fpl_reference_confined_to_root(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "forgebench.yml").write_text('fpl: "../escape.fpl"\n', encoding="utf-8")
            with self.assertRaises(GuardrailsParseError):
                load_layered_guardrails(root / "forgebench.yml")

    def test_resolve_confined_path_rejects_traversal(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            sub = root / "policy"
            sub.mkdir()
            with self.assertRaises(PathConfinementError):
                resolve_confined_path("../../outside.yml", trusted_root=root, base_dir=sub)

    def test_llm_command_parsed_without_shell(self) -> None:
        argv = parse_command_argv("python -c 'print(1)'")
        self.assertEqual(argv[0], "python")
        with self.assertRaises(CommandParseError):
            parse_command_argv("")

    def test_http_content_length_cap(self) -> None:
        with self.assertRaises(HTTPBodyTooLargeError):
            parse_content_length(str(10 * 1024 * 1024))

    def test_webhook_secret_required(self) -> None:
        with TemporaryDirectory() as tmp:
            previous = os.environ.pop("FORGEBENCH_GITHUB_WEBHOOK_SECRET", None)
            try:
                with self.assertRaises(SecretValidationError):
                    require_webhook_secret()
            finally:
                if previous is not None:
                    os.environ["FORGEBENCH_GITHUB_WEBHOOK_SECRET"] = previous

    def test_webhook_rejects_spoofed_forgebench_posture(self) -> None:
        result = handle_github_webhook(
            {"action": "opened", "forgebench": {"posture": "LOW_CONCERN"}},
            config_path=ORG_CONFIG,
            webhook_secret="test-secret",
        )
        self.assertFalse(result.handled)

    def test_webhook_accepts_check_run_posture(self) -> None:
        payload = {
            "_event_type": "check_run",
            "check_run": {
                "name": "ForgeBench",
                "conclusion": "neutral",
                "output": {"title": "ForgeBench posture: REVIEW"},
            },
        }
        result = handle_github_webhook(
            payload,
            config_path=ORG_CONFIG,
            webhook_secret="secret",
            policy_fingerprint="fp",
        )
        self.assertTrue(result.handled)
        assert result.enforcement is not None
        self.assertEqual(result.enforcement.posture, "REVIEW")

    def test_signed_attestation_accepted(self) -> None:
        secret = "attestation-secret-12345"
        signature = sign_attestation(
            secret=secret,
            org_id="acme",
            pr_number=42,
            head_sha="abc123",
            posture="REVIEW",
            policy_fingerprint="fp",
        )
        payload = {
            "_event_type": "pull_request",
            "forgebench_attestation": {
                "org_id": "acme",
                "pr_number": 42,
                "head_sha": "abc123",
                "posture": "REVIEW",
                "policy_fingerprint": "fp",
            },
        }
        result = handle_github_webhook(
            payload,
            config_path=ORG_CONFIG,
            webhook_secret=secret,
            attestation_signature=signature,
            policy_fingerprint="fp",
        )
        self.assertTrue(result.handled)

    def test_posture_from_check_run_payload(self) -> None:
        posture = posture_from_check_run_payload(
            {
                "check_run": {
                    "name": "ForgeBench",
                    "conclusion": "failure",
                    "output": {"title": "ForgeBench posture: BLOCK"},
                }
            }
        )
        self.assertEqual(posture, "BLOCK")

    def test_policy_rbac_requires_admin_for_mutations(self) -> None:
        previous = os.environ.get("FORGEBENCH_POLICY_READONLY_TOKEN")
        os.environ["FORGEBENCH_POLICY_READONLY_TOKEN"] = "readonly-token-123456"
        os.environ["FORGEBENCH_POLICY_ADMIN_TOKEN"] = "admin-token-12345678"
        try:
            with self.assertRaises(PolicyAuthorizationError):
                authorize_policy_request(
                    "Bearer readonly-token-123456",
                    required_role=__import__(
                        "forgebench.security.rbac", fromlist=["PolicyServiceRole"]
                    ).PolicyServiceRole.ADMIN,
                )
        finally:
            if previous is None:
                os.environ.pop("FORGEBENCH_POLICY_READONLY_TOKEN", None)
            else:
                os.environ["FORGEBENCH_POLICY_READONLY_TOKEN"] = previous

    def test_audit_chain_detects_tampering(self) -> None:
        with TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit-chain.jsonl"
            record_tamper_evident_event("policy_served", payload={"test": True}, log_path=log_path)
            lines = log_path.read_text(encoding="utf-8").splitlines()
            event = json.loads(lines[0])
            event["payload"]["test"] = False
            log_path.write_text(json.dumps(event) + "\n", encoding="utf-8")
            ok, errors = verify_audit_chain(log_path=log_path)
            self.assertFalse(ok)
            self.assertTrue(errors)

    def test_fpl_size_limit(self) -> None:
        huge = "version 1\n" + ("name x\n" * 20000)
        with self.assertRaises(FPLParseError):
            parse_fpl(huge)

    def test_github_signature_round_trip(self) -> None:
        payload = b'{"action":"completed"}'
        import hashlib
        import hmac

        secret = "webhook-secret-123456"
        digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        self.assertTrue(verify_github_signature(payload, f"sha256={digest}", secret))


if __name__ == "__main__":
    unittest.main()