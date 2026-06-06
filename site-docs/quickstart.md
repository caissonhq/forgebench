# Quickstart

## Install

```bash
pip install forgebench
forgebench doctor
```

Fix any **FAIL** checks before PR review. Warnings are acceptable for local diff review.

## First review (no setup)

```bash
forgebench demo
```

Or review your own patch:

```bash
forgebench review --repo . --diff ./patch.diff --task ./task.md
```

## Add guardrails

```bash
forgebench init --repo . --out forgebench.yml
forgebench validate --file forgebench.yml --strict
```

## GitHub PR review

```bash
forgebench review-pr https://github.com/org/repo/pull/123
```

With trusted CI guardrails and checks:

```bash
forgebench review-pr PR_URL \
  --guardrails .github/forgebench.yml \
  --checkout-pr \
  --run-checks
```

## Stack-specific presets

| Stack | Init |
|-------|------|
| Python | `forgebench init --preset python` |
| Node | `forgebench init --preset node` |
| Next.js | `forgebench init --preset nextjs` |
| Rust | `forgebench init --preset rust` |
| Swift | `forgebench init --preset swift` |

## Repair loop

```bash
forgebench repair --out forgebench-output
```

Paste the repair prompt into your coding agent and re-run review.