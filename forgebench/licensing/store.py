from __future__ import annotations

import hashlib
import json
import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forgebench.licensing.keys import LicenseError, verify_license_key
from forgebench.licensing.tiers import LicenseTier, parse_tier, tier_at_least


LICENSE_ENV = "FORGEBENCH_LICENSE_PATH"
DEFAULT_LICENSE_PATH = Path.home() / ".config" / "forgebench" / "license.json"
FALLBACK_LICENSE_PATH = Path("forgebench-output") / "license.json"


class LicenseStoreError(LicenseError):
    pass


@dataclass(frozen=True)
class LicenseRecord:
    tier: LicenseTier
    organization: str
    seats: int
    expires_at: str
    license_id: str
    activated_at: str
    machine_id: str
    activations: list[str]
    features: list[str]
    valid: bool
    message: str


def license_path() -> Path:
    override = os.environ.get(LICENSE_ENV, "").strip()
    if override:
        return Path(override)
    if DEFAULT_LICENSE_PATH.exists():
        return DEFAULT_LICENSE_PATH
    return FALLBACK_LICENSE_PATH


def machine_id() -> str:
    seed = f"{platform.node()}:{platform.system()}:{os.getenv('USER', '')}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def load_license(*, path: str | Path | None = None) -> LicenseRecord:
    target = Path(path) if path else license_path()
    if not target.exists():
        return _free_record("No license activated; using Free tier.")
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return _free_record(f"License file unreadable: {exc}")
    if not isinstance(payload, dict):
        return _free_record("License file is malformed.")
    key = str(payload.get("key") or "")
    if not key:
        return _free_record("License file missing key.")
    try:
        verified = verify_license_key(key)
    except LicenseError as exc:
        return _free_record(str(exc))
    activations = [str(item) for item in payload.get("activations") or []]
    current_machine = str(payload.get("machine_id") or machine_id())
    if current_machine not in activations:
        activations.append(current_machine)
    if verified.tier != LicenseTier.ENTERPRISE and len(activations) > verified.seats:
        return LicenseRecord(
            tier=verified.tier,
            organization=verified.organization,
            seats=verified.seats,
            expires_at=verified.expires_at,
            license_id=verified.license_id,
            activated_at=str(payload.get("activated_at") or ""),
            machine_id=current_machine,
            activations=activations,
            features=verified.features,
            valid=False,
            message=f"Seat limit exceeded ({len(activations)}/{verified.seats}).",
        )
    return LicenseRecord(
        tier=verified.tier,
        organization=verified.organization,
        seats=verified.seats,
        expires_at=verified.expires_at,
        license_id=verified.license_id,
        activated_at=str(payload.get("activated_at") or ""),
        machine_id=current_machine,
        activations=activations,
        features=verified.features,
        valid=True,
        message="License valid.",
    )


def save_license(payload: dict[str, Any], *, path: str | Path | None = None) -> Path:
    target = Path(path) if path else license_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def activate_and_store(key: str, *, path: str | Path | None = None) -> LicenseRecord:
    from forgebench.licensing.keys import activate_license_key

    current = machine_id()
    target = Path(path) if path else license_path()
    existing_activations: list[str] = []
    if target.exists():
        try:
            prior = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(prior, dict) and str(prior.get("license_id")) == verify_license_key(key).license_id:
                existing_activations = [str(item) for item in prior.get("activations") or []]
        except (json.JSONDecodeError, OSError, LicenseError):
            existing_activations = []
    payload = activate_license_key(key, machine_id=current)
    activations = list(dict.fromkeys(existing_activations + [current]))
    payload["activations"] = activations
    save_license(payload, path=target)
    return load_license(path=target)


def effective_tier(record: LicenseRecord | None = None) -> LicenseTier:
    current = record or load_license()
    if current.valid:
        return current.tier
    return LicenseTier.FREE


def has_feature(feature: str, *, record: LicenseRecord | None = None) -> bool:
    from forgebench.licensing.tiers import feature_requires_tier

    required = feature_requires_tier(feature)
    if required is None:
        return True
    tier = effective_tier(record)
    return tier_at_least(tier, required)


def _free_record(message: str) -> LicenseRecord:
    return LicenseRecord(
        tier=LicenseTier.FREE,
        organization="",
        seats=0,
        expires_at="",
        license_id="",
        activated_at="",
        machine_id=machine_id(),
        activations=[],
        features=[],
        valid=True,
        message=message,
    )


def format_license_status(record: LicenseRecord) -> str:
    tier_name = record.tier.name.lower() if record.valid else "free"
    lines = [
        "ForgeBench license status",
        f"Tier: {tier_name}",
        f"Valid: {'yes' if record.valid else 'no'}",
        f"Message: {record.message}",
    ]
    if record.organization:
        lines.append(f"Organization: {record.organization}")
    if record.seats:
        lines.append(f"Seats: {len(record.activations)}/{record.seats}")
    if record.expires_at:
        lines.append(f"Expires: {record.expires_at}")
    if record.license_id:
        lines.append(f"License ID: {record.license_id}")
    return "\n".join(lines) + "\n"