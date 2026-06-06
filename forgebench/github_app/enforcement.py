from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


VALID_POSTURES = {"BLOCK", "REVIEW", "LOW_CONCERN"}


class OrgEnforcementError(ValueError):
    pass


@dataclass(frozen=True)
class OrgEnforcementConfig:
    org_id: str
    policy_path: str
    block_on_posture: str = "BLOCK"
    require_review_on_posture: str = "REVIEW"
    allow_low_concern: bool = True
    required_policy_version: str | None = None
    audit_required: bool = True


@dataclass(frozen=True)
class OrgPolicyEnforcementResult:
    org_id: str
    posture: str
    allowed: bool
    check_conclusion: str
    violations: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    policy_fingerprint: str | None = None


def load_org_enforcement_config(path: str | Path) -> OrgEnforcementConfig:
    file_path = Path(path)
    if not file_path.exists():
        raise OrgEnforcementError(f"Org enforcement config not found: {file_path}")
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OrgEnforcementError(f"Invalid org enforcement JSON: {file_path}") from exc
    if not isinstance(payload, dict):
        raise OrgEnforcementError("Org enforcement config must be a JSON object.")
    org_id = str(payload.get("org_id") or "").strip()
    policy_path = str(payload.get("policy_path") or "").strip()
    if not org_id:
        raise OrgEnforcementError("org_id is required in org enforcement config.")
    if not policy_path:
        raise OrgEnforcementError("policy_path is required in org enforcement config.")
    rules = payload.get("rules") if isinstance(payload.get("rules"), dict) else {}
    return OrgEnforcementConfig(
        org_id=org_id,
        policy_path=policy_path,
        block_on_posture=str(rules.get("block_on_posture") or "BLOCK").upper(),
        require_review_on_posture=str(rules.get("require_review_on_posture") or "REVIEW").upper(),
        allow_low_concern=bool(rules.get("allow_low_concern", True)),
        required_policy_version=_optional_str(payload.get("required_policy_version")),
        audit_required=bool(payload.get("audit_required", True)),
    )


def enforce_org_policy(
    *,
    posture: str,
    config: OrgEnforcementConfig,
    policy_fingerprint: str | None = None,
    finding_count: int = 0,
) -> OrgPolicyEnforcementResult:
    normalized = posture.strip().upper()
    if normalized not in VALID_POSTURES:
        raise OrgEnforcementError(f"Unsupported posture for enforcement: {posture}")

    violations: list[str] = []
    recommendations: list[str] = []

    if normalized == config.block_on_posture:
        violations.append(f"ForgeBench posture is {normalized}; org policy blocks merge.")
        recommendations.append("Address BLOCK findings or request human exception with audit trail.")
    elif normalized == config.require_review_on_posture:
        recommendations.append("Human review required before merge per org policy.")
    elif normalized == "LOW_CONCERN" and not config.allow_low_concern:
        violations.append("LOW_CONCERN is not allowed by org policy for this repository.")

    if config.required_policy_version and not policy_fingerprint:
        violations.append("Policy fingerprint missing; cannot verify required policy version.")

    if finding_count > 0 and normalized == "LOW_CONCERN":
        recommendations.append("Findings present under LOW_CONCERN; confirm suppressions with policy tests.")

    allowed = not violations
    conclusion = "success" if allowed else "failure"
    if normalized == config.require_review_on_posture and allowed:
        conclusion = "neutral"

    return OrgPolicyEnforcementResult(
        org_id=config.org_id,
        posture=normalized,
        allowed=allowed,
        check_conclusion=conclusion,
        violations=violations,
        recommendations=recommendations,
        policy_fingerprint=policy_fingerprint,
    )


def enforcement_to_check_output(result: OrgPolicyEnforcementResult) -> dict[str, Any]:
    title = "ForgeBench org policy"
    if result.allowed and result.posture == "REVIEW":
        summary = "Human review required by org policy."
    elif result.allowed:
        summary = f"Org policy allows posture {result.posture}."
    else:
        summary = "Org policy enforcement failed."
    return {
        "name": title,
        "headline": summary,
        "conclusion": result.check_conclusion,
        "output": {
            "title": title,
            "summary": summary,
            "text": "\n".join(
                [
                    f"Posture: {result.posture}",
                    f"Org: {result.org_id}",
                    "",
                    "Violations:",
                    *([f"- {item}" for item in result.violations] or ["- none"]),
                    "",
                    "Recommendations:",
                    *([f"- {item}" for item in result.recommendations] or ["- none"]),
                ]
            ),
        },
    }


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None