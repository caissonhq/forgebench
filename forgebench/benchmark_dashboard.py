from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.benchmark import BenchmarkSnapshot, build_benchmark_snapshot, load_default_pr_outcomes
from forgebench.benchmark_outcomes import load_pr_outcomes, outcomes_to_manifest, summarize_pr_outcomes
from forgebench.review_arena import build_review_arena_leaderboard, leaderboard_to_manifest
from forgebench.telemetry import export_telemetry_bundle, summarize_telemetry_events


@dataclass(frozen=True)
class BenchmarkDashboardExportResult:
    output_dir: Path
    index_path: Path
    manifest_path: Path


class BenchmarkDashboardError(ValueError):
    pass


def export_benchmark_dashboard(
    *,
    cases_dir: str | Path = "examples/golden_cases",
    repo_path: str | Path = ".",
    calibration_output_dir: str | Path | None = None,
    outcomes_path: str | Path | None = None,
    output_dir: str | Path | None = None,
    include_telemetry: bool = True,
) -> BenchmarkDashboardExportResult:
    resolved_outcomes = outcomes_path
    if resolved_outcomes is None and load_default_pr_outcomes() is not None:
        resolved_outcomes = Path("examples/benchmark_outcomes/eo002-pr-outcomes.json")

    snapshot = build_benchmark_snapshot(
        cases_dir,
        repo_path=repo_path,
        output_dir=calibration_output_dir or Path("forgebench-benchmark-output"),
        outcomes_path=resolved_outcomes,
    )

    outcomes_bundle = load_pr_outcomes(resolved_outcomes) if resolved_outcomes else None
    arena = build_review_arena_leaderboard(snapshot, outcomes_bundle=outcomes_bundle)
    manifest = _build_manifest(snapshot, arena, outcomes_bundle, include_telemetry=include_telemetry)

    out_dir = Path(output_dir) if output_dir else Path("forgebench-output") / "benchmark-dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "benchmark-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    index_path = out_dir / "index.html"
    index_path.write_text(_render_dashboard_html(manifest), encoding="utf-8")

    try:
        from forgebench.telemetry import is_telemetry_enabled, record_telemetry_event

        if is_telemetry_enabled():
            record_telemetry_event(
                "dashboard_exported",
                {
                    "dashboard_type": "benchmark",
                    "case_count": snapshot.case_count,
                    "pass_rate": snapshot.passed_count / max(snapshot.case_count, 1),
                },
            )
    except Exception:
        pass

    return BenchmarkDashboardExportResult(
        output_dir=out_dir,
        index_path=index_path,
        manifest_path=manifest_path,
    )


def _build_manifest(
    snapshot: BenchmarkSnapshot,
    arena,
    outcomes_bundle,
    *,
    include_telemetry: bool,
) -> dict[str, Any]:
    manifest: dict[str, Any] = {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "benchmark": {
            "case_count": snapshot.case_count,
            "passed_count": snapshot.passed_count,
            "failed_count": snapshot.failed_count,
            "pass_rate": round(snapshot.passed_count / max(snapshot.case_count, 1), 4),
            "posture_distribution": snapshot.posture_distribution,
            "top_finding_kinds": snapshot.top_finding_kinds,
            "review_lens_fire_rate": snapshot.review_lens_fire_rate,
        },
        "review_arena": leaderboard_to_manifest(arena),
        "privacy_note": (
            "This dashboard is a local static export. No network upload is performed automatically. "
            "PR outcomes and telemetry are anonymized and opt-in."
        ),
    }
    if outcomes_bundle is not None:
        manifest["pr_outcomes"] = outcomes_to_manifest(outcomes_bundle, summarize_pr_outcomes(outcomes_bundle))
    if include_telemetry:
        bundle = export_telemetry_bundle()
        manifest["telemetry"] = {
            "opt_in": bundle.get("opt_in"),
            "event_count": bundle.get("event_count"),
            "summary": summarize_telemetry_events(bundle.get("events") or []),
            "privacy_note": bundle.get("privacy_note"),
        }
    return manifest


def _render_dashboard_html(manifest: dict[str, Any]) -> str:
    benchmark = manifest.get("benchmark") or {}
    arena = manifest.get("review_arena") or {}
    outcomes = manifest.get("pr_outcomes")
    telemetry = manifest.get("telemetry")

    def render_kv_table(data: dict[str, Any]) -> str:
        if not data:
            return "<p class='muted'>No data.</p>"
        rows = "".join(
            f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>"
            for key, value in sorted(data.items())
        )
        return f"<table><tbody>{rows}</tbody></table>"

    def render_leaderboard(entries: list[dict[str, Any]]) -> str:
        if not entries:
            return "<p class='muted'>No leaderboard entries.</p>"
        rows = []
        for entry in entries:
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(entry.get('rank')))}</td>"
                f"<td>{html.escape(str(entry.get('display_name')))}</td>"
                f"<td>{html.escape(str(entry.get('contender_type')))}</td>"
                f"<td>{html.escape(str(entry.get('score')))}</td>"
                "</tr>"
            )
        return (
            "<table><thead><tr><th>Rank</th><th>Contender</th><th>Type</th><th>Score</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )

    outcomes_section = ""
    if outcomes:
        summary = outcomes.get("summary") or {}
        outcomes_section = f"""
    <section class="grid">
      <article class="card">
        <h2>Real PR outcomes</h2>
        <p class="muted">{html.escape(str(outcomes.get('description') or ''))}</p>
        {render_kv_table(summary)}
      </article>
    </section>
"""

    telemetry_section = ""
    if telemetry:
        telemetry_section = f"""
    <section class="grid">
      <article class="card">
        <h2>Opt-in telemetry</h2>
        <p class="muted">{html.escape(str(telemetry.get('privacy_note') or ''))}</p>
        <ul>
          <li>Enabled: {html.escape(str(telemetry.get('opt_in')))}</li>
          <li>Events: {html.escape(str(telemetry.get('event_count')))}</li>
        </ul>
        {render_kv_table((telemetry.get('summary') or {}).get('event_counts') or {})}
      </article>
    </section>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>ForgeBench Merge Risk Benchmark</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #0f1419;
      --panel: #1a222d;
      --text: #e8eef7;
      --muted: #9aa7b8;
      --accent: #4da3ff;
      --border: #2b3645;
    }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif;
      background: linear-gradient(180deg, #0b1016 0%, var(--bg) 100%);
      color: var(--text);
      line-height: 1.5;
    }}
    header, main {{ max-width: 1080px; margin: 0 auto; padding: 24px; }}
    header {{ border-bottom: 1px solid var(--border); }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    .muted {{ color: var(--muted); }}
    .grid {{
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      margin-top: 16px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    td, th {{ border-bottom: 1px solid var(--border); padding: 8px; text-align: left; }}
    .badge {{
      display: inline-block;
      background: rgba(77, 163, 255, 0.18);
      color: var(--accent);
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      margin-right: 8px;
    }}
  </style>
</head>
<body>
  <header>
    <p class="muted">ForgeBench public benchmark dashboard (local export)</p>
    <h1>Merge Risk Benchmark</h1>
    <p class="muted">Golden-case calibration plus anonymized real PR outcomes. Not a hosted leaderboard.</p>
    <p>
      <span class="badge">Schema {html.escape(str(manifest.get('schema_version')))}</span>
      <span class="badge">Generated {html.escape(str(manifest.get('generated_at')))}</span>
    </p>
  </header>
  <main>
    <section class="grid">
      <article class="card">
        <h2>Calibration snapshot</h2>
        <ul>
          <li>Cases: {html.escape(str(benchmark.get('case_count')))}</li>
          <li>Pass rate: {html.escape(str(round((benchmark.get('pass_rate') or 0) * 100, 1)))}%</li>
          <li>Failed: {html.escape(str(benchmark.get('failed_count')))}</li>
        </ul>
        <h3>Posture distribution</h3>
        {render_kv_table(benchmark.get('posture_distribution') or {})}
      </article>
      <article class="card">
        <h2>Top finding kinds</h2>
        {render_kv_table(benchmark.get('top_finding_kinds') or {})}
      </article>
      <article class="card">
        <h2>Review lens fire-rate</h2>
        {render_kv_table(benchmark.get('review_lens_fire_rate') or {})}
      </article>
    </section>
    <section style="margin-top: 32px">
      <h2>Review Arena leaderboard</h2>
      <p class="muted">Ranking from calibration pass rate, lens activity, and PR outcome agreement.</p>
      {render_leaderboard(arena.get('entries') or [])}
    </section>
    {outcomes_section}
    {telemetry_section}
    <section style="margin-top: 32px">
      <p class="muted">{html.escape(str(manifest.get('privacy_note') or ''))}</p>
    </section>
  </main>
</body>
</html>
"""