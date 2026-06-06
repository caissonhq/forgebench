from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.models import ForgeBenchReport, LLMReviewerConfig
from forgebench.mutation.skeleton import build_mutation_plan
from forgebench.semantic.models import BehavioralDiffSummary, CrossFileEdge, SymbolChange


def behavioral_from_static_signals(static_signals: dict[str, object]) -> BehavioralDiffSummary:
    changed_symbols = _symbols_from_signal(static_signals.get("changed_symbols"))
    cross_file_edges = _edges_from_signal(static_signals.get("cross_file_behavior_edges"))
    uncovered = static_signals.get("symbols_without_test_reference")
    parsers = static_signals.get("semantic_parsers_used")
    warnings = static_signals.get("semantic_warnings")
    return BehavioralDiffSummary(
        enabled=bool(static_signals.get("semantic_analysis_enabled")),
        parsers_used=[str(item) for item in parsers] if isinstance(parsers, list) else [],
        changed_symbols=changed_symbols,
        cross_file_edges=cross_file_edges,
        symbols_without_test_reference=[str(item) for item in uncovered] if isinstance(uncovered, list) else [],
        warnings=[str(item) for item in warnings] if isinstance(warnings, list) else [],
    )


def load_report_for_prove_it(report_path: str | Path) -> ForgeBenchReport:
    payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    from forgebench.models import MergePosture

    return ForgeBenchReport(
        posture=MergePosture[str(payload.get("posture", "REVIEW"))],
        summary=str(payload.get("summary") or ""),
        task_summary=str(payload.get("task_summary") or ""),
        changed_files=[str(item) for item in payload.get("changed_files") or []],
        findings=[],
        static_signals=dict(payload.get("static_signals") or {}),
        guardrail_hits=[str(item) for item in payload.get("guardrail_hits") or []],
        generated_at=str(payload.get("generated_at") or ""),
    )


@dataclass(frozen=True)
class ProveItExportResult:
    output_dir: Path
    plan_path: Path
    checklist_path: Path


def export_prove_it_plan(
    *,
    report: ForgeBenchReport,
    behavioral: BehavioralDiffSummary,
    llm_config: LLMReviewerConfig | None,
    output_dir: str | Path,
) -> ProveItExportResult:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    mutation = build_mutation_plan(behavioral, output_dir=out_dir)
    checklist = _build_checklist(report, behavioral, llm_config)
    plan = {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "skeleton",
        "posture": report.posture.value,
        "summary": report.summary,
        "prove_it_mode": True,
        "behavioral_diff": behavioral.to_dict(),
        "mutation_plan": json.loads(mutation.plan_path.read_text(encoding="utf-8")),
        "ensemble": _ensemble_metadata(llm_config),
        "evidence_checklist": checklist,
        "next_steps": [
            "Run mutation candidates with your language-specific mutation runner.",
            "Re-run ForgeBench with --llm-review and ensemble models for adversarial review.",
            "Attach mutation survivor output and updated tests before merge.",
        ],
    }
    plan_path = out_dir / "prove-it-plan.json"
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")

    checklist_path = out_dir / "prove-it-checklist.md"
    checklist_path.write_text(_render_checklist_markdown(plan), encoding="utf-8")

    return ProveItExportResult(output_dir=out_dir, plan_path=plan_path, checklist_path=checklist_path)


def _build_checklist(
    report: ForgeBenchReport,
    behavioral: BehavioralDiffSummary,
    llm_config: LLMReviewerConfig | None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for finding in report.findings:
        items.append(
            {
                "kind": finding.kind or finding.id,
                "severity": finding.severity.value,
                "title": finding.title,
                "status": "open",
                "proof_required": finding.severity.value in {"BLOCKER", "HIGH", "MEDIUM"},
            }
        )
    for symbol in behavioral.symbols_without_test_reference:
        items.append(
            {
                "kind": "symbol_test_proof",
                "severity": "MEDIUM",
                "title": f"Prove test coverage for changed symbol {symbol}",
                "status": "open",
                "proof_required": True,
            }
        )
    if llm_config and llm_config.enabled and llm_config.ensemble_models:
        items.append(
            {
                "kind": "ensemble_review",
                "severity": "ADVISORY",
                "title": f"Ensemble review requested across {', '.join(llm_config.ensemble_models)}",
                "status": "open",
                "proof_required": False,
            }
        )
    return items


def _ensemble_metadata(llm_config: LLMReviewerConfig | None) -> dict[str, Any]:
    if llm_config is None or not llm_config.enabled:
        return {"enabled": False, "models": [], "strategy": "first_success"}
    return {
        "enabled": True,
        "models": list(llm_config.ensemble_models or ([llm_config.openai_model] if llm_config.openai_model else [])),
        "strategy": llm_config.ensemble_strategy,
        "provider": llm_config.provider,
    }


def _render_checklist_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# ForgeBench Prove-it Checklist",
        "",
        "Prove-it mode is a skeleton workflow for mutation testing and multi-model adversarial review.",
        "",
        f"Posture: **{plan.get('posture')}**",
        "",
        "## Evidence checklist",
        "",
    ]
    for item in plan.get("evidence_checklist") or []:
        proof = "required" if item.get("proof_required") else "optional"
        lines.append(f"- [{item.get('status', 'open')}] ({proof}) {item.get('title')}")
    lines.extend(
        [
            "",
            "## Next steps",
            "",
        ]
    )
    for step in plan.get("next_steps") or []:
        lines.append(f"- {step}")
    lines.append("")
    lines.append("ForgeBench does not prove code is safe. Prove-it mode structures evidence gathering before merge.")
    return "\n".join(lines) + "\n"


def _symbols_from_signal(value: object) -> list[SymbolChange]:
    if not isinstance(value, list):
        return []
    symbols: list[SymbolChange] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        symbols.append(
            SymbolChange(
                name=str(item.get("name") or ""),
                kind=str(item.get("kind") or ""),
                file_path=str(item.get("file_path") or ""),
                parser=str(item.get("parser") or ""),
            )
        )
    return [symbol for symbol in symbols if symbol.name and symbol.file_path]


def _edges_from_signal(value: object) -> list[CrossFileEdge]:
    if not isinstance(value, list):
        return []
    edges: list[CrossFileEdge] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        edges.append(
            CrossFileEdge(
                source_file=str(item.get("source_file") or ""),
                target_file=str(item.get("target_file") or ""),
                symbol=str(item.get("symbol") or ""),
                edge_type=str(item.get("edge_type") or ""),
            )
        )
    return edges