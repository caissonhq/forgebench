# VS Code Marketplace Submission

## Package

```bash
cd integrations/vscode-forgebench
npm install && npm run compile
npx @vscode/vsce package
```

Publish via CI (`.github/workflows/vscode-marketplace.yml`) with `VSCE_PAT` secret, or:

```bash
npx @vscode/vsce publish -p "$VSCE_PAT"
```

## Marketplace copy

**Short description:** Merge-risk review for AI-generated diffs — sidebar, onboarding, repair prompts.

**Long description highlights:**

- Findings sidebar with posture colors
- Onboarding wizard (doctor → demo → status)
- Review diff + task from workspace
- SARIF, policy test, enterprise init commands
- Requires local `forgebench` CLI (`pipx install forgebench`)

## Assets

| Asset | Path |
|-------|------|
| Icon 128×128 | `media/icon.png` |
| Screenshot 1 | Sidebar + findings (capture manually) |
| Screenshot 2 | Onboarding wizard |
| Screenshot 3 | Repair prompt |

## Keywords

`code review`, `ai`, `merge risk`, `cursor`, `copilot`, `codex`, `sarif`, `guardrails`

## Links

- Homepage: https://forgebench.dev/docs/ide/vscode/
- Repository: https://github.com/caissonhq/forgebench
- Issues: https://github.com/caissonhq/forgebench/issues