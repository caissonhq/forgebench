from pathlib import Path
from tempfile import mkdtemp
import json
import unittest

from forgebench.diff_parser import parse_diff_file
from forgebench.guardrails import evaluate_guardrails, load_guardrails
from forgebench.models import MergePosture
from forgebench.policy import apply_guardrails_policy
from forgebench.posture import determine_posture
from forgebench.review import run_review
from forgebench.static_checks import run_static_checks


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
GOLDEN_CASES = ROOT / "examples" / "golden_cases"


class GuardrailsPolicyTests(unittest.TestCase):
    def test_v2_config_parsing_is_backward_compatible(self) -> None:
        guardrails = load_guardrails(FIXTURES / "guardrails.yml")

        self.assertEqual(guardrails.project, "Quarterly")
        self.assertIn("**/TaxEngine/**", guardrails.risk_files_high)
        self.assertIn("subscription", guardrails.forbidden_patterns)
        self.assertEqual(guardrails.policy.path_categories, {})

    def test_path_categories_classify_docs_correctly(self) -> None:
        _, _, decision = _apply_policy_for_case("docs_only_policy_low_concern")

        self.assertIn("docs", {category.name for category in decision.active_categories})

    def test_path_categories_classify_assets_correctly(self) -> None:
        _, _, decision = _apply_policy_for_case("asset_only_broad_surface_low_concern")

        self.assertIn("assets", {category.name for category in decision.active_categories})

    def test_path_categories_classify_read_models_correctly(self) -> None:
        _, _, decision = _apply_policy_for_case("read_model_not_persistence_review_or_low_concern")

        self.assertIn("read_models", {category.name for category in decision.active_categories})

    def test_suppress_findings_suppresses_ui_copy_on_docs(self) -> None:
        findings, _, decision = _apply_policy_for_case("docs_only_policy_low_concern")

        self.assertNotIn("ui_copy_changed", {finding.id for finding in findings})
        self.assertIn("ui_copy_changed", {finding.finding_id for finding in decision.suppressed_findings})

    def test_broad_file_surface_suppressed_for_asset_only_broad_diffs(self) -> None:
        findings, _, decision = _apply_policy_for_case("asset_only_broad_surface_low_concern")

        self.assertNotIn("broad_file_surface", {finding.id for finding in findings})
        self.assertIn("broad_file_surface", {finding.finding_id for finding in decision.suppressed_findings})

    def test_docs_only_posture_ceiling_caps_review_to_low_concern(self) -> None:
        findings, signals, decision = _apply_policy_for_case("docs_only_policy_low_concern")
        posture, _ = determine_posture(findings, signals, [], policy_decision=decision)

        self.assertEqual(posture, MergePosture.LOW_CONCERN)
        self.assertEqual(decision.posture_ceiling, MergePosture.LOW_CONCERN)

    def test_asset_only_posture_ceiling_caps_review_to_low_concern(self) -> None:
        findings, signals, decision = _apply_policy_for_case("asset_only_broad_surface_low_concern")
        posture, _ = determine_posture(findings, signals, [], policy_decision=decision)

        self.assertEqual(posture, MergePosture.LOW_CONCERN)
        self.assertEqual(decision.posture_ceiling, MergePosture.LOW_CONCERN)

    def test_deterministic_blocker_bypasses_posture_ceiling(self) -> None:
        result = _run_case("deterministic_failure_ignores_posture_ceiling", run_checks=True)

        self.assertEqual(result.report.posture, MergePosture.BLOCK)
        self.assertIn("tests_failed", {finding.id for finding in result.report.findings})
        self.assertEqual(result.report.policy.posture_ceiling, MergePosture.LOW_CONCERN)

    def test_forbidden_pattern_bypasses_posture_ceiling(self) -> None:
        result = _run_case("forbidden_pattern_ignores_docs_ceiling")

        self.assertEqual(result.report.posture, MergePosture.BLOCK)
        self.assertIn("forbidden_pattern_added", {finding.id for finding in result.report.findings})
        self.assertEqual(result.report.policy.posture_ceiling, MergePosture.LOW_CONCERN)

    def test_read_model_does_not_trigger_persistence_schema_changed(self) -> None:
        findings, _, _ = _apply_policy_for_case("read_model_not_persistence_review_or_low_concern")

        self.assertIn("implementation_without_tests", {finding.id for finding in findings})
        self.assertNotIn("persistence_schema_changed", {finding.id for finding in findings})

    def test_explicit_migration_schema_file_still_triggers_persistence_schema_changed(self) -> None:
        findings, _, _ = _apply_policy_for_case("explicit_persistence_still_blocks")

        self.assertIn("persistence_schema_changed", {finding.id for finding in findings})

    def test_markdown_report_includes_guardrails_policy_section(self) -> None:
        result = _run_case("docs_only_policy_low_concern")
        markdown = result.written_paths["markdown"].read_text(encoding="utf-8")

        self.assertIn("## Guardrails Policy", markdown)
        self.assertIn("Suppressed findings:", markdown)

    def test_json_report_includes_policy_object(self) -> None:
        result = _run_case("docs_only_policy_low_concern")
        payload = json.loads(result.written_paths["json"].read_text(encoding="utf-8"))

        self.assertIn("policy", payload)
        self.assertIn("suppressed_findings", payload["policy"])

    def test_repair_prompt_excludes_suppressed_findings_from_required_repairs(self) -> None:
        result = _run_case("docs_only_policy_low_concern")
        prompt = result.written_paths["repair_prompt"].read_text(encoding="utf-8")

        self.assertNotIn("- ADVISORY: User-facing copy or UI surface changed", prompt)
        self.assertIn("Suppressed or policy-calibrated findings:", prompt)


def _apply_policy_for_case(case_name: str):
    case_dir = GOLDEN_CASES / case_name
    diff = parse_diff_file(case_dir / "patch.diff")
    guardrails = load_guardrails(case_dir / "forgebench.yml")
    static_findings, signals = run_static_checks(diff)
    guardrail_findings, _ = evaluate_guardrails(diff, guardrails)
    return apply_guardrails_policy(diff, static_findings + guardrail_findings, signals, guardrails)


def _run_case(case_name: str, run_checks: bool = False):
    case_dir = GOLDEN_CASES / case_name
    return run_review(
        repo_path=ROOT,
        diff_path=case_dir / "patch.diff",
        task_path=case_dir / "task.md",
        guardrails_path=case_dir / "forgebench.yml",
        output_dir=Path(mkdtemp()) / "out",
        run_checks=run_checks,
    )


if __name__ == "__main__":
    unittest.main()
