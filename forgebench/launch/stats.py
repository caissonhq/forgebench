from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PUBLIC_STATS_PATH = Path(__file__).resolve().parents[2] / "examples" / "launch" / "public-stats.json"


def load_public_stats(path: str | Path | None = None) -> dict[str, Any]:
    target = Path(path) if path else PUBLIC_STATS_PATH
    if not target.exists():
        return {}
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def update_public_stats(
    *,
    path: str | Path | None = None,
    github_stars: int | None = None,
    pypi_downloads_monthly: str | int | None = None,
    vscode_installs: str | int | None = None,
    design_partners_active: int | None = None,
    success_stories_published: int | None = None,
    first_reviews_reported: int | None = None,
    hn_points: int | None = None,
    launch_day_installs: int | None = None,
    tagline: str | None = None,
) -> Path:
    target = Path(path) if path else PUBLIC_STATS_PATH
    payload = load_public_stats(target)
    fields = {
        "github_stars": github_stars,
        "pypi_downloads_monthly": pypi_downloads_monthly,
        "vscode_installs": vscode_installs,
        "design_partners_active": design_partners_active,
        "success_stories_published": success_stories_published,
        "first_reviews_reported": first_reviews_reported,
        "hn_points": hn_points,
        "launch_day_installs": launch_day_installs,
    }
    for key, value in fields.items():
        if value is not None:
            payload[key] = value
    payload.setdefault("github_url", "https://github.com/caissonhq/forgebench")
    payload.setdefault("launch_date", datetime.now(timezone.utc).date().isoformat())
    payload["updated_at"] = datetime.now(timezone.utc).date().isoformat()
    if tagline:
        payload["tagline"] = tagline
    else:
        payload.setdefault("tagline", "ForgeBench v1.0.0 public launch metrics")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def format_public_stats_summary(path: str | Path | None = None) -> str:
    payload = load_public_stats(path)
    lines = ["ForgeBench public launch stats", ""]
    for key in (
        "launch_date",
        "github_stars",
        "pypi_downloads_monthly",
        "vscode_installs",
        "design_partners_active",
        "success_stories_published",
        "first_reviews_reported",
        "hn_points",
        "updated_at",
    ):
        if key in payload:
            lines.append(f"  {key}: {payload[key]}")
    return "\n".join(lines)