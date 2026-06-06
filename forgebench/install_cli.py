from __future__ import annotations

import argparse
import sys

from forgebench.adoption import record_milestone
from forgebench.distribution import (
    detect_environment,
    format_install_guide,
    format_methods_table,
    post_install_message,
    render_shell_completion,
    upgrade_instructions,
)
from forgebench.ux.output import heading, info, success


def add_install_subparser(subparsers: argparse._SubParsersAction) -> None:
    install = subparsers.add_parser(
        "install",
        help="Install guidance — detect environment and recommend the best method.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Detect your platform and recommend pip, pipx, Homebrew, binary, or source install.",
    )
    install_sub = install.add_subparsers(dest="install_action")
    install_sub.add_parser("guide", help="Show personalized install guide (default).")
    install_sub.add_parser("methods", help="List all install methods with pros/cons.")
    completions = install_sub.add_parser("completions", help="Print shell completion script.")
    completions.add_argument("--shell", required=True, choices=["bash", "zsh", "fish"])
    upgrade = install_sub.add_parser("upgrade", help="Show upgrade commands for detected install method.")
    install.add_argument("--welcome", action="store_true", help="Show post-install welcome message.")


def run_install_command(args: argparse.Namespace) -> int:
    action = getattr(args, "install_action", None) or "guide"
    if action == "guide" or (action is None and not getattr(args, "welcome", False)):
        if getattr(args, "welcome", False):
            print(post_install_message(first_run=True))
            record_milestone("first_install")
            return 0
        print(format_install_guide())
        _maybe_record_first_install()
        return 0
    if action == "methods":
        print(format_methods_table())
        return 0
    if action == "completions":
        print(render_shell_completion(args.shell))
        return 0
    if action == "upgrade":
        env = detect_environment()
        lines = upgrade_instructions(env.detected_method)
        heading("ForgeBench upgrade")
        info(f"Detected method: {env.detected_method.value}")
        for line in lines:
            print(f"  {line}")
        return 0
    print(format_install_guide())
    return 0


def maybe_show_first_run_welcome(argv: list[str] | None) -> None:
    if not argv or len(argv) > 2:
        return
    if argv[0] in {"--version", "-V", "--help", "-h"}:
        return
    from forgebench.adoption import load_adoption_state

    state = load_adoption_state()
    if "first_install" in state.milestones:
        return
    if argv[0] in {"install", "quickstart", "doctor"}:
        return
    success(post_install_message(first_run=True))
    record_milestone("first_install")


def _maybe_record_first_install() -> None:
    env = detect_environment()
    if env.detected_method.value != "unknown":
        record_milestone("first_install")


