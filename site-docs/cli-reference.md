# CLI Reference

## Global flags

| Flag | Description |
|------|-------------|
| `--version` | Print version |
| `--explain` | Print actionable hints on errors |
| `--help` | Command help |

## Commands

### `forgebench doctor`

Verify Python, package, git, GitHub CLI, writable output, guardrails, CI workflow, and onboarding checklist.

### `forgebench status`

Repository health summary with recommendations. Use `--json` for automation.

### `forgebench demo`

Run a bundled golden-case review. No network or guardrails required.

### `forgebench init`

Create `forgebench.yml`. Use `--enterprise` for org policy, CI workflow, and team docs.

```bash
forgebench init --enterprise --yes --org-name "Acme Engineering"
```

### `forgebench review`

Review a local diff and task prompt.

### `forgebench review-pr`

Fetch a GitHub PR via `gh`, review, optionally post comment or check run.

### `forgebench repair`

Print `repair-prompt.md` for your coding agent.

### `forgebench validate`

Lint `forgebench.yml` against the documented schema.

### `forgebench policy test`

Run policy regression tests from `examples/policy_tests/`.

### `forgebench dashboard`

Export local policy dashboard HTML.

See also: [Report schema](api/report-schema.md), [MCP server](api/mcp.md).