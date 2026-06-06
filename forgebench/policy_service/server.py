from __future__ import annotations

import json
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from forgebench.audit_chain import record_tamper_evident_event
from forgebench.fpl.compiler import compile_fpl_text
from forgebench.guardrails import GuardrailsParseError, parse_guardrails
from forgebench.observability.logging import log_event
from forgebench.policy_simulation import simulate_policy
from forgebench.policy_versioning import load_policy_text_fingerprint
from forgebench.security.http_limits import (
    HTTPBodyTooLargeError,
    InsecureBindError,
    enforce_loopback_or_explicit,
    parse_content_length,
    read_bounded_body,
)
from forgebench.security.path_confinement import PathConfinementError, assert_path_within_root
from forgebench.security.rbac import PolicyAuthorizationError, PolicyServiceRole, authorize_policy_request
from forgebench.validate import validate_guardrails_file

MAX_FPL_SOURCE_BYTES = 512 * 1024


@dataclass(frozen=True)
class PolicyServiceConfig:
    host: str = "127.0.0.1"
    port: int = 8791
    repo_path: Path = Path(".")
    guardrails_path: Path | None = None
    require_tokens_on_public_bind: bool = True


class PolicyServiceError(ValueError):
    pass


def serve_policy_service(config: PolicyServiceConfig) -> None:
    try:
        enforce_loopback_or_explicit(config.host)
    except InsecureBindError as exc:
        raise PolicyServiceError(str(exc)) from exc
    handler = _build_handler(config)
    server = ThreadingHTTPServer((config.host, config.port), handler)
    record_tamper_evident_event(
        "policy_served",
        payload={"host": config.host, "port": config.port, "repo": str(config.repo_path)},
    )
    log_event("info", "policy_service_started", host=config.host, port=config.port)
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
            try:
                role = authorize_policy_request(
                    self.headers.get("Authorization"),
                    required_role=PolicyServiceRole.READONLY,
                )
            except PolicyAuthorizationError as exc:
                self._json_response(401, {"error": str(exc)})
                return
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                self._json_response(200, {"status": "ok", "service": "forgebench-policy"})
                return
            if parsed.path == "/v1/policy":
                self._handle_get_policy(role)
                return
            self._json_response(404, {"error": "not_found"})

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/v1/policy/validate":
                    role = authorize_policy_request(
                        self.headers.get("Authorization"),
                        required_role=PolicyServiceRole.ADMIN,
                    )
                    self._handle_validate(role)
                    return
                if parsed.path == "/v1/policy/simulate":
                    role = authorize_policy_request(
                        self.headers.get("Authorization"),
                        required_role=PolicyServiceRole.ADMIN,
                    )
                    self._handle_simulate(role)
                    return
                if parsed.path == "/v1/policy/compile-fpl":
                    role = authorize_policy_request(
                        self.headers.get("Authorization"),
                        required_role=PolicyServiceRole.ADMIN,
                    )
                    self._handle_compile_fpl(role)
                    return
            except PolicyAuthorizationError as exc:
                self._json_response(401, {"error": str(exc)})
                return
            self._json_response(404, {"error": "not_found"})

        def _handle_get_policy(self, role: PolicyServiceRole) -> None:
            guardrails_file = _resolve_guardrails(config)
            text = guardrails_file.read_text(encoding="utf-8", errors="replace")
            record_tamper_evident_event(
                "policy_served",
                payload={"path": str(guardrails_file), "role": role.value, "operation": "get_policy"},
            )
            self._json_response(
                200,
                {
                    "path": str(guardrails_file),
                    "fingerprint": load_policy_text_fingerprint(text),
                    "content": text,
                },
            )

        def _handle_validate(self, role: PolicyServiceRole) -> None:
            payload = self._read_json_body()
            if payload is None:
                return
            path_value = payload.get("path")
            if not isinstance(path_value, str):
                self._json_response(400, {"error": "path is required"})
                return
            try:
                confined = _confine_service_path(config, path_value)
            except PolicyServiceError as exc:
                self._json_response(400, {"error": str(exc)})
                return
            report = validate_guardrails_file(confined, strict=bool(payload.get("strict")))
            record_tamper_evident_event(
                "policy_served",
                payload={"path": str(confined), "role": role.value, "operation": "validate"},
            )
            self._json_response(
                200,
                {
                    "valid": report.valid,
                    "error_count": report.error_count,
                    "warning_count": report.warning_count,
                    "issues": [issue.format() for issue in report.issues],
                },
            )

        def _handle_simulate(self, role: PolicyServiceRole) -> None:
            payload = self._read_json_body()
            if payload is None:
                return
            try:
                diff_path = _confine_service_path(config, payload["diff"])
                guardrails_value = payload.get("guardrails") or _resolve_guardrails(config)
                guardrails_path = (
                    _confine_service_path(config, guardrails_value)
                    if isinstance(guardrails_value, str)
                    else guardrails_value
                )
                repo_path = (
                    _confine_service_path(config, payload.get("repo") or ".")
                    if isinstance(payload.get("repo"), str)
                    else config.repo_path.resolve()
                )
                result = simulate_policy(
                    repo_path=repo_path,
                    diff_path=diff_path,
                    guardrails_path=guardrails_path,
                )
            except (KeyError, TypeError, OSError, ValueError, PolicyServiceError) as exc:
                self._json_response(400, {"error": str(exc)})
                return
            record_tamper_evident_event(
                "policy_simulated",
                payload={"role": role.value, "posture": result.posture.value},
            )
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

        def _handle_compile_fpl(self, role: PolicyServiceRole) -> None:
            payload = self._read_json_body()
            if payload is None:
                return
            source = payload.get("source")
            if not isinstance(source, str) or not source.strip():
                self._json_response(400, {"error": "source is required"})
                return
            if len(source.encode("utf-8")) > MAX_FPL_SOURCE_BYTES:
                self._json_response(413, {"error": "FPL source exceeds size limit"})
                return
            try:
                compiled = compile_fpl_text(source)
            except (GuardrailsParseError, ValueError) as exc:
                self._json_response(400, {"error": str(exc)})
                return
            record_tamper_evident_event(
                "policy_compiled",
                payload={"role": role.value, "fpl_name": compiled.get("fpl_name")},
            )
            self._json_response(200, compiled)

        def _read_json_body(self) -> dict[str, Any] | None:
            try:
                length = parse_content_length(self.headers.get("Content-Length"))
                raw = read_bounded_body(self.rfile, length)
            except HTTPBodyTooLargeError as exc:
                self._json_response(413, {"error": str(exc)})
                return None
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
        return config.guardrails_path.resolve()
    candidate = config.repo_path / "forgebench.yml"
    if candidate.exists():
        return candidate.resolve()
    raise PolicyServiceError("No guardrails file configured for policy service.")


def _confine_service_path(config: PolicyServiceConfig, raw: str | Path) -> Path:
    root = config.repo_path.resolve()
    try:
        return assert_path_within_root(Path(raw), root)
    except PathConfinementError as exc:
        raise PolicyServiceError(str(exc)) from exc