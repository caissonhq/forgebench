# IDE Integrations

ForgeBench integrates with editors through local CLI workflows, MCP, and lightweight plugin scaffolds.

## Cursor

- Project rule: [.cursor/rules/forgebench-review.mdc](../.cursor/rules/forgebench-review.mdc)
- Docs: [cursor-integration.md](cursor-integration.md)
- MCP server: `forgebench mcp` — see [mcp-server.md](mcp-server.md)

Typical loop:

```bash
forgebench review --repo . --diff ./patch.diff --task ./task.md --guardrails forgebench.yml
forgebench repair --out forgebench-output
```

## VS Code extension scaffold

Starter extension: [integrations/vscode-forgebench/](../integrations/vscode-forgebench/)

Planned commands:

- `forgebench.reviewDiff` — run review on active diff + task file
- `forgebench.openReport` — open `forgebench-report.md`
- `forgebench.exportDashboard` — run `forgebench dashboard`

Install for local development:

```bash
cd integrations/vscode-forgebench
npm install
npm run compile
code --install-extension .
```

## JetBrains plugin scaffold

Starter plugin: [integrations/jetbrains-forgebench/](../integrations/jetbrains-forgebench/)

Planned actions:

- Run ForgeBench review on selected patch and task files
- Open latest Markdown report
- Export policy dashboard skeleton

The scaffold documents Gradle setup and intended action wiring. Full marketplace publish is deferred to the public roadmap.

## MCP tools (all IDEs)

When `forgebench mcp` is configured, compatible clients can call:

- `forgebench_review` — review a diff with task + optional guardrails
- `forgebench_repair_prompt` — fetch repair prompt from output directory

## Team policy

Set org policy in IDE terminals or devcontainer env:

```bash
export FORGEBENCH_ORG_POLICY=/path/to/forgebench-org.yml
```

See [team-enterprise.md](team-enterprise.md).