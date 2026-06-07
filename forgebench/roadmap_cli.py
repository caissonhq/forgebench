from __future__ import annotations

import argparse
import sys

from forgebench.roadmap_sync import format_roadmap_suggestions, update_roadmap


def add_roadmap_subparser(subparsers: argparse._SubParsersAction) -> None:
    roadmap = subparsers.add_parser("roadmap", help="Sync feedback themes into ROADMAP.md.")
    roadmap_sub = roadmap.add_subparsers(dest="roadmap_action")
    update = roadmap_sub.add_parser("update", help="Analyze feedback and suggest or apply roadmap items.")
    update.add_argument("--period", default="7d", help="Feedback lookback period (7d, 14d, 2w).")
    update.add_argument("--feedback-log", default="forgebench-output/feedback.jsonl")
    update.add_argument("--roadmap", help="Path to ROADMAP.md (default: repo ROADMAP.md).")
    update.add_argument("--apply", action="store_true", help="Write new items into ROADMAP.md.")
    update.add_argument("--out", help="Write suggestions to file.")


def run_roadmap_command(args: argparse.Namespace) -> int:
    if args.roadmap_action != "update":
        print("roadmap requires update.", file=sys.stderr)
        return 2
    result = update_roadmap(
        roadmap_path=args.roadmap,
        feedback_logs=[args.feedback_log],
        period=args.period,
        apply=args.apply,
    )
    text = format_roadmap_suggestions(result)
    if args.out:
        from pathlib import Path

        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"Roadmap suggestions written to {out}.")
    else:
        print(text)
    return 0