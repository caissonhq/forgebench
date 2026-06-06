from __future__ import annotations

from dataclasses import dataclass, field


FPL_SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class FPLDocument:
    version: str = "1.0.0"
    name: str = ""
    categories: list["CategoryDecl"] = field(default_factory=list)
    suppress_rules: list["SuppressDecl"] = field(default_factory=list)
    ceiling_rules: list["CeilingDecl"] = field(default_factory=list)
    override_rules: list["OverrideDecl"] = field(default_factory=list)
    advisory_only_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CategoryDecl:
    name: str
    patterns: list[str]
    default_severity: str | None = None


@dataclass(frozen=True)
class SuppressDecl:
    finding_id: str
    paths: list[str] = field(default_factory=list)
    when_all_paths: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass(frozen=True)
class CeilingDecl:
    name: str
    posture: str
    reason: str = ""


@dataclass(frozen=True)
class OverrideDecl:
    finding_id: str
    severity: str | None = None
    confidence: str | None = None
    applies_to: list[str] = field(default_factory=list)
    reason: str = ""