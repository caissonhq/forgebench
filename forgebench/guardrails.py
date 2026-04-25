from __future__ import annotations

import fnmatch
from pathlib import Path

from forgebench.models import Confidence, DiffSummary, EvidenceType, Finding, Guardrails, Severity


def load_guardrails(path: str | Path | None) -> Guardrails:
    if path is None:
        return Guardrails()
    return parse_guardrails(Path(path).read_text(encoding="utf-8", errors="replace"))


def parse_guardrails(text: str) -> Guardrails:
    project: str | None = None
    protected_behavior: list[str] = []
    risk_files_high: list[str] = []
    risk_files_medium: list[str] = []
    forbidden_patterns: list[str] = []
    checks: dict[str, str | None] = {}
    custom_checks: dict[str, str | None] = {}
    checks_present = False
    check_timeout_seconds = 120

    current_key: str | None = None
    current_nested_key: str | None = None

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()

        if indent == 0:
            current_nested_key = None
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            current_key = key.strip()
            value = _clean_scalar(value.strip())
            if current_key == "project" and value:
                project = value
            elif current_key == "check_timeout_seconds" and value is not None:
                check_timeout_seconds = _parse_timeout(value)
            elif current_key == "checks":
                checks_present = True
            continue

        if indent == 2:
            if current_key == "risk_files" and line.endswith(":"):
                current_nested_key = line[:-1].strip()
                continue
            if current_key == "checks":
                if line.endswith(":"):
                    current_nested_key = line[:-1].strip()
                    continue
                if ":" in line:
                    key, value = line.split(":", 1)
                    checks[key.strip()] = _clean_scalar(value.strip())
                continue
            if line.startswith("- "):
                item = _clean_scalar(line[2:].strip())
                if current_key == "protected_behavior":
                    protected_behavior.append(item)
                elif current_key == "forbidden_patterns":
                    forbidden_patterns.append(item)
            continue

        if indent == 4 and current_key == "risk_files" and current_nested_key and line.startswith("- "):
            item = _clean_scalar(line[2:].strip())
            if current_nested_key == "high":
                risk_files_high.append(item)
            elif current_nested_key == "medium":
                risk_files_medium.append(item)
            continue

        if indent == 4 and current_key == "checks" and current_nested_key == "custom" and ":" in line:
            key, value = line.split(":", 1)
            custom_checks[key.strip()] = _clean_scalar(value.strip())
            continue

    return Guardrails(
        project=project,
        protected_behavior=protected_behavior,
        risk_files_high=risk_files_high,
        risk_files_medium=risk_files_medium,
        forbidden_patterns=forbidden_patterns,
        checks=checks,
        custom_checks=custom_checks,
        checks_present=checks_present,
        check_timeout_seconds=check_timeout_seconds,
    )


def evaluate_guardrails(diff: DiffSummary, guardrails: Guardrails) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    hits: list[str] = []

    high_matches = _matched_file_patterns(diff.changed_files, guardrails.risk_files_high)
    high_risk_files = sorted(high_matches)
    if high_risk_files:
        high_evidence = _format_file_pattern_evidence("High-risk", high_matches)
        hits.extend(high_evidence)
        findings.append(
            Finding(
                id="high_risk_guardrail_file",
                title="High-risk project area changed",
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                evidence_type=EvidenceType.STATIC,
                files=high_risk_files,
                evidence=high_evidence,
                explanation=(
                    "The patch changes files matched by high-risk project guardrails. These areas usually "
                    "encode protected behavior or fragile architecture and need deliberate review before merge."
                ),
                suggested_fix=(
                    "Review the changed high-risk files against the original task and add focused tests "
                    "or reduce the patch scope if the changes are not required."
                ),
            )
        )

    medium_matches = _matched_file_patterns(diff.changed_files, guardrails.risk_files_medium)
    for file_path in high_risk_files:
        medium_matches.pop(file_path, None)
    medium_risk_files = sorted(medium_matches)
    if medium_risk_files:
        medium_evidence = _format_file_pattern_evidence("Medium-risk", medium_matches)
        hits.extend(medium_evidence)
        findings.append(
            Finding(
                id="medium_risk_guardrail_file",
                title="Medium-risk project area changed",
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                evidence_type=EvidenceType.STATIC,
                files=medium_risk_files,
                evidence=medium_evidence,
                explanation=(
                    "The patch changes files that project guardrails mark as medium risk. "
                    "This is not automatically wrong, but it should be reviewed deliberately."
                ),
                suggested_fix=(
                    "Confirm these changes are necessary for the task and covered by tests or manual checks."
                ),
            )
        )

    forbidden_matches = _find_forbidden_pattern_hits(diff, guardrails.forbidden_patterns)
    if forbidden_matches:
        forbidden_evidence = [match["evidence"] for match in forbidden_matches]
        hits.extend(forbidden_evidence)
        files = sorted({match["file"] for match in forbidden_matches})
        findings.append(
            Finding(
                id="forbidden_pattern_added",
                title="Forbidden product or architecture pattern introduced",
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                evidence_type=EvidenceType.STATIC,
                files=files,
                evidence=forbidden_evidence,
                explanation=(
                    "Added lines include a pattern that project guardrails explicitly forbid. This may indicate "
                    "scope creep or an architecture direction the project has rejected."
                ),
                suggested_fix=(
                    "Remove the forbidden pattern or explain why the guardrail is no longer valid before merging."
                ),
            )
        )

    return findings, hits


def _matched_file_patterns(files: list[str], patterns: list[str]) -> dict[str, list[str]]:
    matched: dict[str, list[str]] = {}
    for file_path in files:
        normalized = file_path.replace("\\", "/")
        file_patterns = [pattern for pattern in patterns if _matches_pattern(normalized, pattern)]
        if file_patterns:
            matched[file_path] = sorted(set(file_patterns))
    return matched


def _matches_pattern(path: str, pattern: str) -> bool:
    normalized_pattern = pattern.replace("\\", "/")
    candidates = {
        normalized_pattern,
        normalized_pattern.removeprefix("**/"),
        normalized_pattern.replace("**/", ""),
    }
    return any(fnmatch.fnmatch(path, candidate) or fnmatch.fnmatch("/" + path, candidate) for candidate in candidates)


def _find_forbidden_pattern_hits(diff: DiffSummary, patterns: list[str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    lowered_patterns = [(pattern, pattern.lower()) for pattern in patterns]
    for changed_file in diff.files:
        for added_line in changed_file.added_lines:
            lowered_line = added_line.lower()
            for original_pattern, lowered_pattern in lowered_patterns:
                if lowered_pattern and lowered_pattern in lowered_line:
                    snippet = added_line.strip()
                    if len(snippet) > 120:
                        snippet = snippet[:117].rstrip() + "..."
                    hits.append(
                        {
                            "file": changed_file.path,
                            "pattern": original_pattern,
                            "evidence": f"Forbidden pattern '{original_pattern}' added in {changed_file.path}: {snippet}",
                        }
                    )
    unique: dict[tuple[str, str, str], dict[str, str]] = {}
    for hit in hits:
        unique[(hit["file"], hit["pattern"], hit["evidence"])] = hit
    return [unique[key] for key in sorted(unique)]


def _format_file_pattern_evidence(label: str, matches: dict[str, list[str]]) -> list[str]:
    evidence: list[str] = []
    for file_path in sorted(matches):
        for pattern in matches[file_path]:
            evidence.append(f"{label} guardrail pattern '{pattern}' matched {file_path}")
    return evidence


def _clean_scalar(value: str) -> str | None:
    stripped = value.strip()
    if not stripped or stripped.lower() in {"null", "none", "~"}:
        return None
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1].replace('\\"', '"').replace("\\'", "'")
    return stripped


def _parse_timeout(value: object) -> int:
    try:
        timeout = int(str(value))
    except (TypeError, ValueError):
        return 120
    return max(1, timeout)
