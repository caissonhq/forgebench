from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from forgebench.models import ForgeBenchReport, MergePosture, Severity


GH_MISSING_MESSAGE = "GitHub Check Runs require GitHub CLI. Install gh and run gh auth login, then retry."
MAX_ANNOTATIONS = 50


class GitHubCheckRunError(ValueError):
    pass


@dataclass(frozen=True)
class CheckRunResult:
    posted: bool
    check_run_id: int | None = None
    check_run_url: str | None = None
    error_message: str | None = None


def post_check_run(
    *,
    owner: str,
    repo: str,
    head_sha: str,
    report: ForgeBenchReport,
    cwd: str | Path | None = None,
) -> CheckRunResult:
    payload = build_check_run_payload(report, head_sha=head_sha)
    command = [
        "gh",
        "api",
        "-X",
        "POST",
        f"repos/{owner}/{repo}/check-runs",
        "--input",
        "-",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=Path(cwd) if cwd else None,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitHubCheckRunError(GH_MISSING_MESSAGE) from exc
    except OSError as exc:
        raise GitHubCheckRunError(f"failed to run gh: {exc}") from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise GitHubCheckRunError(f"failed to post GitHub Check Run: {detail}")

    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GitHubCheckRunError("GitHub Check Run response was not valid JSON.") from exc

    return CheckRunResult(
        posted=True,
        check_run_id=_optional_int(response.get("id")),
        check_run_url=_optional_string(response.get("html_url")),
    )


def fetch_pr_head_sha(owner: str, repo: str, number: int, cwd: str | Path | None = None) -> str:
    command = [
        "gh",
        "pr",
        "view",
        str(number),
        "-R",
        f"{owner}/{repo}",
        "--json",
        "headRefOid",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=Path(cwd) if cwd else None,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitHubCheckRunError(GH_MISSING_MESSAGE) from exc
    except OSError as exc:
        raise GitHubCheckRunError(f"failed to run gh: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise GitHubCheckRunError(f"failed to fetch PR head SHA: {detail}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GitHubCheckRunError("PR head SHA response was not valid JSON.") from exc
    head_sha = _optional_string(payload.get("headRefOid"))
    if not head_sha:
        raise GitHubCheckRunError("PR head SHA was missing from gh response.")
    return head_sha


def build_check_run_payload(report: ForgeBenchReport, *, head_sha: str) -> dict[str, object]:
    annotations = _annotations_from_findings(report)
    summary = _check_run_summary(report)
    return {
        "name": "ForgeBench",
        "head_sha": head_sha,
        "status": "completed",
        "conclusion": _posture_to_conclusion(report.posture),
        "output": {
            "title": f"ForgeBench posture: {report.posture.value}",
            "summary": summary,
            "annotations": annotations,
        },
    }


def _check_run_summary(report: ForgeBenchReport) -> str:
    lines = [
        report.summary,
        "",
        f"Posture: **{report.posture.value}**",
        f"Configuration mode: {report.config_mode}",
        f"Findings: {len(report.findings)}",
    ]
    if report.findings:
        lines.append("")
        lines.append("Top findings:")
        for finding in report.findings[:10]:
            files = ", ".join(finding.files[:3]) if finding.files else "unknown"
            lines.append(f"- {finding.severity.value}: {finding.title} ({files})")
        if len(report.findings) > 10:
            lines.append(f"- ...and {len(report.findings) - 10} more")
    return "\n".join(lines)


def _annotations_from_findings(report: ForgeBenchReport) -> list[dict[str, object]]:
    annotations: list[dict[str, object]] = []
    for finding in report.findings:
        if len(annotations) >= MAX_ANNOTATIONS:
            break
        file_path, start_line = _annotation_location(finding)
        if not file_path:
            continue
        annotations.append(
            {
                "path": file_path,
                "start_line": start_line,
                "end_line": start_line,
                "annotation_level": _severity_to_annotation_level(finding.severity),
                "title": finding.title[:255],
                "message": _annotation_message(finding),
                "raw_details": finding.uid,
            }
        )
    return annotations


def _annotation_location(finding) -> tuple[str | None, int]:
    if not finding.files:
        return None, 1
    file_path = finding.files[0]
    start_line = 1
    for snippet in finding.evidence:
        match = re.search(rf"{re.escape(file_path)}:(\d+):", snippet)
        if match:
            start_line = int(match.group(1))
            break
    return file_path, start_line


def _annotation_message(finding) -> str:
    parts = [finding.explanation]
    if finding.suggested_fix:
        parts.append(f"Suggested fix: {finding.suggested_fix}")
    message = " ".join(parts)
    return message[:65535]


def _severity_to_annotation_level(severity: Severity) -> str:
    if severity in {Severity.BLOCKER, Severity.HIGH}:
        return "failure"
    if severity == Severity.MEDIUM:
        return "warning"
    return "notice"


def _posture_to_conclusion(posture: MergePosture) -> str:
    if posture == MergePosture.BLOCK:
        return "failure"
    if posture == MergePosture.REVIEW:
        return "neutral"
    return "success"


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None