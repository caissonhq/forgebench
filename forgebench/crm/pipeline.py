from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any


PIPELINE_PATH = Path("forgebench-output") / "crm-pipeline.json"


class PipelineStage(str, Enum):
    LEAD = "lead"
    DESIGN_PARTNER = "design_partner"
    TRIAL = "trial"
    PAID = "paid"
    CHURNED = "churned"


@dataclass(frozen=True)
class PipelineEntry:
    id: str
    organization: str
    stage: str
    tier: str
    seats: int
    source: str
    updated_at: str
    metadata: dict[str, Any]


def load_pipeline(*, path: str | Path | None = None) -> list[PipelineEntry]:
    target = Path(path) if path else PIPELINE_PATH
    if not target.exists():
        return []
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(payload, list):
        return []
    entries: list[PipelineEntry] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        entries.append(
            PipelineEntry(
                id=str(item.get("id") or ""),
                organization=str(item.get("organization") or ""),
                stage=str(item.get("stage") or PipelineStage.LEAD.value),
                tier=str(item.get("tier") or "free"),
                seats=int(item.get("seats") or 0),
                source=str(item.get("source") or ""),
                updated_at=str(item.get("updated_at") or ""),
                metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
            )
        )
    return entries


def save_pipeline(entries: list[PipelineEntry], *, path: str | Path | None = None) -> Path:
    target = Path(path) if path else PIPELINE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "id": entry.id,
            "organization": entry.organization,
            "stage": entry.stage,
            "tier": entry.tier,
            "seats": entry.seats,
            "source": entry.source,
            "updated_at": entry.updated_at,
            "metadata": entry.metadata,
        }
        for entry in entries
    ]
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def upsert_pipeline_entry(
    *,
    organization: str,
    stage: str | PipelineStage,
    tier: str = "team",
    seats: int = 5,
    source: str = "manual",
    metadata: dict[str, Any] | None = None,
    path: str | Path | None = None,
) -> PipelineEntry:
    stage_value = stage.value if isinstance(stage, PipelineStage) else str(stage)
    entries = load_pipeline(path=path)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry_id = _stable_id(organization, tier)
    updated = PipelineEntry(
        id=entry_id,
        organization=organization,
        stage=stage_value,
        tier=tier,
        seats=seats,
        source=source,
        updated_at=now,
        metadata=metadata or {},
    )
    replaced = False
    next_entries: list[PipelineEntry] = []
    for item in entries:
        if item.id == entry_id:
            next_entries.append(updated)
            replaced = True
        else:
            next_entries.append(item)
    if not replaced:
        next_entries.append(updated)
    save_pipeline(next_entries, path=path)
    return updated


def record_subscription_event(
    *,
    organization: str,
    stage: str | PipelineStage,
    tier: str,
    seats: int,
    source: str,
    metadata: dict[str, Any] | None = None,
) -> PipelineEntry:
    entry = upsert_pipeline_entry(
        organization=organization,
        stage=stage,
        tier=tier,
        seats=seats,
        source=source,
        metadata=metadata,
    )
    try:
        from forgebench.crm.linear import maybe_sync_pipeline_to_linear

        maybe_sync_pipeline_to_linear(entry)
    except Exception:
        pass
    return entry


def format_pipeline_summary(entries: list[PipelineEntry] | None = None) -> str:
    rows = entries if entries is not None else load_pipeline()
    if not rows:
        return "CRM pipeline empty. Add leads with `forgebench crm add`."
    lines = ["ForgeBench CRM pipeline:", ""]
    for entry in rows:
        lines.append(
            f"  [{entry.stage}] {entry.organization} · {entry.tier} · {entry.seats} seats · {entry.source}"
        )
    return "\n".join(lines)


def _stable_id(organization: str, tier: str) -> str:
    import hashlib

    return hashlib.sha256(f"{organization}:{tier}".encode("utf-8")).hexdigest()[:12]