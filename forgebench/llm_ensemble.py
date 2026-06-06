from __future__ import annotations

from dataclasses import replace
from typing import Any

from forgebench.llm_review import LLMJSONResult, _run_llm_json_once
from forgebench.models import LLMReviewerConfig, LLMReviewStatus


def resolve_ensemble_models(config: LLMReviewerConfig) -> list[str]:
    if config.ensemble_models:
        return list(config.ensemble_models)
    if config.openai_model:
        return [config.openai_model]
    return []


def run_ensemble_json(config: LLMReviewerConfig, bundle: str) -> LLMJSONResult:
    models = resolve_ensemble_models(config)
    if len(models) <= 1:
        return _run_llm_json_once(config, bundle)

    payloads: list[dict[str, Any]] = []
    errors: list[str] = []
    for model in models:
        model_config = replace(config, openai_model=model, reviewer_name=f"{config.reviewer_name} ({model})")
        result = _run_llm_json_once(model_config, bundle)
        if result.status == LLMReviewStatus.COMPLETED and result.payload:
            payloads.append(result.payload)
        elif result.error_message:
            errors.append(f"{model}: {result.error_message}")

    if not payloads:
        return LLMJSONResult(
            enabled=True,
            provider=config.provider,
            status=LLMReviewStatus.FAILED,
            error_message="; ".join(errors) or "Ensemble produced no successful model responses.",
        )

    merged = _merge_ensemble_payloads(payloads, strategy=config.ensemble_strategy)
    merged["ensemble_models"] = models
    merged["ensemble_strategy"] = config.ensemble_strategy
    if errors:
        merged["ensemble_errors"] = errors
    return LLMJSONResult(
        enabled=True,
        provider=config.provider,
        status=LLMReviewStatus.COMPLETED,
        payload=merged,
    )


def _merge_ensemble_payloads(payloads: list[dict[str, Any]], *, strategy: str) -> dict[str, Any]:
    summaries = [str(item.get("summary") or "").strip() for item in payloads if item.get("summary")]
    findings: list[dict[str, Any]] = []
    seen: set[str] = set()
    for payload in payloads:
        for finding in payload.get("findings") or []:
            if not isinstance(finding, dict):
                continue
            marker = repr((finding.get("id"), finding.get("title"), finding.get("files")))
            if marker in seen:
                continue
            seen.add(marker)
            findings.append(finding)

    reviewer_names = [str(item.get("reviewer_name") or "LLM Reviewer") for item in payloads]
    summary = summaries[0] if strategy == "first_success" and summaries else " | ".join(summaries[:3])
    if strategy == "consensus" and len(payloads) > 1:
        summary = f"Ensemble consensus across {len(payloads)} model(s): {summary}"

    return {
        "reviewer_name": " + ".join(reviewer_names[:3]),
        "summary": summary or "Ensemble completed with no additional findings.",
        "findings": findings,
    }