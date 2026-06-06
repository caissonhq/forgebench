from __future__ import annotations

import argparse
import sys

from forgebench.init_enterprise import (
    EnterpriseInitOptions,
    format_enterprise_init_result,
    run_enterprise_init,
    write_enterprise_manifest,
)
from forgebench.adoption import record_milestone


def add_team_subparser(subparsers: argparse._SubParsersAction) -> None:
    team = subparsers.add_parser(
        "team",
        help="Team adoption commands — org policy, CI, and onboarding kit.",
    )
    team_sub = team.add_subparsers(dest="team_action")
    init = team_sub.add_parser(
        "init",
        help="Interactive team setup wizard (org policy, CI, docs, GitHub App notes).",
    )
    init.add_argument("--repo", default=".", help="Repository path.")
    init.add_argument("--org-name", default="", help="Organization name.")
    init.add_argument("--team-slug", default="engineering", help="Team slug.")
    init.add_argument("--preset", default="auto", choices=["auto", "python", "node", "nextjs", "swift", "rust"])
    init.add_argument("--force", action="store_true")
    init.add_argument("--yes", action="store_true", help="Non-interactive with smart defaults.")
    init.add_argument("--no-ci", action="store_true")
    init.add_argument("--no-github-app", action="store_true")
    init.add_argument("--manifest", help="Write team-init-manifest.json path.")


def run_team_command(args: argparse.Namespace) -> int:
    if args.team_action != "init":
        print("team requires init.", file=sys.stderr)
        return 2
    from forgebench.licensing.quotas import LicenseRequired, require_feature
    from pathlib import Path

    try:
        require_feature("init_enterprise")
    except LicenseRequired as exc:
        print(f"ForgeBench license error: {exc}", file=sys.stderr)
        print("Team init requires a Team license. Run: forgebench license activate <KEY>", file=sys.stderr)
        return 2

    org_name = args.org_name.strip() or None
    options = EnterpriseInitOptions(
        org_name=org_name or "Your Engineering Team",
        team_slug=args.team_slug,
        preset=args.preset,
        enable_github_app=not args.no_github_app,
        enable_ci=not args.no_ci,
        force=args.force,
        non_interactive=args.yes,
        wizard_mode="team",
    )
    if not args.yes and not org_name:
        options = _interactive_team_options(args.repo)

    result = run_enterprise_init(repo_path=args.repo, options=options)
    if args.manifest:
        write_enterprise_manifest(result, Path(args.manifest))
    record_milestone("first_team_init")
    print(format_enterprise_init_result(result).replace("enterprise init", "team init"))
    return 0


def _interactive_team_options(repo_path: str) -> EnterpriseInitOptions:
    from forgebench.init_enterprise import _prompt, _prompt_options, _prompt_yes_no
    from pathlib import Path

    base = _prompt_options(Path(repo_path))
    heading_msg = "ForgeBench Team Init"
    print(heading_msg)
    print("Sets up org policy, CI workflow, trusted guardrails, and team docs.")
    primary_lang = _prompt("Primary stack (auto|python|node|nextjs|rust|swift)", base.preset)
    agent_workflow = _prompt_yes_no("Optimize for AI agent PRs (stricter scope + test checks)?", default=True)
    return EnterpriseInitOptions(
        org_name=base.org_name,
        team_slug=base.team_slug,
        preset=primary_lang,
        enable_github_app=base.enable_github_app,
        enable_ci=base.enable_ci,
        force=base.force,
        non_interactive=False,
        wizard_mode="team",
        agent_pr_mode=agent_workflow,
    )


def heading_msg_print(text: str) -> None:
    from forgebench.ux.output import heading

    heading(text)