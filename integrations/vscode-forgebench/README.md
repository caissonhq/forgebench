# ForgeBench VS Code Extension

Production-grade local integration for the ForgeBench CLI — findings sidebar, onboarding wizard, and repair prompts.

[![VS Code Marketplace](https://img.shields.io/badge/Marketplace-caissonhq.forgebench-007ACC)](https://marketplace.visualstudio.com/items?itemName=caissonhq.forgebench)

## Requirements

- VS Code 1.85+
- `forgebench` on `PATH` (`pipx install forgebench` recommended)
- Verify: `forgebench doctor --checklist`

## Commands

| Command | Description |
|---------|-------------|
| ForgeBench: Review Diff + Task | Pick diff and task files, run review, open report |
| ForgeBench: Review Active File as Diff | Review the active editor file as the diff |
| ForgeBench: Open Markdown Report | Open `forgebench-report.md` |
| ForgeBench: Open SARIF Report | Open SARIF output |
| ForgeBench: Validate Guardrails | Run `forgebench validate --strict` |
| ForgeBench: Run Policy Tests | Run `forgebench policy test` |
| ForgeBench: Export Policy Dashboard | Export local policy dashboard HTML |
| ForgeBench: Export Benchmark Dashboard | Export benchmark dashboard HTML |

## Settings

- `forgebench.guardrailsFile` — default `forgebench.yml`
- `forgebench.outputDir` — default `forgebench-output`
- `forgebench.policyTestsDir` — default `examples/policy_tests`
- `forgebench.runChecks` — pass `--run-checks`
- `forgebench.skipReviewers` — pass `--no-reviewers`

## Development

```bash
cd integrations/vscode-forgebench
npm install
npm run compile
```

Press F5 in VS Code to launch the Extension Development Host.

## Marketplace publish (Early Access)

1. `npm run compile`
2. `npx @vscode/vsce package`
3. Publish to Open VSX / Visual Studio Marketplace under the `caissonhq` publisher.

ForgeBench does not prove code is safe. The extension runs the local CLI only; no hosted review service is required.