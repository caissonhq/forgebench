from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forgebench.calibration import format_calibration_result, run_calibration
from forgebench.github_pr import GitHubPRError, GitHubPRReviewResult, run_github_pr_review
from forgebench.models import ForgeBenchReport
from forgebench.review import ReviewInputError, run_review


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "calibrate":
        return _run_calibrate(args)

    if args.command == "review-pr":
        return _run_review_pr(args)

    if args.command != "review":
        parser.print_help()
        return 2

    return _run_review(args)


def _run_review(args: argparse.Namespace) -> int:
    try:
        result = run_review(
            repo_path=args.repo,
            diff_path=args.diff,
            task_path=args.task,
            guardrails_path=args.guardrails,
            output_dir=args.out or "forgebench-output",
            run_checks=args.run_checks,
            llm_review=args.llm_review,
            llm_provider=args.llm_provider,
            llm_command=args.llm_command,
            llm_timeout=args.llm_timeout,
            llm_max_diff_chars=args.llm_max_diff_chars,
        )
    except ReviewInputError as exc:
        _fail(str(exc))

    _print_summary(result.report, result.written_paths)
    return 0


def _run_review_pr(args: argparse.Namespace) -> int:
    pr_url = args.pr_url or args.pr_url_option
    if not pr_url:
        _fail("review-pr requires a GitHub PR URL.")
    if args.post_comment and not args.dry_run:
        print("Posting ForgeBench comment to PR...")
    try:
        result = run_github_pr_review(
            repo_path=args.repo,
            pr_url=pr_url,
            guardrails_path=args.guardrails,
            output_dir=args.out,
            run_checks=args.run_checks,
            post_comment=args.post_comment,
            comment_file=args.comment_file,
            dry_run=args.dry_run or not args.post_comment,
            llm_review=args.llm_review,
            llm_provider=args.llm_provider,
            llm_command=args.llm_command,
            llm_timeout=args.llm_timeout,
            llm_max_diff_chars=args.llm_max_diff_chars,
        )
    except (ReviewInputError, GitHubPRError) as exc:
        _fail(str(exc))

    _print_pr_summary(result)
    if result.comment_posted:
        print("PR comment posted.")
    return 0


def _run_calibrate(args: argparse.Namespace) -> int:
    try:
        result = run_calibration(cases_dir=args.cases, output_dir=args.out, repo_path=args.repo)
    except (FileNotFoundError, ValueError, OSError) as exc:
        _fail(str(exc))

    print(format_calibration_result(result))
    return 1 if result.failed_count else 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forgebench", description="Adversarial pre-merge QA for coding-agent output.")
    subparsers = parser.add_subparsers(dest="command")

    review = subparsers.add_parser("review", help="Review an AI-generated diff before merge.")
    review.add_argument("--repo", required=True, help="Path to the repository being reviewed.")
    review.add_argument("--diff", required=True, help="Path to a unified git diff.")
    review.add_argument("--task", required=True, help="Path to the original task prompt.")
    review.add_argument("--guardrails", required=False, help="Optional path to forgebench.yml.")
    review.add_argument("--out", required=False, help="Output directory. Defaults to ./forgebench-output/.")
    review.add_argument("--run-checks", action="store_true", help="Execute configured local deterministic checks from forgebench.yml.")
    review.add_argument("--llm-review", action="store_true", help="Run an optional advisory LLM reviewer after deterministic/static review.")
    review.add_argument("--llm-provider", choices=["mock", "command"], required=False, help="LLM provider to use when --llm-review is passed.")
    review.add_argument("--llm-command", required=False, help="Command provider shell command. Receives the review bundle on stdin and returns JSON on stdout.")
    review.add_argument("--llm-timeout", type=int, default=60, help="LLM command timeout in seconds. Defaults to 60.")
    review.add_argument("--llm-max-diff-chars", type=int, default=20000, help="Maximum diff characters included in the LLM bundle.")

    review_pr = subparsers.add_parser("review-pr", help="Fetch a GitHub PR diff, run ForgeBench, and optionally post a PR comment.")
    review_pr.add_argument("pr_url", nargs="?", help="GitHub pull request URL.")
    review_pr.add_argument("--repo", required=False, default=".", help="Local repository path. Defaults to current directory.")
    review_pr.add_argument("--pr-url", dest="pr_url_option", required=False, help="GitHub pull request URL. Kept for compatibility; positional URL is preferred.")
    review_pr.add_argument("--guardrails", required=False, help="Optional path to forgebench.yml.")
    review_pr.add_argument("--out", required=False, help="Output directory. Defaults to ./forgebench-output/pr-OWNER-REPO-NUMBER/.")
    review_pr.add_argument("--run-checks", action="store_true", help="Execute configured local deterministic checks from forgebench.yml.")
    review_pr.add_argument("--post-comment", action="store_true", help="Post the ForgeBench Markdown report as a GitHub PR comment.")
    review_pr.add_argument("--comment-file", required=False, help="Path to write the PR comment Markdown. Defaults to pr-comment.md in the output directory.")
    review_pr.add_argument("--dry-run", action="store_true", help="Write local artifacts but do not post a PR comment.")
    review_pr.add_argument("--llm-review", action="store_true", help="Run an optional advisory LLM reviewer after deterministic/static review.")
    review_pr.add_argument("--llm-provider", choices=["mock", "command"], required=False, help="LLM provider to use when --llm-review is passed.")
    review_pr.add_argument("--llm-command", required=False, help="Command provider shell command. Receives the review bundle on stdin and returns JSON on stdout.")
    review_pr.add_argument("--llm-timeout", type=int, default=60, help="LLM command timeout in seconds. Defaults to 60.")
    review_pr.add_argument("--llm-max-diff-chars", type=int, default=20000, help="Maximum diff characters included in the LLM bundle.")

    calibrate = subparsers.add_parser("calibrate", help="Run the golden corpus calibration suite.")
    calibrate.add_argument("--cases", required=True, help="Path to the golden cases directory.")
    calibrate.add_argument("--out", required=False, default="forgebench-calibration-output", help="Output directory for calibration reports.")
    calibrate.add_argument("--repo", required=False, default=".", help="Repo root used when running configured checks. Defaults to current directory.")

    return parser


def _fail(message: str) -> None:
    print(f"ForgeBench error: {message}", file=sys.stderr)
    raise SystemExit(2)


def _print_summary(report: ForgeBenchReport, written: dict[str, Path]) -> None:
    print("ForgeBench review complete.")
    print()
    print(f"Posture: {report.posture.value}")
    if report.pre_llm_posture and report.pre_llm_posture != report.posture:
        print(f"Pre-LLM posture: {report.pre_llm_posture.value}")
    print()
    print("Findings:")
    if report.findings:
        for finding in report.findings:
            print(f"- {finding.severity.value}: {finding.title}")
    else:
        print("- No findings.")
    print()
    print(f"Deterministic checks: {_checks_summary(report)}")
    print(f"LLM review: {_llm_summary(report)}")
    print()
    print("Reports written:")
    print(f"- {written['markdown']}")
    print(f"- {written['json']}")
    print(f"- {written['repair_prompt']}")


def _print_pr_summary(result: GitHubPRReviewResult) -> None:
    print("ForgeBench GitHub PR review complete.")
    print()
    print(f"PR: {result.intake.ref.url}")
    print(f"Title: {result.intake.metadata.title or '(No PR title provided.)'}")
    print()
    _print_summary(result.review_result.report, result.review_result.written_paths)
    print(f"- {result.comment_path}")
    print()
    print("GitHub comment:")
    if result.comment_posted:
        print("- posted")
    elif result.comment_error:
        print(f"- failed: {result.comment_error}")
    elif result.comment_requested and result.dry_run:
        print("- dry run; not posted")
    else:
        print("- not requested")


def _checks_summary(report: ForgeBenchReport) -> str:
    checks = report.deterministic_checks
    if not checks.run_requested:
        return "not run"
    if not checks.results:
        return "no checks configured"
    summary = checks.summary
    parts = [
        f"passed={summary['passed']}",
        f"failed={summary['failed']}",
        f"timed_out={summary['timed_out']}",
        f"not_configured={summary['not_configured']}",
        f"errors={summary['errors']}",
    ]
    return ", ".join(parts)


def _llm_summary(report: ForgeBenchReport) -> str:
    review = report.llm_review
    if not review.enabled:
        return "not run"
    if review.status.value == "completed":
        return f"completed ({review.provider or 'unknown'}, findings={len(review.findings)})"
    if review.status.value == "failed":
        return f"failed ({review.error_message or 'unknown error'})"
    return review.status.value


if __name__ == "__main__":
    raise SystemExit(main())
