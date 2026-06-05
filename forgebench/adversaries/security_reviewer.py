from __future__ import annotations

import re

from forgebench.adversaries.models import ReviewerContext, SECURITY_REVIEWER
from forgebench.models import Confidence, EvidenceType, Finding, Severity, SpecializedReviewerResult, SpecializedReviewerStatus


REVIEWER_NAME = "Security Reviewer"

SECRET_PATTERNS: tuple[tuple[str, str, Severity], ...] = (
    ("aws_access_key", r"\bAKIA[0-9A-Z]{16}\b", Severity.HIGH),
    ("github_token", r"\b(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{20,}\b", Severity.HIGH),
    ("private_key_block", r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----", Severity.BLOCKER),
    ("generic_api_secret", r"(?i)(?:api[_-]?key|secret|token|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]", Severity.HIGH),
    ("bearer_token", r"(?i)authorization\s*:\s*bearer\s+[A-Za-z0-9._-]{12,}", Severity.HIGH),
)

DANGEROUS_IMPORT_PATTERNS: tuple[tuple[str, str, Severity], ...] = (
    ("eval_call", r"\beval\s*\(", Severity.HIGH),
    ("exec_call", r"\bexec\s*\(", Severity.HIGH),
    ("os_system", r"\bos\.system\s*\(", Severity.HIGH),
    ("subprocess_shell", r"subprocess\.(?:run|Popen|call|check_output)\([^)]*shell\s*=\s*True", Severity.HIGH),
    ("dunder_import", r"\b__import__\s*\(", Severity.MEDIUM),
    ("pickle_loads", r"\bpickle\.loads\s*\(", Severity.HIGH),
    ("marshal_loads", r"\bmarshal\.loads\s*\(", Severity.MEDIUM),
    ("unsafe_yaml_load", r"\byaml\.load\s*\(", Severity.MEDIUM),
)


def review(context: ReviewerContext) -> SpecializedReviewerResult:
    findings: list[Finding] = []
    referenced: list[str] = []
    secret_hits = _scan_added_lines(context, SECRET_PATTERNS, category="secret")
    import_hits = _scan_added_lines(context, DANGEROUS_IMPORT_PATTERNS, category="dangerous_import")

    if secret_hits:
        files = sorted({hit["file"] for hit in secret_hits})
        findings.append(
            Finding(
                id="security_secret_in_added_lines",
                title="Possible secret or credential added in patch",
                severity=_max_severity(hit["severity"] for hit in secret_hits),
                confidence=Confidence.HIGH,
                evidence_type=EvidenceType.REVIEWER,
                files=files,
                evidence=[hit["evidence"] for hit in secret_hits[:12]],
                explanation=(
                    "Added lines match common secret or credential patterns. This may expose credentials in version "
                    "control or CI logs and should be reviewed before merge."
                ),
                suggested_fix=(
                    "Remove the secret from the patch, rotate the exposed credential, and load secrets from "
                    "environment variables or a secrets manager instead."
                ),
                reviewer=SECURITY_REVIEWER,
            )
        )
        referenced.append("security_secret_in_added_lines")

    if import_hits:
        files = sorted({hit["file"] for hit in import_hits})
        findings.append(
            Finding(
                id="security_dangerous_import_or_call",
                title="Dangerous import or dynamic execution pattern added",
                severity=_max_severity(hit["severity"] for hit in import_hits),
                confidence=Confidence.MEDIUM,
                evidence_type=EvidenceType.REVIEWER,
                files=files,
                evidence=[hit["evidence"] for hit in import_hits[:12]],
                explanation=(
                    "Added lines include dynamic execution, shell invocation, or unsafe deserialization patterns. "
                    "These increase exploit surface, especially in agent-generated code."
                ),
                suggested_fix=(
                    "Replace dynamic execution with explicit, reviewable code paths. Avoid shell=True, eval, exec, "
                    "and unsafe deserialization unless there is a documented, tested reason."
                ),
                reviewer=SECURITY_REVIEWER,
            )
        )
        referenced.append("security_dangerous_import_or_call")

    summary = "No secret or dangerous-import signals detected in added lines."
    if findings:
        summary = (
            f"Security lens flagged {len(findings)} concern(s): "
            + ", ".join(finding.title for finding in findings)
        )

    return SpecializedReviewerResult(
        reviewer_id=SECURITY_REVIEWER,
        reviewer_name=REVIEWER_NAME,
        status=SpecializedReviewerStatus.COMPLETED,
        summary=summary,
        findings=findings,
        referenced_finding_ids=referenced,
    )


def _scan_added_lines(
    context: ReviewerContext,
    patterns: tuple[tuple[str, str, Severity], ...],
    *,
    category: str,
) -> list[dict[str, object]]:
    hits: list[dict[str, object]] = []
    for changed_file in context.diff.files:
        if changed_file.is_binary or changed_file.is_deleted:
            continue
        for hunk in changed_file.hunks:
            line_number = _line_number_from_hunk_header(hunk.header)
            for raw_line in hunk.lines:
                if raw_line.startswith("+"):
                    content = raw_line[1:]
                    for pattern_id, expression, severity in patterns:
                        if re.search(expression, content):
                            snippet = content.strip()
                            if len(snippet) > 100:
                                snippet = snippet[:97].rstrip() + "..."
                            hits.append(
                                {
                                    "file": changed_file.path,
                                    "line": line_number,
                                    "pattern_id": pattern_id,
                                    "category": category,
                                    "severity": severity,
                                    "evidence": (
                                        f"{category} pattern '{pattern_id}' in {changed_file.path}:{line_number}: "
                                        f"{snippet}"
                                    ),
                                }
                            )
                    line_number += 1
                elif raw_line.startswith(" "):
                    line_number += 1
    return hits


def _line_number_from_hunk_header(header: str) -> int:
    match = re.search(r"\+(\d+)", header)
    if not match:
        return 1
    return int(match.group(1))


def _max_severity(severities) -> Severity:
    order = {
        Severity.BLOCKER: 5,
        Severity.HIGH: 4,
        Severity.MEDIUM: 3,
        Severity.LOW: 2,
        Severity.ADVISORY: 1,
    }
    return max(severities, key=lambda severity: order.get(severity, 0))