from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SymbolChange:
    name: str
    kind: str
    file_path: str
    parser: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "file_path": self.file_path,
            "parser": self.parser,
        }


@dataclass(frozen=True)
class CrossFileEdge:
    source_file: str
    target_file: str
    symbol: str
    edge_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "target_file": self.target_file,
            "symbol": self.symbol,
            "edge_type": self.edge_type,
        }


@dataclass(frozen=True)
class BehavioralDiffSummary:
    enabled: bool
    parsers_used: list[str] = field(default_factory=list)
    changed_symbols: list[SymbolChange] = field(default_factory=list)
    cross_file_edges: list[CrossFileEdge] = field(default_factory=list)
    symbols_without_test_reference: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "parsers_used": list(self.parsers_used),
            "changed_symbols": [symbol.to_dict() for symbol in self.changed_symbols],
            "cross_file_edges": [edge.to_dict() for edge in self.cross_file_edges],
            "symbols_without_test_reference": list(self.symbols_without_test_reference),
            "warnings": list(self.warnings),
        }