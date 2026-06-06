from __future__ import annotations

import argparse
import json
import sys

from forgebench.licensing.keys import LicenseError
from forgebench.licensing.quotas import export_quota_report
from forgebench.licensing.store import activate_and_store, format_license_status, license_path, load_license
from forgebench.licensing.tiers import TIER_FEATURES, LicenseTier
from forgebench.product_analytics import record_product_event


def add_license_subparser(subparsers: argparse._SubParsersAction) -> None:
    license_parser = subparsers.add_parser("license", help="Manage Team and Enterprise license keys.")
    license_sub = license_parser.add_subparsers(dest="license_action")
    activate = license_sub.add_parser("activate", help="Activate a license key for this machine.")
    activate.add_argument("key", help="ForgeBench license key (FB-TEAM-... or FB-ENTERPRISE-...).")
    activate.add_argument("--path", required=False, help="Optional license file path.")
    check = license_sub.add_parser("check", help="Validate the active license and optional feature access.")
    check.add_argument("--feature", required=False, help="Feature slug to verify (e.g. policy_serve).")
    check.add_argument("--json", action="store_true", help="Emit JSON.")
    status = license_sub.add_parser("status", help="Show license tier, seats, and expiry.")
    status.add_argument("--json", action="store_true", help="Emit JSON.")
    report = license_sub.add_parser("report", help="Export usage and quota report for customer success.")
    report.add_argument("--out", required=False, help="Output JSON path.")
    report.add_argument("--json", action="store_true", help="Print JSON to stdout.")


def run_license_command(args: argparse.Namespace) -> int:
    action = args.license_action
    if action == "activate":
        return _run_activate(args)
    if action == "check":
        return _run_check(args)
    if action == "status":
        return _run_status(args)
    if action == "report":
        return _run_report(args)
    print("license requires activate, check, status, or report.", file=sys.stderr)
    return 2


def _run_activate(args: argparse.Namespace) -> int:
    try:
        record = activate_and_store(args.key, path=args.path)
    except LicenseError as exc:
        print(f"ForgeBench license error: {exc}", file=sys.stderr)
        return 2
    record_product_event("license_activated", {"tier": record.tier.name.lower(), "valid": record.valid})
    try:
        from forgebench.adoption import record_milestone

        record_milestone("first_paid_feature")
    except Exception:
        pass
    print(format_license_status(record))
    print(f"License file: {license_path() if not args.path else args.path}")
    return 0 if record.valid else 2


def _run_check(args: argparse.Namespace) -> int:
    record = load_license()
    if args.feature:
        from forgebench.licensing.quotas import require_feature

        try:
            require_feature(args.feature, record=record)
            allowed = True
            message = f"Feature '{args.feature}' is allowed."
        except Exception as exc:
            allowed = False
            message = str(exc)
        payload = {
            "valid": record.valid,
            "tier": record.tier.name.lower(),
            "feature": args.feature,
            "allowed": allowed,
            "message": message,
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(message)
        return 0 if allowed else 2
    payload = _license_payload(record)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_license_status(record))
    return 0 if record.valid else 2


def _run_status(args: argparse.Namespace) -> int:
    record = load_license()
    payload = _license_payload(record)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_license_status(record))
        print("Features by tier: see docs/pricing.md")
    return 0


def _run_report(args: argparse.Namespace) -> int:
    from forgebench.product_analytics import export_product_analytics_bundle

    record = load_license()
    bundle = {
        "license": _license_payload(record),
        "quotas": export_quota_report(),
        "product_analytics": export_product_analytics_bundle(),
    }
    text = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
    if args.out:
        from pathlib import Path

        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"ForgeBench license report written to {output}.")
    elif args.json or not args.out:
        print(text, end="")
    record_product_event("license_report_exported", {"tier": record.tier.name.lower()})
    return 0


def _license_payload(record) -> dict[str, object]:
    return {
        "tier": record.tier.name.lower(),
        "valid": record.valid,
        "organization": record.organization,
        "seats": record.seats,
        "activations": len(record.activations),
        "expires_at": record.expires_at,
        "license_id": record.license_id,
        "message": record.message,
        "features": {
            tier.name.lower(): sorted(TIER_FEATURES[tier])
            for tier in (LicenseTier.FREE, LicenseTier.TEAM, LicenseTier.ENTERPRISE)
        },
    }