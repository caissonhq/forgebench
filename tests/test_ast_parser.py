from __future__ import annotations

import unittest

from forgebench.semantic.ast_parser import detect_language, extract_symbols_from_snippet


class ASTParserTests(unittest.TestCase):
    def test_detect_language_for_supported_files(self) -> None:
        self.assertEqual(detect_language("src/app.py"), "python")
        self.assertEqual(detect_language("src/app.ts"), "typescript")
        self.assertEqual(detect_language("src/lib.rs"), "rust")

    def test_python_stdlib_ast_extracts_function_and_class(self) -> None:
        result = extract_symbols_from_snippet(
            file_path="payments/service.py",
            added_lines=[
                "class ReceiptService:",
                "    def capture(self, amount: int) -> int:",
                "        return amount",
            ],
        )
        names = {symbol.name for symbol in result.symbols}
        self.assertIn("ReceiptService", names)
        self.assertIn("capture", names)
        self.assertEqual(result.language, "python")
        self.assertIn(result.parser, {"stdlib-ast", "tree-sitter-python"})

    def test_typescript_regex_fallback_extracts_symbol(self) -> None:
        result = extract_symbols_from_snippet(
            file_path="src/payments.ts",
            added_lines=[
                "export function capturePayment(amount: number) {",
                "  return amount;",
                "}",
            ],
        )
        self.assertEqual([symbol.name for symbol in result.symbols], ["capturePayment"])

    def test_rust_regex_fallback_extracts_symbol(self) -> None:
        result = extract_symbols_from_snippet(
            file_path="src/payments.rs",
            added_lines=[
                "pub fn capture_payment(amount: i64) -> i64 {",
                "    amount",
                "}",
            ],
        )
        self.assertEqual(result.symbols[0].name, "capture_payment")


if __name__ == "__main__":
    unittest.main()