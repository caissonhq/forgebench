# ForgeBench v1.0.0 — Press One-Pager

**FOR IMMEDIATE RELEASE — June 6, 2026**

## Headline

**ForgeBench launches v1.0 — local merge-risk review for AI-generated code**

## Summary

ForgeBench helps developers and engineering teams answer one question before merge: *Would a serious engineer ship this AI-generated diff?* The local CLI reviews agent output with evidence-backed posture classification (BLOCK, REVIEW, LOW_CONCERN), optional deterministic checks, and repair prompts for coding agents.

## Problem

Coding agents ship patches quickly, but broad diffs, missing tests, and task drift create merge risk. Generic linters do not evaluate merge intent against the original task.

## Solution

ForgeBench provides adversarial pre-merge QA: static analysis, configurable guardrails, heuristic review lenses, and optional advisory LLM review — all running locally without sending code to a hosted review service.

## Key facts

| | |
|---|---|
| **Product** | ForgeBench CLI + VS Code / JetBrains extensions |
| **License** | Apache-2.0 core; Team/Enterprise commercial tiers |
| **Install** | `pipx install forgebench` |
| **Website** | https://forgebench.dev |
| **Repository** | https://github.com/caissonhq/forgebench |
| **Contact** | hello@forgebench.dev |

## Differentiators

- Evidence hierarchy — deterministic failures are never downgraded
- Local-first — no mandatory hosted review
- Merge Risk Benchmark — 47+ golden cases + anonymized PR outcomes
- Team kit — `forgebench team init` for org policy and CI in one flow

## Quote (placeholder)

> "ForgeBench is the merge-risk checkpoint we wanted before agent-generated code hits main." — Design Partner (pending)

## Boilerplate

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.