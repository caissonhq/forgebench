from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from forgebench.models import (
    Confidence,
    DeterministicChecks,
    DiffSummary,
    EvidenceType,
    Finding,
    Guardrails,
    LLMReviewerConfig,
    LLMReviewResult,
    LLMReviewStatus,
    MergePosture,
    PolicyDecision,
    Severity,
)


class LLMProvider:
    def review(self, bundle: str, existing_findings: list[Finding]) -> LLMReviewResult:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    def __init__(self, response: dict[str, Any] | None = None, reviewer_name: str = "General LLM Reviewer") -> None:
        self.response = response
        self.reviewer_name = reviewer_name

    def review(self, bundle: str, existing_findings: list[Finding]) -> LLMReviewResult:
        payload = self.response or {
            "reviewer_name": self.reviewer_name,
            "summary": "No additional LLM findings beyond existing deterministic/static evidence.",
            "findings": [],
        }
        return _result_from_payload(payload, provider="mock", existing_findings=existing_findings)


class CommandLLMProvider(LLMProvider):
    def __init__(self, command: str | None, timeout_seconds: int) -> None:
        self.command = (command or "").strip()
        self.timeout_seconds = timeout_seconds

    def review(self, bundle: str, existing_findings: list[Finding]) -> LLMReviewResult:
        if not self.command:
            return LLMReviewResult(
                enabled=True,
                provider="command",
                status=LLMReviewStatus.FAILED,
                error_message="LLM command provider selected but no --llm-command was provided.",
            )

        try:
            completed = subprocess.run(
                self.command,
                shell=True,
                input=bundle,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return LLMReviewResult(
                enabled=True,
                provider="command",
                status=LLMReviewStatus.FAILED,
                error_message=f"LLM command timed out after {self.timeout_seconds} seconds.",
            )
        except OSError as exc:
            return LLMReviewResult(
                enabled=True,
                provider="command",
                status=LLMReviewStatus.FAILED,
                error_message=str(exc),
            )

        if completed.returncode != 0:
            stderr = _single_line(completed.stderr)
            stdout = _single_line(completed.stdout)
            detail = stderr or stdout or f"exit code {completed.returncode}"
            return LLMReviewResult(
                enabled=True,
                provider="command",
                status=LLMReviewStatus.FAILED,
                error_message=f"LLM command failed: {detail}",
            )

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            return LLMReviewResult(
                enabled=True,
                provider="command",
                status=LLMReviewStatus.FAILED,
                error_message=f"LLM command returned invalid JSON: {exc}",
            )
        return _result_from_payload(payload, provider="command", existing_findings=existing_findings)


def llm_review_not_run() -> LLMReviewResult:
    return LLMReviewResult(enabled=False, provider=None, status=LLMReviewStatus.SKIPPED)


def run_llm_review(config: LLMReviewerConfig, bundle: str, existing_findings: list[Finding]) -> LLMReviewResult:
    if not config.enabled:
        return llm_review_not_run()
    provider_name = config.provider or ("command" if config.command else None)
    if provider_name is None:
        return LLMReviewResult(
            enabled=True,
            provider=None,
            reviewer_name=config.reviewer_name,
            status=LLMReviewStatus.FAILED,
            error_message="LLM review was requested but no provider was configured. Use --llm-provider command with --llm-command.",
        )
    if provider_name == "mock":
        return MockLLMProvider(response=config.mock_response, reviewer_name=config.reviewer_name).review(bundle, existing_findings)
    if provider_name == "command":
        return CommandLLMProvider(command=config.command, timeout_seconds=config.timeout_seconds).review(bundle, existing_findings)
    return LLMReviewResult(
        enabled=True,
        provider=provider_name,
        reviewer_name=config.reviewer_name,
        status=LLMReviewStatus.FAILED,
        error_message=f"Unsupported LLM provider: {provider_name}",
    )


def build_review_bundle(
    *,
    task_text: str,
    diff_text: str,
    diff_summary: DiffSummary,
    guardrails: Guardrails,
    findings: list[Finding],
    pre_llm_posture: MergePosture,
    pre_llm_summary: str,
    deterministic_checks: DeterministicChecks,
    policy: PolicyDecision,
    config: LLMReviewerConfig,
) -> str:
    task_excerpt, task_truncated = _truncate(task_text, config.max_task_chars)
    diff_excerpt, diff_truncated = _truncate(diff_text, config.max_diff_chars)
    findings_payload = [finding.to_dict() for finding in findings]
    findings_json, findings_truncated = _truncate(json.dumps(findings_payload, indent=2, sort_keys=True), config.max_report_chars)
    policy_json, policy_truncated = _truncate(json.dumps(policy.to_dict(), indent=2, sort_keys=True), config.max_report_chars)
    bundle = {
        "project": guardrails.project,
        "original_task": task_excerpt,
        "original_task_truncated": task_truncated,
        "pre_llm_posture": pre_llm_posture.value,
        "pre_llm_summary": pre_llm_summary,
        "deterministic_checks": deterministic_checks.to_dict(),
        "static_and_guardrail_findings": findings_json,
        "static_and_guardrail_findings_truncated": findings_truncated,
        "guardrails_policy": policy_json,
        "guardrails_policy_truncated": policy_truncated,
        "changed_files": diff_summary.changed_files,
        "diff_excerpt": diff_excerpt,
        "diff_truncated": diff_truncated,
        "protected_behavior": list(guardrails.protected_behavior),
        "suppressed_findings": [finding.to_dict() for finding in policy.suppressed_findings],
    }
    return _review_prompt(json.dumps(bundle, indent=2, sort_keys=True))


def apply_llm_posture(
    pre_llm_posture: MergePosture,
    pre_llm_summary: str,
    llm_review: LLMReviewResult,
) -> tuple[MergePosture, str]:
    if pre_llm_posture == MergePosture.BLOCK:
        return pre_llm_posture, pre_llm_summary
    if not llm_review.enabled or llm_review.status != LLMReviewStatus.COMPLETED:
        return pre_llm_posture, pre_llm_summary
    if pre_llm_posture == MergePosture.REVIEW:
        return pre_llm_posture, pre_llm_summary
    if any(finding.severity == Severity.MEDIUM for finding in llm_review.findings):
        return (
            MergePosture.REVIEW,
            (
                "Review before merge. The optional LLM reviewer raised medium-severity advisory concerns. "
                "Deterministic and static ForgeBench evidence remains authoritative, and LLM findings do not approve the patch."
            ),
        )
    return pre_llm_posture, pre_llm_summary


def _result_from_payload(payload: object, provider: str, existing_findings: list[Finding]) -> LLMReviewResult:
    if not isinstance(payload, dict):
        return LLMReviewResult(
            enabled=True,
            provider=provider,
            status=LLMReviewStatus.FAILED,
            error_message="LLM provider returned JSON that was not an object.",
        )
    reviewer_name = str(payload.get("reviewer_name") or "General LLM Reviewer")
    raw_findings = payload.get("findings") if isinstance(payload.get("findings"), list) else []
    existing_ids = {finding.id for finding in existing_findings if finding.evidence_type != EvidenceType.LLM}
    findings = [_finding_from_payload(item, provider, existing_ids) for item in raw_findings if isinstance(item, dict)]
    return LLMReviewResult(
        enabled=True,
        provider=provider,
        reviewer_name=reviewer_name,
        status=LLMReviewStatus.COMPLETED,
        findings=findings,
        raw_summary=str(payload.get("summary") or ""),
    )


def _finding_from_payload(payload: dict[str, object], provider: str, existing_ids: set[str]) -> Finding:
    finding_id = _clean_identifier(str(payload.get("id") or "llm_review_finding"))
    severity = _parse_llm_severity(payload.get("severity"), finding_id, existing_ids)
    confidence = _parse_llm_confidence(payload.get("confidence"))
    title = str(payload.get("title") or finding_id.replace("_", " ").title())
    files = [str(item) for item in payload.get("files", []) if isinstance(item, str)] if isinstance(payload.get("files"), list) else []
    explanation = str(payload.get("explanation") or "The LLM reviewer raised this as an advisory review concern.")
    suggested_fix = str(payload.get("suggested_fix") or "Review this concern manually before merge.")
    return Finding(
        id=finding_id,
        title=title,
        severity=severity,
        confidence=confidence,
        evidence_type=EvidenceType.LLM,
        files=files,
        evidence=[
            f"LLM provider: {provider}",
            "LLM findings are advisory and do not override deterministic or static ForgeBench evidence.",
        ],
        explanation=explanation,
        suggested_fix=suggested_fix,
    )


def _parse_llm_severity(value: object, finding_id: str, existing_ids: set[str]) -> Severity:
    normalized = str(value or "low").strip().upper()
    if normalized == "BLOCKER":
        return Severity.MEDIUM
    severity = Severity.__members__.get(normalized, Severity.LOW)
    if severity == Severity.HIGH and finding_id not in existing_ids:
        return Severity.MEDIUM
    return severity


def _parse_llm_confidence(value: object) -> Confidence:
    normalized = str(value or "low").strip().upper()
    confidence = Confidence.__members__.get(normalized, Confidence.LOW)
    if confidence == Confidence.HIGH:
        return Confidence.MEDIUM
    return confidence


def _clean_identifier(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "_" for char in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "llm_review_finding"


def _truncate(value: str, max_chars: int) -> tuple[str, bool]:
    if len(value) <= max_chars:
        return value, False
    return value[:max_chars].rstrip() + "\n[truncated]", True


def _single_line(value: str) -> str:
    collapsed = " ".join(value.split())
    if len(collapsed) <= 500:
        return collapsed
    return collapsed[:497].rstrip() + "..."


def _review_prompt(bundle_json: str) -> str:
    return (
        "You are reviewing an AI-generated code diff before merge.\n\n"
        "Your job is not to approve the merge.\n"
        "Your job is to identify plausible merge risks a serious engineer should review.\n\n"
        "Use the provided deterministic/static/guardrail evidence.\n"
        "Do not invent facts not present in the diff or report.\n"
        "Do not claim the code is safe.\n"
        "Do not assign a numeric score.\n"
        "Do not override deterministic failures.\n"
        "Return only structured JSON.\n\n"
        "Return JSON with this shape:\n"
        "{\n"
        '  "reviewer_name": "General LLM Reviewer",\n'
        '  "summary": "...",\n'
        '  "findings": [\n'
        "    {\n"
        '      "id": "llm_missing_edge_case",\n'
        '      "title": "...",\n'
        '      "severity": "medium",\n'
        '      "confidence": "medium",\n'
        '      "files": ["..."],\n'
        '      "explanation": "...",\n'
        '      "suggested_fix": "..."\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "If no useful findings, return:\n"
        "{\n"
        '  "reviewer_name": "General LLM Reviewer",\n'
        '  "summary": "No additional LLM findings beyond existing deterministic/static evidence.",\n'
        '  "findings": []\n'
        "}\n\n"
        "Evidence bundle:\n"
        f"{bundle_json}\n"
    )
