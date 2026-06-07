from __future__ import annotations

import argparse
import sys

from forgebench.partner.onboarding import (
    build_partner_onboarding_kit,
    format_onboard_guided_flow,
    format_priority_support_process,
    format_welcome_email,
    install_partner_preset,
    list_partner_presets,
    load_pilot_license_keys,
)
from forgebench.presets import PresetError, format_preset_list
from forgebench.ux.output import heading, info, success


def add_partner_subparser(subparsers: argparse._SubParsersAction) -> None:
    partner = subparsers.add_parser("partner", help="Design Partner program — onboarding kit and private presets.")
    partner_sub = partner.add_subparsers(dest="partner_action")
    onboard = partner_sub.add_parser("onboard", help="Guided design partner onboarding flow and kit export.")
    onboard.add_argument("--organization", required=False, default="", help="Partner organization name.")
    onboard.add_argument("--email", required=False, default="", help="Primary contact email.")
    onboard.add_argument("--tier", choices=["team", "enterprise"], default="team")
    onboard.add_argument("--seats", type=int, default=10)
    onboard.add_argument("--license-key", required=False, help="Pre-assigned pilot license key.")
    onboard.add_argument("--out", required=False, help="Export onboarding kit directory.")
    support = partner_sub.add_parser("support", help="Print priority support process for design partners.")
    keys = partner_sub.add_parser("keys", help="List pilot license keys (assigned status only).")
    presets = partner_sub.add_parser("presets", help="Private design-partner guardrail presets.")
    presets_sub = presets.add_subparsers(dest="partner_presets_action")
    presets_sub.add_parser("list", help="List private partner presets.")
    install = presets_sub.add_parser("install", help="Install a private partner preset.")
    install.add_argument("name", help="Preset name (e.g. agent-pr-strict).")
    install.add_argument("--repo", default=".", help="Repository path.")
    install.add_argument("--force", action="store_true", help="Overwrite existing forgebench.yml.")


def run_partner_command(args: argparse.Namespace) -> int:
    action = args.partner_action
    if action == "onboard":
        return _run_onboard(args)
    if action == "support":
        print(format_priority_support_process())
        return 0
    if action == "keys":
        return _run_keys()
    if action == "presets":
        return _run_presets(args)
    print("partner requires onboard, support, keys, or presets.", file=sys.stderr)
    return 2


def _run_onboard(args: argparse.Namespace) -> int:
    org = (args.organization or "").strip()
    if not org:
        print(format_onboard_guided_flow())
        info("Pass --organization to generate a personalized kit and welcome email.")
        return 0
    try:
        kit = build_partner_onboarding_kit(
            organization=org,
            contact_email=args.email or "",
            tier=args.tier,
            seats=args.seats,
            license_key=args.license_key,
            output_dir=args.out,
        )
        _record_partner_onboarded(kit.organization, kit.tier)
    except ValueError as exc:
        print(f"ForgeBench partner error: {exc}", file=sys.stderr)
        return 2
    heading(f"Design Partner onboarding — {kit.organization}")
    print(format_onboard_guided_flow(
        organization=kit.organization,
        contact_email=kit.contact_email,
        tier=kit.tier,
        seats=kit.seats,
    ))
    print("")
    print("--- Welcome email (copy to send) ---")
    print(kit.welcome_email)
    if kit.kit_path:
        success(f"Onboarding kit exported to {kit.kit_path}")
        info(f"License key: {kit.license_key[:24]}...")
    return 0


def _run_keys() -> int:
    keys = load_pilot_license_keys()
    if not keys:
        print("No pilot license keys found. See examples/design-partner/pilot-license-keys.json")
        return 0
    lines = ["Pilot license keys (delivery status):"]
    for entry in keys:
        org = str(entry.get("organization") or "unassigned")
        tier = str(entry.get("tier") or "team")
        assigned = "assigned" if entry.get("assigned") else "available"
        key_preview = str(entry.get("key") or "")[:28] + "..."
        lines.append(f"  [{assigned}] {org} · {tier} · {key_preview}")
    print("\n".join(lines))
    return 0


def _run_presets(args: argparse.Namespace) -> int:
    action = args.partner_presets_action
    if action == "list":
        items = list_partner_presets()
        if not items:
            print("No private partner presets bundled.")
            return 0
        print(format_preset_list(items).replace("Bundled presets:", "Design Partner presets (private):"))
        return 0
    if action == "install":
        try:
            path = install_partner_preset(args.name, repo_path=args.repo, force=args.force)
        except (PresetError, ValueError) as exc:
            print(f"ForgeBench partner error: {exc}", file=sys.stderr)
            return 2
        success(f"Partner preset '{args.name}' installed → {path}")
        return 0
    print("partner presets requires list or install.", file=sys.stderr)
    return 2


def _record_partner_onboarded(organization: str, tier: str) -> None:
    try:
        from forgebench.product_analytics import record_product_event

        record_product_event(
            "design_partner_onboarded",
            {"organization": organization, "tier": tier},
        )
    except Exception:
        pass