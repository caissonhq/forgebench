#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from forgebench.feedback import FeedbackSummary, summarize_feedback


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize local ForgeBench dogfood feedback JSONL logs.")
    parser.add_argument("feedback_logs", nargs="+", help="One or more local feedback.jsonl files.")
    args = parser.parse_args(argv)

    print(generate_markdown_summary([Path(path) for path in args.feedback_logs]))
    return 0


def generate_markdown_summary(paths: list[Path]) -> str:
    summary = summarize_feedback(paths)
    lines = [
        "# ForgeBench Dogfood Feedback Summary",
        "",
        f"- Total feedback entries: {summary.total}",
        f"- Accepted: {_count_with_percent(summary, 'accepted')}",
        f"- Dismissed: {_count_with_percent(summary, 'dismissed')}",
        f"- Wrong: {_count_with_percent(summary, 'wrong')}",
        f"- Entries missing kind: {summary.missing_kind_count}",
        f"- Malformed lines skipped: {summary.malformed_count}",
        "",
        "## Top Useful Kinds",
        "",
        *_top_kind_lines(summary, "accepted"),
        "",
        "## Top Noisy Kinds",
        "",
        *_top_kind_lines(summary, "dismissed"),
        "",
        "## Top Wrong Kinds",
        "",
        *_top_kind_lines(summary, "wrong"),
        "",
    ]
    return "\n".join(lines)


def _count_with_percent(summary: FeedbackSummary, status: str) -> str:
    count = summary.status_counts.get(status, 0)
    if summary.total == 0:
        return f"{count} (0.0%)"
    return f"{count} ({(count / summary.total) * 100:.1f}%)"


def _top_kind_lines(summary: FeedbackSummary, status: str) -> list[str]:
    counter = summary.kind_counts.get(status)
    if not counter:
        return ["- None."]
    return [f"- {kind}: {count}" for kind, count in counter.most_common(5)] or ["- None."]


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
