from __future__ import annotations

from pathlib import Path


class PathConfinementError(ValueError):
    pass


def resolve_confined_path(
    raw: str | Path,
    *,
    trusted_root: Path,
    base_dir: Path | None = None,
    allow_absolute: bool = False,
) -> Path:
    root = trusted_root.resolve()
    path = Path(raw)
    if path.is_absolute():
        if not allow_absolute:
            raise PathConfinementError(f"Absolute policy paths are not allowed: {path}")
        candidate = path.resolve()
    else:
        anchor = (base_dir or root).resolve()
        candidate = (anchor / path).resolve()
    _assert_within_root(candidate, root)
    return candidate


def assert_path_within_root(path: Path, trusted_root: Path) -> Path:
    candidate = path.resolve()
    _assert_within_root(candidate, trusted_root.resolve())
    return candidate


def _assert_within_root(candidate: Path, root: Path) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PathConfinementError(
            f"Path '{candidate}' escapes trusted root '{root}'."
        ) from exc