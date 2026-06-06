from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forgebench.github_app.enforcement import enforce_org_policy, load_org_enforcement_config
from forgebench.github_app.manifest import export_github_app_manifest
from forgebench.github_app.server import GitHubAppServiceConfig, serve_github_app


def run_github_app_command(args: argparse.Namespace) -> int:
    action = args.github_app_action
    if action == "manifest":
        return _run_manifest(args)
    if action == "enforce":
        return _run_enforce(args)
    if action == "serve":
        return _run_serve(args)
    _fail("github-app requires manifest, enforce, or serve.")
    return 2


def _run_manifest(args: argparse.Namespace) -> int:
    manifest = export_github_app_manifest(
        webhook_url=args.webhook_url,
        setup_url=args.setup_url,
    )
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"GitHub App manifest written to {output}.")
    else:
        print(json.dumps(manifest, indent=2))
    return 0


def _run_enforce(args: argparse.Namespace) -> int:
    config = load_org_enforcement_config(args.config)
    result = enforce_org_policy(
        posture=args.posture,
        config=config,
        policy_fingerprint=args.policy_fingerprint,
        finding_count=args.finding_count,
    )
    payload = {
        "allowed": result.allowed,
        "posture": result.posture,
        "check_conclusion": result.check_conclusion,
        "violations": result.violations,
        "recommendations": result.recommendations,
    }
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Org enforcement result written to {output}.")
    else:
        print(json.dumps(payload, indent=2))
    return 0 if result.allowed else 1


def _run_serve(args: argparse.Namespace) -> int:
    config = GitHubAppServiceConfig(
        host=args.host,
        port=args.port,
        webhook_secret=args.webhook_secret or "",
        org_enforcement_config=args.config,
    )
    print(f"ForgeBench GitHub App service listening on http://{args.host}:{args.port}")
    print("Endpoints: GET /health, GET /v1/manifest, POST /github-app/webhook")
    serve_github_app(config)
    return 0


def add_github_app_subparser(subparsers: argparse._SubParsersAction) -> None:
    github_app = subparsers.add_parser(
        "github-app",
        help="Self-hosted GitHub App manifest, org enforcement, and webhook server.",
    )
    app_sub = github_app.add_subparsers(dest="github_app_action")

    manifest = app_sub.add_parser("manifest", help="Export GitHub App manifest JSON.")
    manifest.add_argument("--webhook-url", required=False, default="https://your-org.example.com/github-app/webhook")
    manifest.add_argument("--setup-url", required=False, default="https://forgebench.dev/docs/early-access")
    manifest.add_argument("--out", required=False, help="Output JSON path.")

    enforce = app_sub.add_parser("enforce", help="Evaluate org policy enforcement for a posture.")
    enforce.add_argument("--config", required=True, help="Org enforcement config JSON path.")
    enforce.add_argument("--posture", required=True, choices=["BLOCK", "REVIEW", "LOW_CONCERN"])
    enforce.add_argument("--policy-fingerprint", required=False, help="Optional policy fingerprint.")
    enforce.add_argument("--finding-count", type=int, required=False, default=0)
    enforce.add_argument("--out", required=False, help="Output JSON path.")

    serve = app_sub.add_parser("serve", help="Start self-hosted GitHub App webhook server.")
    serve.add_argument("--host", required=False, default="127.0.0.1")
    serve.add_argument("--port", type=int, required=False, default=8792)
    serve.add_argument("--config", required=False, help="Org enforcement config JSON path.")
    serve.add_argument("--webhook-secret", required=False, help="GitHub webhook secret for signature verification.")


def _fail(message: str) -> None:
    print(f"ForgeBench error: {message}", file=sys.stderr)
    raise SystemExit(2)