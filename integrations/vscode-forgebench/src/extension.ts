import * as vscode from "vscode";
import * as path from "node:path";
import * as fs from "node:fs";
import { readPostureFromReport, runForgeBench, runReview } from "./forgebenchRunner";
import { ForgeBenchSidebarProvider } from "./sidebarProvider";
import { runOnboardingWizard } from "./onboarding";

function workspaceRoot(): string {
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? process.cwd();
}

function getConfig(): vscode.WorkspaceConfiguration {
  return vscode.workspace.getConfiguration("forgebench");
}

async function pickWorkspaceFile(prompt: string, defaultValue?: string): Promise<string | undefined> {
  const cwd = workspaceRoot();
  const picks = await vscode.window.showOpenDialog({
    canSelectMany: false,
    defaultUri: vscode.Uri.file(cwd),
    openLabel: prompt,
    filters: {
      "ForgeBench inputs": ["diff", "patch", "md", "txt", "json"],
      "All files": ["*"],
    },
  });
  if (!picks || picks.length === 0) {
    return defaultValue;
  }
  return picks[0].fsPath;
}

async function openReportFile(reportPath: string): Promise<void> {
  if (!fs.existsSync(reportPath)) {
    vscode.window.showWarningMessage(`ForgeBench report not found: ${reportPath}`);
    return;
  }
  const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(reportPath));
  await vscode.window.showTextDocument(doc, { preview: false });
}

function postureColor(posture?: string): string {
  if (posture === "BLOCK") {
    return "$(error)";
  }
  if (posture === "REVIEW") {
    return "$(warning)";
  }
  if (posture === "LOW_CONCERN") {
    return "$(pass)";
  }
  return "$(shield)";
}

function updateStatusBar(statusBar: vscode.StatusBarItem, posture?: string): void {
  if (!posture) {
    statusBar.text = "$(shield) ForgeBench";
    statusBar.tooltip = "Run ForgeBench review from the sidebar or command palette.";
    statusBar.backgroundColor = undefined;
    return;
  }
  statusBar.text = `${postureColor(posture)} ForgeBench: ${posture}`;
  statusBar.tooltip = `Latest ForgeBench posture: ${posture}. Click to open report.`;
  if (posture === "BLOCK") {
    statusBar.backgroundColor = new vscode.ThemeColor("statusBarItem.errorBackground");
  } else if (posture === "REVIEW") {
    statusBar.backgroundColor = new vscode.ThemeColor("statusBarItem.warningBackground");
  } else {
    statusBar.backgroundColor = undefined;
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
  statusBar.command = "forgebench.openReport";
  statusBar.show();
  context.subscriptions.push(statusBar);

  const cwd = () => workspaceRoot();
  const outputDir = () => {
    const configured = getConfig().get<string>("outputDir");
    return configured && configured.trim() ? path.join(cwd(), configured) : path.join(cwd(), "forgebench-output");
  };

  const sidebar = new ForgeBenchSidebarProvider(outputDir);
  context.subscriptions.push(
    vscode.window.registerTreeDataProvider("forgebench.findings", sidebar),
  );

  const refreshSidebar = (): void => sidebar.refresh();

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.reviewDiff", async () => {
      const diff = await pickWorkspaceFile("Select diff", "patch.diff");
      const task = await pickWorkspaceFile("Select task prompt", "task.md");
      if (!diff || !task) {
        return;
      }
      const guardrails = getConfig().get<string>("guardrailsFile") || "forgebench.yml";
      const result = await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: "ForgeBench review", cancellable: false },
        () =>
          runReview(cwd(), diff, task, {
            guardrails,
            outputDir: getConfig().get<string>("outputDir"),
            runChecks: getConfig().get<boolean>("runChecks", false),
            noReviewers: getConfig().get<boolean>("skipReviewers", false),
          }),
      );
      const posture = readPostureFromReport(result.reportJson);
      updateStatusBar(statusBar, posture);
      refreshSidebar();
      vscode.window.showInformationMessage(
        posture ? `ForgeBench review complete: ${posture}` : "ForgeBench review complete.",
        "Open repair prompt",
      ).then((choice) => {
        if (choice === "Open repair prompt") {
          void vscode.commands.executeCommand("forgebench.openRepairPrompt");
        }
      });
      await openReportFile(result.reportMarkdown);
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.reviewActiveFileAsDiff", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("Open a diff file to review.");
        return;
      }
      const diff = editor.document.uri.fsPath;
      const task = await pickWorkspaceFile("Select task prompt", "task.md");
      if (!task) {
        return;
      }
      const guardrails = getConfig().get<string>("guardrailsFile") || "forgebench.yml";
      const result = await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: "ForgeBench review" },
        () =>
          runReview(cwd(), diff, task, {
            guardrails,
            outputDir: getConfig().get<string>("outputDir"),
          }),
      );
      updateStatusBar(statusBar, readPostureFromReport(result.reportJson));
      refreshSidebar();
      await openReportFile(result.reportMarkdown);
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.openReport", async () => {
      await openReportFile(path.join(outputDir(), "forgebench-report.md"));
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.openRepairPrompt", async () => {
      const repairPath = path.join(outputDir(), "repair-prompt.md");
      if (!fs.existsSync(repairPath)) {
        vscode.window.showWarningMessage("No repair prompt found. Run a review first.");
        return;
      }
      const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(repairPath));
      await vscode.window.showTextDocument(doc, { preview: false });
      const text = doc.getText();
      await vscode.env.clipboard.writeText(text);
      vscode.window.showInformationMessage("Repair prompt copied to clipboard — paste into your coding agent.");
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.openSarif", async () => {
      const sarifPath = path.join(outputDir(), "forgebench-report.sarif.json");
      if (!fs.existsSync(sarifPath)) {
        vscode.window.showWarningMessage("No SARIF report found. Run a review first.");
        return;
      }
      await openReportFile(sarifPath);
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.validateGuardrails", async () => {
      const guardrails = getConfig().get<string>("guardrailsFile") || "forgebench.yml";
      await runForgeBench(["validate", "--repo", cwd(), "--file", guardrails, "--strict"], cwd());
      vscode.window.showInformationMessage("ForgeBench guardrails validated.");
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.policyTest", async () => {
      const testsDir = getConfig().get<string>("policyTestsDir") || "examples/policy_tests";
      await runForgeBench(["policy", "test", "--tests", testsDir, "--repo", cwd()], cwd());
      vscode.window.showInformationMessage("ForgeBench policy tests finished.");
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.exportDashboard", async () => {
      await runForgeBench(["dashboard", "--repo", cwd()], cwd());
      const indexPath = path.join(cwd(), "forgebench-output", "policy-dashboard", "index.html");
      await vscode.env.openExternal(vscode.Uri.file(indexPath));
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.exportBenchmarkDashboard", async () => {
      await runForgeBench(["benchmark-dashboard", "--repo", cwd()], cwd());
      const indexPath = path.join(cwd(), "forgebench-output", "benchmark-dashboard", "index.html");
      await vscode.env.openExternal(vscode.Uri.file(indexPath));
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.runStatus", async () => {
      const output = await runForgeBench(["status", "--repo", cwd()], cwd());
      const channel = vscode.window.createOutputChannel("ForgeBench");
      channel.appendLine(output);
      channel.show();
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.runDemo", async () => {
      await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: "ForgeBench demo" },
        () => runForgeBench(["demo", "--repo", cwd()], cwd()),
      );
      updateStatusBar(statusBar, readPostureFromReport(path.join(cwd(), "forgebench-output", "demo", "forgebench-report.json")));
      refreshSidebar();
      await openReportFile(path.join(cwd(), "forgebench-output", "demo", "forgebench-report.md"));
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.runDoctor", async () => {
      const output = await runForgeBench(["doctor", "--repo", cwd()], cwd());
      const channel = vscode.window.createOutputChannel("ForgeBench");
      channel.appendLine(output);
      channel.show();
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.onboarding", async () => {
      await runOnboardingWizard(cwd());
      refreshSidebar();
      updateStatusBar(statusBar, readPostureFromReport(path.join(outputDir(), "forgebench-report.json")));
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.initEnterprise", async () => {
      await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: "ForgeBench enterprise init" },
        () => runForgeBench(["init", "--enterprise", "--yes", "--repo", cwd()], cwd()),
      );
      vscode.window.showInformationMessage("Enterprise starter kit generated.");
    }),
  );

  const existing = readPostureFromReport(path.join(outputDir(), "forgebench-report.json"));
  updateStatusBar(statusBar, existing);

  if (getConfig().get<boolean>("showOnboardingOnFirstRun", true) && !context.globalState.get<boolean>("forgebench.onboardingSeen")) {
    void vscode.window
      .showInformationMessage(
        "Welcome to ForgeBench — run the onboarding wizard to get started.",
        "Start onboarding",
        "Dismiss",
      )
      .then((choice) => {
        if (choice === "Start onboarding") {
          void vscode.commands.executeCommand("forgebench.onboarding");
        }
        void context.globalState.update("forgebench.onboardingSeen", true);
      });
  }
}

export function deactivate(): void {}