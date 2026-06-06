from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from forgebench.fpl.compiler import compile_fpl_text
from forgebench.guardrails import GuardrailsParseError, parse_guardrails
from forgebench.policy_audit import record_policy_audit_event
from forgebench.policy_simulation import simulate_policy
from forgebench.policy_versioning import load_policy_text_fingerprint
from forgebench.validate import validate_guardrails_file


@dataclass(frozen=True)
class PolicyServiceConfig:
    host: str = "127.0.0.1"
    port: int = 8791
    repo_path: Path = Path(".")
    guardrails_path: Path | None = None


class PolicyServiceError(ValueError):
    pass


def serve_policy_service(config: PolicyServiceConfig) -> None:
    handler = _build_handler(config)
    server = ThreadingHTTPServer((config.host, config.port), handler)
    record_policy_audit_event(
        "policy_served",
        payload={"host": config.host, "port": config.port, "repo": str(config.repo_path)},
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _build_handler(config: PolicyServiceConfig):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            del format, args

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._json_response(200, {"status": "ok", "service": "forgebench-policy"})
                return
            if parsed.path == "/v1/policy":
                self._handle_get_policy()
                return
            self._json_response(404, {"error": "not_found"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/v1/policy/validate":
                self._handle_validate()
                return
            if parsed.path == "/v1/policy/simulate":
                self._handle_simulate()
                return
            if parsed.path == "/v1/policy/compile-fpl":
                self._handle_compile_fpl()
                return
            self._json_response(404, {"error": "not_found"})

        def _handle_get_policy(self) -> None:
            guardrails_file = _resolve_guardrails(config)
            text = guardrails_file.read_text(encoding="utf-8", errors="replace")
            self._json_response(
                200,
                {
                    "path": str(guardrails_file),
                    "fingerprint": load_policy_text_fingerprint(text),
                    "content": text,
                },
            )

        def _handle_validate(self) -> None:
            payload = self._read_json_body()
            if payload is None:
                return
            path_value = payload.get("path")
            if not isinstance(path_value, str):
                self._json_response(400, {"error": "path is required"})
                return
            report = validate_guardrails_file(path_value, strict=bool(payload.get("strict")))
            self._json_response(
                200,
                {
                    "valid": report.valid,
                    "error_count": report.error_count,
                    "warning_count": report.warning_count,
                    "issues": [issue.format() for issue in report.issues],
                },
            )

        def _handle_simulate(self) -> None:
            payload = self._read_json_body()
            if payload is None:
                return
            try:
                result = simulate_policy(
                    repo_path=payload.get("repo") or config.repo_path,
                    diff_path=payload["diff"],
                    guardrails_path=payload.get("guardrails") or _resolve_guardrails(config),
                )
            except (KeyError, TypeError, OSError, ValueError) as exc:
                self._json_response(400, {"error": str(exc)})
                return
            self._json_response(
                200,
                {
                    "posture": result.posture.value,
                    "findings": result.findings,
                    "suppressed_findings": result.suppressed_findings,
                    "active_categories": result.active_categories,
                    "posture_ceiling": result.posture_ceiling,
                    "formal_violations": result.formal_violations,
                },
            )

        def _handle_compile_fpl(self) -> None:
            payload = self._read_json_body()
            if payload is None:
                return
            source = payload.get("source")
            if not isinstance(source, str) or not source.strip():
                self._json_response(400, {"error": "source is required"})
                return
            try:
                compiled = compile_fpl_text(source)
            except (GuardrailsParseError, ValueError) as exc:
                self._json_response(400, {"error": str(exc)})
                return
            self._json_response(200, compiled)

        def _read_json_body(self) -> dict[str, Any] | None:
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                self._json_response(400, {"error": "invalid_json"})
                return None
            if not isinstance(payload, dict):
                self._json_response(400, {"error": "json_object_required"})
                return None
            return payload

        def _json_response(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def _resolve_guardrails(config: PolicyServiceConfig) -> Path:
    if config.guardrails_path is not None:
        return config.guardrails_path
    candidate = config.repo_path / "forgebench.yml"
    if candidate.exists():
        return candidate
    raise PolicyServiceError("No guardrails file configured for policy service.")