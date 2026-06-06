from __future__ import annotations

import ast
import re
from dataclasses import dataclass

from forgebench.semantic.models import SymbolChange


SUPPORTED_LANGUAGES = ("python", "typescript", "rust")


@dataclass(frozen=True)
class ParseResult:
    language: str
    parser: str
    symbols: list[SymbolChange]
    warnings: list[str]


def detect_language(file_path: str) -> str | None:
    normalized = file_path.replace("\\", "/").lower()
    if normalized.endswith(".py"):
        return "python"
    if normalized.endswith((".ts", ".tsx", ".mts", ".cts")):
        return "typescript"
    if normalized.endswith(".rs"):
        return "rust"
    return None


def extract_symbols_from_snippet(
    *,
    file_path: str,
    added_lines: list[str],
    deleted_lines: list[str] | None = None,
) -> ParseResult:
    language = detect_language(file_path)
    if language is None:
        return ParseResult(language="unknown", parser="none", symbols=[], warnings=[])

    snippet = "\n".join(line for line in added_lines if line.strip())
    if not snippet.strip():
        return ParseResult(language=language, parser="none", symbols=[], warnings=[])

    if language == "python":
        return _parse_python(file_path, snippet)
    if language == "typescript":
        tree_sitter = _try_tree_sitter_typescript(file_path, snippet)
        if tree_sitter is not None:
            return tree_sitter
        return _parse_regex_symbols(file_path, snippet, language, "regex-typescript")
    if language == "rust":
        tree_sitter = _try_tree_sitter_rust(file_path, snippet)
        if tree_sitter is not None:
            return tree_sitter
        return _parse_regex_symbols(file_path, snippet, language, "regex-rust")
    return ParseResult(language=language, parser="none", symbols=[], warnings=[])


def _parse_python(file_path: str, snippet: str) -> ParseResult:
    tree_sitter = _try_tree_sitter_python(file_path, snippet)
    if tree_sitter is not None:
        return tree_sitter

    warnings: list[str] = []
    symbols: list[SymbolChange] = []
    try:
        module = ast.parse(snippet)
    except SyntaxError as exc:
        warnings.append(f"Python AST parse failed for {file_path}: {exc.msg}")
        return _parse_regex_symbols(file_path, snippet, "python", "regex-python", warnings=warnings)

    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef):
            symbols.append(SymbolChange(name=node.name, kind="function", file_path=file_path, parser="stdlib-ast"))
        elif isinstance(node, ast.AsyncFunctionDef):
            symbols.append(SymbolChange(name=node.name, kind="async_function", file_path=file_path, parser="stdlib-ast"))
        elif isinstance(node, ast.ClassDef):
            symbols.append(SymbolChange(name=node.name, kind="class", file_path=file_path, parser="stdlib-ast"))
    return ParseResult(language="python", parser="stdlib-ast", symbols=_dedupe_symbols(symbols), warnings=warnings)


def _try_tree_sitter_python(file_path: str, snippet: str) -> ParseResult | None:
    try:
        import tree_sitter_python as tspython
        from tree_sitter import Language, Parser
    except ImportError:
        return None

    try:
        language = Language(tspython.language())
        parser = Parser(language)
        tree = parser.parse(snippet.encode("utf-8"))
    except Exception:
        return None

    symbols: list[SymbolChange] = []
    cursor = tree.walk()
    visited: set[int] = set()

    def visit() -> None:
        node = cursor.node
        if node is None:
            return
        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)
        if node.type == "function_definition":
            name = _tree_sitter_child_identifier(node)
            if name:
                symbols.append(SymbolChange(name=name, kind="function", file_path=file_path, parser="tree-sitter-python"))
        elif node.type == "class_definition":
            name = _tree_sitter_child_identifier(node)
            if name:
                symbols.append(SymbolChange(name=name, kind="class", file_path=file_path, parser="tree-sitter-python"))
        if cursor.goto_first_child():
            while True:
                visit()
                if not cursor.goto_next_sibling():
                    break
            cursor.goto_parent()

    visit()
    if not symbols:
        return None
    return ParseResult(language="python", parser="tree-sitter-python", symbols=_dedupe_symbols(symbols), warnings=[])


def _try_tree_sitter_typescript(file_path: str, snippet: str) -> ParseResult | None:
    try:
        import tree_sitter_typescript as tstypescript
        from tree_sitter import Language, Parser
    except ImportError:
        return None

    try:
        language = Language(tstypescript.language_typescript())
        parser = Parser(language)
        tree = parser.parse(snippet.encode("utf-8"))
    except Exception:
        return None

    symbols: list[SymbolChange] = []
    cursor = tree.walk()
    visited: set[int] = set()

    def visit() -> None:
        node = cursor.node
        if node is None:
            return
        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)
        if node.type in {"function_declaration", "method_definition", "arrow_function"}:
            name = _tree_sitter_child_identifier(node)
            if name:
                symbols.append(
                    SymbolChange(name=name, kind="function", file_path=file_path, parser="tree-sitter-typescript")
                )
        elif node.type == "class_declaration":
            name = _tree_sitter_child_identifier(node)
            if name:
                symbols.append(SymbolChange(name=name, kind="class", file_path=file_path, parser="tree-sitter-typescript"))
        if cursor.goto_first_child():
            while True:
                visit()
                if not cursor.goto_next_sibling():
                    break
            cursor.goto_parent()

    visit()
    if not symbols:
        return None
    return ParseResult(language="typescript", parser="tree-sitter-typescript", symbols=_dedupe_symbols(symbols), warnings=[])


def _try_tree_sitter_rust(file_path: str, snippet: str) -> ParseResult | None:
    try:
        import tree_sitter_rust as tsrust
        from tree_sitter import Language, Parser
    except ImportError:
        return None

    try:
        language = Language(tsrust.language())
        parser = Parser(language)
        tree = parser.parse(snippet.encode("utf-8"))
    except Exception:
        return None

    symbols: list[SymbolChange] = []
    cursor = tree.walk()
    visited: set[int] = set()

    def visit() -> None:
        node = cursor.node
        if node is None:
            return
        node_id = id(node)
        if node_id in visited:
            return
        visited.add(node_id)
        if node.type == "function_item":
            name = _tree_sitter_child_identifier(node)
            if name:
                symbols.append(SymbolChange(name=name, kind="function", file_path=file_path, parser="tree-sitter-rust"))
        elif node.type in {"struct_item", "enum_item", "trait_item", "impl_item"}:
            name = _tree_sitter_child_identifier(node)
            if name:
                symbols.append(SymbolChange(name=name, kind=node.type.replace("_item", ""), file_path=file_path, parser="tree-sitter-rust"))
        if cursor.goto_first_child():
            while True:
                visit()
                if not cursor.goto_next_sibling():
                    break
            cursor.goto_parent()

    visit()
    if not symbols:
        return None
    return ParseResult(language="rust", parser="tree-sitter-rust", symbols=_dedupe_symbols(symbols), warnings=[])


def _tree_sitter_child_identifier(node) -> str | None:
    for child in node.children:
        if child.type in {"identifier", "type_identifier", "property_identifier"}:
            return child.text.decode("utf-8", errors="replace")
        if child.type == "name":
            return child.text.decode("utf-8", errors="replace")
    return None


def _parse_regex_symbols(
    file_path: str,
    snippet: str,
    language: str,
    parser: str,
    *,
    warnings: list[str] | None = None,
) -> ParseResult:
    patterns = {
        "python": [
            (r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", "function"),
            (r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*[\(:]", "class"),
        ],
        "typescript": [
            (r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", "function"),
            (r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)\s*", "class"),
            (r"^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(", "function"),
        ],
        "rust": [
            (r"^\s*(?:pub\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", "function"),
            (r"^\s*(?:pub\s+)?struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*", "struct"),
            (r"^\s*(?:pub\s+)?enum\s+([A-Za-z_][A-Za-z0-9_]*)\s*", "enum"),
            (r"^\s*(?:pub\s+)?trait\s+([A-Za-z_][A-Za-z0-9_]*)\s*", "trait"),
        ],
    }
    symbols: list[SymbolChange] = []
    for line in snippet.splitlines():
        for pattern, kind in patterns.get(language, []):
            match = re.match(pattern, line)
            if match:
                symbols.append(SymbolChange(name=match.group(1), kind=kind, file_path=file_path, parser=parser))
    return ParseResult(
        language=language,
        parser=parser,
        symbols=_dedupe_symbols(symbols),
        warnings=list(warnings or []),
    )


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