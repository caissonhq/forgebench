# GitHub Marketplace listing prep — ForgeBench Action

Use this document when submitting `caissonhq/forgebench` to the GitHub Marketplace.

## Listing summary

| Field | Value |
|-------|-------|
| Name | ForgeBench |
| Category | Code quality |
| Subcategory | Testing (or Code review) |
| Tagline | Review AI-generated PR diffs before merge |
| Pricing | Free |
| Verified creator | caissonhq |

## Short description (max ~100 chars)

Review AI-generated pull request diffs for merge risk before they reach main.

## Full description

ForgeBench is a local-first merge-risk reviewer for AI-generated code changes.

The GitHub Action wraps the ForgeBench CLI in Docker. On each pull request it can:

- Fetch the PR diff and original task context through the local `gh` CLI inside the runner
- Run deterministic static review, guardrails policy, and heuristic review lenses
- Optionally run configured build/test/lint checks against a temporary PR worktree
- Write Markdown, JSON, SARIF, repair prompt, and PR-comment artifacts
- Optionally post a PR comment or GitHub Check Run when explicitly enabled

ForgeBench classifies merge posture as `BLOCK`, `REVIEW`, or `LOW_CONCERN`. It does not prove code is safe and does not auto-merge.

### Safe defaults

- PR comments are **off** unless `post-comment: true`
- Check Runs are **off** unless `post-check-run: true`
- `run-checks: true` automatically adds `--checkout-pr` so checks run against PR code
- Missing `forgebench.yml` falls back to generic review rules with visible guidance

### Requirements

- `GH_TOKEN` or `GITHUB_TOKEN` with PR read access
- Optional `forgebench.yml` in the repository

## Example workflow

```yaml
name: ForgeBench
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  forgebench:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: caissonhq/forgebench@v0.9.0
        with:
          run-checks: "true"
          post-comment: "false"
```

## Branding assets checklist

- [ ] Repository social preview image (1280×640)
- [ ] Action icon (square, high contrast)
- [ ] Screenshot of PR comment or Check Run annotations
- [ ] Link to https://forgebench.dev
- [ ] Link to synthetic sample reports in `examples/sample_report/`

## Marketplace metadata files

| File | Purpose |
|------|---------|
| `action/action.yml` | Action manifest |
| `action/README.md` | Marketplace-facing action README |
| `README.md` | Repository overview |
| `SECURITY.md` | Trust boundaries |
| `docs/trust-model.md` | Deterministic vs advisory evidence |

## Pre-submission verification

```bash
forgebench doctor
python3 -m pytest tests/test_github_action.py -q
```

Confirm Docker image builds in CI and `action/entrypoint.sh` sets outputs:

- `posture`
- `report-path`
- `pr-comment-path`
- `sarif-path`

## Support and privacy

- No ForgeBench-hosted telemetry in the Action
- Feedback remains local unless users export and share it manually
- Issues: https://github.com/caissonhq/forgebench/issues