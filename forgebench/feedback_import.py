from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.feedback import FeedbackError, append_feedback, export_feedback_bundle


@dataclass(frozen=True)
class ImportResult:
    imported: int
    skipped: int
    source_format: str
    log_path: Path
    entries: list[dict[str, Any]]


def import_feedback(
    path: str | Path,
    *,
    format_hint: str | None = None,
    feedback_log: str | Path | None = None,
    dry_run: bool = False,
) -> ImportResult:
    source = Path(path)
    if not source.exists():
        raise FeedbackError(f"import file not found: {source}")

    fmt = (format_hint or _detect_format(source)).lower()
    if fmt == "json":
        entries = _parse_json_import(source)
    elif fmt in {"discussion", "discussions", "github"}:
        entries = _parse_discussion_import(source)
    elif fmt == "email":
        entries = _parse_email_import(source)
    elif fmt == "jsonl":
        entries = _parse_jsonl_import(source)
    else:
        raise FeedbackError(f"unsupported import format: {fmt}. Use json, jsonl, email, or discussion.")

    log_path = Path(feedback_log) if feedback_log else Path("forgebench-output") / "feedback.jsonl"
    imported = 0
    skipped = 0
    stored: list[dict[str, Any]] = []

    for entry in entries:
        uid = str(entry.get("uid") or entry.get("finding_uid") or "").strip()
        status = str(entry.get("status") or "dismissed").strip()
        if not uid:
            uid = f"imp_{_hash_note(str(entry.get('note') or entry.get('title') or imported))}"
        if status not in {"accepted", "dismissed", "wrong"}:
            skipped += 1
            continue
        if dry_run:
            stored.append(entry)
            imported += 1
            continue
        append_feedback(
            uid,
            status=status,
            note=str(entry.get("note") or entry.get("body") or ""),
            feedback_log=log_path,
            kind=entry.get("kind"),
            repo_name=entry.get("repo") or entry.get("repo_name"),
            source=str(entry.get("source") or fmt),
            posture=entry.get("posture"),
            agent_tool=entry.get("agent_tool") or entry.get("agent"),
            workflow=entry.get("workflow"),
            finding_count=entry.get("finding_count"),
            severity=entry.get("severity"),
            confidence=entry.get("confidence"),
            files=entry.get("files"),
            expected_posture=entry.get("expected_posture"),
            outcome_label=entry.get("outcome_label"),
            reviewer_lens=entry.get("reviewer_lens"),
            case_slug=entry.get("case_slug"),
            category=entry.get("category"),
            triage=entry.get("triage") or entry.get("triage_priority"),
            context=entry.get("context"),
            nps=entry.get("nps"),
            external_id=entry.get("external_id") or entry.get("id"),
        )
        stored.append(entry)
        imported += 1

    return ImportResult(
        imported=imported,
        skipped=skipped,
        source_format=fmt,
        log_path=log_path,
        entries=stored,
    )


def _detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return "jsonl"
    if suffix == ".json":
        return "json"
    text = path.read_text(encoding="utf-8", errors="replace")[:2000]
    if text.strip().startswith("{") or text.strip().startswith("["):
        return "json"
    if "Subject:" in text or "From:" in text or "To:" in text:
        return "email"
    if "##" in text or "ForgeBench" in text:
        return "discussion"
    return "discussion"


def _parse_json_import(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "entries" in payload:
        entries = payload["entries"]
    elif isinstance(payload, list):
        entries = payload
    elif isinstance(payload, dict):
        entries = [payload]
    else:
        raise FeedbackError("JSON import must be an object, array, or export bundle with entries.")
    if not isinstance(entries, list):
        raise FeedbackError("JSON entries must be an array.")
    return [item for item in entries if isinstance(item, dict)]


def _parse_jsonl_import(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            entries.append(payload)
    return entries


def _parse_email_import(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    subject = _extract_header(text, "Subject") or "Email feedback"
    body = _extract_email_body(text)
    category = "feature_request" if "feature" in subject.lower() else "other"
    return [
        {
            "uid": f"email_{_hash_note(subject)}",
            "status": "dismissed",
            "note": f"{subject}\n\n{body}".strip(),
            "source": "email",
            "category": category,
            "external_id": subject[:80],
        }
    ]


def _parse_discussion_import(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem
    kind = _extract_field(text, "kind") or _extract_field(text, "finding kind")
    posture = _extract_field(text, "posture")
    agent = _extract_field(text, "agent")
    category = "feature_request" if "idea" in title.lower() or "feature" in text.lower()[:500] else "other"
    return [
        {
            "uid": f"disc_{_hash_note(title)}",
            "status": "dismissed",
            "note": text.strip()[:4000],
            "source": "discussion",
            "kind": kind,
            "posture": posture,
            "agent_tool": agent,
            "category": category,
            "external_id": title[:80],
        }
    ]


def _extract_header(text: str, name: str) -> str | None:
    match = re.search(rf"^{name}:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    return match.group(1).strip() if match else None


def _extract_email_body(text: str) -> str:
    parts = re.split(r"\n\n+", text, maxsplit=2)
    if len(parts) >= 3:
        return parts[2].strip()
    if len(parts) == 2:
        return parts[1].strip()
    return text.strip()


def _extract_field(text: str, label: str) -> str | None:
    pattern = rf"(?i){re.escape(label)}\s*[:=]\s*`?([A-Za-z0-9_ /]+)`?"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def _hash_note(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]


def format_import_result(result: ImportResult) -> str:
    lines = [
        "ForgeBench feedback import",
        "",
        f"Format: {result.source_format}",
        f"Imported: {result.imported}",
        f"Skipped: {result.skipped}",
        f"Log: {result.log_path}",
    ]
    return "\n".join(lines)