# ForgeBench v1.0.0 — Public Launch

**Release date:** 2026-06-06  
**Tag:** `v1.0.0`

ForgeBench is now **v1.0** — adversarial pre-merge QA for AI-generated diffs, local-first and production-ready.

## Highlights

- **One-command onboarding:** `forgebench quickstart`, `forgebench install`, `forgebench doctor --checklist`
- **Team adoption:** `forgebench team init`, presets gallery, shareable HTML reports
- **Distribution:** pip, pipx, Homebrew, official binary bundles, macOS `.pkg`
- **IDE:** VS Code extension 1.2, JetBrains plugin — Marketplace ready
- **Enterprise:** Team/Enterprise licensing, self-hosted GitHub App kit, SOC2-style security pack
- **Evidence-backed review:** deterministic checks → static signals → guardrails → heuristic lenses → optional LLM

## Install

```bash
pipx install forgebench
forgebench quickstart
```

Or: [Installation guide](https://forgebench.dev/docs/installation/)

## Upgrade from 0.9.x

```bash
pipx upgrade forgebench   # or: pip install --upgrade forgebench
forgebench install upgrade
```

## Release artifacts

- PyPI: `forgebench==1.0.0`
- GitHub Release: wheels, sdist, SBOM, `attestations.json`, binary `.tar.gz`, macOS `.pkg`, Homebrew formula
- VS Code: `caissonhq.forgebench` v1.2.0

## What's free forever

Local `review`, `review-pr`, `demo`, `doctor`, calibration, MCP server, GitHub Action wrapper, IDE extensions (CLI required).

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.