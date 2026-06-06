from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


DEFAULT_FEEDBACK_LOG = Path("forgebench-output") / "feedback.jsonl"
FEEDBACK_SCHEMA_VERSION = "3.0.0"
VALID_FEEDBACK_STATUSES = {"accepted", "dismissed", "wrong"}
VALID_FEEDBACK_POSTURES = {"BLOCK", "REVIEW", "LOW_CONCERN"}
VALID_AGENT_TOOLS = {"cursor", "codex", "claude", "copilot", "other"}
VALID_FEEDBACK_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_FEEDBACK_CONFIDENCE = {"low", "medium", "high"}
VALID_OUTCOME_LABELS = {
    "false_positive",
    "true_positive",
    "missed_concern",
    "noise",
    "calibration_gap",
    "other",
}


class FeedbackError(ValueError):
    pass


@dataclass(frozen=True)
class FeedbackSummary:
    total: int = 0
    status_counts: dict[str, int] = field(default_factory=dict)
    kind_counts: dict[str, Counter[str]] = field(default_factory=dict)
    missing_kind_count: int = 0
    malformed_count: int = 0


def append_feedback(
    uid: str,
    *,
    status: str,
    note: str | None = None,
    feedback_log: str | Path | None = None,
    kind: str | None = None,
    repo_name: str | None = None,
    source: str | None = None,
    posture: str | None = None,
    agent_tool: str | None = None,
    workflow: str | None = None,
    finding_count: int | None = None,
    review_command: str | None = None,
    severity: str | None = None,
    confidence: str | None = None,
    files: list[str] | None = None,
    expected_posture: str | None = None,
    outcome_label: str | None = None,
    reviewer_lens: str | None = None,
    case_slug: str | None = None,
) -> Path:
    normalized_uid = uid.strip()
    if not normalized_uid:
        raise FeedbackError("finding UID is required.")
    if status not in VALID_FEEDBACK_STATUSES:
        raise FeedbackError("status must be one of: accepted, dismissed, wrong.")
    if posture is not None and posture not in VALID_FEEDBACK_POSTURES:
        raise FeedbackError("posture must be one of: BLOCK, REVIEW, LOW_CONCERN.")
    if agent_tool is not None and agent_tool not in VALID_AGENT_TOOLS:
        raise FeedbackError("agent_tool must be one of: cursor, codex, claude, copilot, other.")
    if finding_count is not None and finding_count < 0:
        raise FeedbackError("finding_count must be zero or positive.")
    if severity is not None and severity not in VALID_FEEDBACK_SEVERITIES:
        raise FeedbackError("severity must be one of: low, medium, high, critical.")
    if confidence is not None and confidence not in VALID_FEEDBACK_CONFIDENCE:
        raise FeedbackError("confidence must be one of: low, medium, high.")
    if expected_posture is not None and expected_posture not in VALID_FEEDBACK_POSTURES:
        raise FeedbackError("expected_posture must be one of: BLOCK, REVIEW, LOW_CONCERN.")
    if outcome_label is not None and outcome_label not in VALID_OUTCOME_LABELS:
        raise FeedbackError(
            "outcome_label must be one of: false_positive, true_positive, missed_concern, noise, calibration_gap, other."
        )

    path = Path(feedback_log) if feedback_log else DEFAULT_FEEDBACK_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    v2_fields = any(
        value is not None
        for value in (posture, agent_tool, workflow, finding_count, review_command)
    )
    v3_fields = any(
        value is not None
        for value in (
            severity,
            confidence,
            files,
            expected_posture,
            outcome_label,
            reviewer_lens,
            case_slug,
        )
    )
    if v3_fields:
        fb_version = 3
    elif v2_fields:
        fb_version = 2
    else:
        fb_version = 1
    payload: dict[str, Any] = {
        "uid": normalized_uid,
        "status": status,
        "note": note or "",
        "ts": datetime.now(timezone.utc).isoformat(),
        "fb_version": fb_version,
    }
    if kind:
        payload["kind"] = kind
    if repo_name:
        payload["repo"] = repo_name
    if source:
        payload["source"] = source
    if posture:
        payload["posture"] = posture
    if agent_tool:
        payload["agent_tool"] = agent_tool
    if workflow:
        payload["workflow"] = workflow
    if finding_count is not None:
        payload["finding_count"] = finding_count
    if review_command:
        payload["review_command"] = review_command
    if severity:
        payload["severity"] = severity
    if confidence:
        payload["confidence"] = confidence
    if files:
        payload["files"] = [str(item) for item in files if str(item).strip()]
    if expected_posture:
        payload["expected_posture"] = expected_posture
    if outcome_label:
        payload["outcome_label"] = outcome_label
    if reviewer_lens:
        payload["reviewer_lens"] = reviewer_lens
    if case_slug:
        payload["case_slug"] = case_slug

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return path


def summarize_feedback(feedback_logs: list[str | Path]) -> FeedbackSummary:
    status_counts: Counter[str] = Counter()
    kind_counts: dict[str, Counter[str]] = {
        "accepted": Counter(),
        "dismissed": Counter(),
        "wrong": Counter(),
    }
    total = 0
    missing_kind_count = 0
    malformed_count = 0

    for log_path in feedback_logs:
        path = Path(log_path)
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                malformed_count += 1
                continue
            status = str(payload.get("status") or "")
            if status not in VALID_FEEDBACK_STATUSES:
                malformed_count += 1
                continue
            total += 1
            status_counts[status] += 1
            kind = str(payload.get("kind") or "").strip()
            if kind:
                kind_counts[status][kind] += 1
            else:
                missing_kind_count += 1

    return FeedbackSummary(
        total=total,
        status_counts={status: status_counts.get(status, 0) for status in sorted(VALID_FEEDBACK_STATUSES)},
        kind_counts=kind_counts,
        missing_kind_count=missing_kind_count,
        malformed_count=malformed_count,
    )


def export_feedback_bundle(
    feedback_logs: list[str | Path],
    *,
    repo_name: str | None = None,
    source: str = "forgebench-beta",
) -> dict[str, Any]:
    entries, malformed_count, missing_logs = _load_feedback_entries(feedback_logs)
    summary = summarize_feedback(feedback_logs)
    has_v3 = any(int(entry.get("fb_version") or 1) >= 3 for entry in entries)
    return {
        "export_version": 2 if has_v3 else 1,
        "schema_version": FEEDBACK_SCHEMA_VERSION if has_v3 else "2.0.0",
        "source": source,
        "repo": repo_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": summary.total,
            "status_counts": summary.status_counts,
            "kind_counts": {
                status: dict(counter) for status, counter in summary.kind_counts.items()
            },
            "missing_kind_count": summary.missing_kind_count,
            "malformed_count": summary.malformed_count + malformed_count,
            "missing_logs": missing_logs,
        },
        "entries": entries,
        "share_instructions": (
            "This bundle is local-only. Share it manually via a GitHub issue or email if you want "
            "ForgeBench beta feedback reviewed. No network upload is performed automatically."
        ),
    }


def format_feedback_summary(summary: FeedbackSummary) -> str:
    lines = [
        "ForgeBench feedback summary",
        "",
        f"Total entries: {summary.total}",
        f"accepted: {summary.status_counts.get('accepted', 0)}",
        f"dismissed: {summary.status_counts.get('dismissed', 0)}",
        f"wrong: {summary.status_counts.get('wrong', 0)}",
    ]
    kind_totals: Counter[str] = Counter()
    for counter in summary.kind_counts.values():
        kind_totals.update(counter)
    if kind_totals:
        lines.extend(["", "Counts by kind:"])
        for kind, count in kind_totals.most_common():
            lines.append(f"- {kind}: {count}")
    if summary.missing_kind_count:
        lines.append(f"Entries missing kind: {summary.missing_kind_count}")
    if summary.malformed_count:
        lines.append(f"Malformed entries skipped: {summary.malformed_count}")
    return "\n".join(lines)


def suggest_guardrails(feedback_logs: list[str | Path]) -> str:
    entries, malformed_count, missing_logs = _load_feedback_entries(feedback_logs)
    dismissed_or_wrong = [
        entry
        for entry in entries
        if str(entry.get("status") or "") in {"dismissed", "wrong"} and str(entry.get("kind") or "").strip()
    ]
    kind_counts: Counter[str] = Counter(str(entry.get("kind")) for entry in dismissed_or_wrong)

    lines = [
        "# ForgeBench Guardrail Suggestions",
        "",
        "These suggestions are generated from local feedback only. ForgeBench did not modify forgebench.yml.",
        "",
    ]
    if missing_logs:
        lines.append("Missing feedback logs:")
        lines.extend(f"- {path}" for path in missing_logs)
        lines.append("")
    if malformed_count:
        lines.append(f"Malformed feedback lines skipped: {malformed_count}")
        lines.append("")
    if not dismissed_or_wrong:
        lines.extend(
            [
                "No dismissed or wrong finding feedback was found.",
                "",
                "Record local feedback first, for example:",
                "",
                "```bash",
                "forgebench feedback FINDING_UID --status dismissed --kind ui_copy_changed --note \"docs-only noise\"",
                "```",
            ]
        )
        return "\n".join(lines) + "\n"

    lines.append("Dismissed/wrong finding kinds:")
    for kind, count in sorted(kind_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {kind}: {count}")
    lines.append("")
    lines.extend(["## Suggested forgebench.yml snippets", ""])

    for kind in sorted(kind_counts):
        lines.extend(_suggestion_for_kind(kind, dismissed_or_wrong))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _load_feedback_entries(feedback_logs: list[str | Path]) -> tuple[list[dict[str, Any]], int, list[str]]:
    entries: list[dict[str, Any]] = []
    malformed_count = 0
    missing_logs: list[str] = []
    for log_path in feedback_logs:
        path = Path(log_path)
        if not path.exists():
            missing_logs.append(str(path))
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                malformed_count += 1
                continue
            if not isinstance(payload, dict):
                malformed_count += 1
                continue
            entries.append(payload)
    return entries, malformed_count, missing_logs


def _suggestion_for_kind(kind: str, entries: list[dict[str, Any]]) -> list[str]:
    if kind == "ui_copy_changed":
        return [
            "### ui_copy_changed",
            "",
            "If dismissed UI/copy findings are docs-only noise, suppress them on docs paths:",
            "",
            "```yaml",
            "policy:",
            "  suppress_findings:",
            "    - finding_id: ui_copy_changed",
            "      paths:",
            "        - \"docs/**\"",
            "        - \"README.md\"",
            "      reason: \"Dismissed in local feedback.\"",
            "```",
        ]
    if kind == "broad_file_surface":
        asset_paths = _feedback_files_for_kind(kind, entries)
        asset_only_hint = asset_paths and all(_looks_like_asset_path(path) for path in asset_paths)
        intro = "If broad-file feedback came from asset-only diffs, suppress broad surface risk for asset-only changes:"
        if not asset_only_hint:
            intro = "If broad-file feedback came from assets or generated files, use path-specific suppression rather than disabling the finding globally:"
        return [
            "### broad_file_surface",
            "",
            intro,
            "",
            "```yaml",
            "policy:",
            "  suppress_findings:",
            "    - finding_id: broad_file_surface",
            "      when_all_changed_files_match:",
            "        - \"**/*.png\"",
            "        - \"**/*.jpg\"",
            "        - \"**/*.svg\"",
            "        - \"**/Assets.xcassets/**\"",
            "      reason: \"Asset-only broad diffs were dismissed in local feedback.\"",
            "  posture_overrides:",
            "    asset_only_changes:",
            "      posture_ceiling: LOW_CONCERN",
            "      reason: \"Asset-only changes should not escalate without another blocker.\"",
            "```",
        ]
    if kind == "implementation_without_tests":
        return [
            "### implementation_without_tests",
            "",
            "Do not blanket-suppress implementation_without_tests. Prefer adding trusted checks or narrowing low-risk paths:",
            "",
            "```yaml",
            "checks:",
            "  test: \"python3 -m unittest discover -s tests\"",
            "",
            "policy:",
            "  advisory_only:",
            "    - \"docs/**\"",
            "    - \"**/*.md\"",
            "    - \"**/fixtures/**\"",
            "```",
        ]
    if kind == "dependency_surface_changed":
        return [
            "### dependency_surface_changed",
            "",
            "If dependency findings are noisy, add deterministic validation and tune only specific dependency paths:",
            "",
            "```yaml",
            "checks:",
            "  build: \"npm run build\"",
            "  test: \"npm run test\"",
            "",
            "policy:",
            "  finding_overrides:",
            "    dependency_surface_changed:",
            "      severity: medium",
            "      confidence: medium",
            "      applies_to:",
            "        - \"package-lock.json\"",
            "      reason: \"Lockfile-only changes are reviewed with configured checks.\"",
            "```",
        ]
    return [
        f"### {kind}",
        "",
        "No canned suggestion exists for this finding kind yet. Prefer path-specific policy over blanket suppression.",
    ]


def _feedback_files_for_kind(kind: str, entries: list[dict[str, Any]]) -> list[str]:
    files: list[str] = []
    for entry in entries:
        if entry.get("kind") != kind:
            continue
        value = entry.get("files")
        if isinstance(value, list):
            files.extend(str(item) for item in value if item)
    return files


def _looks_like_asset_path(path: str) -> bool:
    lower = path.replace("\\", "/").lower()
    return lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico", ".icns")) or "assets.xcassets/" in lower
