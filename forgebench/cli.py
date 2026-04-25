from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forgebench.calibration import format_calibration_result, run_calibration
from forgebench.models import ForgeBenchReport
from forgebench.review import ReviewInputError, run_review


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "calibrate":
        return _run_calibrate(args)

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
        )
    except ReviewInputError as exc:
        _fail(str(exc))

    _print_summary(result.report, result.written_paths)
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
    print()
    print("Findings:")
    if report.findings:
        for finding in report.findings:
            print(f"- {finding.severity.value}: {finding.title}")
    else:
        print("- No findings.")
    print()
    print(f"Deterministic checks: {_checks_summary(report)}")
    print()
    print("Reports written:")
    print(f"- {written['markdown']}")
    print(f"- {written['json']}")
    print(f"- {written['repair_prompt']}")


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


if __name__ == "__main__":
    raise SystemExit(main())
