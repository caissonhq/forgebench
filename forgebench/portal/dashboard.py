from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forgebench import __version__
from forgebench.crm.pipeline import format_pipeline_summary, load_pipeline
from forgebench.licensing.quotas import export_quota_report
from forgebench.licensing.store import format_license_status, load_license


@dataclass(frozen=True)
class PortalExportResult:
    output_dir: Path
    index_path: Path
    manifest_path: Path


def export_customer_portal(*, output_dir: str | Path = "forgebench-output/portal") -> PortalExportResult:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    license_record = load_license()
    quotas = export_quota_report()
    pipeline = [entry.__dict__ for entry in load_pipeline()]
    manifest: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "forgebench_version": __version__,
        "license": {
            "tier": license_record.tier.name.lower(),
            "valid": license_record.valid,
            "organization": license_record.organization,
            "seats": license_record.seats,
            "activations": len(license_record.activations),
            "expires_at": license_record.expires_at,
            "message": license_record.message,
        },
        "quotas": quotas,
        "pipeline": pipeline,
        "invoices_note": "Invoices available via Stripe Customer Portal when billing is configured.",
        "policy_links": [
            "forgebench policy test",
            "forgebench init --enterprise",
            "forgebench github-app manifest",
        ],
    }
    manifest_path = out / "portal-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    index_path = out / "index.html"
    index_path.write_text(_render_portal_html(manifest, license_record), encoding="utf-8")
    return PortalExportResult(output_dir=out, index_path=index_path, manifest_path=manifest_path)


def _render_portal_html(manifest: dict[str, Any], license_record) -> str:
    license_block = html.escape(format_license_status(license_record).strip())
    quotas = manifest.get("quotas") or {}
    quota_rows = ""
    for name, status in (quotas.get("quotas") or {}).items():
        if not isinstance(status, dict):
            continue
        quota_rows += (
            f"<tr><td>{html.escape(str(name))}</td>"
            f"<td>{int(status.get('used', 0))}</td>"
            f"<td>{int(status.get('limit', 0))}</td>"
            f"<td>{int(status.get('remaining', 0))}</td></tr>"
        )
    pipeline_text = html.escape(format_pipeline_summary())
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>ForgeBench Customer Portal</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 56rem; color: #1a1a2e; }}
    h1 {{ color: #4c1d95; }}
    pre {{ background: #f5f3ff; padding: 1rem; border-radius: 8px; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 0.5rem; text-align: left; }}
    .card {{ background: #fafafa; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
    .muted {{ color: #6b7280; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <h1>ForgeBench Customer Portal</h1>
  <p class="muted">Self-hosted dashboard · v{html.escape(__version__)}</p>
  <div class="card">
    <h2>License</h2>
    <pre>{license_block}</pre>
  </div>
  <div class="card">
    <h2>Usage &amp; quotas</h2>
    <table>
      <thead><tr><th>Quota</th><th>Used</th><th>Limit</th><th>Remaining</th></tr></thead>
      <tbody>{quota_rows or "<tr><td colspan='4'>No quota data</td></tr>"}</tbody>
    </table>
  </div>
  <div class="card">
    <h2>Invoices</h2>
    <p>{html.escape(str(manifest.get("invoices_note") or ""))}</p>
    <p><code>forgebench subscribe portal</code> when Stripe billing portal is configured.</p>
  </div>
  <div class="card">
    <h2>Policy management</h2>
    <ul>
      <li><code>forgebench init --enterprise</code></li>
      <li><code>forgebench policy test</code></li>
      <li><code>forgebench github-app manifest</code></li>
    </ul>
  </div>
  <div class="card">
    <h2>CRM pipeline (local)</h2>
    <pre>{pipeline_text}</pre>
  </div>
  <p><a href="https://forgebench.dev/docs/pricing/">Pricing</a> · <a href="mailto:hello@forgebench.dev">Support</a></p>
</body>
</html>
"""