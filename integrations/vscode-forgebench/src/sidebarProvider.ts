import * as vscode from "vscode";
import * as fs from "node:fs";
import * as path from "node:path";

interface FindingNode {
  uid: string;
  title: string;
  severity: string;
}

export class ForgeBenchSidebarProvider implements vscode.TreeDataProvider<ForgeBenchTreeItem> {
  private readonly _onDidChangeTreeData = new vscode.EventEmitter<void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private readonly outputDir: () => string) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: ForgeBenchTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: ForgeBenchTreeItem): ForgeBenchTreeItem[] {
    if (element) {
      if (element.contextValue === "finding") {
        return [
          new ForgeBenchTreeItem(
            "Open repair prompt",
            vscode.TreeItemCollapsibleState.None,
            { command: "forgebench.openRepairPrompt", title: "Open repair prompt" },
          ),
        ];
      }
      return [];
    }

    const reportPath = path.join(this.outputDir(), "forgebench-report.json");
    if (!fs.existsSync(reportPath)) {
      return [
        new ForgeBenchTreeItem(
          "No report yet — run a review",
          vscode.TreeItemCollapsibleState.None,
          { command: "forgebench.reviewDiff", title: "Review diff" },
        ),
        new ForgeBenchTreeItem(
          "Try guided demo",
          vscode.TreeItemCollapsibleState.None,
          { command: "forgebench.runDemo", title: "Run demo" },
        ),
      ];
    }

    try {
      const payload = JSON.parse(fs.readFileSync(reportPath, "utf-8")) as {
        posture?: string;
        findings?: FindingNode[];
      };
      const posture = payload.posture ?? "UNKNOWN";
      const items: ForgeBenchTreeItem[] = [
        new ForgeBenchTreeItem(
          `Posture: ${posture}`,
          vscode.TreeItemCollapsibleState.None,
          { command: "forgebench.openReport", title: "Open report" },
        ),
      ];
      const findings = payload.findings ?? [];
      if (!findings.length) {
        items.push(
          new ForgeBenchTreeItem("No findings", vscode.TreeItemCollapsibleState.None),
        );
        return items;
      }
      for (const finding of findings) {
        items.push(
          new ForgeBenchTreeItem(
            `${finding.severity}: ${finding.title}`,
            vscode.TreeItemCollapsibleState.Collapsed,
            undefined,
            "finding",
            finding.uid,
          ),
        );
      }
      return items;
    } catch {
      return [new ForgeBenchTreeItem("Could not parse report", vscode.TreeItemCollapsibleState.None)];
    }
  }
}

export class ForgeBenchTreeItem extends vscode.TreeItem {
  constructor(
    label: string,
    collapsibleState: vscode.TreeItemCollapsibleState,
    command?: vscode.Command,
    contextValue?: string,
    description?: string,
  ) {
    super(label, collapsibleState);
    this.command = command;
    this.contextValue = contextValue;
    this.description = description;
    this.iconPath = new vscode.ThemeIcon("shield");
  }
}