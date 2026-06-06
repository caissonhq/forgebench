# VS Code extension

Path: `integrations/vscode-forgebench/`

## Features

- **Findings sidebar** — posture and findings from the latest report
- **Status bar** — live posture with color cues (`BLOCK`, `REVIEW`, `LOW_CONCERN`)
- **Onboarding wizard** — doctor → demo → status → init
- **Repair prompt** — open and copy to clipboard
- **Command palette** — review, validate, policy test, dashboards, enterprise init

## Install (development)

```bash
cd integrations/vscode-forgebench
npm install
npm run compile
```

Press F5 in VS Code to launch Extension Development Host.

## Settings

| Setting | Default |
|---------|---------|
| `forgebench.guardrailsFile` | `forgebench.yml` |
| `forgebench.outputDir` | `forgebench-output` |
| `forgebench.runChecks` | `false` |
| `forgebench.showOnboardingOnFirstRun` | `true` |