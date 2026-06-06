import { execFile } from "node:child_process";
import { promisify } from "node:util";
import * as path from "node:path";
import * as fs from "node:fs";

const execFileAsync = promisify(execFile);

export interface ForgeBenchRunResult {
  stdout: string;
  outputDir: string;
  reportMarkdown: string;
  reportJson: string;
  sarifPath: string;
}

export function resolveOutputDir(cwd: string, configured?: string): string {
  if (configured && configured.trim()) {
    return path.isAbsolute(configured) ? configured : path.join(cwd, configured);
  }
  return path.join(cwd, "forgebench-output");
}

export async function runForgeBench(args: string[], cwd: string): Promise<string> {
  const binary = process.env.FORGEBENCH_BIN || "forgebench";
  const { stdout, stderr } = await execFileAsync(binary, args, {
    cwd,
    maxBuffer: 10 * 1024 * 1024,
  });
  return `${stdout}${stderr}`.trim();
}

export async function runReview(
  cwd: string,
  diffPath: string,
  taskPath: string,
  options: {
    guardrails?: string;
    outputDir?: string;
    runChecks?: boolean;
    noReviewers?: boolean;
  } = {},
): Promise<ForgeBenchRunResult> {
  const outputDir = resolveOutputDir(cwd, options.outputDir);
  const args = [
    "review",
    "--repo",
    cwd,
    "--diff",
    diffPath,
    "--task",
    taskPath,
    "--out",
    outputDir,
  ];
  if (options.guardrails) {
    args.push("--guardrails", options.guardrails);
  }
  if (options.runChecks) {
    args.push("--run-checks");
  }
  if (options.noReviewers) {
    args.push("--no-reviewers");
  }
  const stdout = await runForgeBench(args, cwd);
  return {
    stdout,
    outputDir,
    reportMarkdown: path.join(outputDir, "forgebench-report.md"),
    reportJson: path.join(outputDir, "forgebench-report.json"),
    sarifPath: path.join(outputDir, "forgebench-report.sarif.json"),
  };
}

export function readPostureFromReport(reportJsonPath: string): string | undefined {
  if (!fs.existsSync(reportJsonPath)) {
    return undefined;
  }
  try {
    const payload = JSON.parse(fs.readFileSync(reportJsonPath, "utf-8")) as { posture?: string };
    return payload.posture;
  } catch {
    return undefined;
  }
}