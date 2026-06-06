from __future__ import annotations

import re
import shlex
from dataclasses import replace

from forgebench.fpl.ast import (
    CategoryDecl,
    CeilingDecl,
    FPLDocument,
    OverrideDecl,
    SuppressDecl,
)


class FPLParseError(ValueError):
    pass


MAX_FPL_LINES = 10_000
MAX_FPL_BYTES = 512 * 1024


_DIRECTIVE_RE = re.compile(
    r"^(?P<cmd>version|name|category|suppress|ceiling|override|advisory_only)\b(?P<rest>.*)$",
    re.IGNORECASE,
)


def parse_fpl(text: str) -> FPLDocument:
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_FPL_BYTES:
        raise FPLParseError(f"FPL source exceeds {MAX_FPL_BYTES} bytes.")
    lines = text.splitlines()
    if len(lines) > MAX_FPL_LINES:
        raise FPLParseError(f"FPL source exceeds {MAX_FPL_LINES} lines.")
    document = FPLDocument()
    categories: list[CategoryDecl] = []
    suppress_rules: list[SuppressDecl] = []
    ceiling_rules: list[CeilingDecl] = []
    override_rules: list[OverrideDecl] = []
    advisory_only_paths: list[str] = []

    for line_number, raw_line in enumerate(lines, start=1):
        line = _strip_comment(raw_line).strip()
        if not line:
            continue
        match = _DIRECTIVE_RE.match(line)
        if not match:
            raise FPLParseError(f"FPL line {line_number}: unrecognized directive: {line}")
        cmd = match.group("cmd").lower()
        rest = match.group("rest").strip()
        try:
            if cmd == "version":
                document = replace(document, version=_parse_scalar(rest, line_number))
            elif cmd == "name":
                document = replace(document, name=_parse_scalar(rest, line_number))
            elif cmd == "category":
                categories.append(_parse_category(rest, line_number))
            elif cmd == "suppress":
                suppress_rules.append(_parse_suppress(rest, line_number))
            elif cmd == "ceiling":
                ceiling_rules.append(_parse_ceiling(rest, line_number))
            elif cmd == "override":
                override_rules.append(_parse_override(rest, line_number))
            elif cmd == "advisory_only":
                advisory_only_paths.extend(_parse_path_list(rest, line_number))
            else:
                raise FPLParseError(f"FPL line {line_number}: unsupported directive {cmd}")
        except FPLParseError:
            raise
        except ValueError as exc:
            raise FPLParseError(f"FPL line {line_number}: {exc}") from exc

    return replace(
        document,
        categories=categories,
        suppress_rules=suppress_rules,
        ceiling_rules=ceiling_rules,
        override_rules=override_rules,
        advisory_only_paths=advisory_only_paths,
    )


def _strip_comment(line: str) -> str:
    if "#" not in line:
        return line
    in_quote = False
    for index, char in enumerate(line):
        if char == '"':
            in_quote = not in_quote
        elif char == "#" and not in_quote:
            return line[:index]
    return line


def _parse_scalar(value: str, line_number: int) -> str:
    text = value.strip()
    if not text:
        raise FPLParseError(f"FPL line {line_number}: expected value after directive")
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    return text


def _tokenize(rest: str) -> list[str]:
    return shlex.split(rest, comments=False, posix=True)


def _parse_path_list(rest: str, line_number: int) -> list[str]:
    tokens = _tokenize(rest)
    if not tokens:
        raise FPLParseError(f"FPL line {line_number}: expected one or more path globs")
    return tokens


def _parse_category(rest: str, line_number: int) -> CategoryDecl:
    tokens = _tokenize(rest)
    if len(tokens) < 3 or tokens[1].lower() != "paths":
        raise FPLParseError(f"FPL line {line_number}: category syntax is category <name> paths <globs...> [severity <level>]")
    name = tokens[0]
    patterns: list[str] = []
    default_severity: str | None = None
    index = 2
    while index < len(tokens) and tokens[index].lower() != "severity":
        patterns.append(tokens[index])
        index += 1
    if index < len(tokens) and tokens[index].lower() == "severity":
        if index + 1 >= len(tokens):
            raise FPLParseError(f"FPL line {line_number}: severity requires a value")
        default_severity = tokens[index + 1]
    if not patterns:
        raise FPLParseError(f"FPL line {line_number}: category requires at least one path glob")
    return CategoryDecl(name=name, patterns=patterns, default_severity=default_severity)


def _parse_suppress(rest: str, line_number: int) -> SuppressDecl:
    tokens = _tokenize(rest)
    if len(tokens) < 2:
        raise FPLParseError(f"FPL line {line_number}: suppress requires finding_id and path selector")
    finding_id = tokens[0]
    paths: list[str] = []
    when_all_paths: list[str] = []
    reason = ""
    index = 1
    while index < len(tokens):
        token = tokens[index].lower()
        if token == "paths":
            index += 1
            while index < len(tokens) and tokens[index].lower() not in {"when_all", "reason"}:
                paths.append(tokens[index])
                index += 1
            continue
        if token == "when_all":
            index += 1
            while index < len(tokens) and tokens[index].lower() != "reason":
                when_all_paths.append(tokens[index])
                index += 1
            continue
        if token == "reason":
            reason = " ".join(tokens[index + 1 :])
            break
        raise FPLParseError(f"FPL line {line_number}: unknown suppress clause '{tokens[index]}'")
    if not paths and not when_all_paths:
        raise FPLParseError(f"FPL line {line_number}: suppress requires paths or when_all")
    return SuppressDecl(finding_id=finding_id, paths=paths, when_all_paths=when_all_paths, reason=reason)


def _parse_ceiling(rest: str, line_number: int) -> CeilingDecl:
    tokens = _tokenize(rest)
    if len(tokens) < 4 or tokens[1].lower() != "posture":
        raise FPLParseError(f"FPL line {line_number}: ceiling syntax is ceiling <name> posture <BLOCK|REVIEW|LOW_CONCERN> [reason \"...\"]")
    reason = ""
    if "reason" in (item.lower() for item in tokens):
        reason_index = next(index for index, item in enumerate(tokens) if item.lower() == "reason")
        reason = " ".join(tokens[reason_index + 1 :])
    return CeilingDecl(name=tokens[0], posture=tokens[2].upper(), reason=reason)


def _parse_override(rest: str, line_number: int) -> OverrideDecl:
    tokens = _tokenize(rest)
    if len(tokens) < 2:
        raise FPLParseError(f"FPL line {line_number}: override requires finding_id and clauses")
    finding_id = tokens[0]
    severity: str | None = None
    confidence: str | None = None
    applies_to: list[str] = []
    reason = ""
    index = 1
    while index < len(tokens):
        token = tokens[index].lower()
        if token == "severity":
            severity = tokens[index + 1]
            index += 2
            continue
        if token == "confidence":
            confidence = tokens[index + 1]
            index += 2
            continue
        if token == "applies":
            index += 1
            while index < len(tokens) and tokens[index].lower() != "reason":
                applies_to.append(tokens[index])
                index += 1
            continue
        if token == "reason":
            reason = " ".join(tokens[index + 1 :])
            break
        raise FPLParseError(f"FPL line {line_number}: unknown override clause '{tokens[index]}'")
    return OverrideDecl(
        finding_id=finding_id,
        severity=severity,
        confidence=confidence,
        applies_to=applies_to,
        reason=reason,
    )