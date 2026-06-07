from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import shutil

from forgebench.adoption import record_milestone
from forgebench.crm.onboarding import format_welcome_sequence
from forgebench.licensing.keys import generate_license_key
from forgebench.presets import PresetError, PresetInfo


PARTNER_ROOT = Path(__file__).resolve().parents[2] / "examples" / "design-partner"
PRIVATE_PRESETS_ROOT = PARTNER_ROOT / "private-presets"
PILOT_KEYS_PATH = PARTNER_ROOT / "pilot-license-keys.json"
DESIGN_PARTNER_DISCUSSION_HINT = "github.com/caissonhq/forgebench/discussions/new?category=general"
DESIGN_PARTNER_LABEL = "design-partner"
PRIORITY_SUPPORT_EMAIL = "hello@forgebench.dev"


@dataclass(frozen=True)
class PartnerOnboardingKit:
    organization: str
    contact_email: str
    tier: str
    seats: int
    license_key: str
    welcome_email: str
    welcome_sequence: str
    support_process: str
    preset_names: list[str]
    feedback_channel: str
    kit_path: Path | None = None


def partner_presets_root() -> Path:
    return PRIVATE_PRESETS_ROOT


def list_partner_presets() -> list[PresetInfo]:
    root = partner_presets_root()
    if not root.is_dir():
        return []
    items: list[PresetInfo] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        manifest = entry / "preset.json"
        if not manifest.exists():
            continue
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        items.append(
            PresetInfo(
                name=entry.name,
                title=str(payload.get("title") or entry.name),
                description=str(payload.get("description") or ""),
                stack=str(payload.get("stack") or "generic"),
                path=entry,
            )
        )
    return items


def install_partner_preset(name: str, *, repo_path: str | Path = ".", force: bool = False) -> Path:
    normalized = name.strip().lower()
    preset = next((item for item in list_partner_presets() if item.name == normalized), None)
    if preset is None:
        available = ", ".join(item.name for item in list_partner_presets()) or "(none bundled)"
        raise PresetError(f"unknown partner preset: {name}. Available: {available}")

    repo = Path(repo_path).resolve()
    if not repo.is_dir():
        raise PresetError(f"repo path does not exist: {repo}")

    target = repo / "forgebench.yml"
    source = preset.path / "forgebench.yml"
    if not source.exists():
        raise PresetError(f"preset missing forgebench.yml: {source}")
    if target.exists() and not force:
        raise PresetError(f"refusing to overwrite {target}. Re-run with --force.")

    shutil.copy2(source, target)
    extras = preset.path / "extras"
    if extras.is_dir():
        for item in extras.rglob("*"):
            if item.is_file():
                rel = item.relative_to(extras)
                dest = repo / rel
                if dest.exists() and not force:
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)

    record_milestone("first_preset_installed")
    return target


def format_welcome_email(
    *,
    organization: str = "",
    contact_name: str = "",
    tier: str = "team",
    seats: int = 10,
    license_key: str = "",
) -> str:
    org = organization.strip() or "your team"
    name = contact_name.strip() or "there"
    key_line = license_key.strip() or "FB-TEAM-<your-pilot-key>"
    return "\n".join(
        [
            f"Subject: Welcome to the ForgeBench Design Partner program — {org}",
            "",
            f"Hi {name},",
            "",
            f"Welcome to the ForgeBench Design Partner program. We're excited to work with {org} "
            "as you ship AI-assisted code with merge-risk guardrails.",
            "",
            "Your pilot includes:",
            f"  • {tier.title()} tier access ({seats} seats) — 50% discount through pilot end",
            "  • Priority support (hello@forgebench.dev, <4h response during business hours)",
            "  • Private guardrail presets tuned for agent PR workflows",
            "  • Direct roadmap input — your feedback shapes v1.x priorities",
            "",
            "Day 0 — Activate your license:",
            f"  forgebench license activate {key_line}",
            "  forgebench license status",
            "",
            "Day 1 — Guided setup:",
            "  forgebench partner onboard --organization \"" + org + "\"",
            "  forgebench team init --yes",
            "",
            "Private feedback channel:",
            f"  GitHub Discussions (label: {DESIGN_PARTNER_LABEL})",
            f"  {DESIGN_PARTNER_DISCUSSION_HINT}",
            "",
            "We're here for white-glove onboarding. Reply to this email or book a 30-min kickoff.",
            "",
            "— The ForgeBench team",
            "",
            "ForgeBench does not prove code is safe.",
        ]
    )


def format_priority_support_process() -> str:
    return "\n".join(
        [
            "Design Partner — Priority Support Process",
            "",
            "Channels (in order):",
            f"  1. Email: {PRIORITY_SUPPORT_EMAIL} (subject: [Design Partner] <org>)",
            f"  2. GitHub Discussions with label `{DESIGN_PARTNER_LABEL}`",
            "  3. Weekly 30-min sync (optional) — calendar link in welcome email",
            "",
            "SLA (business hours, Mon–Fri):",
            "  • P0 (CI blocked / false BLOCK on main): <4 hours",
            "  • P1 (guardrail tuning, preset help): <1 business day",
            "  • P2 (feature requests, roadmap input): weekly digest",
            "",
            "Escalation:",
            "  • Include `forgebench doctor --checklist` output",
            "  • Attach anonymized report: `forgebench share-report`",
            "  • False positives: `forgebench feedback --paid` structured export",
            "",
            "What we need from you:",
            "  • Weekly async update (5 min) via `forgebench feedback digest`",
            "  • Dismissed findings with `--kind` for calibration",
            "  • Optional success story: `forgebench feedback --share`",
        ]
    )


def build_partner_onboarding_kit(
    *,
    organization: str,
    contact_email: str = "",
    tier: str = "team",
    seats: int = 10,
    license_key: str | None = None,
    output_dir: str | Path | None = None,
) -> PartnerOnboardingKit:
    org = organization.strip()
    if not org:
        raise ValueError("organization is required for design partner onboarding.")
    key = license_key or _next_pilot_license_key(organization=org, tier=tier, seats=seats)
    welcome_email = format_welcome_email(
        organization=org,
        tier=tier,
        seats=seats,
        license_key=key,
    )
    welcome_sequence = format_welcome_sequence(organization=org, tier=tier)
    support_process = format_priority_support_process()
    preset_names = [item.name for item in list_partner_presets()]
    kit_path: Path | None = None
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        kit_payload: dict[str, Any] = {
            "schema_version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "organization": org,
            "contact_email": contact_email,
            "tier": tier,
            "seats": seats,
            "license_key": key,
            "preset_names": preset_names,
            "feedback_channel": f"GitHub Discussions · label `{DESIGN_PARTNER_LABEL}`",
            "files": {},
        }
        for filename, content in (
            ("welcome-email.txt", welcome_email),
            ("welcome-sequence.txt", welcome_sequence),
            ("priority-support.txt", support_process),
            ("license-key.txt", key + "\n"),
        ):
            path = out / filename
            path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
            kit_payload["files"][filename] = str(path)
        manifest = out / "partner-kit.json"
        manifest.write_text(json.dumps(kit_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        kit_payload["files"]["partner-kit.json"] = str(manifest)
        kit_path = out
    return PartnerOnboardingKit(
        organization=org,
        contact_email=contact_email,
        tier=tier,
        seats=seats,
        license_key=key,
        welcome_email=welcome_email,
        welcome_sequence=welcome_sequence,
        support_process=support_process,
        preset_names=preset_names,
        feedback_channel=f"GitHub Discussions · label `{DESIGN_PARTNER_LABEL}`",
        kit_path=kit_path,
    )


def format_onboard_guided_flow(
    *,
    organization: str = "",
    contact_email: str = "",
    tier: str = "team",
    seats: int = 10,
) -> str:
    org = organization.strip() or "Your Team"
    lines = [
        "ForgeBench Design Partner — Guided Onboarding",
        "",
        f"Organization: {org}",
        f"Tier: {tier.title()} · Seats: {seats}",
        "",
        "Step 1 — Activate pilot license",
        "  forgebench license activate <KEY from welcome email>",
        "  forgebench license status",
        "",
        "Step 2 — Install private preset (agent-PR tuned guardrails)",
        "  forgebench partner presets list",
        "  forgebench partner presets install agent-pr-strict",
        "",
        "Step 3 — Team kit + CI",
        "  forgebench team init --yes --org-name \"" + org + "\"",
        "  forgebench review-pr <PR_URL> --checkout-pr --run-checks",
        "",
        "Step 4 — Join private feedback channel",
        f"  Post in GitHub Discussions with label `{DESIGN_PARTNER_LABEL}`",
        f"  {DESIGN_PARTNER_DISCUSSION_HINT}",
        "",
        "Step 5 — Weekly check-in",
        "  forgebench feedback digest --days 7",
        "  forgebench feedback --paid  # structured prompts for paid pilots",
        "",
        "Step 6 — Share wins",
        "  forgebench feedback --share",
        "  forgebench share-report --out forgebench-output",
        "",
        "Priority support:",
        f"  {PRIORITY_SUPPORT_EMAIL}",
        "",
        "Export full kit:",
        f"  forgebench partner onboard --organization \"{org}\" --email \"{contact_email or 'you@company.com'}\" --out forgebench-output/partner-kit",
    ]
    if contact_email.strip():
        lines.insert(3, f"Contact: {contact_email.strip()}")
    return "\n".join(lines)


def load_pilot_license_keys() -> list[dict[str, Any]]:
    if not PILOT_KEYS_PATH.exists():
        return []
    try:
        payload = json.loads(PILOT_KEYS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    keys = payload.get("keys") if isinstance(payload, dict) else None
    return [item for item in keys if isinstance(item, dict)] if isinstance(keys, list) else []


def _next_pilot_license_key(*, organization: str, tier: str, seats: int) -> str:
    for entry in load_pilot_license_keys():
        if not entry.get("assigned") and str(entry.get("organization") or "").strip().lower() in {"", "unassigned"}:
            return str(entry.get("key") or "")
    return generate_license_key(tier=tier, organization=organization, seats=seats)