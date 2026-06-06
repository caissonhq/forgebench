from __future__ import annotations

import shlex
import subprocess
from typing import Sequence


class CommandParseError(ValueError):
    pass


def run_shell_free_command(
    command: str,
    *,
    input_text: str,
    timeout_seconds: int,
    cwd: str | None = None,
) -> subprocess.CompletedProcess[str]:
    argv = parse_command_argv(command)
    return subprocess.run(
        argv,
        cwd=cwd,
        shell=False,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )


def parse_command_argv(command: str) -> list[str]:
    text = (command or "").strip()
    if not text:
        raise CommandParseError("Command is empty.")
    try:
        argv: Sequence[str] = shlex.split(text, posix=True)
    except ValueError as exc:
        raise CommandParseError(f"Invalid command syntax: {exc}") from exc
    if not argv:
        raise CommandParseError("Command is empty.")
    return list(argv)