from __future__ import annotations

import fnmatch
from pathlib import Path

from forgebench.models import (
    Confidence,
    DiffSummary,
    EvidenceType,
    Finding,
    FindingOverride,
    Guardrails,
    GuardrailsPolicy,
    MergePosture,
    PathCategory,
    PostureOverride,
    Severity,
    SuppressFindingRule,
)


def load_guardrails(path: str | Path | None) -> Guardrails:
    if path is None:
        return Guardrails()
    return parse_guardrails(Path(path).read_text(encoding="utf-8", errors="replace"))


def parse_guardrails(text: str) -> Guardrails:
    payload = _parse_yaml_like(text)
    risk_files = _as_dict(payload.get("risk_files"))
    checks_payload = _as_dict(payload.get("checks"))

    return Guardrails(
        project=_optional_string(payload.get("project")),
        protected_behavior=_string_list(payload.get("protected_behavior")),
        risk_files_high=_string_list(risk_files.get("high")),
        risk_files_medium=_string_list(risk_files.get("medium")),
        forbidden_patterns=_string_list(payload.get("forbidden_patterns")),
        checks=_checks_dict(checks_payload, include_custom=False),
        custom_checks=_checks_dict(_as_dict(checks_payload.get("custom")), include_custom=True),
        checks_present="checks" in payload,
        check_timeout_seconds=_parse_timeout(payload.get("check_timeout_seconds", 120)),
        policy=_parse_policy(_as_dict(payload.get("policy"))),
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


def matches_path_pattern(path: str, pattern: str) -> bool:
    return _matches_pattern(path.replace("\\", "/"), pattern)


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


def _parse_policy(payload: dict[str, object]) -> GuardrailsPolicy:
    finding_overrides_payload = _as_dict(payload.get("finding_overrides"))
    path_categories_payload = _as_dict(payload.get("path_categories"))
    posture_overrides_payload = _as_dict(payload.get("posture_overrides"))

    finding_overrides: dict[str, FindingOverride] = {}
    for finding_id, value in finding_overrides_payload.items():
        config = _as_dict(value)
        finding_overrides[str(finding_id)] = FindingOverride(
            finding_id=str(finding_id),
            severity=_parse_severity(config.get("severity")),
            confidence=_parse_confidence(config.get("confidence")),
            applies_to=_string_list(config.get("applies_to")),
            suppress_paths=_string_list(config.get("suppress_paths")),
            suppress_if_all_files_match=_string_list(config.get("suppress_if_all_files_match")),
            reason=_optional_string(config.get("reason")) or "",
        )

    path_categories: dict[str, PathCategory] = {}
    for category_name, value in path_categories_payload.items():
        config = _as_dict(value)
        path_categories[str(category_name)] = PathCategory(
            name=str(category_name),
            patterns=_string_list(config.get("patterns")),
            default_severity=_parse_severity(config.get("default_severity")),
        )

    suppress_findings: list[SuppressFindingRule] = []
    for item in _dict_list(payload.get("suppress_findings")):
        finding_id = _optional_string(item.get("finding_id"))
        if not finding_id:
            continue
        suppress_findings.append(
            SuppressFindingRule(
                finding_id=finding_id,
                paths=_string_list(item.get("paths")),
                when_all_changed_files_match=_string_list(item.get("when_all_changed_files_match")),
                reason=_optional_string(item.get("reason")) or "",
            )
        )

    posture_overrides: dict[str, PostureOverride] = {}
    for override_name, value in posture_overrides_payload.items():
        config = _as_dict(value)
        posture_overrides[str(override_name)] = PostureOverride(
            name=str(override_name),
            posture_ceiling=_parse_posture(config.get("posture_ceiling")),
            reason=_optional_string(config.get("reason")) or "",
        )

    return GuardrailsPolicy(
        finding_overrides=finding_overrides,
        path_categories=path_categories,
        advisory_only=_string_list(payload.get("advisory_only")),
        suppress_findings=suppress_findings,
        posture_overrides=posture_overrides,
    )


def _parse_yaml_like(text: str) -> dict[str, object]:
    lines = [
        (len(raw_line) - len(raw_line.lstrip(" ")), raw_line.strip())
        for raw_line in text.splitlines()
        if raw_line.strip() and not raw_line.lstrip().startswith("#")
    ]
    if not lines:
        return {}
    parsed, _ = _parse_block(lines, 0, lines[0][0])
    return _as_dict(parsed)


def _parse_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[object, int]:
    if index >= len(lines):
        return {}, index
    if lines[index][1].startswith("- "):
        return _parse_list_block(lines, index, indent)
    return _parse_dict_block(lines, index, indent)


def _parse_dict_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, object], int]:
    payload: dict[str, object] = {}
    while index < len(lines):
        line_indent, line = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            index += 1
            continue
        if line.startswith("- ") or ":" not in line:
            break

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            payload[key] = _clean_scalar(value)
            index += 1
            continue

        index += 1
        if index < len(lines) and lines[index][0] > line_indent:
            payload[key], index = _parse_block(lines, index, lines[index][0])
        else:
            payload[key] = None
    return payload, index


def _parse_list_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list[object], int]:
    items: list[object] = []
    while index < len(lines):
        line_indent, line = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            index += 1
            continue
        if not line.startswith("- "):
            break

        item = line[2:].strip()
        if ":" in item:
            key, value = item.split(":", 1)
            item_payload: dict[str, object] = {}
            item_payload[key.strip()] = _clean_scalar(value.strip()) if value.strip() else None
            index += 1
            if index < len(lines) and lines[index][0] > line_indent:
                nested, index = _parse_block(lines, index, lines[index][0])
                if isinstance(nested, dict):
                    item_payload.update(nested)
                elif value.strip() == "":
                    item_payload[key.strip()] = nested
            items.append(item_payload)
        else:
            items.append(_clean_scalar(item))
            index += 1
    return items, index


def _as_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _dict_list(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _checks_dict(payload: dict[str, object], include_custom: bool) -> dict[str, str | None]:
    checks: dict[str, str | None] = {}
    for key, value in payload.items():
        if key == "custom" and not include_custom:
            continue
        if isinstance(value, dict):
            continue
        checks[str(key)] = _optional_string(value)
    return checks


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _parse_severity(value: object) -> Severity | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return Severity.__members__.get(normalized)


def _parse_confidence(value: object) -> Confidence | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return Confidence.__members__.get(normalized)


def _parse_posture(value: object) -> MergePosture | None:
    if value is None:
        return None
    normalized = str(value).strip().upper()
    return MergePosture.__members__.get(normalized)


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
