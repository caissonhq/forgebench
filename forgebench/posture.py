from __future__ import annotations

from forgebench.models import CheckStatus, Confidence, DeterministicChecks, EvidenceType, Finding, MergePosture, PolicyDecision, Severity


def determine_posture(
    findings: list[Finding],
    static_signals: dict[str, object],
    guardrail_hits: list[str],
    deterministic_checks: DeterministicChecks | None = None,
    policy_decision: PolicyDecision | None = None,
    config_mode: str = "configured",
) -> tuple[MergePosture, str]:
    posture, summary = _determine_posture(findings, static_signals, guardrail_hits, deterministic_checks, config_mode)
    return _apply_posture_ceiling(posture, summary, findings, policy_decision)


def _determine_posture(
    findings: list[Finding],
    static_signals: dict[str, object],
    guardrail_hits: list[str],
    deterministic_checks: DeterministicChecks | None = None,
    config_mode: str = "configured",
) -> tuple[MergePosture, str]:
    finding_ids = {finding.id for finding in findings}
    tests_changed = bool(static_signals.get("tests_changed"))
    dependency_files = static_signals.get("dependency_files_changed") or []
    persistence_files = static_signals.get("persistence_or_schema_files_changed") or []
    generic_mode = config_mode == "generic"

    if any(finding.severity == Severity.BLOCKER for finding in findings):
        return (
            MergePosture.BLOCK,
            _with_check_context(
                "Do not merge. ForgeBench found a blocker-level issue that needs repair before review should continue.",
                deterministic_checks,
            ),
        )

    high_confidence_high_findings = [
        finding
        for finding in findings
        if finding.severity == Severity.HIGH and finding.confidence == Confidence.HIGH
    ]
    block_ids = {"deleted_tests", "forbidden_pattern_added"}
    if any(finding.id in block_ids for finding in high_confidence_high_findings):
        return (
            MergePosture.BLOCK,
            _with_check_context(
                "Do not merge yet. ForgeBench found a high-confidence merge risk, such as deleted tests or a forbidden pattern in added code.",
                deterministic_checks,
            ),
        )

    if persistence_files and not tests_changed and (not generic_mode or _has_strong_generic_persistence_path(persistence_files)):
        return (
            MergePosture.BLOCK,
            _with_check_context(
                "Do not merge yet. The patch changes likely persistence or schema behavior without corresponding test coverage.",
                deterministic_checks,
            ),
        )

    if dependency_files and not tests_changed and not generic_mode:
        return (
            MergePosture.BLOCK,
            _with_check_context(
                "Do not merge yet. The patch changes dependency surface without corresponding test coverage or validation evidence.",
                deterministic_checks,
            ),
        )

    timed_out_ids = {"build_timed_out", "tests_timed_out", "lint_timed_out", "typecheck_timed_out", "custom_check_timed_out"}
    if finding_ids & timed_out_ids:
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. At least one configured deterministic check timed out, so local verification is incomplete.",
                deterministic_checks,
            ),
        )

    if "lint_failed" in finding_ids:
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. The patch has no build, test, or typecheck blocker, but a configured quality check failed.",
                deterministic_checks,
            ),
        )

    if any(finding.severity == Severity.HIGH for finding in findings):
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. The patch may be valid, but ForgeBench found high-severity risk that needs human review.",
                deterministic_checks,
            ),
        )

    medium_count = sum(1 for finding in findings if finding.severity == Severity.MEDIUM)
    if medium_count >= 2:
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. Multiple static signals indicate risk even though ForgeBench did not find a deterministic blocker.",
                deterministic_checks,
            ),
        )

    if any(finding.evidence_type == EvidenceType.REVIEWER and finding.severity == Severity.MEDIUM for finding in findings):
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. A heuristic review lens found a medium-severity risk that should be checked by a human.",
                deterministic_checks,
            ),
        )

    if any(finding.evidence_type == EvidenceType.LLM and finding.reviewer and finding.severity == Severity.MEDIUM for finding in findings):
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. An opt-in LLM-assisted review lens raised a medium-severity advisory concern. "
                "This cannot block merge by itself and should be checked by a human.",
                deterministic_checks,
            ),
        )

    if "implementation_without_tests" in finding_ids:
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. The patch may be valid, but it changes implementation behavior without test updates.",
                deterministic_checks,
            ),
        )

    if "broad_file_surface" in finding_ids and not (
        generic_mode and _generic_broad_surface_without_code_or_config_risk(finding_ids, static_signals)
    ):
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. The patch touches a broad file surface and should be inspected for unrelated changes.",
                deterministic_checks,
            ),
        )

    review_ids = {"build_config_changed", "generated_files_changed"}
    if finding_ids & review_ids:
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. ForgeBench found static signals that can affect build behavior or add review noise.",
                deterministic_checks,
            ),
        )

    if "tests_assertions_removed_without_replacement" in finding_ids:
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. The patch removes test assertions without a clear replacement.",
                deterministic_checks,
            ),
        )

    if guardrail_hits:
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. Project guardrails were hit and should be checked against the original task.",
                deterministic_checks,
            ),
        )

    if dependency_files:
        return (
            MergePosture.REVIEW,
            _with_check_context(
                "Review before merge. The dependency surface changed, so build and install behavior should be checked.",
                deterministic_checks,
            ),
        )

    return (
        MergePosture.LOW_CONCERN,
        _low_concern_summary(deterministic_checks),
    )


def _has_strong_generic_persistence_path(paths: object) -> bool:
    if not isinstance(paths, list):
        return False
    return any(_is_strong_generic_persistence_path(str(path)) for path in paths)


def _is_strong_generic_persistence_path(path: str) -> bool:
    lower = path.replace("\\", "/").lower()
    markers = (
        "migration",
        "migrations",
        "schema",
        "database",
        "prisma",
        "drizzle",
        "alembic",
        "coredata",
        "swiftdata",
    )
    if lower.endswith(".sql"):
        return True
    if any(marker in lower for marker in markers):
        return True
    tokens = [token for token in lower.replace(".", "/").replace("_", "/").replace("-", "/").split("/") if token]
    return "db" in tokens


def _generic_broad_surface_without_code_or_config_risk(finding_ids: set[str], static_signals: dict[str, object]) -> bool:
    if finding_ids & {"implementation_without_tests", "build_config_changed", "dependency_surface_changed", "persistence_schema_changed"}:
        return False
    return bool(static_signals.get("broad_file_surface_low_noise"))


def _apply_posture_ceiling(
    posture: MergePosture,
    summary: str,
    findings: list[Finding],
    policy_decision: PolicyDecision | None,
) -> tuple[MergePosture, str]:
    if policy_decision is None or policy_decision.posture_ceiling is None:
        return posture, summary
    if _posture_rank(posture) <= _posture_rank(policy_decision.posture_ceiling):
        return posture, summary
    if _ceiling_bypass_present(findings):
        return posture, summary
    reason = policy_decision.posture_ceiling_reason or "Guardrails policy capped this posture."
    if policy_decision.posture_ceiling == MergePosture.LOW_CONCERN:
        capped_summary = (
            f"Low concern after guardrails calibration. {reason} "
            "ForgeBench found no high-confidence merge blockers after applying repo policy, "
            "but this is not a substitute for human review."
        )
    else:
        capped_summary = f"Review before merge after guardrails calibration. {reason}"
    return policy_decision.posture_ceiling, capped_summary


def _posture_rank(posture: MergePosture) -> int:
    return {
        MergePosture.LOW_CONCERN: 0,
        MergePosture.REVIEW: 1,
        MergePosture.BLOCK: 2,
    }[posture]


def _ceiling_bypass_present(findings: list[Finding]) -> bool:
    bypass_ids = {
        "deleted_tests",
        "forbidden_pattern_added",
        "high_risk_guardrail_file",
        "build_failed",
        "tests_failed",
        "typecheck_failed",
        "custom_check_failed",
        "build_timed_out",
        "tests_timed_out",
        "typecheck_timed_out",
        "custom_check_timed_out",
    }
    if any(finding.severity == Severity.BLOCKER for finding in findings):
        return True
    if any(finding.id in bypass_ids for finding in findings):
        return True
    return any(finding.evidence_type == EvidenceType.DETERMINISTIC for finding in findings)


def _with_check_context(summary: str, deterministic_checks: DeterministicChecks | None) -> str:
    context = _check_context_sentence(deterministic_checks)
    if not context:
        return summary
    return f"{summary} {context}"


def _low_concern_summary(deterministic_checks: DeterministicChecks | None) -> str:
    context = _check_context_sentence(deterministic_checks)
    if context:
        return f"Low concern. {context} ForgeBench found no high-confidence merge blockers, but this is not a substitute for human review."
    return "Low concern. ForgeBench found no high-confidence merge blockers, but this is not a substitute for human review."


def _check_context_sentence(deterministic_checks: DeterministicChecks | None) -> str:
    if deterministic_checks is None or not deterministic_checks.run_requested:
        return "Deterministic checks were not run."
    if not deterministic_checks.results:
        return "No deterministic checks were configured."
    results = deterministic_checks.results
    configured_results = [result for result in results if result.status != CheckStatus.NOT_CONFIGURED]
    if configured_results and all(result.status == CheckStatus.PASSED for result in configured_results):
        if any(result.status == CheckStatus.NOT_CONFIGURED for result in results):
            return "Configured deterministic checks passed. Some deterministic checks were not configured."
        return "Configured deterministic checks passed."
    if any(result.status in {CheckStatus.FAILED, CheckStatus.ERROR} for result in results):
        return "Configured deterministic checks found failures."
    if any(result.status == CheckStatus.TIMED_OUT for result in results):
        return "At least one deterministic check timed out."
    if all(result.status == CheckStatus.NOT_CONFIGURED for result in results):
        return "No deterministic checks were configured."
    return "Some deterministic checks were not configured."
