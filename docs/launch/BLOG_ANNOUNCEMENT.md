# ForgeBench v1.0.0 Is Live — Merge-Risk Review for AI-Generated Code

*June 6, 2026 · CaissonHQ*

Your team ships faster with Cursor, Codex, and Claude Code. But who reviews the diffs before they hit `main`?

Today we're launching **ForgeBench v1.0** — a local CLI that answers one question: *would a serious engineer merge this AI-generated patch?*

## The problem

Coding agents complete tasks. They also ship broad diffs, weak tests, and scope creep. Generic linters catch syntax. They don't catch task drift or missing coverage on behavior changes.

## What ForgeBench does

ForgeBench takes a unified git diff and your original task prompt, then returns:

- **Posture:** `BLOCK`, `REVIEW`, or `LOW_CONCERN`
- **Findings** with evidence-backed merge-risk signals
- **Repair prompt** you paste back into your agent
- **SARIF / JSON** for CI and IDE integration

Everything runs locally. Your code never leaves your machine.

## Try it in two minutes

```bash
pipx install forgebench
forgebench quickstart
```

Or run a guided demo with no setup:

```bash
forgebench demo
```

## Built for teams

Engineering leads can run `forgebench team init` to generate org policy, CI workflows, and onboarding docs in one wizard. Team and Enterprise tiers add licensing, analytics dashboards, and self-hosted GitHub App enforcement.

## Design Partner program

We're inviting eight teams for a 4–6 week pilot — 50% Team discount, white-glove onboarding, and direct roadmap input. Apply via [GitHub Discussions](https://github.com/caissonhq/forgebench/discussions) or `forgebench partner onboard`.

## What we don't claim

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.

## Links

- **Site:** https://forgebench.dev
- **GitHub:** https://github.com/caissonhq/forgebench
- **Docs:** https://forgebench.dev/docs/installation/
- **VS Code:** [Marketplace](https://marketplace.visualstudio.com/items?itemName=caissonhq.forgebench)

Share your experience: `forgebench feedback --share`