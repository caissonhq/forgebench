# VS Code ForgeBench Extension (Scaffold)

Local development scaffold for running ForgeBench from VS Code.

## Commands

- **ForgeBench: Review Diff** — runs `forgebench review` with repo-relative diff and task paths
- **ForgeBench: Open Report** — opens `forgebench-output/forgebench-report.md`
- **ForgeBench: Export Policy Dashboard** — runs `forgebench dashboard` and opens the HTML preview

## Requirements

- `forgebench` on `PATH` (`pip install forgebench`)
- Workspace with optional `forgebench.yml`

## Develop

```bash
npm install
npm run compile
```

Load the extension folder in VS Code's Extension Development Host.

This is a scaffold. Marketplace publishing is tracked on the public [ROADMAP.md](../../ROADMAP.md).