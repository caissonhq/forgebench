# VS Code Marketplace Submission

Extension path: `integrations/vscode-forgebench/`

## Pre-submission checklist

- [ ] `npm run compile` passes
- [ ] `vsce package` produces `.vsix`
- [ ] Version in `package.json` matches release tag
- [ ] README in extension folder describes commands
- [ ] Publisher account `caissonhq` configured
- [ ] `VSCE_PAT` secret in GitHub Actions

## Publish

Manual:

```bash
cd integrations/vscode-forgebench
npm install && npm run compile
npx @vscode/vsce publish -p $VSCE_PAT
```

CI: `.github/workflows/vscode-marketplace.yml` (workflow_dispatch)

## Listing copy

| Field | Value |
|-------|-------|
| Name | ForgeBench |
| Category | Linters |
| Tagline | Merge-risk review for AI-generated diffs |
| Description | Professional sidebar, onboarding wizard, repair prompts. Runs local `forgebench` CLI. |

## Commands to highlight

- Onboarding Wizard
- Findings sidebar
- Review Diff + Task
- Run Demo Review
- Open Repair Prompt (clipboard)
- Enterprise Init

## Requirements

Users must install ForgeBench CLI: `pip install forgebench`