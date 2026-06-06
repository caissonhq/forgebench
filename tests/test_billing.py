from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.billing.stripe_checkout import build_checkout_url
from forgebench.billing.upgrade import format_upgrade_prompt
from forgebench.billing.webhooks import handle_stripe_event, verify_stripe_signature
from forgebench.crm.pipeline import PIPELINE_PATH, load_pipeline, upsert_pipeline_entry
from forgebench.portal.dashboard import export_customer_portal


class BillingTests(unittest.TestCase):
    def test_build_checkout_url_fallback_without_stripe(self) -> None:
        session = build_checkout_url(tier="team", seats=3)
        self.assertEqual(session.tier, "team")
        self.assertEqual(session.seats, 3)
        self.assertIn("subscribe", session.url)

    def test_verify_stripe_signature(self) -> None:
        secret = "whsec_test"
        payload = b'{"id":"evt_test"}'
        timestamp = str(int(time.time()))
        signed = f"{timestamp}.{payload.decode()}".encode()
        signature = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
        header = f"t={timestamp},v1={signature}"
        self.assertTrue(verify_stripe_signature(payload, header, secret))

    def test_handle_checkout_completed_updates_pipeline(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "pipeline.json"
            with _pipeline_path(path):
                event = {
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "id": "cs_test",
                            "metadata": {"tier": "team", "seats": "5"},
                            "customer_details": {"email": "team@example.com"},
                        }
                    },
                }
                result = handle_stripe_event(event)
                self.assertTrue(result.handled)
                entries = load_pipeline()
                self.assertEqual(len(entries), 1)
                self.assertEqual(entries[0].stage, "paid")
                self.assertEqual(entries[0].organization, "team@example.com")

    def test_upgrade_prompt_includes_subscribe_cta(self) -> None:
        text = format_upgrade_prompt("policy_serve")
        self.assertIn("forgebench subscribe", text)
        self.assertIn("policy_serve", text)

    def test_customer_portal_export(self) -> None:
        with TemporaryDirectory() as tmp:
            result = export_customer_portal(output_dir=tmp)
            self.assertTrue(result.index_path.exists())
            html = result.index_path.read_text(encoding="utf-8")
            self.assertIn("Customer Portal", html)


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