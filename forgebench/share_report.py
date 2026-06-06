from __future__ import annotations

import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


class ShareReportError(ValueError):
    pass


@dataclass(frozen=True)
class ShareReportResult:
    html_path: Path
    source_markdown: Path
    source_json: Path | None


def export_shareable_report(
    *,
    output_dir: str | Path = "forgebench-output",
    dest: str | Path | None = None,
) -> ShareReportResult:
    out = Path(output_dir)
    md_path = out / "forgebench-report.md"
    json_path = out / "forgebench-report.json"
    if not md_path.exists():
        raise ShareReportError(f"report not found at {md_path}. Run a review first.")

    posture = "UNKNOWN"
    finding_count = 0
    if json_path.exists():
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            posture = str(payload.get("posture") or posture)
            findings = payload.get("findings")
            if isinstance(findings, list):
                finding_count = len(findings)
        except json.JSONDecodeError:
            pass

    markdown = md_path.read_text(encoding="utf-8", errors="replace")
    html_path = Path(dest) if dest else out / "forgebench-share.html"
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(_render_share_html(markdown, posture=posture, finding_count=finding_count), encoding="utf-8")

    from forgebench.adoption import record_milestone

    record_milestone("first_share_report")
    return ShareReportResult(html_path=html_path, source_markdown=md_path, source_json=json_path if json_path.exists() else None)


def _render_share_html(markdown: str, *, posture: str, finding_count: int) -> str:
    body = html.escape(markdown)
    color = {"BLOCK": "#dc2626", "REVIEW": "#d97706", "LOW_CONCERN": "#16a34a"}.get(posture, "#4c1d95")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>ForgeBench Review — {html.escape(posture)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; background: #fafafa; color: #1a1a2e; }}
    header {{ background: {color}; color: #fff; padding: 1.5rem 2rem; }}
    main {{ max-width: 52rem; margin: 2rem auto; padding: 0 1rem; }}
    pre {{ white-space: pre-wrap; background: #fff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 1.25rem; line-height: 1.5; }}
    .muted {{ opacity: 0.85; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <header>
    <h1>ForgeBench Merge-Risk Report</h1>
    <p class="muted">Posture: {html.escape(posture)} · Findings: {finding_count}</p>
  </header>
  <main>
    <pre>{body}</pre>
    <p class="muted">Generated {html.escape(datetime.now(timezone.utc).isoformat(timespec="seconds"))} · forgebench.dev</p>
  </main>
</body>
</html>
"""