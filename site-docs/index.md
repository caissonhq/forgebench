# ForgeBench v1.0

**Would a serious engineer merge this AI-generated diff?**

ForgeBench is adversarial pre-merge QA for coding-agent output — local-first, evidence-backed, honest about limits.

[![PyPI](https://img.shields.io/pypi/v/forgebench.svg)](https://pypi.org/project/forgebench/)
[![GitHub](https://img.shields.io/github/stars/caissonhq/forgebench?style=social)](https://github.com/caissonhq/forgebench)

## Install in 30 seconds

```bash
pipx install forgebench
forgebench quickstart
```

Not sure which method? `forgebench install` · [Full installation guide](installation.md)

## What you get

| Output | Description |
|--------|-------------|
| **Posture** | `BLOCK`, `REVIEW`, or `LOW_CONCERN` |
| **Findings** | Evidence-backed merge-risk signals |
| **Repair prompt** | Paste back into Cursor, Codex, or Claude Code |
| **SARIF / JSON** | CI and IDE integration |

## Demo

```bash
forgebench demo              # guided review, no setup
forgebench doctor --checklist
forgebench status
```

![Demo flow](assets/demo-placeholder.md) — capture `forgebench demo` GIF for forgebench.dev

## For teams

```bash
forgebench team init
forgebench review-pr PR_URL --guardrails .github/forgebench.yml --checkout-pr --run-checks
```

[Design Partner program](design-partner.md) · [Early Access](early-access.md) · [GitHub App](github-app-listing.md)

## Evidence hierarchy

1. Deterministic checks  
2. Static risk signals  
3. Guardrails policy (`forgebench.yml`)  
4. Heuristic review lenses  
5. Optional LLM review (advisory)

Deterministic failures are never downgraded.

## Integrations

| Surface | Install |
|---------|---------|
| CLI | `pipx install forgebench` |
| VS Code | [Marketplace](https://marketplace.visualstudio.com/items?itemName=caissonhq.forgebench) |
| JetBrains | Marketplace plugin |
| GitHub Action | `caissonhq/forgebench` |
| MCP | `forgebench mcp` |

## Share your experience

```bash
forgebench feedback --share --posture REVIEW --finding-count 3
```

## Testimonials

> *"ForgeBench caught scope creep our agent missed — repair prompt saved the PR."* — Design Partner (anonymous)

> *"Finally a merge-risk checkpoint that runs locally."* — Indie hacker beta user

*Submit yours via [GitHub Discussions](https://github.com/caissonhq/forgebench/discussions/new?category=show-and-tell) or `forgebench feedback --share`.*

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.