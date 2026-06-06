from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench import __version__
from forgebench.adoption import load_adoption_state
from forgebench.product_analytics import export_product_analytics_bundle, is_product_analytics_enabled


PUBLIC_STATS_PATH = Path(__file__).resolve().parents[1] / "examples" / "launch" / "public-stats.json"

FUNNEL_STAGES = ("install", "first_review", "team_init", "license_activate")


@dataclass(frozen=True)
class AdoptionDashboardResult:
    output_dir: Path
    index_path: Path
    manifest_path: Path


def export_adoption_dashboard(
    *,
    output_dir: str | Path = "forgebench-output/adoption-dashboard",
    public_stats_path: str | Path | None = None,
) -> AdoptionDashboardResult:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    public = _load_public_stats(public_stats_path)
    local_funnel = _local_funnel_counts()
    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "forgebench_version": __version__,
        "public_stats": public,
        "local_funnel": local_funnel,
        "product_analytics_opt_in": is_product_analytics_enabled(),
        "funnel_stages": list(FUNNEL_STAGES),
        "privacy_note": "Public stats are manually curated. Local funnel reflects this machine only.",
    }
    if is_product_analytics_enabled():
        bundle = export_product_analytics_bundle()
        manifest["product_analytics_summary"] = bundle.get("summary")

    manifest_path = out / "adoption-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    index_path = out / "index.html"
    index_path.write_text(_render_html(manifest), encoding="utf-8")
    return AdoptionDashboardResult(output_dir=out, index_path=index_path, manifest_path=manifest_path)


def _load_public_stats(path: str | Path | None) -> dict[str, Any]:
    target = Path(path) if path else PUBLIC_STATS_PATH
    if not target.exists():
        return {
            "github_stars": 0,
            "github_url": "https://github.com/caissonhq/forgebench",
            "pypi_downloads_monthly": "—",
            "vscode_installs": "—",
            "updated_at": datetime.now(timezone.utc).date().isoformat(),
            "tagline": "Launch metrics — update examples/launch/public-stats.json",
        }
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _local_funnel_counts() -> dict[str, int]:
    state = load_adoption_state()
    mapping = {
        "install": "first_install" in state.milestones,
        "first_review": "first_review" in state.milestones,
        "team_init": "first_team_init" in state.milestones,
        "license_activate": "first_paid_feature" in state.milestones,
    }
    return {stage: int(mapping[stage]) for stage in FUNNEL_STAGES}


def _render_html(manifest: dict[str, Any]) -> str:
    public = manifest.get("public_stats") or {}
    local = manifest.get("local_funnel") or {}
    stars = html.escape(str(public.get("github_stars", "—")))
    pypi = html.escape(str(public.get("pypi_downloads_monthly", "—")))
    vscode = html.escape(str(public.get("vscode_installs", "—")))
    rows = "".join(
        f"<tr><td>{html.escape(stage)}</td><td>{int(local.get(stage, 0))}</td></tr>"
        for stage in FUNNEL_STAGES
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>ForgeBench Adoption Dashboard</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 52rem; color: #1a1a2e; }}
    h1 {{ color: #4c1d95; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr)); gap: 1rem; }}
    .card {{ background: #f5f3ff; border-radius: 8px; padding: 1rem; }}
    .card strong {{ font-size: 1.5rem; display: block; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 0.5rem; text-align: left; }}
    .muted {{ color: #6b7280; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <h1>ForgeBench Adoption</h1>
  <p class="muted">Public launch funnel · v{html.escape(__version__)}</p>
  <div class="cards">
    <div class="card"><span class="muted">GitHub stars</span><strong>{stars}</strong></div>
    <div class="card"><span class="muted">PyPI downloads/mo</span><strong>{pypi}</strong></div>
    <div class="card"><span class="muted">VS Code installs</span><strong>{vscode}</strong></div>
  </div>
  <h2>Adoption funnel (this machine)</h2>
  <table>
    <thead><tr><th>Stage</th><th>Reached</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <p class="muted">{html.escape(str(manifest.get("privacy_note") or ""))}</p>
  <p><a href="https://forgebench.dev">forgebench.dev</a> · <a href="https://github.com/caissonhq/forgebench">GitHub</a></p>
</body>
</html>
"""