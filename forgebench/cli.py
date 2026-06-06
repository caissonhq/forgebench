from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forgebench import __version__
from forgebench.calibration import format_calibration_result, run_calibration
from forgebench.doctor import format_doctor_report, run_doctor
from forgebench.benchmark import build_benchmark_snapshot, format_benchmark_markdown
from forgebench.benchmark_dashboard import BenchmarkDashboardError, export_benchmark_dashboard
from forgebench.feedback import (
    FeedbackError,
    append_feedback,
    export_feedback_bundle,
    format_feedback_summary,
    suggest_guardrails,
    summarize_feedback,
)
from forgebench.adoption import format_feature_suggestion, format_next_actions, increment_review_count, next_actions_after_review
from forgebench.presets import PresetError, export_preset_bundle, format_preset_list, install_preset, list_presets
from forgebench.quickstart import run_quickstart
from forgebench.share_report import ShareReportError, export_shareable_report
from forgebench.team_cli import add_team_subparser, run_team_command
from forgebench.golden_case_generator import generate_golden_case_candidates
from forgebench.telemetry import disable_telemetry, enable_telemetry, export_telemetry_bundle, telemetry_status
from forgebench.mcp_server import run_mcp_server
from forgebench.github_pr import GitHubPRError, GitHubPRReviewResult, run_github_pr_review
from forgebench.demo import format_demo_result, run_demo
from forgebench.init import InitError, write_starter_guardrails
from forgebench.init_enterprise import (
    EnterpriseInitOptions,
    format_enterprise_init_result,
    run_enterprise_init,
    write_enterprise_manifest,
)
from forgebench.status import build_status_report, format_status_report, print_status_report
from forgebench.ux.explain import explain_error
from forgebench.ux.output import error as ux_error
from forgebench.ux.output import heading, info, success
from forgebench.models import ForgeBenchReport
from forgebench.review import ReviewInputError, run_review
from forgebench.dashboard import DashboardExportError, export_policy_dashboard
from forgebench.mutation import build_mutation_plan
from forgebench.prove_it import behavioral_from_static_signals, export_prove_it_plan, load_report_for_prove_it
from forgebench.github_app_cli import add_github_app_subparser, run_github_app_command
from forgebench.policy_cli import add_policy_subparser, run_policy_command
from forgebench.validate import format_validation_report, validate_guardrails_file
from forgebench.licensing.cli import add_license_subparser, run_license_command
from forgebench.analytics_cli import add_analytics_subparser, maybe_record_cli_command, run_analytics_command


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    maybe_record_cli_command(getattr(args, "command", None))

    if args.command == "license":
        return run_license_command(args)

    if args.command == "analytics":
        return run_analytics_command(args)

    if args.command == "status":
        return _run_status(args)

    if args.command == "demo":
        return _run_demo(args)

    if args.command == "calibrate":
        return _run_calibrate(args)

    if args.command == "doctor":
        return _run_doctor(args)

    if args.command == "quickstart":
        return _run_quickstart(args)

    if args.command == "team":
        return run_team_command(args)

    if args.command == "presets":
        return _run_presets(args)

    if args.command == "share-report":
        return _run_share_report(args)

    if args.command == "init":
        return _run_init(args)

    if args.command == "feedback":
        return _run_feedback(args)

    if args.command == "validate":
        return _run_validate(args)

    if args.command == "dashboard":
        return _run_dashboard(args)

    if args.command == "benchmark":
        return _run_benchmark(args)

    if args.command == "benchmark-dashboard":
        return _run_benchmark_dashboard(args)

    if args.command == "telemetry":
        return _run_telemetry(args)

    if args.command == "data":
        return _run_data(args)

    if args.command == "audit":
        return _run_audit(args)

    if args.command == "policy":
        return run_policy_command(args)

    if args.command == "github-app":
        return run_github_app_command(args)

    if args.command == "repair":
        return _run_repair(args)

    if args.command == "mcp":
        return _run_mcp(args)

    if args.command == "review-pr":
        return _run_review_pr(args)

    if args.command == "prove-it":
        return _run_prove_it(args)

    if args.command == "mutation":
        return _run_mutation(args)

    if args.command != "review":
        parser.print_help()
        return 2

    return _run_review(args)


def _run_doctor(args: argparse.Namespace) -> int:
    report = run_doctor(repo_path=args.repo)
    print(
        format_doctor_report(
            report,
            repo_path=args.repo,
            include_checklist=getattr(args, "checklist", False),
        )
    )
    return report.exit_code


def _run_quickstart(args: argparse.Namespace) -> int:
    result = run_quickstart(
        repo_path=args.repo,
        skip_init=args.skip_init,
        skip_demo=args.skip_demo,
    )
    return result.doctor_exit_code


def _run_presets(args: argparse.Namespace) -> int:
    if args.presets_action == "list":
        print(format_preset_list(list_presets()))
        return 0
    if args.presets_action == "install":
        try:
            path = install_preset(args.name, repo_path=args.repo, force=args.force)
        except PresetError as exc:
            _fail(str(exc), explain=getattr(args, "explain", False))
        success(f"Preset installed: {path}")
        return 0
    if args.presets_action == "export":
        try:
            manifest = export_preset_bundle(args.file, output_dir=args.out or "forgebench-output/preset-export")
        except PresetError as exc:
            _fail(str(exc), explain=getattr(args, "explain", False))
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    _fail("presets requires list, install, or export.")
    return 2


def _run_share_report(args: argparse.Namespace) -> int:
    try:
        result = export_shareable_report(output_dir=args.out, dest=args.dest)
    except ShareReportError as exc:
        _fail(str(exc), explain=getattr(args, "explain", False))
    success(f"Shareable report: {result.html_path}")
    info("Open in a browser or attach to Slack/email. No network upload performed.")
    return 0


def _run_init(args: argparse.Namespace) -> int:
    try:
        if args.enterprise or getattr(args, "team", False):
            from forgebench.adoption import record_milestone
            from forgebench.licensing.quotas import LicenseRequired, require_feature

            try:
                require_feature("init_enterprise")
            except LicenseRequired as exc:
                _fail(str(exc), explain=getattr(args, "explain", False))
            wizard_mode = "team" if getattr(args, "team", False) else "enterprise"
            options = EnterpriseInitOptions(
                org_name=args.org_name,
                team_slug=args.team_slug,
                preset=args.preset,
                enable_github_app=not args.no_github_app,
                enable_ci=not args.no_ci,
                ci_provider=args.ci_provider,
                org_policy_dir=args.org_policy_dir,
                force=args.force,
                non_interactive=args.yes,
                wizard_mode=wizard_mode,
            )
            result = run_enterprise_init(repo_path=args.repo, options=options)
            if args.manifest:
                write_enterprise_manifest(result, Path(args.manifest))
            if wizard_mode == "team":
                record_milestone("first_team_init")
            print(format_enterprise_init_result(result))
            return 0
        result = write_starter_guardrails(repo_path=args.repo, output_path=args.out, force=args.force, preset=args.preset)
    except InitError as exc:
        _fail(str(exc), explain=getattr(args, "explain", False))

    heading("ForgeBench init")
    success("Guardrails file created.")
    info(f"Repo: {result.repo_path}")
    info(f"Output: {result.path}")
    if result.detected:
        info(f"Detected: {', '.join(result.detected)}")
    else:
        info("Detected: no supported project manifest; checks defaulted to null")
    info("Edit protected_behavior and forbidden_patterns before relying on project-specific guardrails.")
    return 0


def _run_status(args: argparse.Namespace) -> int:
    report = build_status_report(repo_path=args.repo)
    if args.json:
        payload = {
            "version": report.version,
            "ready": report.doctor.ready,
            "guardrails_path": str(report.guardrails_path) if report.guardrails_path else None,
            "ci_guardrails_path": str(report.ci_guardrails_path) if report.ci_guardrails_path else None,
            "policy_tests_present": report.policy_tests_present,
            "telemetry_enabled": report.telemetry_enabled,
            "recommendations": report.recommendations,
            "checks": [
                {"name": c.name, "status": c.status.value, "message": c.message}
                for c in report.doctor.checks
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if report.doctor.ready else 2
    if args.plain:
        print(format_status_report(report))
    else:
        print_status_report(report)
    if getattr(args, "explain", False):
        info("")
        info("Status explains repository readiness. Run forgebench doctor for fix hints per check.")
    return 0 if report.doctor.ready else 2


def _run_demo(args: argparse.Namespace) -> int:
    import os

    plain_env = os.environ.get("FORGEBENCH_PLAIN_OUTPUT", "")
    if args.json:
        os.environ["FORGEBENCH_PLAIN_OUTPUT"] = "1"
    try:
        result = run_demo(repo_path=args.repo, output_dir=args.out, case_name=args.case)
    except ReviewInputError as exc:
        _fail(str(exc), explain=getattr(args, "explain", False))
    finally:
        if args.json:
            if plain_env:
                os.environ["FORGEBENCH_PLAIN_OUTPUT"] = plain_env
            else:
                os.environ.pop("FORGEBENCH_PLAIN_OUTPUT", None)
    if args.json:
        print(
            json.dumps(
                {
                    "case": result.case_name,
                    "posture": result.posture,
                    "finding_count": result.finding_count,
                    "report_markdown": str(result.report_markdown),
                    "report_json": str(result.report_json),
                },
                indent=2,
            )
        )
        return 0
    print(format_demo_result(result))
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
            semantic_analysis=not args.no_semantic_analysis,
            prove_it=args.prove_it,
            llm_ensemble_models=_parse_ensemble_models(args.llm_ensemble),
            llm_ensemble_strategy=args.llm_ensemble_strategy,
        )
    except ReviewInputError as exc:
        _fail(str(exc), explain=getattr(args, "explain", False))

    _print_summary(result.report, result.written_paths, guardrails_explicit=bool(args.guardrails))
    if "prove_it_plan" in result.written_paths:
        print()
        print("Prove-it artifacts:")
        print(f"- {result.written_paths['prove_it_plan']}")
        print(f"- {result.written_paths['prove_it_checklist']}")
    print()
    print(f"Paste repair prompt: forgebench repair --out {result.output_dir}")
    increment_review_count()
    actions = next_actions_after_review(
        posture=result.report.posture.value,
        config_mode=result.report.config_mode,
        finding_count=len(result.report.findings),
    )
    print()
    print(format_next_actions(actions))
    return 0


def _run_benchmark(args: argparse.Namespace) -> int:
    outcomes_path = args.outcomes or None
    try:
        snapshot = build_benchmark_snapshot(
            args.cases,
            repo_path=args.repo,
            output_dir=args.out,
            outcomes_path=outcomes_path,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        _fail(str(exc))
    try:
        from forgebench.telemetry import record_telemetry_event

        record_telemetry_event(
            "benchmark_run",
            {
                "case_count": snapshot.case_count,
                "failed_count": snapshot.failed_count,
                "has_pr_outcomes": snapshot.pr_outcomes is not None,
            },
        )
    except Exception:
        pass
    markdown = format_benchmark_markdown(snapshot, cases_dir=args.cases)
    if args.out_markdown:
        output = Path(args.out_markdown)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        print(f"Merge Risk Benchmark written to {output}.")
    else:
        print(markdown)
    return 1 if snapshot.failed_count else 0


def _run_benchmark_dashboard(args: argparse.Namespace) -> int:
    outcomes_path = args.outcomes or None
    try:
        result = export_benchmark_dashboard(
            cases_dir=args.cases,
            repo_path=args.repo,
            calibration_output_dir=args.calibration_out,
            outcomes_path=outcomes_path,
            output_dir=args.out,
            include_telemetry=not args.no_telemetry,
        )
    except (BenchmarkDashboardError, FileNotFoundError, ValueError, OSError) as exc:
        _fail(str(exc))
    print("ForgeBench benchmark dashboard exported.")
    print(f"- HTML: {result.index_path}")
    print(f"- Manifest: {result.manifest_path}")
    return 0


def _run_telemetry(args: argparse.Namespace) -> int:
    action = args.telemetry_action
    if action == "enable":
        path = enable_telemetry(flag_path=args.flag_path)
        print("ForgeBench telemetry enabled (opt-in, local-only, anonymized).")
        print(f"Flag: {path}")
        print("Set FORGEBENCH_TELEMETRY=1 in CI to enable without writing a flag file.")
        return 0
    if action == "disable":
        disable_telemetry(flag_path=args.flag_path)
        print("ForgeBench telemetry disabled.")
        return 0
    if action == "status":
        status = telemetry_status(log_path=args.log_path)
        print("ForgeBench telemetry status")
        print(f"- enabled: {status.enabled}")
        print(f"- log: {status.log_path}")
        print(f"- events: {status.event_count}")
        return 0
    if action == "export":
        bundle = export_telemetry_bundle(log_path=args.log_path)
        if args.out:
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"ForgeBench telemetry export written to {output}.")
        else:
            print(json.dumps(bundle, indent=2, sort_keys=True))
        return 0
    _fail("telemetry requires enable, disable, status, or export.")
    return 2


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
            prove_it=args.prove_it,
            llm_ensemble_models=_parse_ensemble_models(args.llm_ensemble),
            llm_ensemble_strategy=args.llm_ensemble_strategy,
            trust_pr_guardrails=args.trust_pr_guardrails,
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


def _run_prove_it(args: argparse.Namespace) -> int:
    report_path = Path(args.report)
    if not report_path.exists():
        _fail(f"report not found: {report_path}")
    report = load_report_for_prove_it(report_path)
    behavioral = behavioral_from_static_signals(report.static_signals)
    if not behavioral.enabled:
        _fail("Report has no semantic analysis signals. Re-run review without --no-semantic-analysis.")
    result = export_prove_it_plan(
        report=report,
        behavioral=behavioral,
        llm_config=None,
        output_dir=args.out,
    )
    print("ForgeBench prove-it plan exported.")
    print(f"- Plan: {result.plan_path}")
    print(f"- Checklist: {result.checklist_path}")
    return 0


def _run_mutation(args: argparse.Namespace) -> int:
    report_path = Path(args.report)
    if not report_path.exists():
        _fail(f"report not found: {report_path}")
    report = load_report_for_prove_it(report_path)
    behavioral = behavioral_from_static_signals(report.static_signals)
    if not behavioral.changed_symbols:
        _fail("Report has no changed symbols for mutation planning.")
    result = build_mutation_plan(behavioral, output_dir=args.out)
    print("ForgeBench mutation plan exported.")
    print(f"- Plan: {result.plan_path}")
    print(f"- Candidates: {result.candidate_count}")
    return 0


def _run_dashboard(args: argparse.Namespace) -> int:
    try:
        result = export_policy_dashboard(
            args.repo,
            guardrails_path=args.guardrails,
            output_dir=args.out,
        )
    except DashboardExportError as exc:
        _fail(str(exc))
    print("ForgeBench policy dashboard exported.")
    print(f"- HTML: {result.index_path}")
    print(f"- Manifest: {result.manifest_path}")
    if result.guardrails_path:
        print(f"- Guardrails: {result.guardrails_path}")
    return 0


def _run_calibrate(args: argparse.Namespace) -> int:
    try:
        result = run_calibration(cases_dir=args.cases, output_dir=args.out, repo_path=args.repo)
    except (FileNotFoundError, ValueError, OSError) as exc:
        _fail(str(exc))

    print(format_calibration_result(result))
    return 1 if result.failed_count else 0


def _run_feedback(args: argparse.Namespace) -> int:
    if args.generate_golden_cases:
        result = generate_golden_case_candidates(
            [args.feedback_log],
            output_dir=args.out or "forgebench-output/golden-case-candidates",
        )
        print("ForgeBench golden case candidates generated.")
        print(f"- Output: {result.output_dir}")
        print(f"- Candidates: {len(result.candidates)}")
        print(f"- Skipped: {result.skipped_count}")
        print(f"- Manifest: {result.manifest_path}")
        print("Human review required before promoting cases to examples/golden_cases/.")
        return 0

    if args.export:
        bundle = export_feedback_bundle(
            [args.feedback_log],
            repo_name=args.repo_name,
            source=args.source or "forgebench-beta",
        )
        if args.out:
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(f"ForgeBench feedback export written to {output}.")
        else:
            print(json.dumps(bundle, indent=2, sort_keys=True))
        return 0

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

    if getattr(args, "suggest", False):
        text = format_feature_suggestion(
            title=args.note or "",
            description=getattr(args, "feature_description", "") or "",
            use_case=args.workflow or "",
        )
        if args.out:
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(text, encoding="utf-8")
            print(f"Feature suggestion template written to {output}.")
        else:
            print(text)
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
            posture=args.posture,
            agent_tool=args.agent,
            workflow=args.workflow,
            finding_count=args.finding_count,
            review_command=args.review_command,
            severity=args.severity,
            confidence=args.confidence,
            files=args.files,
            expected_posture=args.expected_posture,
            outcome_label=args.outcome_label,
            reviewer_lens=args.reviewer_lens,
            case_slug=args.case_slug,
        )
    except FeedbackError as exc:
        _fail(str(exc))
    try:
        from forgebench.telemetry import record_telemetry_event

        record_telemetry_event(
            "feedback_recorded",
            {
                "status": args.status,
                "kind": args.kind,
                "fb_version": 3 if any(
                    value is not None
                    for value in (
                        args.severity,
                        args.confidence,
                        args.files,
                        args.expected_posture,
                        args.outcome_label,
                        args.reviewer_lens,
                        args.case_slug,
                    )
                ) else (2 if any(
                    value is not None
                    for value in (args.posture, args.agent, args.workflow, args.finding_count, args.review_command)
                ) else 1),
            },
        )
    except Exception:
        pass
    print("ForgeBench feedback recorded.")
    print(f"Log: {path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forgebench",
        description="Adversarial pre-merge QA for coding-agent output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  forgebench quickstart\n"
            "  forgebench doctor --checklist\n"
            "  forgebench demo\n"
            "  forgebench status\n"
            "  forgebench team init\n"
            "  forgebench init --enterprise\n"
            "  forgebench review --repo . --diff patch.diff --task task.md\n"
            "\n"
            "Use --explain on any command for actionable error suggestions."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--explain",
        action="store_true",
        help="When an error occurs, print an actionable explanation and remediation hint.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    status = subparsers.add_parser(
        "status",
        help="Show repository health summary and recommended next steps.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Summarize ForgeBench readiness for the current repository.",
    )
    status.add_argument("--repo", required=False, default=".", help="Repository path. Defaults to current directory.")
    status.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    status.add_argument("--plain", action="store_true", help="Plain text output without ANSI colors.")
    status.add_argument("--explain", action="store_true", help="Include extended guidance in output.")

    demo = subparsers.add_parser(
        "demo",
        help="Run a guided realistic review using a bundled golden case.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="One-command demo for new users. No guardrails or network required.",
    )
    demo.add_argument("--repo", required=False, default=".", help="Repository path. Defaults to current directory.")
    demo.add_argument("--out", required=False, help="Output directory. Defaults to forgebench-output/demo.")
    demo.add_argument(
        "--case",
        required=False,
        default="generic_dependency_without_tests_review",
        help="Golden case slug under examples/golden_cases/.",
    )
    demo.add_argument("--json", action="store_true", help="Emit machine-readable JSON summary.")

    doctor = subparsers.add_parser("doctor", help="Verify local install, tooling, and first-run readiness.")
    doctor.add_argument("--repo", required=False, default=".", help="Repository path to inspect. Defaults to current directory.")
    doctor.add_argument("--checklist", action="store_true", help="Show adoption success checklist and milestone progress.")

    quickstart = subparsers.add_parser(
        "quickstart",
        help="Solo developer onboarding — doctor, demo, status, and starter guardrails.",
    )
    quickstart.add_argument("--repo", required=False, default=".", help="Repository path.")
    quickstart.add_argument("--skip-init", action="store_true", help="Skip forgebench.yml creation.")
    quickstart.add_argument("--skip-demo", action="store_true", help="Skip guided demo review.")

    init = subparsers.add_parser(
        "init",
        help="Write starter guardrails or an enterprise team kit.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Create forgebench.yml for a repo, or --enterprise for org policy, CI, and onboarding docs.",
    )
    init.add_argument("--repo", required=False, default=".", help="Repository to inspect. Defaults to current directory.")
    init.add_argument("--out", required=False, default="forgebench.yml", help="Output guardrails path. Defaults to forgebench.yml in the repo.")
    init.add_argument("--force", action="store_true", help="Overwrite the output file if it already exists.")
    init.add_argument(
        "--preset",
        choices=["auto", "python", "node", "nextjs", "swift", "rust"],
        default="auto",
        help="Starter guardrails preset. Defaults to auto.",
    )
    init.add_argument("--enterprise", action="store_true", help="Generate org policy, CI workflow, and team onboarding kit.")
    init.add_argument("--team", action="store_true", help="Alias for team init wizard (same as forgebench team init).")
    init.add_argument("--org-name", required=False, default="Acme Engineering", help="Organization name for enterprise init.")
    init.add_argument("--team-slug", required=False, default="platform", help="Team slug for enterprise policy paths.")
    init.add_argument("--org-policy-dir", required=False, default="org-policy", help="Directory for org-wide policy file.")
    init.add_argument("--ci-provider", choices=["github-actions"], default="github-actions", help="CI provider for enterprise init.")
    init.add_argument("--no-github-app", action="store_true", help="Omit GitHub App notes from onboarding docs.")
    init.add_argument("--no-ci", action="store_true", help="Skip CI workflow and .github/forgebench.yml generation.")
    init.add_argument("--yes", action="store_true", help="Non-interactive enterprise init (use flag defaults).")
    init.add_argument("--manifest", required=False, help="Write enterprise-init-manifest.json to this path.")

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
    _add_semantic_llm_flags(review)

    review_pr = subparsers.add_parser("review-pr", help="Fetch a GitHub PR diff, run ForgeBench, and optionally post a PR comment.")
    review_pr.add_argument("pr_url", nargs="?", help="GitHub pull request URL.")
    review_pr.add_argument("--repo", required=False, default=".", help="Local repository path. Defaults to current directory.")
    review_pr.add_argument("--pr-url", dest="pr_url_option", required=False, help="GitHub pull request URL. Kept for compatibility; positional URL is preferred.")
    review_pr.add_argument("--guardrails", required=False, help="Optional path to forgebench.yml. Required with --run-checks (trusted base-branch policy).")
    review_pr.add_argument(
        "--trust-pr-guardrails",
        action="store_true",
        help="Allow --guardrails inside the PR worktree when --run-checks is passed. Not recommended for fork PRs.",
    )
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
    _add_semantic_llm_flags(review_pr)

    prove_it = subparsers.add_parser("prove-it", help="Export prove-it checklist and plan from a ForgeBench report.")
    prove_it.add_argument("--report", required=False, default="forgebench-output/forgebench-report.json", help="Report JSON path.")
    prove_it.add_argument("--out", required=False, default="forgebench-output/prove-it", help="Output directory.")

    mutation = subparsers.add_parser("mutation", help="Export mutation testing plan skeleton from a ForgeBench report.")
    mutation.add_argument("action", nargs="?", choices=["plan"], default="plan", help="Mutation action. Only plan is supported.")
    mutation.add_argument("--report", required=False, default="forgebench-output/forgebench-report.json", help="Report JSON path.")
    mutation.add_argument("--out", required=False, default="forgebench-output/mutation", help="Output directory.")

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
    feedback.add_argument("--suggest", action="store_true", help="Print a feature-request template for GitHub Discussions.")
    feedback.add_argument("--feature-description", required=False, help="Problem description for --suggest template.")
    feedback.add_argument("--export", action="store_true", help="Export structured beta feedback bundle as JSON.")
    feedback.add_argument("--posture", required=False, choices=["BLOCK", "REVIEW", "LOW_CONCERN"], help="Optional review posture for structured beta feedback.")
    feedback.add_argument("--agent", required=False, choices=["cursor", "codex", "claude", "copilot", "other"], help="Optional coding agent label for structured beta feedback.")
    feedback.add_argument("--workflow", required=False, help="Optional workflow label, such as review_then_repair.")
    feedback.add_argument("--finding-count", type=int, required=False, help="Optional finding count from the reviewed report.")
    feedback.add_argument("--review-command", required=False, help="Optional command used to produce the reviewed report.")
    feedback.add_argument("--severity", required=False, choices=["low", "medium", "high", "critical"], help="Structured feedback v3 severity.")
    feedback.add_argument("--confidence", required=False, choices=["low", "medium", "high"], help="Structured feedback v3 confidence.")
    feedback.add_argument("--files", nargs="*", required=False, help="Structured feedback v3 affected file paths.")
    feedback.add_argument("--expected-posture", required=False, choices=["BLOCK", "REVIEW", "LOW_CONCERN"], help="Expected merge posture for calibration.")
    feedback.add_argument(
        "--outcome-label",
        required=False,
        choices=["false_positive", "true_positive", "missed_concern", "noise", "calibration_gap", "other"],
        help="Structured feedback v3 outcome label.",
    )
    feedback.add_argument("--reviewer-lens", required=False, help="Reviewer lens that produced the finding.")
    feedback.add_argument("--case-slug", required=False, help="Optional golden case slug for linking feedback to calibration.")
    feedback.add_argument("--generate-golden-cases", action="store_true", help="Generate draft golden cases from dismissed/wrong feedback.")
    feedback.add_argument("--out", required=False, help="Optional output path for export, suggestions, or other write modes.")

    benchmark = subparsers.add_parser("benchmark", help="Run the Merge Risk Benchmark and print publishable summary Markdown.")
    benchmark.add_argument("--cases", required=False, default="examples/golden_cases", help="Golden cases directory.")
    benchmark.add_argument("--repo", required=False, default=".", help="Repo root for configured checks.")
    benchmark.add_argument("--out", required=False, default="forgebench-benchmark-output", help="Calibration output directory.")
    benchmark.add_argument("--out-markdown", required=False, help="Optional path to write benchmark Markdown.")
    benchmark.add_argument(
        "--outcomes",
        required=False,
        default="examples/benchmark_outcomes/eo002-pr-outcomes.json",
        help="Anonymized real PR outcomes JSON. Pass empty string to skip.",
    )

    benchmark_dashboard = subparsers.add_parser(
        "benchmark-dashboard",
        help="Export public Merge Risk Benchmark dashboard (static HTML + JSON manifest).",
    )
    benchmark_dashboard.add_argument("--cases", required=False, default="examples/golden_cases", help="Golden cases directory.")
    benchmark_dashboard.add_argument("--repo", required=False, default=".", help="Repo root for configured checks.")
    benchmark_dashboard.add_argument("--calibration-out", required=False, default="forgebench-benchmark-output", help="Calibration output directory.")
    benchmark_dashboard.add_argument(
        "--outcomes",
        required=False,
        default="examples/benchmark_outcomes/eo002-pr-outcomes.json",
        help="Anonymized real PR outcomes JSON. Pass empty string to skip.",
    )
    benchmark_dashboard.add_argument(
        "--out",
        required=False,
        help="Output directory. Defaults to ./forgebench-output/benchmark-dashboard/.",
    )
    benchmark_dashboard.add_argument("--no-telemetry", action="store_true", help="Omit telemetry summary section from manifest.")

    telemetry = subparsers.add_parser("telemetry", help="Manage opt-in local anonymized telemetry.")
    telemetry.add_argument("telemetry_action", choices=["enable", "disable", "status", "export"], help="Telemetry action.")
    telemetry.add_argument("--flag-path", required=False, help="Optional path for .telemetry-enabled flag file.")
    telemetry.add_argument("--log-path", required=False, help="Optional telemetry JSONL log path.")
    telemetry.add_argument("--out", required=False, help="Output path for telemetry export JSON.")

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

    dashboard = subparsers.add_parser("dashboard", help="Export a local policy dashboard skeleton from forgebench.yml.")
    dashboard.add_argument("--repo", required=False, default=".", help="Repository path. Defaults to current directory.")
    dashboard.add_argument("--guardrails", required=False, help="Optional path to forgebench.yml.")
    dashboard.add_argument(
        "--out",
        required=False,
        help="Output directory. Defaults to ./forgebench-output/policy-dashboard/.",
    )

    data = subparsers.add_parser("data", help="Local data retention and privacy utilities.")
    data_sub = data.add_subparsers(dest="data_action")
    retention = data_sub.add_parser("retention", help="Purge telemetry and feedback older than max age.")
    retention.add_argument("--max-age-days", type=int, default=90, help="Delete records older than this many days.")
    retention.add_argument("--dry-run", action="store_true", help="Report what would be deleted without writing.")

    audit = subparsers.add_parser("audit", help="Tamper-evident audit chain utilities.")
    audit_sub = audit.add_subparsers(dest="audit_action")
    verify = audit_sub.add_parser("verify", help="Verify audit-chain.jsonl integrity.")
    verify.add_argument("--log-path", required=False, help="Audit chain JSONL path.")

    presets = subparsers.add_parser("presets", help="Browse and install curated guardrail presets.")
    presets_sub = presets.add_subparsers(dest="presets_action")
    presets_list = presets_sub.add_parser("list", help="List bundled guardrail presets.")
    presets_install = presets_sub.add_parser("install", help="Install a preset into the current repo.")
    presets_install.add_argument("name", help="Preset name (e.g. python, node, nextjs).")
    presets_install.add_argument("--repo", required=False, default=".", help="Repository path.")
    presets_install.add_argument("--force", action="store_true", help="Overwrite existing files.")
    presets_export = presets_sub.add_parser("export", help="Export local forgebench.yml as a shareable preset bundle.")
    presets_export.add_argument("--file", required=False, default="forgebench.yml", help="Guardrails file to export.")
    presets_export.add_argument("--out", required=False, help="Output directory.")

    share_report = subparsers.add_parser("share-report", help="Generate a clean shareable HTML report from review output.")
    share_report.add_argument("--out", required=False, default="forgebench-output", help="Review output directory.")
    share_report.add_argument("--dest", required=False, help="Optional HTML output path.")

    add_team_subparser(subparsers)
    add_policy_subparser(subparsers)
    add_github_app_subparser(subparsers)
    add_license_subparser(subparsers)
    add_analytics_subparser(subparsers)

    return parser


def _run_data(args: argparse.Namespace) -> int:
    if args.data_action == "retention":
        from forgebench.data_retention import apply_data_retention_policy

        report = apply_data_retention_policy(max_age_days=args.max_age_days, dry_run=args.dry_run)
        print(json.dumps(report, indent=2))
        return 0
    _fail("data requires retention.")
    return 2


def _run_audit(args: argparse.Namespace) -> int:
    if args.audit_action == "verify":
        from forgebench.audit_chain import verify_audit_chain

        ok, errors = verify_audit_chain(log_path=args.log_path)
        if ok:
            print("Audit chain integrity: OK")
            return 0
        print("Audit chain integrity: FAILED")
        for item in errors:
            print(f"- {item}")
        return 1
    _fail("audit requires verify.")
    return 2


def _add_semantic_llm_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--llm-ensemble",
        required=False,
        help="Comma-separated OpenAI-compatible model list for ensemble review. Defaults to FORGEBENCH_LLM_ENSEMBLE_MODELS.",
    )
    parser.add_argument(
        "--llm-ensemble-strategy",
        required=False,
        choices=["consensus", "first_success"],
        help="Ensemble merge strategy. Defaults to FORGEBENCH_LLM_ENSEMBLE_STRATEGY or consensus.",
    )
    parser.add_argument(
        "--prove-it",
        action="store_true",
        help="Export prove-it mode skeleton artifacts (mutation plan + evidence checklist).",
    )
    parser.add_argument(
        "--no-semantic-analysis",
        action="store_true",
        help="Disable tree-sitter/AST semantic diff analysis.",
    )


def _parse_ensemble_models(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    models = [item.strip() for item in raw.split(",") if item.strip()]
    return models or None


def _fail(message: str, *, explain: bool = False) -> None:
    ux_error(message)
    hint = explain_error(message)
    if explain and hint:
        info(f"Suggestion: {hint}")
    elif hint and sys.stderr.isatty():
        print(f"Hint: {hint}", file=sys.stderr)
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
