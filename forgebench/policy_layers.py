from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from forgebench.guardrails import Guardrails, GuardrailsParseError, guardrails_from_payload
from forgebench.security.path_confinement import PathConfinementError, resolve_confined_path


LAYER_DIRECTIVE_KEYS = {"extends", "include"}
MAX_LAYER_DEPTH = 8
ORG_POLICY_ENV = "FORGEBENCH_ORG_POLICY"


def resolve_guardrails_path(repo: Path, guardrails_path: str | Path | None) -> Path | None:
    repo = Path(repo)
    if guardrails_path:
        path = Path(guardrails_path)
        if path.is_absolute():
            return path if path.exists() else path
        for base in (repo, Path.cwd()):
            candidate = base / path
            if candidate.exists():
                return candidate
        return repo / path
    candidate = repo / "forgebench.yml"
    return candidate if candidate.exists() else None


def load_layered_guardrails(path: str | Path | None) -> Guardrails:
    if path is None:
        return Guardrails()
    resolved = Path(path).resolve()
    trusted_root = _policy_trusted_root(resolved)
    merged_payload, sources = _load_merged_payload(resolved, trusted_root=trusted_root)
    guardrails = guardrails_from_payload(merged_payload)
    org_path = _resolve_org_policy_path(resolved)
    if org_path is not None and org_path.resolve() != resolved.resolve():
        org_root = org_path.parent.resolve()
        org_payload, org_sources = _load_merged_payload(org_path, trusted_root=org_root)
        guardrails = _merge_guardrails(guardrails_from_payload(org_payload), guardrails)
        sources = [*org_sources, *sources]
    return _with_sources(guardrails, sources)


def _load_merged_payload(
    path: Path,
    *,
    trusted_root: Path,
    _depth: int = 0,
    _seen: set[Path] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    if _depth > MAX_LAYER_DEPTH:
        raise GuardrailsParseError(f"forgebench.yml layer depth exceeded {MAX_LAYER_DEPTH} layers at {path}")
    seen = _seen or set()
    resolved = path.resolve()
    if resolved in seen:
        raise GuardrailsParseError(f"forgebench.yml layer cycle detected at {path}")
    seen.add(resolved)

    if not resolved.exists() or not resolved.is_file():
        raise GuardrailsParseError(f"guardrails file does not exist: {path}")

    raw_payload = _parse_file_payload(resolved)
    current = _payload_without_directives(raw_payload)
    current_dir = resolved.parent.resolve()
    current = _merge_fpl_payload(current, trusted_root, current_dir)
    sources = [_portable_source_path(resolved)]
    base_paths = _layer_paths(raw_payload, trusted_root, current_dir)
    merged: dict[str, Any] = {}
    for base_path in base_paths:
        base_payload, base_sources = _load_merged_payload(
            base_path,
            trusted_root=trusted_root,
            _depth=_depth + 1,
            _seen=seen,
        )
        merged = _merge_payload_dicts(merged, base_payload)
        sources.extend(base_sources)
    merged = _merge_payload_dicts(merged, current)
    return merged, sources


def _merge_fpl_payload(payload: dict[str, Any], trusted_root: Path, current_dir: Path) -> dict[str, Any]:
    try:
        from forgebench.fpl.loader import merge_fpl_into_payload

        return merge_fpl_into_payload(payload, trusted_root, current_dir)
    except PathConfinementError as exc:
        raise GuardrailsParseError(str(exc)) from exc
    except Exception as exc:
        raise GuardrailsParseError(str(exc)) from exc


def _parse_file_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return _parse_yaml_mapping(text)


def _parse_yaml_mapping(text: str) -> dict[str, Any]:
    import yaml

    loaded = yaml.safe_load(text) or {}
    if not isinstance(loaded, dict):
        raise GuardrailsParseError("forgebench.yml must be a mapping at the top level.")
    return {str(key): value for key, value in loaded.items()}


def _payload_without_directives(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in LAYER_DIRECTIVE_KEYS}


def _layer_paths(payload: dict[str, Any], trusted_root: Path, current_dir: Path) -> list[Path]:
    paths: list[Path] = []
    extends = payload.get("extends")
    if isinstance(extends, str) and extends.strip():
        paths.append(_resolve_relative_path(Path(extends.strip()), trusted_root, current_dir))
    include = payload.get("include")
    if isinstance(include, list):
        for item in include:
            if isinstance(item, str) and item.strip():
                paths.append(_resolve_relative_path(Path(item.strip()), trusted_root, current_dir))
    elif isinstance(include, str) and include.strip():
        paths.append(_resolve_relative_path(Path(include.strip()), trusted_root, current_dir))
    return paths


def _merge_payload_dicts(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if key in LAYER_DIRECTIVE_KEYS:
            continue
        if key not in merged:
            merged[key] = value
            continue
        existing = merged[key]
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _merge_payload_dicts(existing, value)
        elif isinstance(existing, list) and isinstance(value, list):
            merged[key] = _merge_lists(existing, value)
        else:
            merged[key] = value
    return merged


def _merge_lists(base: list[Any], overlay: list[Any]) -> list[Any]:
    merged: list[Any] = []
    seen: set[str] = set()
    for item in [*base, *overlay]:
        marker = repr(item)
        if marker in seen:
            continue
        seen.add(marker)
        merged.append(item)
    return merged


def _merge_guardrails(base: Guardrails, overlay: Guardrails) -> Guardrails:
    return Guardrails(
        project=overlay.project or base.project,
        protected_behavior=_merge_lists(base.protected_behavior, overlay.protected_behavior),
        risk_files_high=_merge_lists(base.risk_files_high, overlay.risk_files_high),
        risk_files_medium=_merge_lists(base.risk_files_medium, overlay.risk_files_medium),
        forbidden_patterns=_merge_lists(base.forbidden_patterns, overlay.forbidden_patterns),
        review_scope_include_paths=_merge_lists(base.review_scope_include_paths, overlay.review_scope_include_paths),
        review_scope_exclude_paths=_merge_lists(base.review_scope_exclude_paths, overlay.review_scope_exclude_paths),
        checks={**base.checks, **overlay.checks},
        custom_checks={**base.custom_checks, **overlay.custom_checks},
        checks_present=base.checks_present or overlay.checks_present,
        check_timeout_seconds=overlay.check_timeout_seconds if overlay.check_timeout_seconds != 120 else base.check_timeout_seconds,
        policy=_merge_policy(base.policy, overlay.policy),
        warnings=_merge_lists(base.warnings, overlay.warnings),
        sources=_merge_lists(base.sources, overlay.sources),
        team=overlay.team or base.team,
        policy_version=overlay.policy_version or base.policy_version,
        fpl_version=overlay.fpl_version or base.fpl_version,
        fpl_name=overlay.fpl_name or base.fpl_name,
        fpl_compiled_from=overlay.fpl_compiled_from or base.fpl_compiled_from,
    )


def _merge_policy(base, overlay):
    from forgebench.models import GuardrailsPolicy

    return GuardrailsPolicy(
        finding_overrides={**base.finding_overrides, **overlay.finding_overrides},
        path_categories={**base.path_categories, **overlay.path_categories},
        advisory_only=_merge_lists(base.advisory_only, overlay.advisory_only),
        suppress_findings=_merge_lists(base.suppress_findings, overlay.suppress_findings),
        posture_overrides={**base.posture_overrides, **overlay.posture_overrides},
    )


def _with_sources(guardrails: Guardrails, sources: list[str]) -> Guardrails:
    unique_sources = list(dict.fromkeys(sources))
    if guardrails.sources == unique_sources:
        return guardrails
    return Guardrails(
        project=guardrails.project,
        protected_behavior=guardrails.protected_behavior,
        risk_files_high=guardrails.risk_files_high,
        risk_files_medium=guardrails.risk_files_medium,
        forbidden_patterns=guardrails.forbidden_patterns,
        review_scope_include_paths=guardrails.review_scope_include_paths,
        review_scope_exclude_paths=guardrails.review_scope_exclude_paths,
        checks=guardrails.checks,
        custom_checks=guardrails.custom_checks,
        checks_present=guardrails.checks_present,
        check_timeout_seconds=guardrails.check_timeout_seconds,
        policy=guardrails.policy,
        warnings=guardrails.warnings,
        sources=unique_sources,
        team=guardrails.team,
        policy_version=guardrails.policy_version,
        fpl_version=guardrails.fpl_version,
        fpl_name=guardrails.fpl_name,
        fpl_compiled_from=guardrails.fpl_compiled_from,
    )


def _resolve_org_policy_path(current: Path) -> Path | None:
    raw = os.environ.get(ORG_POLICY_ENV, "").strip()
    if not raw:
        return None
    org_root = _policy_trusted_root(current)
    candidate = _resolve_relative_path(Path(raw), org_root, current.parent, allow_absolute=True)
    return candidate if candidate.exists() else None


def _policy_trusted_root(entry: Path) -> Path:
    start = entry.resolve().parent
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    return start


def _resolve_relative_path(
    path: Path,
    trusted_root: Path,
    current_dir: Path,
    *,
    allow_absolute: bool = False,
) -> Path:
    try:
        return resolve_confined_path(
            path,
            trusted_root=trusted_root,
            base_dir=current_dir,
            allow_absolute=allow_absolute,
        )
    except PathConfinementError as exc:
        raise GuardrailsParseError(str(exc)) from exc


def _portable_source_path(path: Path) -> str:
    candidate = path.resolve()
    for base in (Path.cwd(), Path.cwd().resolve()):
        try:
            return str(candidate.relative_to(base.resolve()))
        except ValueError:
            continue
    return str(path)


def _merge_lists_str(base: list[str], overlay: list[str]) -> list[str]:
    return [str(item) for item in _merge_lists(base, overlay)]