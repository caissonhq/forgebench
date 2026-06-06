from __future__ import annotations

from forgebench.diff_parser import DiffSummary
from forgebench.semantic.ast_parser import detect_language, extract_symbols_from_snippet
from forgebench.semantic.models import BehavioralDiffSummary, CrossFileEdge, SymbolChange


def analyze_behavioral_diff(diff: DiffSummary) -> BehavioralDiffSummary:
    parsers_used: set[str] = set()
    warnings: list[str] = []
    changed_symbols: list[SymbolChange] = []

    source_files: list[str] = []
    test_files: list[str] = []
    for changed_file in diff.files:
        if changed_file.is_test:
            test_files.append(changed_file.path)
            continue
        if detect_language(changed_file.path) is not None:
            source_files.append(changed_file.path)

    for changed_file in diff.files:
        if changed_file.path not in source_files:
            continue
        result = extract_symbols_from_snippet(
            file_path=changed_file.path,
            added_lines=changed_file.added_lines,
            deleted_lines=changed_file.deleted_lines,
        )
        if result.parser != "none":
            parsers_used.add(result.parser)
        warnings.extend(result.warnings)
        changed_symbols.extend(result.symbols)

    symbol_names = sorted({symbol.name for symbol in changed_symbols})
    cross_file_edges = _build_cross_file_edges(changed_symbols, test_files, diff)
    symbols_without_test_reference = _symbols_without_test_reference(symbol_names, test_files, diff)

    return BehavioralDiffSummary(
        enabled=bool(changed_symbols or source_files),
        parsers_used=sorted(parsers_used),
        changed_symbols=_dedupe_symbols(changed_symbols),
        cross_file_edges=cross_file_edges,
        symbols_without_test_reference=symbols_without_test_reference,
        warnings=warnings,
    )


def behavioral_signals(summary: BehavioralDiffSummary) -> dict[str, object]:
    return {
        "semantic_analysis_enabled": summary.enabled,
        "semantic_parsers_used": list(summary.parsers_used),
        "changed_symbols": [symbol.to_dict() for symbol in summary.changed_symbols],
        "cross_file_behavior_edges": [edge.to_dict() for edge in summary.cross_file_edges],
        "symbols_without_test_reference": list(summary.symbols_without_test_reference),
        "semantic_warnings": list(summary.warnings),
    }


def _build_cross_file_edges(
    changed_symbols: list[SymbolChange],
    test_files: list[str],
    diff: DiffSummary,
) -> list[CrossFileEdge]:
    edges: list[CrossFileEdge] = []
    if not changed_symbols or not test_files:
        return edges

    test_text_by_file = {
        changed_file.path: "\n".join(changed_file.added_lines)
        for changed_file in diff.files
        if changed_file.path in test_files
    }

    for symbol in changed_symbols:
        for test_file, text in test_text_by_file.items():
            if symbol.name in text:
                edges.append(
                    CrossFileEdge(
                        source_file=symbol.file_path,
                        target_file=test_file,
                        symbol=symbol.name,
                        edge_type="test_reference",
                    )
                )
    return edges


def _symbols_without_test_reference(
    symbol_names: list[str],
    test_files: list[str],
    diff: DiffSummary,
) -> list[str]:
    if not symbol_names:
        return []
    if not test_files:
        return list(symbol_names)

    referenced: set[str] = set()
    for changed_file in diff.files:
        if changed_file.path not in test_files:
            continue
        text = "\n".join(changed_file.added_lines + changed_file.deleted_lines)
        for symbol in symbol_names:
            if symbol in text:
                referenced.add(symbol)
    return sorted(name for name in symbol_names if name not in referenced)


def _dedupe_symbols(symbols: list[SymbolChange]) -> list[SymbolChange]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[SymbolChange] = []
    for symbol in symbols:
        key = (symbol.file_path, symbol.name, symbol.kind)
        if key in seen:
            continue
        seen.add(key)
        unique.append(symbol)
    return unique