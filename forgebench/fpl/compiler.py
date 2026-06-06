from __future__ import annotations

from typing import Any

from forgebench.fpl.ast import FPLDocument


def compile_fpl_document(document: FPLDocument) -> dict[str, Any]:
    policy: dict[str, Any] = {}
    if document.categories:
        policy["path_categories"] = {
            category.name: {
                "patterns": list(category.patterns),
                **({"default_severity": category.default_severity} if category.default_severity else {}),
            }
            for category in document.categories
        }
    if document.advisory_only_paths:
        policy["advisory_only"] = list(document.advisory_only_paths)
    if document.suppress_rules:
        policy["suppress_findings"] = [
            {
                "finding_id": rule.finding_id,
                **({"paths": list(rule.paths)} if rule.paths else {}),
                **(
                    {"when_all_changed_files_match": list(rule.when_all_paths)}
                    if rule.when_all_paths
                    else {}
                ),
                **({"reason": rule.reason} if rule.reason else {}),
            }
            for rule in document.suppress_rules
        ]
    if document.ceiling_rules:
        policy["posture_overrides"] = {
            rule.name: {
                "posture_ceiling": rule.posture,
                **({"reason": rule.reason} if rule.reason else {}),
            }
            for rule in document.ceiling_rules
        }
    if document.override_rules:
        policy["finding_overrides"] = {
            rule.finding_id: {
                **({"severity": rule.severity} if rule.severity else {}),
                **({"confidence": rule.confidence} if rule.confidence else {}),
                **({"applies_to": list(rule.applies_to)} if rule.applies_to else {}),
                **({"reason": rule.reason} if rule.reason else {}),
            }
            for rule in document.override_rules
        }
    return {
        "fpl_version": document.version,
        "fpl_name": document.name,
        "policy": policy,
    }


def compile_fpl_text(text: str) -> dict[str, Any]:
    from forgebench.fpl.parser import parse_fpl

    return compile_fpl_document(parse_fpl(text))