# Cursor integration

ForgeBench integrates with Cursor through a project rule and a repair-prompt paste workflow.

## Project rule

This repository ships `.cursor/rules/forgebench-review.mdc`. Enable it in Cursor when reviewing agent-generated diffs.

The rule covers:

1. When to run ForgeBench
2. `forgebench review` and `forgebench review-pr` commands
3. How to paste `repair-prompt.md` back into the coding agent
4. Beta feedback commands

## Review → repair workflow

```bash
# 1. Review the agent patch
forgebench review --repo . --diff ./patch.diff --task ./task.md

# 2. Print the repair prompt for paste
forgebench repair --out forgebench-output
```

Paste the printed prompt into Cursor and ask the agent to apply the smallest necessary fixes without broadening scope.

## Optional MCP server

ForgeBench also exposes an MCP server for tool-based review:

```bash
forgebench mcp
```

Configure it in Cursor MCP settings with command `forgebench` and args `mcp`. See [mcp-server.md](mcp-server.md).

## Beta feedback from Cursor

Record structured local feedback after review:

```bash
forgebench feedback fnd_example --status dismissed --kind ui_copy_changed --agent cursor --posture REVIEW
forgebench feedback export --out forgebench-output/beta-feedback.json
```

Feedback stays local unless you choose to share the export file.