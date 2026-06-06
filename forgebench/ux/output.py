from __future__ import annotations

import os
import sys
from typing import TextIO


def is_rich_output_enabled() -> bool:
    if os.environ.get("NO_COLOR", "").strip():
        return False
    if os.environ.get("FORGEBENCH_PLAIN_OUTPUT", "").strip().lower() in {"1", "true", "yes"}:
        return False
    return sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if not is_rich_output_enabled():
        return text
    return f"\033[{code}m{text}\033[0m"


def heading(text: str, *, stream: TextIO | None = None) -> None:
    out = stream or sys.stdout
    print(_c("1;36", text), file=out)


def success(text: str, *, stream: TextIO | None = None) -> None:
    out = stream or sys.stdout
    print(_c("1;32", f"✓ {text}"), file=out)


def warn(text: str, *, stream: TextIO | None = None) -> None:
    out = stream or sys.stdout
    print(_c("1;33", f"! {text}"), file=out)


def error(text: str, *, stream: TextIO | None = None) -> None:
    out = stream or sys.stderr
    print(_c("1;31", f"✗ {text}"), file=out)


def info(text: str, *, stream: TextIO | None = None) -> None:
    out = stream or sys.stdout
    print(_c("0;37", text), file=out)


def write_kv(label: str, value: str, *, stream: TextIO | None = None) -> None:
    out = stream or sys.stdout
    if is_rich_output_enabled():
        print(f"  {_c('1', label + ':')} {value}", file=out)
    else:
        print(f"  {label}: {value}", file=out)


def progress(message: str) -> None:
    info(f"… {message}")