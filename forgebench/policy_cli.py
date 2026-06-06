from __future__ import annotations

import argparse
import json
import sys
import threading
from pathlib import Path

from forgebench.fpl.compiler import compile_fpl_text
from forgebench.grok_verifier import GrokVerifierError, verify_policy_with_grok
from forgebench.policy_audit import export_policy_audit_bundle, policy_audit_status, record_policy_audit_event
from forgebench.policy_service.server import PolicyServiceConfig, serve_policy_service
from forgebench.policy_simulation import simulate_policy
from forgebench.policy_test import PolicyTestError, format_policy_test_report, run_policy_tests
from forgebench.policy_versioning import (
    bump_policy_version,
    load_policy_text_fingerprint,
    read_version_history,
    record_policy_version,
)


def run_policy_command(args: argparse.Namespace) -> int:
    action = args.policy_action
    if action == "test":
        return _run_policy_test(args)
    if action == "simulate":
        return _run_policy_simulate(args)
    if action == "compile":
        return _run_policy_compile(args)
    if action == "serve":
        return _run_policy_serve(args)
    if action == "verify":
        return _run_policy_verify(args)
    if action == "audit":
        return _run_policy_audit(args)
    if action == "version":
        return _run_policy_version(args)
    _fail("policy requires test, simulate, compile, serve, verify, audit, or version.")
    return 2


def _run_policy_test(args: argparse.Namespace) -> int:
    try:
        result = run_policy_tests(args.tests, repo_path=args.repo, audit=not args.no_audit)
    except PolicyTestError as exc:
        _fail(str(exc))
    print(format_policy_test_report(result))
    return 1 if result.failed_count else 0


def _run_policy_simulate(args: argparse.Namespace) -> int:
    try:
        simulation = simulate_policy(
            repo_path=args.repo,
            diff_path=args.diff,
            guardrails_path=args.guardrails,
            task_path=args.task,
            run_checks=args.run_checks,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        _fail(str(exc))
    if not args.no_audit:
        record_policy_audit_event(
            "policy_simulated",
            payload={
                "posture": simulation.posture.value,
                "guardrails": str(args.guardrails),
                "diff": str(args.diff),
            },
        )
    payload = {
        "posture": simulation.posture.value,
        "findings": simulation.findings,
        "suppressed_findings": simulation.suppressed_findings,
        "active_categories": simulation.active_categories,
        "posture_ceiling": simulation.posture_ceiling,
        "policy_version": simulation.policy_version,
        "policy_fingerprint": simulation.policy_fingerprint,
        "formal_obligations": simulation.formal_obligations,
        "formal_violations": simulation.formal_violations,
    }
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Policy simulation written to {output}.")
    else:
        print(json.dumps(payload, indent=2))
    return 1 if simulation.formal_violations else 0


def _run_policy_compile(args: argparse.Namespace) -> int:
    source_path = Path(args.file)
    if not source_path.exists():
        _fail(f"FPL file not found: {source_path}")
    compiled = compile_fpl_text(source_path.read_text(encoding="utf-8", errors="replace"))
    record_policy_audit_event(
        "policy_compiled",
        payload={"source": str(source_path), "fpl_name": compiled.get("fpl_name")},
    )
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(compiled, indent=2) + "\n", encoding="utf-8")
        print(f"Compiled FPL written to {output}.")
    else:
        print(json.dumps(compiled, indent=2))
    return 0


def _run_policy_serve(args: argparse.Namespace) -> int:
    guardrails = Path(args.guardrails) if args.guardrails else None
    config = PolicyServiceConfig(
        host=args.host,
        port=args.port,
        repo_path=Path(args.repo),
        guardrails_path=guardrails,
    )
    print(f"ForgeBench policy service listening on http://{args.host}:{args.port}")
    print("Endpoints: GET /health, GET /v1/policy, POST /v1/policy/validate, POST /v1/policy/simulate, POST /v1/policy/compile-fpl")
    if args.background:
        thread = threading.Thread(target=serve_policy_service, args=(config,), daemon=True)
        thread.start()
        thread.join(timeout=args.timeout)
        return 0
    serve_policy_service(config)
    return 0


def _run_policy_verify(args: argparse.Namespace) -> int:
    try:
        simulation = simulate_policy(
            repo_path=args.repo,
            diff_path=args.diff,
            guardrails_path=args.guardrails,
            task_path=args.task,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        _fail(str(exc))

    policy_summary = {
        "guardrails": str(args.guardrails),
        "policy_version": simulation.policy_version,
        "policy_fingerprint": simulation.policy_fingerprint,
    }
    simulation_summary = {
        "posture": simulation.posture.value,
        "findings": simulation.findings,
        "suppressed_findings": simulation.suppressed_findings,
        "formal_violations": simulation.formal_violations,
    }
    record_policy_audit_event(
        "formal_verification",
        payload={"passed": not simulation.formal_violations, "violations": simulation.formal_violations},
    )

    grok_result = None
    if args.grok:
        mock_response = None
        if args.grok_mock:
            mock_response = {
                "status": "pass",
                "summary": "Mock Grok verification passed.",
                "obligations": simulation.formal_obligations,
                "satisfied": simulation.formal_obligations,
                "unsatisfied": simulation.formal_violations,
            }
        try:
            grok_result = verify_policy_with_grok(
                policy_summary=policy_summary,
                simulation_summary=simulation_summary,
                mock_response=mock_response,
            )
        except GrokVerifierError as exc:
            _fail(str(exc))
        record_policy_audit_event(
            "grok_verification",
            payload={"status": grok_result.status, "provider": grok_result.provider},
        )

    payload = {
        "formal": {
            "obligations": simulation.formal_obligations,
            "violations": simulation.formal_violations,
            "passed": not simulation.formal_violations,
        },
        "grok": None if grok_result is None else {
            "status": grok_result.status,
            "summary": grok_result.summary,
            "satisfied": grok_result.satisfied,
            "unsatisfied": grok_result.unsatisfied,
            "provider": grok_result.provider,
            "model": grok_result.model,
        },
    }
    if args.out:
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Policy verification written to {output}.")
    else:
        print(json.dumps(payload, indent=2))

    failed = bool(simulation.formal_violations)
    if grok_result is not None and grok_result.status == "fail":
        failed = True
    return 1 if failed else 0


def _run_policy_audit(args: argparse.Namespace) -> int:
    if args.export:
        bundle = export_policy_audit_bundle(log_path=args.log_path)
        if args.out:
            output = Path(args.out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
            print(f"Policy audit export written to {output}.")
        else:
            print(json.dumps(bundle, indent=2))
        return 0
    status = policy_audit_status(log_path=args.log_path)
    print("ForgeBench policy audit status")
    print(f"- log: {status.log_path}")
    print(f"- events: {status.event_count}")
    return 0


def _run_policy_version(args: argparse.Namespace) -> int:
    policy_file = Path(args.file)
    if not policy_file.exists():
        _fail(f"policy file not found: {policy_file}")
    text = policy_file.read_text(encoding="utf-8", errors="replace")
    fingerprint = load_policy_text_fingerprint(text)
    history = read_version_history(args.manifest)
    current_version = args.version
    if args.bump:
        current_version = bump_policy_version(current_version or "1.0.0")
    if args.record:
        record_policy_version(
            policy_id=args.policy_id or policy_file.stem,
            version=current_version or "1.0.0",
            fingerprint=fingerprint,
            source_path=policy_file,
            manifest_path=args.manifest,
            parent_version=history[-1].version if history else None,
            change_summary=args.summary or "",
        )
        record_policy_audit_event(
            "policy_version_recorded",
            payload={"policy_id": args.policy_id or policy_file.stem, "version": current_version},
        )
    print(json.dumps({
        "policy_file": str(policy_file),
        "fingerprint": fingerprint,
        "version": current_version,
        "history_count": len(history),
    }, indent=2))
    return 0


def add_policy_subparser(subparsers: argparse._SubParsersAction) -> None:
    policy = subparsers.add_parser("policy", help="Policy language, simulation, verification, and service commands.")
    policy_sub = policy.add_subparsers(dest="policy_action")

    test = policy_sub.add_parser("test", help="Run policy simulation tests.")
    test.add_argument("--tests", required=False, default="examples/policy_tests", help="Policy tests directory.")
    test.add_argument("--repo", required=False, default=".", help="Repository path.")
    test.add_argument("--no-audit", action="store_true", help="Skip policy audit logging.")

    simulate = policy_sub.add_parser("simulate", help="Simulate policy on a diff.")
    simulate.add_argument("--repo", required=False, default=".", help="Repository path.")
    simulate.add_argument("--diff", required=True, help="Unified diff path.")
    simulate.add_argument("--guardrails", required=True, help="forgebench.yml or layered policy path.")
    simulate.add_argument("--task", required=False, help="Optional task prompt path.")
    simulate.add_argument("--run-checks", action="store_true", help="Run configured deterministic checks.")
    simulate.add_argument("--out", required=False, help="Optional JSON output path.")
    simulate.add_argument("--no-audit", action="store_true", help="Skip policy audit logging.")

    compile_cmd = policy_sub.add_parser("compile", help="Compile an .fpl file to JSON policy.")
    compile_cmd.add_argument("file", help="FPL source file.")
    compile_cmd.add_argument("--out", required=False, help="Optional JSON output path.")

    serve = policy_sub.add_parser("serve", help="Start self-hosted policy service skeleton.")
    serve.add_argument("--repo", required=False, default=".", help="Repository path.")
    serve.add_argument("--guardrails", required=False, help="Optional guardrails file path.")
    serve.add_argument("--host", required=False, default="127.0.0.1", help="Bind host.")
    serve.add_argument("--port", type=int, required=False, default=8791, help="Bind port.")
    serve.add_argument("--background", action="store_true", help="Run server in background thread for smoke tests.")
    serve.add_argument("--timeout", type=float, required=False, default=0.5, help="Background serve duration.")

    verify = policy_sub.add_parser("verify", help="Run formal and optional Grok verification hooks.")
    verify.add_argument("--repo", required=False, default=".", help="Repository path.")
    verify.add_argument("--diff", required=True, help="Unified diff path.")
    verify.add_argument("--guardrails", required=True, help="Policy file path.")
    verify.add_argument("--task", required=False, help="Optional task prompt path.")
    verify.add_argument("--grok", action="store_true", help="Run Grok API verification when FORGEBENCH_GROK_API_KEY is set.")
    verify.add_argument("--grok-mock", action="store_true", help="Use mock Grok verification response.")
    verify.add_argument("--out", required=False, help="Optional JSON output path.")

    audit = policy_sub.add_parser("audit", help="Inspect or export policy audit log.")
    audit.add_argument("--export", action="store_true", help="Export audit bundle as JSON.")
    audit.add_argument("--log-path", required=False, help="Policy audit JSONL path.")
    audit.add_argument("--out", required=False, help="Export output path.")

    version = policy_sub.add_parser("version", help="Show or record policy version metadata.")
    version.add_argument("file", help="Policy file (.fpl or forgebench.yml).")
    version.add_argument("--version", required=False, help="Explicit policy version label.")
    version.add_argument("--policy-id", required=False, help="Policy identifier for version manifest.")
    version.add_argument("--manifest", required=False, help="Version manifest JSONL path.")
    version.add_argument("--record", action="store_true", help="Append version record to manifest.")
    version.add_argument("--bump", action="store_true", help="Bump patch version before recording.")
    version.add_argument("--summary", required=False, help="Change summary for version record.")


def _fail(message: str) -> None:
    print(f"ForgeBench error: {message}", file=sys.stderr)
    raise SystemExit(2)