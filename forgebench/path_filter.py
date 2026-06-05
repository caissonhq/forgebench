from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any

from forgebench.guardrails import matches_path_pattern
from forgebench.models import DiffSummary, Guardrails


MONOREPO_PACKAGE_MARKERS = ("package.json", "pyproject.toml", "cargo.toml", "go.mod", "pnpm-workspace.yaml")


def apply_review_scope(diff: DiffSummary, guardrails: Guardrails) -> tuple[DiffSummary, dict[str, Any]]:
    include_paths = list(guardrails.review_scope_include_paths)
    exclude_paths = list(guardrails.review_scope_exclude_paths)
    monorepo_packages = detect_monorepo_packages(diff.changed_files)

    if not include_paths and not exclude_paths:
        return diff, {
            "path_filter_active": False,
            "path_filter_included_count": len(diff.files),
            "path_filter_excluded_count": 0,
            "path_filter_excluded_paths": [],
            "monorepo_packages_detected": monorepo_packages,
            "monorepo_hint": _monorepo_hint(monorepo_packages),
        }

    kept: list = []
    excluded: list[str] = []
    for changed_file in diff.files:
        normalized = changed_file.path.replace("\\", "/")
        if include_paths and not _matches_any(normalized, include_paths):
            excluded.append(normalized)
            continue
        if exclude_paths and _matches_any(normalized, exclude_paths):
            excluded.append(normalized)
            continue
        kept.append(changed_file)

    filtered = DiffSummary(files=kept)
    return filtered, {
        "path_filter_active": True,
        "path_filter_include_paths": include_paths,
        "path_filter_exclude_paths": exclude_paths,
        "path_filter_included_count": len(kept),
        "path_filter_excluded_count": len(excluded),
        "path_filter_excluded_paths": sorted(set(excluded)),
        "monorepo_packages_detected": monorepo_packages,
        "monorepo_hint": _monorepo_hint(monorepo_packages),
    }


def detect_monorepo_packages(changed_files: list[str]) -> list[str]:
    packages: list[str] = []
    for path in changed_files:
        normalized = path.replace("\\", "/")
        basename = PurePosixPath(normalized).name.lower()
        if basename not in MONOREPO_PACKAGE_MARKERS:
            continue
        parent = str(PurePosixPath(normalized).parent)
        packages.append("." if parent == "." else parent)
    return sorted(set(packages))


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(matches_path_pattern(path, pattern) for pattern in patterns)


def _monorepo_hint(packages: list[str]) -> str | None:
    if len(packages) < 2:
        return None
    joined = ", ".join(packages[:6])
    suffix = f" and {len(packages) - 6} more" if len(packages) > 6 else ""
    return (
        f"Multiple package roots detected ({joined}{suffix}). "
        "Consider review_scope.include_paths in forgebench.yml to scope reviews to one workspace."
    )