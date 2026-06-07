from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forgebench.launch.announcements import format_launch_announcements_bundle
from forgebench.launch.discussions_seed import format_discussions_seed_pack
from forgebench.launch.stats import format_public_stats_summary, update_public_stats
from forgebench.launch.verify import format_launch_report, launch_ready, verify_launch_readiness
from forgebench.roadmap_sync import update_roadmap
from forgebench.feedback_digest import build_feedback_digest, format_feedback_digest
from forgebench.ux.output import heading, info, success


def add_launch_subparser(subparsers: argparse._SubParsersAction) -> None:
    launch = subparsers.add_parser("launch", help="v1.0.0 launch execution — verify, stats, announcements.")
    launch_sub = launch.add_subparsers(dest="launch_action")
    verify = launch_sub.add_parser("verify", help="Verify release, docs, and marketplace readiness.")
    verify.add_argument("--json", action="store_true")
    stats = launch_sub.add_parser("stats", help="Update public-stats.json launch metrics.")
    stats.add_argument("--stars", type=int)
    stats.add_argument("--pypi", default=None)
    stats.add_argument("--vscode", default=None)
    stats.add_argument("--partners", type=int)
    stats.add_argument("--stories", type=int)
    stats.add_argument("--reviews", type=int)
    stats.add_argument("--hn-points", type=int)
    stats.add_argument("--out", help="Stats JSON path (default: examples/launch/public-stats.json)")
    announce = launch_sub.add_parser("announce", help="Print final X thread + Show HN post.")
    announce.add_argument("--out", help="Write to file.")
    seed = launch_sub.add_parser("seed-discussions", help="Generate GitHub Discussions seed posts.")
    seed.add_argument("--out", help="Write seed pack to file.")
    day1 = launch_sub.add_parser("day1-review", help="Day-1 digest + roadmap suggestions.")
    day1.add_argument("--period", default="1d", help="Feedback period (1d, 7d).")
    day1.add_argument("--feedback-log", default="forgebench-output/feedback.jsonl")
    day1.add_argument("--out", default="forgebench-output/launch-day1-review")
    checklist = launch_sub.add_parser("checklist", help="Print launch day checklist path and verify summary.")


def run_launch_command(args: argparse.Namespace) -> int:
    action = args.launch_action
    if action == "verify":
        checks = verify_launch_readiness()
        if args.json:
            print(json.dumps([c.__dict__ for c in checks], indent=2, sort_keys=True))
        else:
            print(format_launch_report(checks))
        return 0 if launch_ready(checks) else 1
    if action == "stats":
        path = update_public_stats(
            path=args.out,
            github_stars=args.stars,
            pypi_downloads_monthly=args.pypi,
            vscode_installs=args.vscode,
            design_partners_active=args.partners,
            success_stories_published=args.stories,
            first_reviews_reported=args.reviews,
            hn_points=args.hn_points,
        )
        success(f"Public stats updated: {path}")
        print(format_public_stats_summary(path))
        return 0
    if action == "announce":
        text = format_launch_announcements_bundle()
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text + "\n", encoding="utf-8")
            success(f"Announcements written to {out}")
        else:
            print(text)
        return 0
    if action == "seed-discussions":
        text = format_discussions_seed_pack()
        if args.out:
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text + "\n", encoding="utf-8")
            success(f"Discussions seed pack written to {out}")
        else:
            print(text)
        return 0
    if action == "day1-review":
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        digest = build_feedback_digest([args.feedback_log], period=args.period)
        digest_text = format_feedback_digest(digest)
        (out / "day1-digest.txt").write_text(digest_text + "\n", encoding="utf-8")
        roadmap = update_roadmap(feedback_logs=[args.feedback_log], period=args.period, apply=False)
        from forgebench.roadmap_sync import format_roadmap_suggestions

        (out / "day1-roadmap.txt").write_text(format_roadmap_suggestions(roadmap) + "\n", encoding="utf-8")
        heading("Launch day-1 review")
        info(f"Digest: {out / 'day1-digest.txt'}")
        info(f"Roadmap: {out / 'day1-roadmap.txt'}")
        print(digest_text)
        return 0
    if action == "checklist":
        root = Path(__file__).resolve().parents[1]
        checklist = root / "docs" / "launch" / "LAUNCH_DAY_CHECKLIST.md"
        checks = verify_launch_readiness()
        print(format_launch_report(checks))
        print("")
        print(f"Launch Day Checklist: {checklist}")
        return 0 if launch_ready(checks) else 1
    print("launch requires verify, stats, announce, seed-discussions, day1-review, or checklist.", file=sys.stderr)
    return 2