# Policy Verification Platform (EO-009)

ForgeBench EO-009 adds policy simulation, testing, audit logging, versioning, formal-ish hooks, optional Grok verification, and a self-hosted policy service skeleton.

## Policy simulation

Run policy without a full review pipeline:

```bash
forgebench policy simulate \
  --repo . \
  --diff examples/golden_cases/docs_only_policy_low_concern/patch.diff \
  --guardrails examples/golden_cases/docs_only_policy_low_concern/forgebench.yml
```

## Policy tests

Policy tests live in `examples/policy_tests/` as `policy_test.json` cases:

```bash
forgebench policy test --tests examples/policy_tests
```

Each case specifies `guardrails`, `diff`, and `expect` assertions for posture, suppressions, categories, and formal hooks.

## Formal-ish verification hooks

Local structural checks (not theorem proving):

- Deterministic failures must produce `BLOCK`
- Posture must respect policy ceiling
- Suppressed findings must not remain active
- `BLOCK` posture requires active findings

```bash
forgebench policy verify --diff patch.diff --guardrails forgebench.yml
```

## Grok API verification (optional)

When `FORGEBENCH_GROK_API_KEY` is set:

```bash
forgebench policy verify --diff patch.diff --guardrails forgebench.yml --grok
```

Use `--grok-mock` for offline smoke tests. Grok verification is advisory; it does not certify code as safe.

Environment variables:

- `FORGEBENCH_GROK_API_KEY`
- `FORGEBENCH_GROK_BASE_URL` (default `https://api.x.ai/v1`)
- `FORGEBENCH_GROK_MODEL` (default `grok-2-latest`)

## Policy audit log

Append-only JSONL at `forgebench-output/policy-audit.jsonl`:

```bash
forgebench policy audit
forgebench policy audit --export --out policy-audit.json
```

## Policy versioning

```bash
forgebench policy version forgebench.yml --record --version 1.0.0
```

Version history is stored in `forgebench-output/policy-versions.jsonl` with content fingerprints.

## Self-hosted policy service

```bash
forgebench policy serve --repo . --guardrails forgebench.yml --port 8791
```

Endpoints:

- `GET /health`
- `GET /v1/policy`
- `POST /v1/policy/validate`
- `POST /v1/policy/simulate`
- `POST /v1/policy/compile-fpl`

Bind to localhost by default. This is a skeleton for Team/Enterprise self-hosting, not a hosted SaaS.