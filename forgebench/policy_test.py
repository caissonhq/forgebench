from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from forgebench.policy_audit import record_policy_audit_event
from forgebench.policy_simulation import PolicySimulationResult, simulate_policy


class PolicyTestError(ValueError):
    pass


@dataclass
class PolicyTestExpectation:
    posture: str | None = None
    suppressed_findings: list[str] = field(default_factory=list)
    required_findings: list[str] = field(default_factory=list)
    forbidden_findings: list[str] = field(default_factory=list)
    posture_ceiling: str | None = None
    active_categories: list[str] = field(default_factory=list)
    formal_must_pass: bool = True


@dataclass
class PolicyTestCase:
    name: str
    directory: Path
    guardrails_path: Path
    diff_path: Path
    task_path: Path | None
    expectation: PolicyTestExpectation


@dataclass
class PolicyTestCaseResult:
    name: str
    passed: bool
    errors: list[str] = field(default_factory=list)
    simulation: PolicySimulationResult | None = None


@dataclass(frozen=True)
class PolicyTestRunResult:
    cases: list[PolicyTestCaseResult]

    @property
    def passed_count(self) -> int:
        return sum(1 for case in self.cases if case.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for case in self.cases if not case.passed)


def discover_policy_tests(tests_dir: str | Path) -> list[PolicyTestCase]:
    root = Path(tests_dir)
    if not root.exists():
        raise PolicyTestError(f"Policy tests directory not found: {root}")
    cases: list[PolicyTestCase] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        spec_path = child / "policy_test.json"
        if not spec_path.exists():
            continue
        cases.append(_load_policy_test_case(child, spec_path))
    if not cases:
        raise PolicyTestError(f"No policy_test.json cases found under {root}")
    return cases


def run_policy_tests(
    tests_dir: str | Path,
    *,
    repo_path: str | Path = ".",
    audit: bool = True,
) -> PolicyTestRunResult:
    cases = discover_policy_tests(tests_dir)
    results: list[PolicyTestCaseResult] = []
    for case in cases:
        result = _run_single_policy_test(case, repo_path=repo_path)
        results.append(result)
    if audit:
        record_policy_audit_event(
            "policy_test_run",
            payload={
                "tests_dir": str(tests_dir),
                "passed": sum(1 for item in results if item.passed),
                "failed": sum(1 for item in results if not item.passed),
            },
        )
    return PolicyTestRunResult(cases=results)


def format_policy_test_report(result: PolicyTestRunResult) -> str:
    lines = [
        "ForgeBench policy test results",
        "",
        f"Passed: {result.passed_count}/{len(result.cases)}",
        "",
    ]
    for case in result.cases:
        status = "PASS" if case.passed else "FAIL"
        lines.append(f"[{status}] {case.name}")
        for error in case.errors:
            lines.append(f"  - {error}")
    return "\n".join(lines) + "\n"


def _load_policy_test_case(case_dir: Path, spec_path: Path) -> PolicyTestCase:
    try:
        payload = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PolicyTestError(f"Invalid policy test JSON in {spec_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PolicyTestError(f"Policy test root must be an object: {spec_path}")

    name = str(payload.get("name") or case_dir.name)
    guardrails = _resolve_case_path(case_dir, payload.get("guardrails"), "guardrails")
    diff = _resolve_case_path(case_dir, payload.get("diff"), "diff")
    task = _resolve_optional_case_path(case_dir, payload.get("task"))
    expect_payload = payload.get("expect")
    if not isinstance(expect_payload, dict):
        raise PolicyTestError(f"Policy test {name} is missing expect object.")

    expectation = PolicyTestExpectation(
        posture=_optional_str(expect_payload.get("posture")),
        suppressed_findings=_string_list(expect_payload.get("suppressed_findings")),
        required_findings=_string_list(expect_payload.get("required_findings")),
        forbidden_findings=_string_list(expect_payload.get("forbidden_findings")),
        posture_ceiling=_optional_str(expect_payload.get("posture_ceiling")),
        active_categories=_string_list(expect_payload.get("active_categories")),
        formal_must_pass=bool(expect_payload.get("formal_must_pass", True)),
    )
    return PolicyTestCase(
        name=name,
        directory=case_dir,
        guardrails_path=guardrails,
        diff_path=diff,
        task_path=task,
        expectation=expectation,
    )


def _run_single_policy_test(case: PolicyTestCase, *, repo_path: str | Path) -> PolicyTestCaseResult:
    errors: list[str] = []
    simulation = simulate_policy(
        repo_path=repo_path,
        diff_path=case.diff_path,
        guardrails_path=case.guardrails_path,
        task_path=case.task_path,
    )
    expected = case.expectation

    if expected.posture and simulation.posture.value != expected.posture:
        errors.append(f"Expected posture {expected.posture}, got {simulation.posture.value}.")
    if expected.posture_ceiling and simulation.posture_ceiling != expected.posture_ceiling:
        errors.append(
            f"Expected posture ceiling {expected.posture_ceiling}, got {simulation.posture_ceiling}."
        )
    for finding_id in expected.suppressed_findings:
        if finding_id not in simulation.suppressed_findings:
            errors.append(f"Expected suppressed finding missing: {finding_id}.")
    for finding_id in expected.required_findings:
        if finding_id not in simulation.findings:
            errors.append(f"Expected active finding missing: {finding_id}.")
    for finding_id in expected.forbidden_findings:
        if finding_id in simulation.findings:
            errors.append(f"Forbidden finding present: {finding_id}.")
    for category in expected.active_categories:
        if category not in simulation.active_categories:
            errors.append(f"Expected active category missing: {category}.")
    if expected.formal_must_pass and simulation.formal_violations:
        errors.extend(simulation.formal_violations)

    return PolicyTestCaseResult(name=case.name, passed=not errors, errors=errors, simulation=simulation)


def _resolve_case_path(case_dir: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise PolicyTestError(f"Policy test {case_dir.name} is missing {label} path.")
    path = Path(value.strip())
    if not path.is_absolute():
        path = (case_dir / path).resolve()
    if not path.exists():
        raise PolicyTestError(f"Policy test {case_dir.name} references missing {label}: {path}")
    return path


def _resolve_optional_case_path(case_dir: Path, value: Any) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value.strip())
    if not path.is_absolute():
        path = (case_dir / path).resolve()
    return path if path.exists() else None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []