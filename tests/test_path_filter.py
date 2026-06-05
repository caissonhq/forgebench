from __future__ import annotations

import unittest

from forgebench.diff_parser import parse_unified_diff
from forgebench.models import Guardrails
from forgebench.path_filter import apply_review_scope, detect_monorepo_packages


class PathFilterTests(unittest.TestCase):
    def test_include_paths_limit_review_scope(self) -> None:
        diff = parse_unified_diff(
            """
diff --git a/apps/server/app.py b/apps/server/app.py
index 1111111..2222222 100644
--- a/apps/server/app.py
+++ b/apps/server/app.py
@@ -1,2 +1,3 @@
 def run():
+    return True
diff --git a/docs/README.md b/docs/README.md
index 1111111..2222222 100644
--- a/docs/README.md
+++ b/docs/README.md
@@ -1,2 +1,3 @@
 # Docs
+updated
"""
        )
        guardrails = Guardrails(review_scope_include_paths=["apps/server/**"])
        filtered, meta = apply_review_scope(diff, guardrails)

        self.assertEqual(filtered.changed_files, ["apps/server/app.py"])
        self.assertTrue(meta["path_filter_active"])
        self.assertEqual(meta["path_filter_excluded_count"], 1)

    def test_detect_monorepo_packages(self) -> None:
        packages = detect_monorepo_packages(["apps/server/package.json", "apps/web/package.json", "README.md"])

        self.assertEqual(packages, ["apps/server", "apps/web"])


if __name__ == "__main__":
    unittest.main()