from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.semantic.models import BehavioralDiffSummary


@dataclass(frozen=True)
class MutationPlanResult:
    output_dir: Path
    plan_path: Path
    candidate_count: int


def build_mutation_plan(
    behavioral: BehavioralDiffSummary,
    *,
    output_dir: str | Path,
) -> MutationPlanResult:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = _mutation_candidates(behavioral)
    plan = {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "skeleton",
        "description": (
            "Mutation testing plan skeleton. ForgeBench does not execute mutants yet; "
            "wire these candidates to mutmut, cargo-mutants, or Stryker in CI."
        ),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "recommended_runners": {
            "python": "mutmut run --paths-to-mutate <file>",
            "rust": "cargo mutants",
            "typescript": "stryker run",
        },
    }
    plan_path = out_dir / "mutation-plan.json"
    plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return MutationPlanResult(output_dir=out_dir, plan_path=plan_path, candidate_count=len(candidates))


def _mutation_candidates(behavioral: BehavioralDiffSummary) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for symbol in behavioral.changed_symbols:
        candidates.append(
            {
                "symbol": symbol.name,
                "kind": symbol.kind,
                "file_path": symbol.file_path,
                "parser": symbol.parser,
                "suggested_mutations": _suggested_mutations(symbol.kind),
                "priority": "high" if symbol.name in behavioral.symbols_without_test_reference else "medium",
            }
        )
    return candidates


def _suggested_mutations(kind: str) -> list[str]:
    if kind in {"function", "async_function"}:
        return ["return_value_inversion", "boundary_off_by_one", "remove_guard_clause"]
    if kind in {"class", "struct"}:
        return ["constructor_default_change", "method_return_substitution"]
    return ["literal_substitution", "operator_flip"]