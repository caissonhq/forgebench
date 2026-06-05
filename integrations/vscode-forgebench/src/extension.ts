import * as vscode from "vscode";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import * as path from "node:path";

const execFileAsync = promisify(execFile);

async function runForgeBench(args: string[], cwd: string): Promise<string> {
  const { stdout, stderr } = await execFileAsync("forgebench", args, { cwd, maxBuffer: 10 * 1024 * 1024 });
  return `${stdout}${stderr}`.trim();
}

export function activate(context: vscode.ExtensionContext): void {
  const workspaceRoot = () => vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? process.cwd();

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.reviewDiff", async () => {
      const diff = await vscode.window.showInputBox({
        prompt: "Path to unified git diff",
        value: "patch.diff",
      });
      const task = await vscode.window.showInputBox({
        prompt: "Path to original task prompt",
        value: "task.md",
      });
      if (!diff || !task) {
        return;
      }
      const cwd = workspaceRoot();
      const output = await vscode.window.withProgress(
        { location: vscode.ProgressLocation.Notification, title: "ForgeBench review" },
        () =>
          runForgeBench(
            ["review", "--repo", cwd, "--diff", diff, "--task", task, "--guardrails", "forgebench.yml"],
            cwd,
          ),
      );
      vscode.window.showInformationMessage("ForgeBench review complete.");
      const reportPath = path.join(cwd, "forgebench-output", "forgebench-report.md");
      const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(reportPath));
      await vscode.window.showTextDocument(doc);
      void output;
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.openReport", async () => {
      const cwd = workspaceRoot();
      const reportPath = path.join(cwd, "forgebench-output", "forgebench-report.md");
      const doc = await vscode.workspace.openTextDocument(vscode.Uri.file(reportPath));
      await vscode.window.showTextDocument(doc);
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("forgebench.exportDashboard", async () => {
      const cwd = workspaceRoot();
      await runForgeBench(["dashboard", "--repo", cwd], cwd);
      const indexPath = path.join(cwd, "forgebench-output", "policy-dashboard", "index.html");
      await vscode.env.openExternal(vscode.Uri.file(indexPath));
    }),
  );
}

export function deactivate(): void {}