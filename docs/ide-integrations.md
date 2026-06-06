# IDE Integrations

ForgeBench integrates with editors through local CLI workflows, MCP, and production IDE extensions.

## Cursor

- Project rule: [.cursor/rules/forgebench-review.mdc](../.cursor/rules/forgebench-review.mdc)
- Docs: [cursor-integration.md](cursor-integration.md)
- MCP server: `forgebench mcp` — see [mcp-server.md](mcp-server.md)

Typical loop:

```bash
forgebench review --repo . --diff ./patch.diff --task ./task.md --guardrails forgebench.yml
forgebench repair --out forgebench-output
```

## VS Code extension

Production extension: [integrations/vscode-forgebench/](../integrations/vscode-forgebench/) (v1.1.0)

Features:

- **Findings sidebar** — posture and findings from the latest report
- **Onboarding wizard** — doctor → demo → status → init
- **Status bar** — live posture with color cues
- **Repair prompt** — open and copy to clipboard
- Commands: review, demo, status, doctor, validate, policy test, enterprise init, dashboards

Install for local development:

```bash
cd integrations/vscode-forgebench
npm install
npm run compile
```

Press F5 in VS Code to launch Extension Development Host.

## JetBrains plugin

Production plugin: [integrations/jetbrains-forgebench/](../integrations/jetbrains-forgebench/)

Features:

- **Tool window** — demo, status, repair prompt viewer
- **Onboarding wizard** — doctor → demo → status checklist
- **Settings** — guardrails path, output dir, run checks
- Actions: review, validate, init/enterprise, policy test, dashboard export

```bash
cd integrations/jetbrains-forgebench
./gradlew buildPlugin
```

Set `FORGEBENCH_BIN` if the CLI is not on PATH.

## MCP tools (all IDEs)

When `forgebench mcp` is configured, compatible clients can call:

- `forgebench_review` — review a diff with task + optional guardrails
- `forgebench_repair_prompt` — fetch repair prompt from output directory

## Team policy

Set org policy in IDE terminals or devcontainer env:

```bash
export FORGEBENCH_ORG_POLICY=/opt/forgebench/org/forgebench-org.yml
forgebench review-pr "$PR_URL" --guardrails forgebench.yml --checkout-pr --run-checks
```

Generate a team starter kit:

```bash
forgebench init --enterprise --yes
```

Docs site: `mkdocs serve` (see [site-docs/](../site-docs/)).