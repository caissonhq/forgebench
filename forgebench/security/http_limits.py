from __future__ import annotations

import ipaddress
import os
import socket
from typing import IO


MAX_HTTP_BODY_BYTES = 5 * 1024 * 1024
MAX_MCP_BODY_BYTES = 10 * 1024 * 1024
INSECURE_BIND_ENV = "FORGEBENCH_ALLOW_INSECURE_BIND"


class HTTPBodyTooLargeError(ValueError):
    pass


class InsecureBindError(ValueError):
    pass


def read_bounded_body(stream: IO[bytes], content_length: int, *, max_bytes: int = MAX_HTTP_BODY_BYTES) -> bytes:
    if content_length < 0:
        raise HTTPBodyTooLargeError("Content-Length must be non-negative.")
    if content_length > max_bytes:
        raise HTTPBodyTooLargeError(f"Request body exceeds limit of {max_bytes} bytes.")
    raw = stream.read(content_length)
    if len(raw) != content_length:
        raise HTTPBodyTooLargeError("Request body shorter than Content-Length.")
    return raw


def parse_content_length(header_value: str | None, *, max_bytes: int = MAX_HTTP_BODY_BYTES) -> int:
    if not header_value:
        return 0
    try:
        length = int(header_value)
    except ValueError as exc:
        raise HTTPBodyTooLargeError("Invalid Content-Length header.") from exc
    if length > max_bytes:
        raise HTTPBodyTooLargeError(f"Request body exceeds limit of {max_bytes} bytes.")
    return max(0, length)


def enforce_loopback_or_explicit(host: str) -> None:
    normalized = (host or "").strip().lower()
    if normalized in {"127.0.0.1", "localhost", "::1"}:
        return
    if os.environ.get(INSECURE_BIND_ENV, "").strip().lower() in {"1", "true", "yes", "on"}:
        return
    try:
        addr = ipaddress.ip_address(normalized)
    except ValueError:
        if normalized == "0.0.0.0":
            raise InsecureBindError(
                "Binding to 0.0.0.0 requires FORGEBENCH_ALLOW_INSECURE_BIND=1. "
                "Use 127.0.0.1 for local-only services."
            ) from None
        # Hostname bind — resolve and require all addresses loopback
        infos = socket.getaddrinfo(normalized, None)
        for info in infos:
            ip = ipaddress.ip_address(info[4][0])
            if not ip.is_loopback:
                raise InsecureBindError(
                    f"Binding to non-loopback host '{host}' requires {INSECURE_BIND_ENV}=1."
                )
        return
    if not addr.is_loopback:
        raise InsecureBindError(
            f"Binding to non-loopback host '{host}' requires {INSECURE_BIND_ENV}=1."
        )