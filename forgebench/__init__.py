"""ForgeBench: adversarial pre-merge QA for coding-agent output."""

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import re


def _version() -> str:
    source_pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if source_pyproject.exists():
        match = re.search(r'^version\s*=\s*"([^"]+)"', source_pyproject.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            return match.group(1)
    try:
        return version("forgebench")
    except PackageNotFoundError:
        return "0.7.0"


__version__ = _version()
