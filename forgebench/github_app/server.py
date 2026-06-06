from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from forgebench.github_app.manifest import export_github_app_manifest
from forgebench.github_app.webhook import handle_github_webhook, verify_github_signature


@dataclass(frozen=True)
class GitHubAppServiceConfig:
    host: str = "127.0.0.1"
    port: int = 8792
    webhook_secret: str = ""
    org_enforcement_config: str | None = None


def serve_github_app(config: GitHubAppServiceConfig) -> None:
    handler = _build_handler(config)
    server = ThreadingHTTPServer((config.host, config.port), handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _build_handler(config: GitHubAppServiceConfig):
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
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            if config.webhook_secret:
                signature = self.headers.get("X-Hub-Signature-256", "")
                if not verify_github_signature(raw, signature, config.webhook_secret):
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
            )
            self._json(200, {
                "handled": result.handled,
                "message": result.message,
                "check_output": result.check_output,
            })

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler