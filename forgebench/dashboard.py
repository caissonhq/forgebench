from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from forgebench.guardrails import GuardrailsParseError, load_guardrails
from forgebench.policy_layers import resolve_guardrails_path


@dataclass(frozen=True)
class DashboardExportResult:
    output_dir: Path
    index_path: Path
    manifest_path: Path
    guardrails_path: Path | None


def export_policy_dashboard(
    repo_path: str | Path,
    *,
    guardrails_path: str | Path | None = None,
    output_dir: str | Path | None = None,
) -> DashboardExportResult:
    repo = Path(repo_path)
    guardrails_file = resolve_guardrails_path(repo, guardrails_path)
    if guardrails_file is None:
        raise DashboardExportError("No forgebench.yml found. Run forgebench init or pass --guardrails.")

    try:
        guardrails = load_guardrails(guardrails_file)
    except GuardrailsParseError as exc:
        raise DashboardExportError(str(exc)) from exc

    out_dir = Path(output_dir) if output_dir else repo / "forgebench-output" / "policy-dashboard"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = _build_manifest(repo, guardrails_file, guardrails)
    manifest_path = out_dir / "policy-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    index_path = out_dir / "index.html"
    index_path.write_text(_render_dashboard_html(manifest), encoding="utf-8")

    return DashboardExportResult(
        output_dir=out_dir,
        index_path=index_path,
        manifest_path=manifest_path,
        guardrails_path=guardrails_file,
    )


class DashboardExportError(ValueError):
    pass


def _build_manifest(repo: Path, guardrails_file: Path, guardrails) -> dict[str, object]:
    return {
        "schema_version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo": str(repo.resolve()),
        "guardrails_file": str(guardrails_file.resolve()),
        "team": guardrails.team,
        "project": guardrails.project,
        "policy_sources": guardrails.sources,
        "protected_behavior": guardrails.protected_behavior,
        "risk_files": {
            "high": guardrails.risk_files_high,
            "medium": guardrails.risk_files_medium,
        },
        "forbidden_patterns": guardrails.forbidden_patterns,
        "review_scope": {
            "include_paths": guardrails.review_scope_include_paths,
            "exclude_paths": guardrails.review_scope_exclude_paths,
        },
        "checks": guardrails.checks,
        "custom_checks": guardrails.custom_checks,
        "policy": {
            "advisory_only": guardrails.policy.advisory_only,
            "finding_override_count": len(guardrails.policy.finding_overrides),
            "path_category_count": len(guardrails.policy.path_categories),
            "suppress_finding_count": len(guardrails.policy.suppress_findings),
            "posture_override_count": len(guardrails.policy.posture_overrides),
        },
        "warnings": guardrails.warnings,
        "hosted_preview_sections": [
            "org_policy_inventory",
            "repo_adoption_status",
            "posture_trends",
            "finding_calibration_queue",
            "audit_log",
        ],
    }


def _render_dashboard_html(manifest: dict[str, object]) -> str:
    title = manifest.get("team") or manifest.get("project") or "ForgeBench Policy"
    sources = manifest.get("policy_sources") or []
    protected = manifest.get("protected_behavior") or []
    risk_files = manifest.get("risk_files") or {}
    forbidden = manifest.get("forbidden_patterns") or []
    checks = manifest.get("checks") or {}
    policy = manifest.get("policy") or {}
    preview_sections = manifest.get("hosted_preview_sections") or []

    def render_list(items: list[object]) -> str:
        if not items:
            return "<p class='muted'>None configured.</p>"
        return "<ul>" + "".join(f"<li>{html.escape(str(item))}</li>" for item in items) + "</ul>"

    def render_checks(items: dict[str, object]) -> str:
        configured = {key: value for key, value in items.items() if value}
        if not configured:
            return "<p class='muted'>No deterministic checks configured.</p>"
        return "<ul>" + "".join(
            f"<li><code>{html.escape(str(key))}</code>: {html.escape(str(value))}</li>"
            for key, value in sorted(configured.items())
        ) + "</ul>"

    preview_cards = "".join(
        f"<article class='card skeleton'><h3>{html.escape(str(section).replace('_', ' ').title())}</h3>"
        f"<p class='muted'>Hosted preview placeholder. Wire this to org-wide review telemetry in a future release.</p></article>"
        for section in preview_sections
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(str(title))} — ForgeBench Policy Dashboard</title>
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
    header, main {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 24px;
    }}
    header {{
      border-bottom: 1px solid var(--border);
    }}
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
    .skeleton {{
      border-style: dashed;
      opacity: 0.92;
    }}
    code {{
      background: rgba(77, 163, 255, 0.12);
      padding: 2px 6px;
      border-radius: 6px;
    }}
    ul {{ margin: 8px 0 0; padding-left: 20px; }}
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
    <p class="muted">ForgeBench policy dashboard skeleton</p>
    <h1>{html.escape(str(title))}</h1>
    <p class="muted">Local export preview for shared <code>forgebench.yml</code> policy. Not a hosted SaaS.</p>
    <p><span class="badge">Schema {html.escape(str(manifest.get("schema_version")))}</span>
       <span class="badge">Generated {html.escape(str(manifest.get("generated_at")))}</span></p>
  </header>
  <main>
    <section class="grid">
      <article class="card">
        <h2>Policy sources</h2>
        {render_list(sources)}
      </article>
      <article class="card">
        <h2>Protected behavior</h2>
        {render_list(protected)}
      </article>
      <article class="card">
        <h2>Risk files</h2>
        <h3>High</h3>
        {render_list(risk_files.get("high", []))}
        <h3>Medium</h3>
        {render_list(risk_files.get("medium", []))}
      </article>
      <article class="card">
        <h2>Forbidden patterns</h2>
        {render_list(forbidden)}
      </article>
      <article class="card">
        <h2>Deterministic checks</h2>
        {render_checks(checks)}
      </article>
      <article class="card">
        <h2>Policy calibration</h2>
        <ul>
          <li>Finding overrides: {html.escape(str(policy.get("finding_override_count", 0)))}</li>
          <li>Path categories: {html.escape(str(policy.get("path_category_count", 0)))}</li>
          <li>Suppress rules: {html.escape(str(policy.get("suppress_finding_count", 0)))}</li>
          <li>Posture ceilings: {html.escape(str(policy.get("posture_override_count", 0)))}</li>
        </ul>
      </article>
    </section>
    <section style="margin-top: 32px">
      <h2>Hosted preview placeholders</h2>
      <p class="muted">Skeleton sections for a future hosted Team/Enterprise dashboard.</p>
      <div class="grid">{preview_cards}</div>
    </section>
  </main>
</body>
</html>
"""