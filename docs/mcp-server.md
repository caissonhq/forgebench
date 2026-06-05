# ForgeBench MCP server

ForgeBench ships a minimal MCP server over stdio for IDE and agent integrations.

## Start the server

```bash
forgebench mcp
```

## Cursor configuration

Add to Cursor MCP settings:

```json
{
  "mcpServers": {
    "forgebench": {
      "command": "forgebench",
      "args": ["mcp"]
    }
  }
}
```

Requires `forgebench` on `PATH` (`pip install forgebench`).

## Tools

### `forgebench_review`

Run a local ForgeBench review and return the repair prompt text.

Arguments:

| Name | Required | Description |
|------|----------|-------------|
| `repo` | yes | Repository root path |
| `diff` | yes | Unified git diff path |
| `task` | yes | Original task prompt path |
| `guardrails` | no | `forgebench.yml` path |
| `output_dir` | no | Output directory (default `forgebench-output`) |
| `run_checks` | no | Run configured deterministic checks |
| `no_reviewers` | no | Skip heuristic review lenses |

Returns JSON with `posture`, artifact paths, and `repair_prompt` ready to paste.

### `forgebench_repair_prompt`

Read `repair-prompt.md` from a prior review output directory.

Arguments:

| Name | Required | Description |
|------|----------|-------------|
| `output_dir` | no | ForgeBench output directory (default `forgebench-output`) |

## Security

- The MCP server runs local review only. It does not upload diffs or post PR comments.
- `run_checks` executes commands from `forgebench.yml`. Use only on trusted repos and trusted guardrails files.
- No network calls are required for deterministic review.