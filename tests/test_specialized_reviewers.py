from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from tempfile import TemporaryDirectory

from forgebench.cli import main
from forgebench.github_pr import GitHubPRMetadata, generate_pr_comment
from forgebench.models import MergePosture
from forgebench.review import run_review


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class SpecializedReviewerTests(unittest.TestCase):
    def test_specialized_reviewers_run_by_default(self) -> None:
        result = _review(
            task="Fix addition behavior.",
            patch="""
diff --git a/src/calculator.py b/src/calculator.py
index 1111111..2222222 100644
--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
""",
        )

        self.assertTrue(result.report.specialized_reviewers.enabled)
        reviewer_ids = {reviewer.reviewer_id for reviewer in result.report.specialized_reviewers.results}
        self.assertTrue(
            {
                "scope_auditor",
                "test_skeptic",
                "contract_keeper",
                "product_guardrail_reviewer",
                "regression_hunter",
            }.issubset(reviewer_ids)
        )

    def test_no_reviewers_disables_reviewer_layer(self) -> None:
        with TemporaryDirectory() as tmp:
            temp = Path(tmp)
            patch = _write(temp / "patch.diff", _source_patch())
            task = _write(temp / "task.md", "Fix addition behavior.")
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(
                    [
                        "review",
                        "--repo",
                        str(ROOT),
                        "--diff",
                        str(patch),
                        "--task",
                        str(task),
                        "--out",
                        str(temp / "out"),
                        "--no-reviewers",
                    ]
                )
            payload = json.loads((temp / "out" / "forgebench-report.json").read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertFalse(payload["specialized_reviewers"]["enabled"])
        self.assertIn("Heuristic review lenses: not run", stdout.getvalue())

    def test_scope_auditor_flags_docs_task_with_code_change(self) -> None:
        result = _review(
            task="Update README wording.",
            patch="""
diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Example
+Clearer wording.
diff --git a/src/runtime.py b/src/runtime.py
index 1111111..2222222 100644
--- a/src/runtime.py
+++ b/src/runtime.py
@@ -1,2 +1,3 @@
 def enabled():
-    return False
+    flag = True
+    return flag
""",
        )

        self.assertIn("scope_auditor_task_scope_expansion", _finding_ids(result))

    def test_scope_auditor_does_not_flag_docs_only_change(self) -> None:
        result = _review(task="Update README wording.", patch=_docs_patch())

        self.assertNotIn("scope_auditor_task_scope_expansion", _finding_ids(result))
        self.assertEqual(result.report.posture, MergePosture.LOW_CONCERN)

    def test_test_skeptic_flags_source_change_without_tests(self) -> None:
        result = _review(task="Fix addition behavior.", patch=_source_patch())

        self.assertIn("test_skeptic_missing_behavior_coverage", _finding_ids(result))

    def test_test_skeptic_does_not_flag_docs_only_change(self) -> None:
        result = _review(task="Update README.", patch=_docs_patch())

        self.assertNotIn("test_skeptic_missing_behavior_coverage", _finding_ids(result))

    def test_test_skeptic_weak_test_signal_works(self) -> None:
        result = _review(
            task="Add paid-state behavior.",
            patch="""
diff --git a/src/payments.py b/src/payments.py
index 1111111..2222222 100644
--- a/src/payments.py
+++ b/src/payments.py
@@ -1,2 +1,4 @@
 def status(payment):
-    return "unpaid"
+    if payment.get("paid"):
+        return "paid"
+    return "unpaid"
diff --git a/tests/test_payments.py b/tests/test_payments.py
index 1111111..2222222 100644
--- a/tests/test_payments.py
+++ b/tests/test_payments.py
@@ -1 +1,4 @@
 from src.payments import status
+
+def test_paid_status():
+    result = status({"paid": True})
""",
        )

        self.assertIn("test_skeptic_weak_test_signal", _finding_ids(result))

    def test_contract_keeper_flags_public_interface_change(self) -> None:
        result = _review(
            task="Adjust payment state model.",
            patch="""
diff --git a/src/types.ts b/src/types.ts
index 1111111..2222222 100644
--- a/src/types.ts
+++ b/src/types.ts
@@ -1,4 +1,5 @@
 export interface PaymentState {
   id: string;
   paid: boolean;
+  paidAt?: string;
 }
""",
        )

        self.assertIn("contract_keeper_contract_changed_without_tests", _finding_ids(result))

    def test_contract_keeper_flags_read_model_contract_without_schema_risk(self) -> None:
        result = _review(
            task="Update signal read model fields used by the operator display.",
            patch="""
diff --git a/operator/read_model.py b/operator/read_model.py
index 1111111..2222222 100644
--- a/operator/read_model.py
+++ b/operator/read_model.py
@@ -4,6 +4,7 @@ class SignalReadModel:
     market: str
     probability: float
     confidence: float
+    last_seen_at: str | None = None
""",
        )

        self.assertNotIn("contract_keeper_contract_changed_without_tests", _finding_ids(result))
        self.assertNotIn("contract_keeper_public_interface_changed", _finding_ids(result))
        self.assertNotIn("persistence_schema_changed", _finding_ids(result))
        self.assertIn("contract_keeper_read_model_contract_changed", _finding_ids(result))

    def test_contract_keeper_does_not_call_dto_persistence(self) -> None:
        result = _review(
            task="Adjust response DTO fields.",
            patch="""
diff --git a/app/payment_dto.py b/app/payment_dto.py
index 1111111..2222222 100644
--- a/app/payment_dto.py
+++ b/app/payment_dto.py
@@ -1,2 +1,3 @@
 class PaymentDTO:
     id: str
+    state: str
""",
        )

        self.assertNotIn("persistence_schema_changed", _finding_ids(result))

    def test_product_guardrail_reviewer_flags_forbidden_pattern(self) -> None:
        result = _review(
            task="Update payment integration copy.",
            patch="""
diff --git a/src/components/PaymentCopy.tsx b/src/components/PaymentCopy.tsx
index 1111111..2222222 100644
--- a/src/components/PaymentCopy.tsx
+++ b/src/components/PaymentCopy.tsx
@@ -1,3 +1,3 @@
 export function PaymentCopy() {
-  return <p>Track payment status locally.</p>;
+  return <p>Connect Stripe to track payment status.</p>;
 }
""",
            guardrails="""
project: Product Guardrail Case
protected_behavior:
  - Keep payment tracking local.
forbidden_patterns:
  - Stripe
""",
        )

        self.assertIn("product_guardrail_forbidden_pattern", _finding_ids(result))
        self.assertEqual(result.report.posture, MergePosture.BLOCK)
        reviewer_finding = _finding(result, "product_guardrail_forbidden_pattern")
        self.assertNotEqual(reviewer_finding.title, "Forbidden product or architecture pattern introduced")

    def test_product_guardrail_reviewer_flags_protected_high_risk_area(self) -> None:
        result = _review(
            task="Update tax calculation behavior.",
            patch="""
diff --git a/src/TaxEngine/calculate.py b/src/TaxEngine/calculate.py
index 1111111..2222222 100644
--- a/src/TaxEngine/calculate.py
+++ b/src/TaxEngine/calculate.py
@@ -1,2 +1,2 @@
 def calculate():
-    return 1
+    return 2
""",
            guardrails="""
project: Quarterly
protected_behavior:
  - Tax calculation trust must be preserved.
risk_files:
  high:
    - "src/TaxEngine/**"
""",
        )

        self.assertIn("product_guardrail_protected_area_changed", _finding_ids(result))

    def test_product_guardrail_reviewer_respects_suppressed_ui_copy(self) -> None:
        result = _review(
            task="Update README.",
            patch=_docs_patch(),
            guardrails="""
project: Docs Case
protected_behavior:
  - Keep docs quiet.
policy:
  suppress_findings:
    - finding_id: ui_copy_changed
      paths:
        - "README.md"
        - "**/*.md"
      reason: "Docs-only copy is not merge-risk relevant."
""",
        )

        self.assertNotIn("product_guardrail_copy_needs_review", _finding_ids(result))

    def test_reviewer_findings_can_escalate_low_concern_to_review(self) -> None:
        result = _review(
            task="Update README wording.",
            patch="""
diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Example
+Clearer wording.
diff --git a/src/runtime.py b/src/runtime.py
index 1111111..2222222 100644
--- a/src/runtime.py
+++ b/src/runtime.py
@@ -1,2 +1,2 @@
 def enabled():
-    return False
+    return True
diff --git a/tests/test_runtime.py b/tests/test_runtime.py
index 1111111..2222222 100644
--- a/tests/test_runtime.py
+++ b/tests/test_runtime.py
@@ -1,2 +1,3 @@
 def test_enabled():
-    assert True
+    assert True
+    result = True
""",
        )

        self.assertIn("scope_auditor_task_scope_expansion", _finding_ids(result))
        self.assertEqual(result.report.posture, MergePosture.REVIEW)

    def test_reviewer_findings_cannot_downgrade_block(self) -> None:
        result = _review(
            task="Update payment integration copy.",
            patch="""
diff --git a/src/components/PaymentCopy.tsx b/src/components/PaymentCopy.tsx
index 1111111..2222222 100644
--- a/src/components/PaymentCopy.tsx
+++ b/src/components/PaymentCopy.tsx
@@ -1,3 +1,3 @@
 export function PaymentCopy() {
-  return <p>Track payment status locally.</p>;
+  return <p>Connect Stripe to track payment status.</p>;
 }
""",
            guardrails="forbidden_patterns:\n  - Stripe\n",
        )

        self.assertEqual(result.report.posture, MergePosture.BLOCK)

    def test_deterministic_failure_remains_block(self) -> None:
        result = _review(
            task="Update README.",
            patch=_docs_patch(),
            guardrails="""
checks:
  test: "python3 -c 'import sys; sys.exit(1)'"
check_timeout_seconds: 5
""",
            run_checks=True,
        )

        self.assertEqual(result.report.posture, MergePosture.BLOCK)
        self.assertIn("tests_failed", _finding_ids(result))

    def test_markdown_json_and_repair_prompt_include_reviewers(self) -> None:
        result = _review(task="Fix addition behavior.", patch=_source_patch())
        markdown = result.written_paths["markdown"].read_text(encoding="utf-8")
        payload = json.loads(result.written_paths["json"].read_text(encoding="utf-8"))
        repair = result.written_paths["repair_prompt"].read_text(encoding="utf-8")

        self.assertIn("## Heuristic Review Lenses", markdown)
        self.assertNotIn("Specialized Reviewer", markdown)
        self.assertNotIn("Specialized Reviewers", markdown)
        self.assertIn("specialized_reviewers", payload)
        self.assertIn("Heuristic review lens findings:", repair)
        self.assertIn("Changed implementation files need coverage review", repair)
        self.assertNotIn("No additional scope concern found from task text and changed files.\n  Explanation", repair)

    def test_pr_comment_includes_concise_reviewer_summary(self) -> None:
        result = _review(task="Fix addition behavior.", patch=_source_patch())
        comment = generate_pr_comment(result.report, _metadata())

        self.assertIn("Heuristic review lenses:", comment)
        self.assertIn("Test Skeptic:", comment)
        self.assertNotIn("Specialized Reviewer", comment)
        self.assertNotIn("Specialized Reviewers", comment)
        self.assertLess(len(comment), 3000)

    def test_test_only_refactor_does_not_become_block(self) -> None:
        result = _review(
            task="Refactor payment tests.",
            patch="""
diff --git a/tests/test_payments.py b/tests/test_payments.py
index 1111111..2222222 100644
--- a/tests/test_payments.py
+++ b/tests/test_payments.py
@@ -1,4 +1,5 @@
 def test_paid_status():
     result = status({"paid": True})
-    assert result == "paid"
+    expected = "paid"
+    assert result == expected
""",
        )

        self.assertNotEqual(result.report.posture, MergePosture.BLOCK)
        self.assertNotIn("tests_assertions_removed_without_replacement", _finding_ids(result))


def _review(task: str, patch: str, guardrails: str | None = None, run_checks: bool = False):
    temp = Path(tempfile.mkdtemp(prefix="forgebench-reviewer-test-"))
    patch_path = _write(temp / "patch.diff", patch.strip() + "\n")
    task_path = _write(temp / "task.md", task)
    guardrails_path = _write(temp / "forgebench.yml", guardrails.strip() + "\n") if guardrails else None
    return run_review(
        repo_path=ROOT,
        diff_path=patch_path,
        task_path=task_path,
        guardrails_path=guardrails_path,
        output_dir=temp / "out",
        run_checks=run_checks,
    )


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _finding_ids(result) -> set[str]:
    return {finding.id for finding in result.report.findings}


def _finding(result, finding_id: str):
    for finding in result.report.findings:
        if finding.id == finding_id:
            return finding
    raise AssertionError(f"missing finding {finding_id}")


def _docs_patch() -> str:
    return """
diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1,2 +1,3 @@
 # Example
 Existing docs.
+Clarify the local workflow.
"""


def _source_patch() -> str:
    return """
diff --git a/src/calculator.py b/src/calculator.py
index 1111111..2222222 100644
--- a/src/calculator.py
+++ b/src/calculator.py
@@ -1,2 +1,2 @@
 def add(a, b):
-    return a - b
+    return a + b
"""


def _metadata() -> GitHubPRMetadata:
    return GitHubPRMetadata(
        owner="caissonhq",
        repo="forgebench",
        number=1,
        title="Test",
        body="Body",
        author="octocat",
        base_ref="main",
        head_ref="branch",
        changed_files=1,
        additions=1,
        deletions=1,
        url="https://github.com/caissonhq/forgebench/pull/1",
    )


if __name__ == "__main__":
    unittest.main()
