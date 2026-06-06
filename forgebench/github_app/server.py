from __future__ import annotations

import json
import os
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from forgebench.github_app.manifest import export_github_app_manifest
from forgebench.github_app.webhook import handle_github_webhook, verify_github_signature
from forgebench.observability.logging import log_event
from forgebench.security.http_limits import (
    HTTPBodyTooLargeError,
    InsecureBindError,
    enforce_loopback_or_explicit,
    parse_content_length,
    read_bounded_body,
)
from forgebench.security.secrets import SecretValidationError, require_webhook_secret


@dataclass(frozen=True)
class GitHubAppServiceConfig:
    host: str = "127.0.0.1"
    port: int = 8792
    webhook_secret: str = ""
    org_enforcement_config: str | None = None


def serve_github_app(config: GitHubAppServiceConfig) -> None:
    secret = config.webhook_secret.strip() or os.environ.get("FORGEBENCH_GITHUB_WEBHOOK_SECRET", "").strip()
    if not secret:
        try:
            secret = require_webhook_secret()
        except SecretValidationError as exc:
            raise SecretValidationError(str(exc)) from exc
    try:
        enforce_loopback_or_explicit(config.host)
    except InsecureBindError as exc:
        raise SecretValidationError(str(exc)) from exc
    handler = _build_handler(config, webhook_secret=secret)
    server = ThreadingHTTPServer((config.host, config.port), handler)
    log_event("info", "github_app_service_started", host=config.host, port=config.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _build_handler(config: GitHubAppServiceConfig, *, webhook_secret: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            del format, args

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._json(200, {"status": "ok", "service": "forgebench-github-app"})
                return
            if parsed.path == "/v1/manifest":
                self._json(200, export_github_app_manifest())
                return
            self._json(404, {"error": "not_found"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path != "/github-app/webhook":
                self._json(404, {"error": "not_found"})
                return
            try:
                length = parse_content_length(self.headers.get("Content-Length"))
                raw = read_bounded_body(self.rfile, length)
            except HTTPBodyTooLargeError as exc:
                self._json(413, {"error": str(exc)})
                return
            signature = self.headers.get("X-Hub-Signature-256", "")
            if not verify_github_signature(raw, signature, webhook_secret):
                self._json(401, {"error": "invalid_signature"})
                return
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                self._json(400, {"error": "invalid_json"})
                return
            if not isinstance(payload, dict):
                self._json(400, {"error": "json_object_required"})
                return
            payload["_event_type"] = self.headers.get("X-GitHub-Event", "unknown")
            result = handle_github_webhook(
                payload,
                config_path=config.org_enforcement_config,
                webhook_secret=webhook_secret,
                attestation_signature=self.headers.get("X-ForgeBench-Attestation"),
            )
            self._json(
                200,
                {
                    "handled": result.handled,
                    "message": result.message,
                    "check_output": result.check_output,
                },
            )

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler