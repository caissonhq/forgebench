from __future__ import annotations

from pathlib import Path
from typing import Any

from forgebench.fpl.compiler import compile_fpl_document, compile_fpl_text
from forgebench.fpl.parser import FPLParseError, parse_fpl
from forgebench.policy_layers import _merge_payload_dicts


FPL_FILE_KEYS = ("fpl", "policy_fpl")


class FPLLoadError(ValueError):
    pass


def compile_fpl_file(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        raise FPLLoadError(f"FPL file not found: {file_path}")
    return compile_fpl_text(file_path.read_text(encoding="utf-8", errors="replace"))


def merge_fpl_into_payload(payload: dict[str, Any], base_dir: Path) -> dict[str, Any]:
    merged = dict(payload)
    for key in FPL_FILE_KEYS:
        reference = payload.get(key)
        if not isinstance(reference, str) or not reference.strip():
            continue
        fpl_path = _resolve_relative_path(Path(reference.strip()), base_dir)
        compiled = compile_fpl_file(fpl_path)
        merged = _merge_payload_dicts(merged, {"policy": compiled.get("policy") or {}})
        merged["fpl_compiled_from"] = str(fpl_path)
        merged["fpl_version"] = compiled.get("fpl_version")
        merged["fpl_name"] = compiled.get("fpl_name")
    return merged


def fpl_document_from_text(text: str):
    return parse_fpl(text)


def _resolve_relative_path(path: Path, base_dir: Path) -> Path:
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()