from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from forgebench.cli import _build_parser
from forgebench.guardrails import parse_guardrails


ROOT = Path(__file__).resolve().parents[1]


class SecurityInvariantTests(unittest.TestCase):
    def test_run_checks_default_is_false(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["review", "--repo", ".", "--diff", "patch.diff", "--task", "task.md"])

        self.assertFalse(args.run_checks)

    def test_post_comment_default_is_false(self) -> None:
        parser = _build_parser()
        args = parser.parse_args(["review-pr", "https://github.com/owner/repo/pull/1"])

        self.assertFalse(args.post_comment)

    def test_feedback_module_has_no_remote_url_constants(self) -> None:
        text = (ROOT / "forgebench" / "feedback.py").read_text(encoding="utf-8")

        self.assertNotIn("http://", text)
        self.assertNotIn("https://", text)

    def test_guardrails_parsing_does_not_execute_commands(self) -> None:
        with TemporaryDirectory() as tmp:
            marker = Path(tmp) / "executed"
            guardrails = parse_guardrails(
                f"""
checks:
  test: >-
    python -c "open({str(marker)!r}, 'w').write('bad')"
"""
            )

            self.assertIn("test", guardrails.checks)
            self.assertFalse(marker.exists())

    def test_command_provider_docs_include_warning(self) -> None:
        text = (ROOT / "docs" / "llm-threat-model.md").read_text(encoding="utf-8")

        self.assertIn("--llm-command", text)
        self.assertIn("untrusted PR", text)
        self.assertIn("trusted local code execution", text)

    def test_security_doc_mentions_trust_boundaries(self) -> None:
        text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")

        self.assertIn("untrusted PR-head `forgebench.yml`", text)
        self.assertIn("Checks run only when `--run-checks` is explicitly passed", text)
        self.assertIn("PR comments are never posted by default", text)
        self.assertIn("No feedback telemetry", text)


if __name__ == "__main__":
    unittest.main()
