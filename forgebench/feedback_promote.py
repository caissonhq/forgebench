from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forgebench.feedback import DEFAULT_FEEDBACK_LOG, FeedbackError
from forgebench.golden_case_generator import generate_golden_case_candidates


@dataclass(frozen=True)
class PromoteResult:
    output_dir: Path
    promoted_count: int
    candidate_slugs: list[str]
    manifest_path: Path
    template_paths: list[Path]


def promote_feedback_to_golden_cases(
    *,
    feedback_log: str | Path | None = None,
    uid: str | None = None,
    output_dir: str | Path = "forgebench-output/golden-case-candidates",
    copy_template: bool = True,
) -> PromoteResult:
    log_path = Path(feedback_log) if feedback_log else DEFAULT_FEEDBACK_LOG
    if not log_path.exists():
        raise FeedbackError(f"feedback log not found: {log_path}")

    entries = _load_entries(log_path)
    if uid:
        normalized = uid.strip()
        entries = [e for e in entries if str(e.get("uid") or "") == normalized]
        if not entries:
            raise FeedbackError(f"no feedback entry found for uid: {normalized}")

    temp_log = Path(output_dir) / ".promote-feedback.jsonl"
    temp_log.parent.mkdir(parents=True, exist_ok=True)
    temp_log.write_text("\n".join(json.dumps(e, sort_keys=True) for e in entries) + "\n", encoding="utf-8")

    result = generate_golden_case_candidates([temp_log], output_dir=output_dir)
    template_paths: list[Path] = []
    if copy_template:
        template_src = Path(__file__).resolve().parents[1] / "docs" / "iteration" / "feedback-to-golden-case.md"
        if template_src.exists():
            dest = Path(output_dir) / "PROMOTE_CHECKLIST.md"
            shutil.copy2(template_src, dest)
            template_paths.append(dest)

    if uid and result.candidates:
        _mark_resolved(log_path, uid)

    return PromoteResult(
        output_dir=result.output_dir,
        promoted_count=len(result.candidates),
        candidate_slugs=[item.case_slug for item in result.candidates],
        manifest_path=result.manifest_path,
        template_paths=template_paths,
    )


def format_promote_result(result: PromoteResult) -> str:
    lines = [
        "ForgeBench feedback promote",
        "",
        f"Candidates: {result.promoted_count}",
        f"Output: {result.output_dir}",
        f"Manifest: {result.manifest_path}",
    ]
    if result.candidate_slugs:
        lines.append("Case slugs:")
        for slug in result.candidate_slugs:
            lines.append(f"  - {slug}")
    lines.extend(
        [
            "",
            "Human review required before moving to examples/golden_cases/.",
            "  1. Add anonymized patch.diff + task.md",
            "  2. forgebench calibrate --cases <output-dir>/<slug>",
            "  3. Open golden case proposal issue",
        ]
    )
    return "\n".join(lines)


def _load_entries(log_path: Path) -> list[dict[str, Any]]:
    from forgebench.feedback import _load_feedback_entries

    entries, _malformed, _missing = _load_feedback_entries([log_path])
    return entries


def _mark_resolved(log_path: Path, uid: str) -> None:
    lines: list[str] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if str(payload.get("uid") or "") == uid.strip():
            payload["resolved"] = True
            payload["promoted_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        lines.append(json.dumps(payload, sort_keys=True))
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")