from __future__ import annotations

import argparse
import sys

from forgebench.weekly_review import format_weekly_review_result, run_weekly_review


def add_weekly_review_subparser(subparsers: argparse._SubParsersAction) -> None:
    weekly = subparsers.add_parser(
        "weekly-review",
        help="Run digest + roadmap suggestions + What's New draft for the week.",
    )
    weekly.add_argument("--period", default="7d", help="Review period (7d, 14d, 2w).")
    weekly.add_argument("--feedback-log", default="forgebench-output/feedback.jsonl")
    weekly.add_argument("--out", default="forgebench-output/weekly-review", help="Output directory.")
    weekly.add_argument("--apply-roadmap", action="store_true", help="Apply roadmap suggestions to ROADMAP.md.")
    weekly.add_argument("--roadmap", help="ROADMAP.md path.")


def run_weekly_review_command(args: argparse.Namespace) -> int:
    result = run_weekly_review(
        feedback_log=args.feedback_log,
        period=args.period,
        output_dir=args.out,
        apply_roadmap=args.apply_roadmap,
        roadmap_path=args.roadmap,
    )
    print(format_weekly_review_result(result))
    return 0