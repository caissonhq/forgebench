import * as vscode from "vscode";
import { runForgeBench } from "./forgebenchRunner";

export async function runOnboardingWizard(cwd: string): Promise<void> {
  const step = await vscode.window.showQuickPick(
    [
      { label: "1. Verify install", description: "forgebench doctor", step: "doctor" },
      { label: "2. Run guided demo", description: "forgebench demo", step: "demo" },
      { label: "3. Check repo status", description: "forgebench status", step: "status" },
      { label: "4. Create guardrails", description: "forgebench init", step: "init" },
      { label: "5. Enterprise team kit", description: "forgebench init --enterprise --yes", step: "enterprise" },
      { label: "Run full checklist", description: "doctor → demo → status", step: "all" },
    ],
    { title: "ForgeBench onboarding", placeHolder: "Choose a setup step" },
  );
  if (!step) {
    return;
  }

  await vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: "ForgeBench onboarding" },
    async () => {
      if (step.step === "doctor" || step.step === "all") {
        await runForgeBench(["doctor", "--repo", cwd], cwd);
      }
      if (step.step === "demo" || step.step === "all") {
        await runForgeBench(["demo", "--repo", cwd], cwd);
      }
      if (step.step === "status" || step.step === "all") {
        await runForgeBench(["status", "--repo", cwd], cwd);
      }
      if (step.step === "init") {
        await runForgeBench(["init", "--repo", cwd, "--out", "forgebench.yml"], cwd);
      }
      if (step.step === "enterprise") {
        await runForgeBench(["init", "--enterprise", "--yes", "--repo", cwd], cwd);
      }
    },
  );

  const openDocs = await vscode.window.showInformationMessage(
    "ForgeBench onboarding step complete.",
    "Open report",
    "Open docs",
  );
  if (openDocs === "Open report") {
    await vscode.commands.executeCommand("forgebench.openReport");
  } else if (openDocs === "Open docs") {
    await vscode.env.openExternal(vscode.Uri.parse("https://forgebench.dev"));
  }
}