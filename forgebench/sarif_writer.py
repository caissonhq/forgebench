from __future__ import annotations

import json
import re
from typing import Any

from forgebench.models import ForgeBenchReport, MergePosture, Severity


SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
TOOL_NAME = "ForgeBench"
TOOL_VERSION = "0.9.0"
REPORT_SARIF = "forgebench-report.sarif.json"

_SEVERITY_TO_SARIF_LEVEL = {
    Severity.BLOCKER: "error",
    Severity.HIGH: "error",
    Severity.MEDIUM: "warning",
    Severity.LOW: "note",
    Severity.ADVISORY: "note",
}

_POSTURE_TO_SARIF_LEVEL = {
    MergePosture.BLOCK: "error",
    MergePosture.REVIEW: "warning",
    MergePosture.LOW_CONCERN: "note",
}


def build_sarif_report(report: ForgeBenchReport) -> dict[str, Any]:
    rules: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []

    for finding in report.findings:
        rule_id = finding.kind or finding.id
        if rule_id not in rules:
            rules[rule_id] = {
                "id": rule_id,
                "name": finding.title,
                "shortDescription": {"text": finding.title},
                "fullDescription": {"text": finding.explanation},
                "help": {"text": finding.suggested_fix},
                "properties": {
                    "tags": [finding.evidence_type.value.lower(), finding.confidence.value.lower()],
                },
            }
        results.append(_finding_to_result(finding, rule_id))

    if not results:
        results.append(
            {
                "ruleId": "forgebench.posture",
                "level": _POSTURE_TO_SARIF_LEVEL.get(report.posture, "note"),
                "message": {"text": report.summary},
                "properties": {"posture": report.posture.value},
            }
        )

    return {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": TOOL_NAME,
                        "version": TOOL_VERSION,
                        "informationUri": "https://forgebench.dev",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
                "properties": {
                    "posture": report.posture.value,
                    "config_mode": report.config_mode,
                    "finding_count": len(report.findings),
                },
            }
        ],
    }


def write_sarif_report(out_dir, report: ForgeBenchReport) -> "Path":
    from pathlib import Path

    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / REPORT_SARIF
    path.write_text(json.dumps(build_sarif_report(report), indent=2) + "\n", encoding="utf-8")
    return path


def _finding_to_result(finding, rule_id: str) -> dict[str, Any]:
    location = _location_from_finding(finding)
    return {
        "ruleId": rule_id,
        "level": _SEVERITY_TO_SARIF_LEVEL.get(finding.severity, "warning"),
        "message": {"text": finding.explanation},
        "locations": [location] if location else [],
        "properties": {
            "uid": finding.uid,
            "kind": finding.kind,
            "severity": finding.severity.value,
            "confidence": finding.confidence.value,
            "evidence_type": finding.evidence_type.value,
            "files": list(finding.files),
            "suggested_fix": finding.suggested_fix,
            "evidence": list(finding.evidence),
        },
    }


def _location_from_finding(finding) -> dict[str, Any] | None:
    if not finding.files:
        return None
    file_path = finding.files[0]
    start_line = 1
    for snippet in finding.evidence:
        match = re.search(rf"{re.escape(file_path)}:(\d+):", snippet)
        if match:
            start_line = int(match.group(1))
            break
    return {
        "physicalLocation": {
            "artifactLocation": {"uri": file_path},
            "region": {"startLine": start_line, "endLine": start_line},
        }
    }