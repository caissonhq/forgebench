from __future__ import annotations

import argparse
import json
import sys

from forgebench.analytics_dashboard import export_analytics_dashboard
from forgebench.licensing.quotas import LicenseRequired, require_feature
from forgebench.product_analytics import (
    disable_product_analytics,
    enable_product_analytics,
    export_product_analytics_bundle,
    product_analytics_status,
    record_product_event,
)


def add_analytics_subparser(subparsers: argparse._SubParsersAction) -> None:
    analytics = subparsers.add_parser(
        "analytics",
        help="Opt-in product adoption analytics (distinct from review telemetry).",
    )
    analytics_sub = analytics.add_subparsers(dest="analytics_action")
    enable = analytics_sub.add_parser("enable", help="Enable local product analytics.")
    enable.add_argument("--flag-path", required=False, help="Optional flag file path.")
    disable = analytics_sub.add_parser("disable", help="Disable product analytics.")
    disable.add_argument("--flag-path", required=False, help="Optional flag file path.")
    status = analytics_sub.add_parser("status", help="Show product analytics status.")
    export = analytics_sub.add_parser("export", help="Export product analytics JSON bundle.")
    export.add_argument("--out", required=False, help="Output JSON path.")
    dashboard = analytics_sub.add_parser("dashboard", help="Export self-hosted usage analytics HTML dashboard.")
    dashboard.add_argument("--out", required=False, default="forgebench-output/analytics-dashboard", help="Output directory.")
    dashboard.add_argument("--no-review-telemetry", action="store_true", help="Omit review telemetry section.")
    dashboard.add_argument("--cloud-export", action="store_true", help="Consume cloud export quota (Team+).")


def run_analytics_command(args: argparse.Namespace) -> int:
    action = args.analytics_action
    if action == "enable":
        path = enable_product_analytics(flag_path=args.flag_path)
        print("ForgeBench product analytics enabled (opt-in, local-only, adoption metrics).")
        print(f"Flag: {path}")
        print("Distinct from review telemetry (`forgebench telemetry`).")
        return 0
    if action == "disable":
        disable_product_analytics(flag_path=args.flag_path)
        print("ForgeBench product analytics disabled.")
        return 0
    if action == "status":
        print(json.dumps(product_analytics_status(), indent=2, sort_keys=True))
        return 0
    if action == "export":
        bundle = export_product_analytics_bundle()
        if args.out:
            from pathlib import Path

            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"Product analytics export written to {output}.")
        else:
            print(json.dumps(bundle, indent=2, sort_keys=True))
        return 0
    if action == "dashboard":
        if args.cloud_export:
            try:
                require_feature("analytics_cloud_export")
            except LicenseRequired as exc:
                print(f"ForgeBench license error: {exc}", file=sys.stderr)
                return 2
        result = export_analytics_dashboard(
            output_dir=args.out,
            include_review_telemetry=not args.no_review_telemetry,
            cloud_export=args.cloud_export,
        )
        print("ForgeBench analytics dashboard exported.")
        print(f"- HTML: {result.index_path}")
        print(f"- Manifest: {result.manifest_path}")
        return 0
    print("analytics requires enable, disable, status, export, or dashboard.", file=sys.stderr)
    return 2


def maybe_record_cli_command(command: str | None) -> None:
    if not command:
        return
    try:
        record_product_event("cli_command", {"command": command})
    except Exception:
        pass