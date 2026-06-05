# JetBrains ForgeBench Plugin (Scaffold)

Planned IntelliJ Platform plugin for ForgeBench merge-risk review.

## Intended actions

| Action | CLI equivalent |
|--------|----------------|
| Review Diff | `forgebench review --repo . --diff patch.diff --task task.md` |
| Open Report | Open `forgebench-output/forgebench-report.md` |
| Export Policy Dashboard | `forgebench dashboard --repo .` |

## Scaffold status

This directory documents the plugin contract and target Gradle layout. Full Kotlin sources and marketplace publish are deferred to the public roadmap.

## Local workflow today

Use the terminal tool window:

```bash
forgebench review --repo . --diff patch.diff --task task.md --guardrails forgebench.yml
forgebench repair --out forgebench-output
```

Configure MCP in compatible JetBrains AI clients via `forgebench mcp` — see [docs/mcp-server.md](../../docs/mcp-server.md).

## Org policy

```bash
export FORGEBENCH_ORG_POLICY=/path/to/forgebench-org.yml
```

See [docs/team-enterprise.md](../../docs/team-enterprise.md).