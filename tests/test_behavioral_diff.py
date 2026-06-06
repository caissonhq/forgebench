from __future__ import annotations

import unittest

from forgebench.diff_parser import parse_unified_diff
from forgebench.semantic.behavioral_diff import analyze_behavioral_diff


class BehavioralDiffTests(unittest.TestCase):
    def test_cross_file_edges_link_source_and_test_symbols(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/payments/service.py b/payments/service.py
index 1111111..2222222 100644
--- a/payments/service.py
+++ b/payments/service.py
@@ -1,2 +1,5 @@
 class ReceiptService:
+    def capture(self, amount: int) -> int:
+        return amount
diff --git a/tests/test_service.py b/tests/test_service.py
index 1111111..2222222 100644
--- a/tests/test_service.py
+++ b/tests/test_service.py
@@ -1,2 +1,4 @@
+def test_capture_calls_service():
+    assert ReceiptService().capture(5) == 5
"""
        )
        summary = analyze_behavioral_diff(diff)

        self.assertTrue(summary.enabled)
        self.assertIn("capture", {symbol.name for symbol in summary.changed_symbols})
        self.assertEqual(summary.symbols_without_test_reference, [])
        self.assertTrue(any(edge.symbol == "capture" for edge in summary.cross_file_edges))

    def test_uncovered_symbols_when_tests_missing(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/payments/service.py b/payments/service.py
index 1111111..2222222 100644
--- a/payments/service.py
+++ b/payments/service.py
@@ -1,2 +1,4 @@
+def refund(self, amount: int) -> int:
+    return amount
"""
        )
        summary = analyze_behavioral_diff(diff)

        self.assertEqual(summary.symbols_without_test_reference, ["refund"])


if __name__ == "__main__":
    unittest.main()