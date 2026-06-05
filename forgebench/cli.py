from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forgebench import __version__
from forgebench.calibration import format_calibration_result, run_calibration
from forgebench.doctor import format_doctor_report, run_doctor
from forgebench.benchmark import build_benchmark_snapshot, format_benchmark_markdown
from forgebench.feedback import FeedbackError, append_feedback, format_feedback_summary, suggest_guardrails, summarize_feedback
from forgebench.mcp_server import run_mcp_server
from forgebench.github_pr import GitHubPRError, GitHubPRReviewResult, run_github_pr_review
from forgebench.init import InitError, write_starter_guardrails
from forgebench.models import ForgeBenchReport
from forgebench.review import ReviewInputError, run_review
from forgebench.validate import format_validation_report, validate_guardrails_file


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "calibrate":
        return _run_calibrate(args)

    if args.command == "doctor":
        return _run_doctor(args)

    if args.command == "init":
        return _run_init(args)

    if args.command == "feedback":
        return _run_feedback(args)

    if args.command == "validate":
        return _run_validate(args)

    if args.command == "benchmark":
        return _run_benchmark(args)

    if args.command == "repair":
        return _run_repair(args)

    if args.command == "mcp":
        return _run_mcp(args)

    if args.command == "review-pr":
        return _run_review_pr(args)

    if args.command != "review":
        parser.print_help()
        return 2

    return _run_review(args)


def _run_doctor(args: argparse.Namespace) -> int:
    report = run_doctor(repo_path=args.repo)
    print(format_doctor_report(report))
    return report.exit_code


def _run_init(args: argparse.Namespace) -> int:
    try:
        result = write_starter_guardrails(repo_path=args.repo, output_path=args.out, force=args.force, preset=args.preset)
    except InitError as exc:
        _fail(str(exc))

    print("ForgeBench guardrails file created.")
    print()
    print(f"Repo: {result.repo_path}")
    print(f"Output: {result.path}")
    if result.detected:
        print(f"Detected: {', '.join(result.detected)}")
    else:
        print("Detected: no supported project manifest; checks defaulted to null")
    print()
    print("Edit protected_behavior and forbidden_patterns before relying on project-specific guardrails.")
    return 0


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
            reviewers_enabled=not args.no_reviewers,
        )
    except ReviewInputError as exc:
        _fail(str(exc))

    _print_summary(result.report, result.written_paths, guardrails_explicit=bool(args.guardrails))
    print()
    print(f"Paste repair prompt: forgebench repair --out {result.output_dir}")
    return 0


def _run_benchmark(args: argparse.Namespace) -> int:
    try:
        snapshot = build_benchmark_snapshot(args.cases, repo_path=args.repo, output_dir=args.out)
    except (FileNotFoundError, ValueError, OSError) as exc:
        _fail(str(exc))
    markdown = format_benchmark_markdown(snapshot, cases_dir=args.cases)
    if args.out_markdown:
        output = Path(args.out_markdown)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        print(f"Merge Risk Benchmark written to {output}.")
    else:
        print(markdown)
    return 1 if snapshot.failed_count else 0


def _run_repair(args: argparse.Namespace) -> int:
    repair_path = Path(args.out) / "repair-prompt.md"
    if not repair_path.exists():
        _fail(
            f"repair prompt not found at {repair_path}. "
            "Run forgebench review or forgebench review-pr first."
        )
    text = repair_path.read_text(encoding="utf-8", errors="replace")
    if args.copy_hint:
        print(f"Repair prompt: {repair_path}")
        print("Paste the content below into your coding agent (Cursor, Codex, or Claude Code).")
        print()
    print(text)
    return 0


def _run_mcp(args: argparse.Namespace) -> int:
    del args
    run_mcp_server()
    return 0


def _run_review_pr(args: argparse.Namespace) -> int:
    pr_url = args.pr_url or args.pr_url_option
    if not pr_url:
        _fail("review-pr requires a GitHub PR URL.")
    if args.run_checks and not args.checkout_pr:
        _fail(
            "review-pr --run-checks requires --checkout-pr so deterministic checks run against PR code, "
            "not your current checkout."
        )
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
            post_check_run=args.check_run,
            comment_file=args.comment_file,
            dry_run=args.dry_run or not args.post_comment,
            llm_review=args.llm_review,
            llm_provider=args.llm_provider,
            llm_command=args.llm_command,
            llm_timeout=args.llm_timeout,
            llm_max_diff_chars=args.llm_max_diff_chars,
            checkout_pr=args.checkout_pr,
            keep_worktree=args.keep_worktree,
            worktree_dir=args.worktree_dir,
            reviewers_enabled=not args.no_reviewers,
        )
    except (ReviewInputError, GitHubPRError) as exc:
        _fail(str(exc))

    _print_pr_summary(result, guardrails_explicit=bool(args.guardrails))
    if result.comment_posted:
        print("PR comment posted.")
    if result.check_run_posted:
        print("GitHub Check Run posted.")
    elif result.check_run_error:
        print(f"GitHub Check Run failed: {result.check_run_error}")
    return 0


def _run_validate(args: argparse.Namespace) -> int:
    path = Path(args.file)
    if not path.is_absolute():
        candidate = Path(args.repo) / path
        if candidate.exists():
            path = candidate
    report = validate_guardrails_file(path, strict=args.strict)
    print(format_validation_report(report))
    return report.exit_code


def _run_calibrate(args: argparse.Namespace) -> int:
    try:
        result = run_calibration(cases_dir=args.cases, output_dir=args.out, repo_path=args.repo)
    except (FileNotFoundError, ValueError, OSError) as exc:
        _fail(str(exc))

    print(format_calibration_result(result))
    return 1 if result.failed_count else 0


def _run_feedback(args: argparse.Namespace) -> int:
    if args.suggest_guardrails:
        suggestions = suggest_guardrails([args.feedback_log])
        if args.out:
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(suggestions, encoding="utf-8")
            print(f"ForgeBench guardrail suggestions written to {output}.")
        else:
            print(suggestions)
        return 0

    if args.summarize:
        summary = summarize_feedback([args.feedback_log])
        if summary.total == 0 and summary.malformed_count == 0:
            print(f"No feedback entries found in {args.feedback_log}.")
        else:
            print(format_feedback_summary(summary))
        return 0

    if not args.finding_uid:
        _fail("feedback requires a finding UID unless --summarize is passed.")
    if not args.status:
        _fail("feedback requires --status accepted|dismissed|wrong.")
    try:
        path = append_feedback(
            args.finding_uid,
            status=args.status,
            note=args.note,
            feedback_log=args.feedback_log,
            kind=args.kind,
            repo_name=args.repo_name,
            source=args.source,
        )
    except FeedbackError as exc:
        _fail(str(exc))
    print("ForgeBench feedback recorded.")
    print(f"Log: {path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="forgebench", description="Adversarial pre-merge QA for coding-agent output.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command")

    doctor = subparsers.add_parser("doctor", help="Verify local install, tooling, and first-run readiness.")
    doctor.add_argument("--repo", required=False, default=".", help="Repository path to inspect. Defaults to current directory.")

    init = subparsers.add_parser("init", help="Write a starter forgebench.yml for a local repo.")
    init.add_argument("--repo", required=False, default=".", help="Repository to inspect. Defaults to current directory.")
    init.add_argument("--out", required=False, default="forgebench.yml", help="Output guardrails path. Defaults to forgebench.yml in the repo.")
    init.add_argument("--force", action="store_true", help="Overwrite the output file if it already exists.")
    init.add_argument(
        "--preset",
        choices=["auto", "python", "node", "nextjs", "swift", "rust"],
        default="auto",
        help="Starter guardrails preset. Defaults to auto.",
    )

    review = subparsers.add_parser("review", help="Review an AI-generated diff before merge.")
    review.add_argument("--repo", required=True, help="Path to the repository being reviewed.")
    review.add_argument("--diff", required=True, help="Path to a unified git diff.")
    review.add_argument("--task", required=True, help="Path to the original task prompt.")
    review.add_argument("--guardrails", required=False, help="Optional path to forgebench.yml.")
    review.add_argument("--out", required=False, help="Output directory. Defaults to ./forgebench-output/.")
    review.add_argument("--run-checks", action="store_true", help="Execute configured local deterministic checks from forgebench.yml.")
    review.add_argument("--no-reviewers", action="store_true", help="Skip Phase 1 heuristic review lenses.")
    review.add_argument("--llm-review", action="store_true", help="Run an optional advisory LLM reviewer after deterministic/static review.")
    review.add_argument(
        "--llm-provider",
        choices=["mock", "command", "openai"],
        required=False,
        help="LLM provider when --llm-review is passed. Defaults to openai when FORGEBENCH_LLM_API_KEY is set, else command when FORGEBENCH_LLM_COMMAND is set.",
    )
    review.add_argument(
        "--llm-command",
        required=False,
        help="Command provider shell command. Defaults to FORGEBENCH_LLM_COMMAND. Receives the review bundle on stdin and returns JSON on stdout.",
    )
    review.add_argument("--llm-timeout", type=int, default=60, help="LLM command timeout in seconds. Defaults to 60.")
    review.add_argument("--llm-max-diff-chars", type=int, default=20000, help="Maximum diff characters included in the LLM bundle.")

    review_pr = subparsers.add_parser("review-pr", help="Fetch a GitHub PR diff, run ForgeBench, and optionally post a PR comment.")
    review_pr.add_argument("pr_url", nargs="?", help="GitHub pull request URL.")
    review_pr.add_argument("--repo", required=False, default=".", help="Local repository path. Defaults to current directory.")
    review_pr.add_argument("--pr-url", dest="pr_url_option", required=False, help="GitHub pull request URL. Kept for compatibility; positional URL is preferred.")
    review_pr.add_argument("--guardrails", required=False, help="Optional path to forgebench.yml.")
    review_pr.add_argument("--out", required=False, help="Output directory. Defaults to ./forgebench-output/pr-OWNER-REPO-NUMBER/.")
    review_pr.add_argument("--run-checks", action="store_true", help="Execute configured local deterministic checks from forgebench.yml.")
    review_pr.add_argument("--no-reviewers", action="store_true", help="Skip Phase 1 heuristic review lenses.")
    review_pr.add_argument("--checkout-pr", action="store_true", help="Checkout the PR code into a temporary git worktree before running checks.")
    review_pr.add_argument("--keep-worktree", action="store_true", help="Do not delete the temporary PR worktree after review. Prints the path in the report.")
    review_pr.add_argument("--worktree-dir", required=False, help="Optional parent directory for temporary PR worktrees.")
    review_pr.add_argument("--post-comment", action="store_true", help="Post the ForgeBench Markdown report as a GitHub PR comment.")
    review_pr.add_argument(
        "--check-run",
        action="store_true",
        help="Post a GitHub Check Run with inline annotations for findings on the PR head commit.",
    )
    review_pr.add_argument("--comment-file", required=False, help="Path to write the PR comment Markdown. Defaults to pr-comment.md in the output directory.")
    review_pr.add_argument("--dry-run", action="store_true", help="Write local artifacts but do not post a PR comment.")
    review_pr.add_argument("--llm-review", action="store_true", help="Run an optional advisory LLM reviewer after deterministic/static review.")
    review_pr.add_argument(
        "--llm-provider",
        choices=["mock", "command", "openai"],
        required=False,
        help="LLM provider when --llm-review is passed. Defaults to openai when FORGEBENCH_LLM_API_KEY is set, else command when FORGEBENCH_LLM_COMMAND is set.",
    )
    review_pr.add_argument(
        "--llm-command",
        required=False,
        help="Command provider shell command. Defaults to FORGEBENCH_LLM_COMMAND. Receives the review bundle on stdin and returns JSON on stdout.",
    )
    review_pr.add_argument("--llm-timeout", type=int, default=60, help="LLM command timeout in seconds. Defaults to 60.")
    review_pr.add_argument("--llm-max-diff-chars", type=int, default=20000, help="Maximum diff characters included in the LLM bundle.")

    feedback = subparsers.add_parser("feedback", help="Record or summarize local finding feedback.")
    feedback.add_argument("finding_uid", nargs="?", help="Stable finding UID, such as fnd_3a91c0e88d12.")
    feedback.add_argument("--status", required=False, help="Feedback status: accepted, dismissed, or wrong.")
    feedback.add_argument("--note", required=False, help="Optional local note about the finding.")
    feedback.add_argument("--kind", required=False, help="Optional logical finding kind.")
    feedback.add_argument("--repo-name", required=False, help="Optional repo/project name for local dogfood summaries.")
    feedback.add_argument("--source", required=False, help="Optional feedback source label.")
    feedback.add_argument("--feedback-log", required=False, default="forgebench-output/feedback.jsonl", help="Local JSONL feedback log path.")
    feedback.add_argument("--summarize", action="store_true", help="Summarize a local feedback JSONL log.")
    feedback.add_argument("--suggest-guardrails", action="store_true", help="Suggest forgebench.yml tuning from local feedback.")
    feedback.add_argument("--out", required=False, help="Optional path to write guardrail suggestions Markdown.")

    benchmark = subparsers.add_parser("benchmark", help="Run the Merge Risk Benchmark and print publishable summary Markdown.")
    benchmark.add_argument("--cases", required=False, default="examples/golden_cases", help="Golden cases directory.")
    benchmark.add_argument("--repo", required=False, default=".", help="Repo root for configured checks.")
    benchmark.add_argument("--out", required=False, default="forgebench-benchmark-output", help="Calibration output directory.")
    benchmark.add_argument("--out-markdown", required=False, help="Optional path to write benchmark Markdown.")

    repair = subparsers.add_parser("repair", help="Print repair-prompt.md for pasting into a coding agent.")
    repair.add_argument("--out", required=False, default="forgebench-output", help="ForgeBench output directory.")
    repair.add_argument("--copy-hint", action="store_true", default=True, help="Print paste instructions before the prompt.")
    repair.add_argument("--no-copy-hint", dest="copy_hint", action="store_false", help="Print only the repair prompt body.")

    mcp = subparsers.add_parser("mcp", help="Start the ForgeBench MCP server over stdio.")
    mcp.add_argument("--transport", choices=["stdio"], default="stdio", help="Transport for MCP. Only stdio is supported.")

    calibrate = subparsers.add_parser("calibrate", help="Run the golden corpus calibration suite.")
    calibrate.add_argument("--cases", required=True, help="Path to the golden cases directory.")
    calibrate.add_argument("--out", required=False, default="forgebench-calibration-output", help="Output directory for calibration reports.")
    calibrate.add_argument("--repo", required=False, default=".", help="Repo root used when running configured checks. Defaults to current directory.")

    validate = subparsers.add_parser("validate", help="Lint forgebench.yml against the documented schema.")
    validate.add_argument("--repo", required=False, default=".", help="Repository path. Defaults to current directory.")
    validate.add_argument("--file", required=False, default="forgebench.yml", help="Guardrails file to validate.")
    validate.add_argument("--strict", action="store_true", help="Treat unknown top-level keys as errors.")

    return parser


def _fail(message: str) -> None:
    print(f"ForgeBench error: {message}", file=sys.stderr)
    raise SystemExit(2)


def _print_summary(report: ForgeBenchReport, written: dict[str, Path], guardrails_explicit: bool = False) -> None:
    print("ForgeBench review complete.")
    print()
    print(f"Posture: {report.posture.value}")
    if report.pre_llm_posture and report.pre_llm_posture != report.posture:
        print(f"Pre-LLM posture: {report.pre_llm_posture.value}")
    print()
    _print_configuration_mode(report, guardrails_explicit=guardrails_explicit)
    print()
    print("Findings:")
    if report.findings:
        for finding in report.findings:
            print(f"- {finding.severity.value}: {finding.title} [{finding.uid}]")
    else:
        print("- No findings.")
    print()
    print(f"Deterministic checks: {_checks_summary(report)}")
    print(f"Heuristic review lenses: {_reviewers_summary(report)}")
    print(f"LLM review: {_llm_summary(report)}")
    print()
    print("Reports written:")
    print(f"- {written['markdown']}")
    print(f"- {written['json']}")
    if "sarif" in written:
        print(f"- {written['sarif']}")
    print(f"- {written['repair_prompt']}")


def _print_pr_summary(result: GitHubPRReviewResult, guardrails_explicit: bool = False) -> None:
    print("ForgeBench GitHub PR review complete.")
    print()
    print(f"PR: {result.intake.ref.url}")
    print(f"Title: {result.intake.metadata.title or '(No PR title provided.)'}")
    print()
    _print_summary(result.review_result.report, result.review_result.written_paths, guardrails_explicit=guardrails_explicit)
    print(f"- {result.comment_path}")
    print()
    print("PR checkout:")
    print(f"- status: {result.pr_checkout.status}")
    print(f"- checks target: {result.pr_checkout.checks_target}")
    if result.pr_checkout.worktree_path:
        print(f"- worktree: {result.pr_checkout.worktree_path}")
    if result.pr_checkout.cleanup_error:
        print(f"- cleanup warning: {result.pr_checkout.cleanup_error}")
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


def _print_configuration_mode(report: ForgeBenchReport, guardrails_explicit: bool = False) -> None:
    if report.config_mode == "configured":
        source = _display_guardrails_source(report.guardrails_source)
        label = "Using guardrails" if guardrails_explicit else "Found guardrails"
        print(f"{label}: {source}")
        print("Configuration mode: configured")
        return

    print("No forgebench.yml found.")
    print("Configuration mode: generic")
    print("Run `forgebench init --repo . --out forgebench.yml`")
    print("to create starter guardrails.")


def _display_guardrails_source(source: str | None) -> str:
    if not source:
        return "unknown"
    path = Path(source)
    text = str(path)
    if not path.is_absolute() and "/" not in text and not text.startswith("."):
        return f"./{text}"
    return text


def _llm_summary(report: ForgeBenchReport) -> str:
    review = report.llm_review
    if not review.enabled:
        return "not run"
    if review.status.value == "completed":
        return f"completed ({review.provider or 'unknown'}, findings={len(review.findings)})"
    if review.status.value == "failed":
        return f"failed ({review.error_message or 'unknown error'})"
    return review.status.value


def _reviewers_summary(report: ForgeBenchReport) -> str:
    reviewers = report.specialized_reviewers
    if not reviewers.enabled:
        return "not run"
    finding_count = len(reviewers.findings)
    if finding_count:
        return f"completed, findings={finding_count}"
    return "completed, no additional findings"


if __name__ == "__main__":
    raise SystemExit(main())
