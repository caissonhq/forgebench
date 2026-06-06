from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from forgebench.billing.config import stripe_webhook_secret
from forgebench.crm.pipeline import record_subscription_event
from forgebench.observability.logging import log_event
from forgebench.security.http_limits import HTTPBodyTooLargeError, parse_content_length, read_bounded_body


class StripeWebhookError(ValueError):
    pass


@dataclass(frozen=True)
class WebhookResult:
    handled: bool
    event_type: str
    message: str
    actions: list[str]


def verify_stripe_signature(payload: bytes, signature_header: str, secret: str, *, tolerance: int = 300) -> bool:
    if not secret or not signature_header:
        return False
    parts: dict[str, str] = {}
    for item in signature_header.split(","):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        parts[key.strip()] = value.strip()
    timestamp = parts.get("t")
    signature = parts.get("v1")
    if not timestamp or not signature:
        return False
    try:
        ts = int(timestamp)
    except ValueError:
        return False
    if abs(int(time.time()) - ts) > tolerance:
        return False
    signed = f"{timestamp}.{payload.decode('utf-8')}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def handle_stripe_event(event: dict[str, Any]) -> WebhookResult:
    event_type = str(event.get("type") or "unknown")
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    obj = data.get("object") if isinstance(data.get("object"), dict) else {}
    actions: list[str] = []
    if event_type == "checkout.session.completed":
        tier = str(obj.get("metadata", {}).get("tier") or obj.get("client_reference_id", ""))
        seats = int(obj.get("metadata", {}).get("seats") or 1)
        customer = str(obj.get("customer_details", {}).get("email") or obj.get("customer_email") or "")
        record_subscription_event(
            stage="paid",
            organization=customer or "stripe-customer",
            tier=tier,
            seats=seats,
            source="stripe_checkout",
            metadata={"session_id": obj.get("id")},
        )
        actions.append("pipeline_stage_paid")
        actions.append("await_license_key_delivery")
    elif event_type in {"customer.subscription.updated", "customer.subscription.created"}:
        status = str(obj.get("status") or "")
        record_subscription_event(
            stage="paid" if status == "active" else "trial",
            organization=str(obj.get("id") or "subscription"),
            tier="team",
            seats=int(obj.get("quantity") or 1),
            source="stripe_subscription",
            metadata={"status": status},
        )
        actions.append(f"subscription_{status}")
    elif event_type == "customer.subscription.deleted":
        record_subscription_event(
            stage="churned",
            organization=str(obj.get("id") or "subscription"),
            tier="team",
            seats=0,
            source="stripe_subscription",
            metadata={"status": "canceled"},
        )
        actions.append("subscription_canceled")
    else:
        return WebhookResult(handled=False, event_type=event_type, message="Event ignored.", actions=[])
    return WebhookResult(handled=True, event_type=event_type, message=f"Handled {event_type}.", actions=actions)


@dataclass(frozen=True)
class StripeWebhookServerConfig:
    host: str = "127.0.0.1"
    port: int = 8794
    webhook_secret: str = ""


def serve_stripe_webhook(config: StripeWebhookServerConfig) -> None:
    secret = config.webhook_secret.strip() or stripe_webhook_secret()
    handler = _build_handler(secret)
    server = ThreadingHTTPServer((config.host, config.port), handler)
    log_event("info", "stripe_webhook_server_started", host=config.host, port=config.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _build_handler(secret: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            del format, args

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/stripe/webhook":
                self._json(404, {"error": "not_found"})
                return
            try:
                length = parse_content_length(self.headers.get("Content-Length"))
                raw = read_bounded_body(self.rfile, length)
            except HTTPBodyTooLargeError as exc:
                self._json(413, {"error": str(exc)})
                return
            signature = self.headers.get("Stripe-Signature", "")
            if not verify_stripe_signature(raw, signature, secret):
                self._json(400, {"error": "invalid_signature"})
                return
            try:
                event = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                self._json(400, {"error": "invalid_json"})
                return
            if not isinstance(event, dict):
                self._json(400, {"error": "invalid_event"})
                return
            result = handle_stripe_event(event)
            self._json(200, {"handled": result.handled, "event_type": result.event_type, "actions": result.actions})

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler