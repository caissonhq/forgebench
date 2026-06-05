from __future__ import annotations

import unittest

from forgebench.adversaries.dependency_watcher import review
from forgebench.adversaries.models import ReviewerContext
from forgebench.diff_parser import parse_unified_diff
from forgebench.guardrails import Guardrails
from forgebench.models import DeterministicChecks, PolicyDecision


class DependencyWatcherTests(unittest.TestCase):
    def test_flags_manifest_change_without_tests(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/package.json b/package.json
index 1111111..2222222 100644
--- a/package.json
+++ b/package.json
@@ -1,3 +1,4 @@
 {
   "name": "app",
+  "dependencies": { "left-pad": "1.3.0" }
 }
"""
        )
        context = ReviewerContext(
            task_text="task",
            diff=diff,
            static_signals={"dependency_files_changed": ["package.json"], "test_files_changed": []},
            findings=[],
            guardrails=Guardrails(),
            guardrail_hits=[],
            policy=PolicyDecision(),
            deterministic_checks=DeterministicChecks(),
        )
        result = review(context)

        kinds = {finding.id for finding in result.findings}
        self.assertIn("dependency_watcher_manifest_without_tests", kinds)


if __name__ == "__main__":
    unittest.main()