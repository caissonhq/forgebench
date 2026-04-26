from __future__ import annotations

import re
import shlex
from pathlib import Path

from forgebench.models import ChangedFile, ChangedHunk, DiffSummary


TEST_FILE_PATTERNS = (
    "__tests__",
    ".test.",
    ".spec.",
    "test.swift",
    "tests.swift",
)


def parse_diff_file(path: str | Path) -> DiffSummary:
    diff_path = Path(path)
    return parse_unified_diff(diff_path.read_text(encoding="utf-8", errors="replace"))


def parse_unified_diff(text: str) -> DiffSummary:
    files: list[ChangedFile] = []
    current: ChangedFile | None = None
    current_hunk: ChangedHunk | None = None

    for line in text.splitlines():
        if line.startswith("diff --git "):
            current = _changed_file_from_diff_header(line)
            current.is_test = is_test_file(current.path)
            files.append(current)
            current_hunk = None
            continue

        if current is None:
            continue

        if line.startswith("new file mode"):
            current.is_added = True
            continue

        if line.startswith("deleted file mode"):
            current.is_deleted = True
            continue

        if line.startswith("Binary files ") or line == "GIT binary patch":
            current.is_binary = True
            continue

        if line.startswith("rename from "):
            current.old_path = _strip_git_prefix(line.removeprefix("rename from ").strip())
            current.is_renamed = True
            continue

        if line.startswith("rename to "):
            current.path = _strip_git_prefix(line.removeprefix("rename to ").strip())
            current.is_renamed = True
            current.is_test = is_test_file(current.path)
            continue

        if line.startswith("--- "):
            old_path = line.removeprefix("--- ").strip()
            if old_path == "/dev/null":
                current.is_added = True
            else:
                current.old_path = _strip_git_prefix(old_path)
            continue

        if line.startswith("+++ "):
            new_path = line.removeprefix("+++ ").strip()
            if new_path == "/dev/null":
                current.is_deleted = True
            else:
                current.path = _strip_git_prefix(new_path)
                current.is_test = is_test_file(current.path)
            continue

        if line.startswith("@@"):
            current_hunk = ChangedHunk(header=line)
            current.hunks.append(current_hunk)
            continue

        if line.startswith("+"):
            added = line[1:]
            current.added_line_count += 1
            current.added_lines.append(added)
            if current_hunk is not None:
                current_hunk.lines.append(line)
                current_hunk.added_lines.append(added)
            continue

        if line.startswith("-"):
            deleted = line[1:]
            current.deleted_line_count += 1
            current.deleted_lines.append(deleted)
            if current_hunk is not None:
                current_hunk.lines.append(line)
                current_hunk.deleted_lines.append(deleted)
            continue

        if current_hunk is not None and (line.startswith(" ") or line.startswith("\\")):
            current_hunk.lines.append(line)
            continue

    return DiffSummary(files=files)


def is_test_file(path: str) -> bool:
    normalized = path.replace("\\", "/")
    lower = normalized.lower()
    basename = lower.rsplit("/", 1)[-1]
    surrounded = f"/{lower}/"

    if any(pattern in lower for pattern in TEST_FILE_PATTERNS):
        return True
    if "/tests/" in surrounded or "/test/" in surrounded or "/spec/" in surrounded:
        return True
    if basename.startswith("test_") or basename.endswith("_test.py"):
        return True
    if re.search(r"(^|[._/-])(test|tests|spec)([._/-]|$)", lower):
        return True
    return False


def _changed_file_from_diff_header(line: str) -> ChangedFile:
    old_raw, new_raw = _split_diff_header_paths(line.removeprefix("diff --git ").strip())
    old_path = _strip_git_prefix(old_raw)
    new_path = _strip_git_prefix(new_raw or old_raw)
    return ChangedFile(path=new_path, old_path=old_path)


def _split_diff_header_paths(header: str) -> tuple[str, str]:
    try:
        quoted_parts = shlex.split(header)
    except ValueError:
        quoted_parts = []
    if len(quoted_parts) == 2:
        return quoted_parts[0], quoted_parts[1]

    if header.startswith("a/"):
        separator = header.find(" b/", 2)
        if separator != -1:
            return header[:separator], header[separator + 1 :]

    parts = header.split(maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1]
    if len(parts) == 1:
        return parts[0], parts[0]
    return "", ""


def _strip_git_prefix(path: str) -> str:
    cleaned = path.strip().strip('"')
    if cleaned.startswith("a/") or cleaned.startswith("b/"):
        return cleaned[2:]
    return cleaned
