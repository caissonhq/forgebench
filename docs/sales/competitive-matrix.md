# Competitive Comparison Matrix

Honest positioning — ForgeBench is **not** a replacement for human review or full SAST suites.

| Capability | ForgeBench | Generic linters | AI PR bots | SWE-Bench evals |
|------------|:----------:|:---------------:|:----------:|:---------------:|
| Merge posture (`BLOCK`/`REVIEW`/`LOW_CONCERN`) | ✓ | | partial | |
| Task + diff context | ✓ | | partial | ✓ (task only) |
| Agent repair prompt | ✓ | | rare | |
| Local-first / no code upload | ✓ | ✓ | | |
| Guardrails policy (FPL) | ✓ | | | |
| Deterministic check gate | ✓ | partial | partial | |
| Golden calibration corpus | ✓ | | | ✓ |
| GitHub Check Runs + SARIF | ✓ | partial | partial | |
| Self-hosted org enforcement | ✓ (Enterprise) | varies | rare | |
| Proves code is safe | **No** | No | often implied | No |

## When ForgeBench wins

- Teams using Cursor/Codex/Claude Code who need a **merge gate** before `main`
- Platform teams standardizing **AI codegen policy** across repos
- Regulated orgs needing **local-first** review with audit artifacts

## When to pair with other tools

- **SAST/DAST** — ForgeBench routes merge risk; security scanners find vuln classes
- **Human review** — ForgeBench narrows attention; engineers decide merge
- **Eval platforms** — SWE-Bench measures task success; ForgeBench measures merge readiness