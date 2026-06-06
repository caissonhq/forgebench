from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
VSCODE = ROOT / "integrations" / "vscode-forgebench"
JETBRAINS = ROOT / "integrations" / "jetbrains-forgebench"


class IDEIntegrationTests(unittest.TestCase):
    def test_vscode_extension_is_production_grade(self) -> None:
        package = json.loads((VSCODE / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(package["version"], "1.1.0")
        commands = {item["command"] for item in package["contributes"]["commands"]}
        self.assertIn("forgebench.reviewDiff", commands)
        self.assertIn("forgebench.policyTest", commands)
        self.assertIn("forgebench.openSarif", commands)
        self.assertIn("forgebench.onboarding", commands)
        self.assertIn("forgebench.openRepairPrompt", commands)
        self.assertIn("forgebench.runDemo", commands)
        self.assertIn("configuration", package["contributes"])
        self.assertIn("viewsContainers", package["contributes"])
        self.assertTrue((VSCODE / "src" / "forgebenchRunner.ts").exists())
        self.assertTrue((VSCODE / "src" / "sidebarProvider.ts").exists())
        self.assertTrue((VSCODE / "src" / "onboarding.ts").exists())

    def test_jetbrains_plugin_has_actions_and_build(self) -> None:
        plugin_xml = (JETBRAINS / "src" / "main" / "resources" / "META-INF" / "plugin.xml").read_text(
            encoding="utf-8"
        )
        self.assertIn("ForgeBench.ReviewDiff", plugin_xml)
        self.assertIn("ForgeBench.PolicyTest", plugin_xml)
        self.assertIn("ForgeBench.Onboarding", plugin_xml)
        self.assertIn("ForgeBenchToolWindowFactory", plugin_xml)
        self.assertTrue((JETBRAINS / "build.gradle.kts").exists())
        self.assertTrue((JETBRAINS / "src" / "main" / "kotlin" / "dev" / "forgebench" / "jetbrains" / "ForgeBenchCli.kt").exists())


if __name__ == "__main__":
    unittest.main()