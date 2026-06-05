from __future__ import annotations

import unittest

from forgebench.adversaries.models import ReviewerContext
from forgebench.adversaries.security_reviewer import review
from forgebench.diff_parser import parse_unified_diff
from forgebench.guardrails import Guardrails
from forgebench.models import DeterministicChecks, PolicyDecision


class SecurityReviewerTests(unittest.TestCase):
    def test_detects_secret_pattern_in_added_lines(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/config.py b/config.py
index 1111111..2222222 100644
--- a/config.py
+++ b/config.py
@@ -1,2 +1,3 @@
 API_URL = "https://example.com"
+API_KEY = "ghp_abcdefghijklmnopqrstuvwxyz1234567890"
"""
        )
        result = review(_context(diff))

        kinds = {finding.id for finding in result.findings}
        self.assertIn("security_secret_in_added_lines", kinds)
        self.assertTrue(any(":2:" in item for item in result.findings[0].evidence))

    def test_detects_dangerous_import_pattern(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/runner.py b/runner.py
index 1111111..2222222 100644
--- a/runner.py
+++ b/runner.py
@@ -1,2 +1,3 @@
 import os
+result = eval(user_input)
"""
        )
        result = review(_context(diff))

        kinds = {finding.id for finding in result.findings}
        self.assertIn("security_dangerous_import_or_call", kinds)

    def test_clean_patch_has_no_security_findings(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/app.py b/app.py
index 1111111..2222222 100644
--- a/app.py
+++ b/app.py
@@ -1,2 +1,3 @@
 def greet():
+    return "hello"
"""
        )
        result = review(_context(diff))

        self.assertEqual(result.findings, [])


def _context(diff):
    return ReviewerContext(
        task_text="task",
        diff=diff,
        static_signals={},
        findings=[],
        guardrails=Guardrails(),
        guardrail_hits=[],
        policy=PolicyDecision(),
        deterministic_checks=DeterministicChecks(),
    )


if __name__ == "__main__":
    unittest.main()