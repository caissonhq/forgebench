from __future__ import annotations

import json
import os
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.adoption import (
    build_conversion_funnel,
    format_first_review_success_banner,
    is_first_review_pending,
    next_actions_after_review,
)
from forgebench.cli import main
from forgebench.feedback import format_paid_feedback_prompt
from forgebench.feedback_digest import build_feedback_digest, format_feedback_digest
from forgebench.licensing.keys import generate_license_key
from forgebench.licensing.store import activate_and_store
from forgebench.partner.onboarding import (
    build_partner_onboarding_kit,
    format_welcome_email,
    list_partner_presets,
    load_pilot_license_keys,
)


ROOT = Path(__file__).resolve().parents[1]


class PartnerOnboardingTests(unittest.TestCase):
    def test_welcome_email_includes_license_and_support(self) -> None:
        text = format_welcome_email(organization="Acme", license_key="FB-TEAM-test.key")
        self.assertIn("Acme", text)
        self.assertIn("FB-TEAM-test.key", text)
        self.assertIn("hello@forgebench.dev", text)
        self.assertIn("design-partner", text)

    def test_build_onboarding_kit_writes_files(self) -> None:
        with TemporaryDirectory() as tmp:
            kit = build_partner_onboarding_kit(
                organization="Acme Corp",
                contact_email="lead@acme.com",
                output_dir=tmp,
            )
            self.assertTrue((Path(tmp) / "welcome-email.txt").exists())
            self.assertTrue((Path(tmp) / "partner-kit.json").exists())
            self.assertIn("agent-pr-strict", kit.preset_names)

    def test_pilot_license_keys_file_has_eight_keys(self) -> None:
        keys = load_pilot_license_keys()
        self.assertGreaterEqual(len(keys), 8)
        self.assertTrue(all(str(item.get("key", "")).startswith("FB-") for item in keys))

    def test_partner_presets_list_includes_agent_pr_strict(self) -> None:
        names = [item.name for item in list_partner_presets()]
        self.assertIn("agent-pr-strict", names)

    def test_cli_partner_onboard_guided_flow(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["partner", "onboard"])
        self.assertEqual(code, 0)
        self.assertIn("Guided Onboarding", stdout.getvalue())

    def test_cli_partner_onboard_with_organization(self) -> None:
        with TemporaryDirectory() as tmp:
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(
                    [
                        "partner",
                        "onboard",
                        "--organization",
                        "Test Org",
                        "--email",
                        "test@example.com",
                        "--out",
                        tmp,
                    ]
                )
            self.assertEqual(code, 0)
            self.assertIn("Welcome to the ForgeBench Design Partner", stdout.getvalue())
            self.assertTrue((Path(tmp) / "partner-kit.json").exists())

    def test_cli_partner_keys_lists_inventory(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["partner", "keys"])
        self.assertEqual(code, 0)
        self.assertIn("Pilot license keys", stdout.getvalue())

    def test_cli_partner_presets_list(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["partner", "presets", "list"])
        self.assertEqual(code, 0)
        self.assertIn("agent-pr-strict", stdout.getvalue())

    def test_cli_partner_presets_install(self) -> None:
        with TemporaryDirectory() as tmp:
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["partner", "presets", "install", "agent-pr-strict", "--repo", tmp])
            self.assertEqual(code, 0)
            self.assertTrue((Path(tmp) / "forgebench.yml").exists())
            self.assertIn("agent-pr-strict", (Path(tmp) / "forgebench.yml").read_text(encoding="utf-8"))

    def test_cli_feedback_paid_prompt(self) -> None:
        stdout = StringIO()
        with redirect_stdout(stdout):
            code = main(["feedback", "--paid", "--agent", "cursor"])
        self.assertEqual(code, 0)
        self.assertIn("structured feedback", stdout.getvalue().lower())
        self.assertIn("digest", stdout.getvalue())

    def test_cli_feedback_digest(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            log.write_text(
                json.dumps(
                    {
                        "uid": "fnd_a",
                        "status": "dismissed",
                        "kind": "ui_copy_changed",
                        "note": "docs only",
                        "ts": "2026-06-06T12:00:00+00:00",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = main(["feedback", "--digest", "--feedback-log", str(log), "--digest-days", "7"])
            self.assertEqual(code, 0)
            self.assertIn("feedback digest", stdout.getvalue().lower())
            self.assertIn("ui_copy_changed", stdout.getvalue())

    def test_feedback_digest_roadmap_candidates(self) -> None:
        with TemporaryDirectory() as tmp:
            log = Path(tmp) / "feedback.jsonl"
            lines = [
                json.dumps(
                    {
                        "uid": f"fnd_{i}",
                        "status": "dismissed",
                        "kind": "broad_file_surface",
                        "ts": "2026-06-06T12:00:00+00:00",
                    }
                )
                for i in range(3)
            ]
            log.write_text("\n".join(lines) + "\n", encoding="utf-8")
            digest = build_feedback_digest([log], days=7)
            text = format_feedback_digest(digest)
            self.assertIn("broad_file_surface", text)
            self.assertTrue(digest.roadmap_candidates)

    def test_first_review_success_actions(self) -> None:
        actions = next_actions_after_review(
            posture="REVIEW",
            config_mode="generic",
            finding_count=2,
            is_first_review=True,
        )
        self.assertTrue(any("partner onboard" in item for item in actions))
        self.assertTrue(any("upgrade" in item for item in actions))
        self.assertTrue(any("feedback --share" in item for item in actions))

    def test_first_review_banner(self) -> None:
        banner = format_first_review_success_banner(posture="BLOCK", finding_count=1)
        self.assertIn("First review complete", banner)

    def test_conversion_funnel_stages(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "adoption-state.json"
            from forgebench.adoption import record_milestone

            record_milestone("first_install", path=path)
            funnel = build_conversion_funnel(path=path)
            self.assertTrue(funnel["install"])
            self.assertFalse(funnel["license_activate"])

    def test_is_first_review_pending(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "adoption-state.json"
            self.assertTrue(is_first_review_pending(path=path))

    def test_paid_feedback_prompt_format(self) -> None:
        text = format_paid_feedback_prompt(organization="Acme", tier="team", agent_tool="cursor")
        self.assertIn("Acme", text)
        self.assertIn("false_positive", text)

    def test_e2e_paid_flow_subscribe_activate_team_init(self) -> None:
        with TemporaryDirectory() as tmp:
            license_path = Path(tmp) / "license.json"
            repo = Path(tmp) / "repo"
            repo.mkdir()
            key = generate_license_key(tier="team", organization="E2E Co", seats=5)
            activate_and_store(key, path=license_path)
            os.environ["FORGEBENCH_LICENSE_PATH"] = str(license_path)

            stdout = StringIO()
            with redirect_stdout(stdout):
                sub_code = main(["subscribe", "team", "--seats", "5"])
            self.assertEqual(sub_code, 0)

            stdout = StringIO()
            with redirect_stdout(stdout):
                act_code = main(["license", "activate", key, "--path", str(license_path)])
            self.assertEqual(act_code, 0)

            stdout = StringIO()
            with redirect_stdout(stdout):
                team_code = main(["team", "init", "--yes", "--repo", str(repo), "--org-name", "E2E Co"])
            self.assertEqual(team_code, 0)
            self.assertTrue((repo / "forgebench.yml").exists())

        os.environ.pop("FORGEBENCH_LICENSE_PATH", None)

    def test_design_partner_docs_exist(self) -> None:
        self.assertTrue((ROOT / "docs" / "design-partner" / "ONBOARDING_KIT.md").exists())
        self.assertTrue((ROOT / "docs" / "design-partner" / "WHY_JOIN_ONE_PAGER.md").exists())
        self.assertTrue((ROOT / ".github" / "DISCUSSION_TEMPLATE" / "design-partner.yml").exists())


if __name__ == "__main__":
    unittest.main()