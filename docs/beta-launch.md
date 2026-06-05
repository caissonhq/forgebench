# ForgeBench public beta

ForgeBench is in public beta as a local CLI for adversarial pre-merge QA on AI-generated diffs.

## Zero-friction first run

```bash
pip install forgebench
forgebench doctor
forgebench review-pr PR_URL
forgebench repair --out forgebench-output
```

No account, OAuth, or hosted service is required.

## Recommended beta workflow

1. Run `forgebench doctor` once per machine.
2. Review an agent PR with `forgebench review-pr PR_URL` or a local diff with `forgebench review`.
3. Paste the repair prompt with `forgebench repair --out forgebench-output`.
4. Record feedback on noisy or useful findings.
5. Export feedback when you want to share beta notes with the ForgeBench team.

## Structured beta feedback

ForgeBench stores feedback locally in JSONL. Structured fields help prioritize beta tuning:

```bash
forgebench feedback fnd_abc123 \
  --status dismissed \
  --kind ui_copy_changed \
  --agent cursor \
  --posture REVIEW \
  --workflow review_then_repair \
  --finding-count 4 \
  --note "docs-only PR; copy heuristic was noise"
```

Export a shareable bundle:

```bash
forgebench feedback export \
  --feedback-log forgebench-output/feedback.jsonl \
  --repo-name my-repo \
  --out forgebench-output/beta-feedback.json
```

Share `beta-feedback.json` manually via a GitHub issue if you want it reviewed. ForgeBench does not upload feedback automatically.

## Reduce noise quickly

```bash
forgebench init --repo . --out forgebench.yml
forgebench validate --repo . --file forgebench.yml
forgebench feedback --suggest-guardrails --out guardrail-suggestions.md
```

## Cursor and MCP integrations

- Cursor rule: `.cursor/rules/forgebench-review.mdc`
- MCP server: `forgebench mcp` — see [mcp-server.md](mcp-server.md)

## GitHub Action beta

Use the Docker action for PR workflows. Marketplace listing prep is in [github-marketplace-listing.md](github-marketplace-listing.md).

## Public benchmark page

Publishable benchmark content lives in [merge-risk-benchmark.md](merge-risk-benchmark.md). Regenerate with:

```bash
forgebench benchmark --cases examples/golden_cases --out-markdown docs/merge-risk-benchmark.md
```

## Beta boundaries

ForgeBench beta does not include:

- Hosted SaaS or dashboard
- Automatic PR comments unless explicitly enabled
- Automatic guardrail tuning from feedback
- Proof that code is safe to merge

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.