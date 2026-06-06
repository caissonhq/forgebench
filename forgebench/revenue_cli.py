from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from pathlib import Path

from forgebench.billing.config import hosted_portal_url
from forgebench.billing.stripe_checkout import StripeCheckoutError, build_checkout_url
from forgebench.billing.upgrade import format_upgrade_prompt, tier_comparison_summary
from forgebench.billing.webhooks import StripeWebhookServerConfig, serve_stripe_webhook
from forgebench.crm.onboarding import (
    build_paid_customer_checklist,
    design_partner_conversion_flow,
    format_paid_customer_checklist,
    format_welcome_sequence,
)
from forgebench.crm.pipeline import PipelineStage, format_pipeline_summary, upsert_pipeline_entry
from forgebench.licensing.server import LicenseServerConfig, serve_license_server
from forgebench.portal.dashboard import export_customer_portal
from forgebench.ux.output import heading, info, success


def add_subscribe_subparser(subparsers: argparse._SubParsersAction) -> None:
    subscribe = subparsers.add_parser("subscribe", help="Start Team or Enterprise checkout.")
    subscribe.add_argument("tier", nargs="?", choices=["team", "enterprise"], default="team")
    subscribe.add_argument("--seats", type=int, default=5, help="Seat count for Team subscription.")
    subscribe.add_argument("--email", required=False, help="Customer email for Stripe checkout.")
    subscribe.add_argument("--open", action="store_true", help="Open checkout URL in browser.")
    subscribe.add_argument("--json", action="store_true", help="Emit JSON.")


def add_upgrade_subparser(subparsers: argparse._SubParsersAction) -> None:
    upgrade = subparsers.add_parser("upgrade", help="Show upgrade path and tier comparison.")
    upgrade.add_argument("--tier", choices=["team", "enterprise"], default="team")
    upgrade.add_argument("--feature", required=False, help="Feature that triggered upgrade interest.")
    upgrade.add_argument("--open", action="store_true", help="Open checkout after showing plan.")


def add_portal_subparser(subparsers: argparse._SubParsersAction) -> None:
    portal = subparsers.add_parser("portal", help="Export or open the customer portal dashboard.")
    portal.add_argument("--out", required=False, default="forgebench-output/portal", help="Output directory.")
    portal.add_argument("--open", action="store_true", help="Open exported portal in browser.")
    portal.add_argument("--hosted", action="store_true", help="Open hosted portal URL.")


def add_crm_subparser(subparsers: argparse._SubParsersAction) -> None:
    crm = subparsers.add_parser("crm", help="Local customer pipeline tracking.")
    crm_sub = crm.add_subparsers(dest="crm_action")
    crm_sub.add_parser("list", help="List pipeline entries.")
    add = crm_sub.add_parser("add", help="Add or update a pipeline entry.")
    add.add_argument("organization", help="Organization or contact name.")
    add.add_argument("--stage", choices=[stage.value for stage in PipelineStage], default=PipelineStage.LEAD.value)
    add.add_argument("--tier", default="team")
    add.add_argument("--seats", type=int, default=5)
    convert = crm_sub.add_parser("convert", help="Design partner conversion checklist.")
    welcome = crm_sub.add_parser("welcome", help="Print paid customer welcome sequence.")
    welcome.add_argument("--organization", default="")
    welcome.add_argument("--tier", default="team")
    checklist = crm_sub.add_parser("checklist", help="Paid customer onboarding checklist.")


def add_billing_serve_subparser(subparsers: argparse._SubParsersAction) -> None:
    serve = subparsers.add_parser("billing-serve", help="Run self-hosted license or Stripe webhook servers.")
    serve_sub = serve.add_subparsers(dest="billing_serve_action")
    license_srv = serve_sub.add_parser("license", help="License validation server.")
    license_srv.add_argument("--host", default="127.0.0.1")
    license_srv.add_argument("--port", type=int, default=8793)
    license_srv.add_argument("--registry", default="forgebench-output/license-server/registry.json")
    stripe_srv = serve_sub.add_parser("stripe-webhook", help="Stripe webhook receiver.")
    stripe_srv.add_argument("--host", default="127.0.0.1")
    stripe_srv.add_argument("--port", type=int, default=8794)


def run_subscribe_command(args: argparse.Namespace) -> int:
    try:
        session = build_checkout_url(tier=args.tier, seats=args.seats, customer_email=args.email or "")
    except StripeCheckoutError as exc:
        print(f"ForgeBench subscribe error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(
            json.dumps(
                {
                    "tier": session.tier,
                    "seats": session.seats,
                    "mode": session.mode,
                    "url": session.url,
                    "session_id": session.session_id,
                    "message": session.message,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        heading(f"ForgeBench {session.tier.title()} checkout")
        info(session.message)
        print(session.url)
        if session.session_id:
            info(f"Session: {session.session_id}")
    if args.open:
        webbrowser.open(session.url)
    return 0


def run_upgrade_command(args: argparse.Namespace) -> int:
    if args.feature:
        print(format_upgrade_prompt(args.feature))
    else:
        print(tier_comparison_summary())
        print("")
        print(format_upgrade_prompt("init_enterprise"))
    if args.open:
        session = build_checkout_url(tier=args.tier, seats=5)
        print("")
        print(session.url)
        webbrowser.open(session.url)
    return 0


def run_portal_command(args: argparse.Namespace) -> int:
    if args.hosted:
        url = hosted_portal_url()
        print(url)
        if args.open:
            webbrowser.open(url)
        return 0
    result = export_customer_portal(output_dir=args.out)
    success(f"Customer portal exported to {result.index_path}")
    info(f"Manifest: {result.manifest_path}")
    if args.open:
        webbrowser.open(result.index_path.resolve().as_uri())
    return 0


def run_crm_command(args: argparse.Namespace) -> int:
    action = args.crm_action
    if action == "list":
        print(format_pipeline_summary())
        return 0
    if action == "add":
        entry = upsert_pipeline_entry(
            organization=args.organization,
            stage=args.stage,
            tier=args.tier,
            seats=args.seats,
            source="cli",
        )
        success(f"Pipeline updated: {entry.organization} → {entry.stage}")
        return 0
    if action == "convert":
        print(design_partner_conversion_flow())
        return 0
    if action == "welcome":
        print(format_welcome_sequence(organization=args.organization, tier=args.tier))
        return 0
    if action == "checklist":
        print(format_paid_customer_checklist(build_paid_customer_checklist()))
        return 0
    print("crm requires list, add, convert, welcome, or checklist.", file=sys.stderr)
    return 2


def run_billing_serve_command(args: argparse.Namespace) -> int:
    action = args.billing_serve_action
    if action == "license":
        serve_license_server(
            LicenseServerConfig(
                host=args.host,
                port=args.port,
                registry_path=Path(args.registry),
            )
        )
        return 0
    if action == "stripe-webhook":
        serve_stripe_webhook(StripeWebhookServerConfig(host=args.host, port=args.port))
        return 0
    print("billing-serve requires license or stripe-webhook.", file=sys.stderr)
    return 2