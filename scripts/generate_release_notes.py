#!/usr/bin/env python3
"""Generate GitHub Release notes from CHANGELOG.md Unreleased section."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def extract_unreleased(changelog_text: str) -> str:
    match = re.search(r"## Unreleased\n(.*?)(?:\n## |\Z)", changelog_text, re.DOTALL)
    if not match:
        return "See CHANGELOG.md for details."
    body = match.group(1).strip()
    lines = [line for line in body.splitlines() if line.strip()]
    return "\n".join(lines)


def main() -> int:
    changelog = Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    version = sys.argv[1] if len(sys.argv) > 1 else "unreleased"
    notes = extract_unreleased(changelog.read_text(encoding="utf-8"))
    print(f"# ForgeBench {version}\n\n{notes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())