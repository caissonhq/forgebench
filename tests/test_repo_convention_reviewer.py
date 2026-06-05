from __future__ import annotations

import unittest

from forgebench.adversaries.models import ReviewerContext
from forgebench.adversaries.repo_convention_reviewer import review
from forgebench.diff_parser import parse_unified_diff
from forgebench.guardrails import Guardrails
from forgebench.models import DeterministicChecks, PolicyDecision


class RepoConventionReviewerTests(unittest.TestCase):
    def test_detects_console_log_in_added_lines(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/src/app.ts b/src/app.ts
index 1111111..2222222 100644
--- a/src/app.ts
+++ b/src/app.ts
@@ -1,2 +1,3 @@
 export function run() {
+  console.log("debug state", state);
 }
"""
        )
        result = review(_context(diff))

        kinds = {finding.id for finding in result.findings}
        self.assertIn("repo_convention_debug_marker_added", kinds)


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