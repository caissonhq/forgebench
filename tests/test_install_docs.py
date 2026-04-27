from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class InstallDocsTests(unittest.TestCase):
    def test_readme_prioritizes_pip_install_and_init(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("pip install forgebench", readme)
        self.assertIn("forgebench init", readme)
        self.assertIn("forgebench review-pr PR_URL", readme)

    def test_readme_says_post_comment_is_explicit(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("PR comments are never posted by default", readme)
        self.assertIn("--post-comment", readme)

    def test_contributing_contains_editable_install(self) -> None:
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

        self.assertIn("python3 -m pip install -e .", contributing)

    def test_readme_does_not_claim_hosted_github_app_or_auto_approval(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()

        self.assertNotIn("hosted github app exists", readme)
        self.assertNotIn("auto-approval", readme)
        self.assertNotIn("autonomous approval", readme)
        self.assertIn("not a github app", readme)


if __name__ == "__main__":
    unittest.main()
