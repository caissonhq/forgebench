from __future__ import annotations

import argparse
import sys

from forgebench.feedback_import import format_import_result, import_feedback
from forgebench.feedback_promote import format_promote_result, promote_feedback_to_golden_cases
from forgebench.feedback_digest import build_feedback_digest, format_feedback_digest, parse_period
from forgebench.iteration.thanks import format_thank_you_response


FEEDBACK_SUBCOMMANDS = frozenset({"import", "digest", "promote", "thank"})


def is_feedback_subcommand(argv: list[str]) -> bool:
    return len(argv) >= 2 and argv[0] == "feedback" and argv[1] in FEEDBACK_SUBCOMMANDS


def build_feedback_action_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forgebench feedback")
    sub = parser.add_subparsers(dest="feedback_action", required=True)
    imp = sub.add_parser("import", help="Import feedback from JSON, JSONL, email, or Discussion export.")
    imp.add_argument("path", help="Source file path.")
    imp.add_argument("--format", choices=["json", "jsonl", "email", "discussion"], help="Override format detection.")
    imp.add_argument("--feedback-log", default="forgebench-output/feedback.jsonl")
    imp.add_argument("--dry-run", action="store_true")
    digest = sub.add_parser("digest", help="Prioritized feedback digest with health metrics.")
    digest.add_argument("--period", default="7d", help="Period such as 7d, 14d, 2w, 30d.")
    digest.add_argument("--feedback-log", default="forgebench-output/feedback.jsonl")
    digest.add_argument("--out", help="Write digest to file.")
    promote = sub.add_parser("promote", help="Promote feedback entries to golden case candidates.")
    promote.add_argument("--uid", help="Specific finding UID to promote.")
    promote.add_argument("--feedback-log", default="forgebench-output/feedback.jsonl")
    promote.add_argument("--out", default="forgebench-output/golden-case-candidates")
    thank = sub.add_parser("thank", help="Print thank-you response template for feedback submitters.")
    thank.add_argument("--name", default="")
    thank.add_argument("--summary", default="")
    thank.add_argument("--tracking-ref", default="")
    return parser


def add_feedback_subparsers(_feedback: argparse.ArgumentParser) -> None:
    """Subcommands are parsed via build_feedback_action_parser() for backward compatibility."""
    return None


def run_feedback_subcommand(args: argparse.Namespace) -> int | None:
    action = getattr(args, "feedback_action", None)
    if action == "import":
        try:
            result = import_feedback(
                args.path,
                format_hint=getattr(args, "format", None),
                feedback_log=args.feedback_log,
                dry_run=getattr(args, "dry_run", False),
            )
        except Exception as exc:
            print(f"ForgeBench feedback import error: {exc}", file=sys.stderr)
            return 2
        print(format_import_result(result))
        return 0
    if action == "digest":
        digest = build_feedback_digest([args.feedback_log], period=args.period)
        text = format_feedback_digest(digest)
        if args.out:
            from pathlib import Path

            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text + "\n", encoding="utf-8")
            print(f"Feedback digest written to {out}.")
        else:
            print(text)
        return 0
    if action == "promote":
        try:
            result = promote_feedback_to_golden_cases(
                feedback_log=args.feedback_log,
                uid=getattr(args, "uid", None),
                output_dir=args.out,
            )
        except Exception as exc:
            print(f"ForgeBench feedback promote error: {exc}", file=sys.stderr)
            return 2
        print(format_promote_result(result))
        return 0
    if action == "thank":
        print(format_thank_you_response(
            name=getattr(args, "name", "") or "",
            issue_summary=getattr(args, "summary", "") or "",
            tracking_ref=getattr(args, "tracking_ref", "") or "",
        ))
        return 0
    return None


def parse_period_arg(args: argparse.Namespace) -> int:
    if getattr(args, "period", None):
        return parse_period(args.period)
    return getattr(args, "digest_days", 7)