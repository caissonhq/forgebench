from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench.licensing.quotas import export_quota_report
from forgebench.licensing.store import load_license
from forgebench.product_analytics import export_product_analytics_bundle
from forgebench.telemetry import export_telemetry_bundle, summarize_telemetry_events


@dataclass(frozen=True)
class AnalyticsDashboardResult:
    output_dir: Path
    index_path: Path
    manifest_path: Path


def export_analytics_dashboard(
    *,
    output_dir: str | Path = "forgebench-output/analytics-dashboard",
    include_review_telemetry: bool = True,
    cloud_export: bool = False,
) -> AnalyticsDashboardResult:
    if cloud_export:
        from forgebench.licensing.quotas import consume_quota

        consume_quota("analytics_cloud_export")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    license_record = load_license()
    product_bundle = export_product_analytics_bundle()
    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "license": {
            "tier": license_record.tier.name.lower(),
            "valid": license_record.valid,
            "organization": license_record.organization,
        },
        "product_analytics": {
            "opt_in": product_bundle.get("opt_in"),
            "event_count": product_bundle.get("event_count"),
            "summary": product_bundle.get("summary"),
        },
        "quotas": export_quota_report(),
    }
    if include_review_telemetry:
        review_bundle = export_telemetry_bundle()
        manifest["review_telemetry"] = {
            "opt_in": review_bundle.get("opt_in"),
            "event_count": review_bundle.get("event_count"),
            "summary": summarize_telemetry_events(review_bundle.get("events") or []),
            "note": "Review telemetry is separate from product analytics.",
        }
    manifest_path = out / "analytics-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    index_path = out / "index.html"
    index_path.write_text(_render_html(manifest), encoding="utf-8")
    from forgebench.product_analytics import record_product_event

    record_product_event(
        "analytics_dashboard_exported",
        {"cloud_export": cloud_export, "include_review_telemetry": include_review_telemetry},
    )
    return AnalyticsDashboardResult(output_dir=out, index_path=index_path, manifest_path=manifest_path)


def _render_html(manifest: dict[str, Any]) -> str:
    product = manifest.get("product_analytics") or {}
    review = manifest.get("review_telemetry") or {}
    license_info = manifest.get("license") or {}
    quotas = (manifest.get("quotas") or {}).get("quotas") or {}
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>ForgeBench Usage Analytics</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a2e; background: #fafafa; }}
    h1 {{ color: #4c1d95; }}
    .card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1.25rem; margin: 1rem 0; }}
    .muted {{ color: #6b7280; font-size: 0.9rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ text-align: left; padding: 0.5rem; border-bottom: 1px solid #eee; }}
    th {{ background: #f3f4f6; }}
  </style>
</head>
<body>
  <h1>ForgeBench Usage Analytics</h1>
  <p class="muted">Self-hosted dashboard — product adoption metrics distinct from review telemetry.</p>
  <div class="card">
    <h2>License</h2>
    <ul>
      <li>Tier: {html.escape(str(license_info.get('tier', 'free')))}</li>
      <li>Organization: {html.escape(str(license_info.get('organization') or '—'))}</li>
      <li>Valid: {html.escape(str(license_info.get('valid')))}</li>
    </ul>
  </div>
  <div class="card">
    <h2>Product analytics (opt-in)</h2>
    <p class="muted">CLI commands, license events, onboarding — no diff content.</p>
    {_kv_table((product.get('summary') or {}).get('event_counts') or {})}
  </div>
  <div class="card">
    <h2>Review telemetry (opt-in, separate)</h2>
    <p class="muted">{html.escape(str(review.get('note') or ''))}</p>
    {_kv_table((review.get('summary') or {}).get('event_counts') or {})}
  </div>
  <div class="card">
    <h2>Quotas</h2>
    {_quota_table(quotas)}
  </div>
  <p class="muted">Generated {html.escape(str(manifest.get('generated_at') or ''))}</p>
</body>
</html>
"""


def _kv_table(data: dict[str, Any]) -> str:
    if not data:
        return "<p class='muted'>No events recorded.</p>"
    rows = "".join(
        f"<tr><td>{html.escape(str(key))}</td><td>{html.escape(str(value))}</td></tr>"
        for key, value in sorted(data.items())
    )
    return f"<table><thead><tr><th>Metric</th><th>Count</th></tr></thead><tbody>{rows}</tbody></table>"


def _quota_table(quotas: dict[str, Any]) -> str:
    if not quotas:
        return "<p class='muted'>No quotas configured.</p>"
    rows = ""
    for name, item in sorted(quotas.items()):
        if not isinstance(item, dict):
            continue
        rows += (
            f"<tr><td>{html.escape(name)}</td>"
            f"<td>{html.escape(str(item.get('used', 0)))}</td>"
            f"<td>{html.escape(str(item.get('limit', 0)))}</td>"
            f"<td>{html.escape(str(item.get('remaining', 0)))}</td></tr>"
        )
    return (
        "<table><thead><tr><th>Quota</th><th>Used</th><th>Limit</th><th>Remaining</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )