# ForgeBench — One-Pager

**Merge-risk governance for AI-generated code. Local-first. Evidence-backed.**

## Problem

Coding agents ship diffs fast. Teams lack a consistent pre-merge gate that answers: *Would a serious engineer merge this?*

## Solution

ForgeBench reviews AI-generated patches **before** they reach `main`. Output: cited `BLOCK` / `REVIEW` / `LOW_CONCERN` posture, SARIF, and a repair prompt for your agent.

## How it works

1. **Deterministic checks** — build/test/lint when configured
2. **Static risk signals** — dependencies, tests, migrations, scope
3. **Guardrails policy** — org + repo `forgebench.yml`
4. **Review lenses** — Scope Auditor, Test Skeptic, Contract Keeper
5. **Optional LLM** — advisory only, never downgrades deterministic failures

## Deployment

| Mode | Fit |
|------|-----|
| **CLI + IDE** | Developers, dogfood, first PR review |
| **GitHub Action** | PR workflow gate (comments/check runs opt-in) |
| **Self-hosted GitHub App** | Org-wide enforcement (Enterprise) |
| **Policy service** | Central policy API (Enterprise) |

## Pricing (Early Access)

- **Free** — full core review, OSS-friendly
- **Team** — $29/dev/mo — org policy, enterprise init, analytics, usage reporting
- **Enterprise** — custom — GitHub App serve, Grok verify quotas, SOC2 pack

## Proof points

- 47+ golden calibration cases + anonymized real PR outcomes
- Merge Risk Benchmark dashboard
- SOC2-style controls matrix and tamper-evident audit chain

## Contact

hello@forgebench.dev · https://forgebench.dev