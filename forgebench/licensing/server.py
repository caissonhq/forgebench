from __future__ import annotations

import json
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from forgebench.licensing.keys import LicenseError, verify_license_key
from forgebench.observability.logging import log_event
from forgebench.security.http_limits import (
    HTTPBodyTooLargeError,
    InsecureBindError,
    enforce_loopback_or_explicit,
    parse_content_length,
    read_bounded_body,
)


@dataclass
class LicenseServerState:
    activation_registry: dict[str, list[str]] = field(default_factory=dict)
    registry_path: Path | None = None

    def load(self) -> None:
        if not self.registry_path or not self.registry_path.exists():
            return
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        if isinstance(payload, dict):
            self.activation_registry = {
                str(key): [str(item) for item in value]
                for key, value in payload.items()
                if isinstance(value, list)
            }

    def save(self) -> None:
        if not self.registry_path:
            return
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(
            json.dumps(self.activation_registry, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def validate_activation(self, key: str, machine_id: str) -> dict[str, Any]:
        try:
            payload = verify_license_key(key)
        except LicenseError as exc:
            return {"valid": False, "message": str(exc)}
        license_id = payload.license_id or key
        machines = list(dict.fromkeys(self.activation_registry.get(license_id, [])))
        if machine_id and machine_id not in machines:
            machines.append(machine_id)
        if payload.tier.name != "ENTERPRISE" and len(machines) > payload.seats:
            return {
                "valid": False,
                "message": f"Seat limit exceeded ({len(machines)}/{payload.seats}).",
                "license_id": license_id,
                "activations": len(machines),
                "seats": payload.seats,
            }
        self.activation_registry[license_id] = machines
        self.save()
        return {
            "valid": True,
            "message": "License valid.",
            "license_id": license_id,
            "tier": payload.tier.name.lower(),
            "organization": payload.organization,
            "activations": len(machines),
            "seats": payload.seats,
            "expires_at": payload.expires_at,
        }


@dataclass(frozen=True)
class LicenseServerConfig:
    host: str = "127.0.0.1"
    port: int = 8793
    registry_path: Path = Path("forgebench-output/license-server/registry.json")


class LicenseServerError(ValueError):
    pass


def serve_license_server(config: LicenseServerConfig) -> None:
    try:
        enforce_loopback_or_explicit(config.host)
    except InsecureBindError as exc:
        raise LicenseServerError(str(exc)) from exc
    state = LicenseServerState(registry_path=config.registry_path)
    state.load()
    handler = _build_handler(state)
    server = ThreadingHTTPServer((config.host, config.port), handler)
    log_event("info", "license_server_started", host=config.host, port=config.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _build_handler(state: LicenseServerState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            del format, args

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._json(200, {"status": "ok", "service": "forgebench-license"})
                return
            self._json(404, {"error": "not_found"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path not in {"/v1/license/validate", "/v1/license/activate"}:
                self._json(404, {"error": "not_found"})
                return
            try:
                length = parse_content_length(self.headers.get("Content-Length"))
                raw = read_bounded_body(self.rfile, length)
                body = json.loads(raw.decode("utf-8"))
            except (HTTPBodyTooLargeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                self._json(400, {"error": str(exc)})
                return
            if not isinstance(body, dict):
                self._json(400, {"error": "body must be a JSON object"})
                return
            key = str(body.get("key") or "")
            machine = str(body.get("machine_id") or "")
            if not key:
                self._json(400, {"error": "key is required"})
                return
            result = state.validate_activation(key, machine)
            status = 200 if result.get("valid") else 403
            self._json(status, result)

        def _json(self, status: int, payload: dict[str, Any]) -> None:
            data = json.dumps(payload, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler