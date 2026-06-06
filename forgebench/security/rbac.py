from __future__ import annotations

import os
from enum import Enum


POLICY_READONLY_TOKEN_ENV = "FORGEBENCH_POLICY_READONLY_TOKEN"
POLICY_ADMIN_TOKEN_ENV = "FORGEBENCH_POLICY_ADMIN_TOKEN"


class PolicyServiceRole(str, Enum):
    ANONYMOUS = "anonymous"
    READONLY = "readonly"
    ADMIN = "admin"


class PolicyAuthorizationError(PermissionError):
    pass


def resolve_policy_tokens() -> tuple[str | None, str | None]:
    readonly = os.environ.get(POLICY_READONLY_TOKEN_ENV, "").strip() or None
    admin = os.environ.get(POLICY_ADMIN_TOKEN_ENV, "").strip() or None
    return readonly, admin


def authorize_policy_request(
    authorization_header: str | None,
    *,
    required_role: PolicyServiceRole,
) -> PolicyServiceRole:
    readonly, admin = resolve_policy_tokens()
    if not readonly and not admin:
        if required_role == PolicyServiceRole.ANONYMOUS:
            return PolicyServiceRole.ANONYMOUS
        # Local loopback services without tokens remain open for dev; callers on
        # non-loopback binds must configure tokens (enforced at serve startup).
        return PolicyServiceRole.ADMIN

    token = _extract_bearer(authorization_header)
    if admin and token == admin:
        return PolicyServiceRole.ADMIN
    if readonly and token == readonly:
        if required_role == PolicyServiceRole.ADMIN:
            raise PolicyAuthorizationError("Admin token required for this operation.")
        return PolicyServiceRole.READONLY
    raise PolicyAuthorizationError("Invalid or missing policy service token.")


def _extract_bearer(header: str | None) -> str | None:
    if not header:
        return None
    parts = header.strip().split(None, 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None