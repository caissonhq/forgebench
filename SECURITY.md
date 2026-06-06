# Security

ForgeBench is a local CLI. By default it reads diffs, task files, and optional guardrails without executing project commands.

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.

## Trust Boundaries

### `forgebench.yml`

`forgebench.yml` is repo-local policy and may contain shell commands under `checks`.

Do not run checks from an untrusted PR-head `forgebench.yml`. Use local/base-branch guardrails unless you intentionally trust the PR branch configuration.

Parsing `forgebench.yml` is passive. ForgeBench uses `yaml.safe_load`, does not use `eval` or `exec`, and does not execute commands while parsing.

### `--run-checks`

Checks run only when `--run-checks` is explicitly passed. When enabled, ForgeBench executes local shell commands from the selected `forgebench.yml` in the repo checkout used for review.

`review-pr --run-checks` **requires** `--guardrails` pointing to a trusted base-branch policy file outside the PR worktree. ForgeBench rejects PR-head `forgebench.yml` for check execution unless `--trust-pr-guardrails` is explicitly passed.

Only run `--run-checks` against trusted repositories and trusted `forgebench.yml` files.

### `--post-comment`

PR comments are never posted by default. ForgeBench posts to GitHub only when `--post-comment` is explicitly passed.

### `--llm-command` / `FORGEBENCH_LLM_COMMAND`

`--llm-review --llm-provider command` executes a user-supplied local command via `shlex` argv parsing (no shell). When `--llm-command` is omitted, ForgeBench uses `FORGEBENCH_LLM_COMMAND` if set. Only use command providers you trust.

### `--llm-provider openai`

`--llm-review --llm-provider openai` sends the review bundle to an OpenAI-compatible HTTP API using `FORGEBENCH_LLM_API_KEY`. Optional: `FORGEBENCH_LLM_BASE_URL`, `FORGEBENCH_LLM_MODEL`. This is network egress with your API key; do not run against untrusted endpoints.

See [docs/llm-threat-model.md](docs/llm-threat-model.md) for the LLM threat model and mitigations.

### PR Worktrees

`review-pr --checkout-pr` uses a temporary git worktree so deterministic checks can run against PR code without mutating the main checkout.

ForgeBench should not run `git reset`, `git clean`, `git checkout`, `git merge`, or `git rebase` in your main checkout. If ForgeBench is interrupted with Ctrl-C or the process is killed, a temporary worktree or temporary ref may remain and require manual cleanup.

### Feedback

`forgebench feedback` writes local JSONL. No feedback telemetry, analytics, or reports are uploaded anywhere.

## Security Reviewer v0

ForgeBench includes a deterministic Security Reviewer lens that scans added diff lines for likely secrets and dangerous imports or dynamic execution patterns. It is pattern-based, local-only, and advisory. It does not replace dedicated secret scanners or SAST.

## CI Artifacts

Reviews can write SARIF (`forgebench-report.sarif.json`) for code scanning workflows and post GitHub Check Run annotations when `review-pr --check-run` is explicitly passed. Neither feature runs by default.

## Trust Model

See [docs/trust-model.md](docs/trust-model.md) for fork PR guidance, guardrails trust, check execution boundaries, and CI operator checklist.

## Self-Hosted Services (EO-011)

- **Policy service** (`forgebench policy serve`): binds loopback by default; set `FORGEBENCH_POLICY_ADMIN_TOKEN` and `FORGEBENCH_POLICY_READONLY_TOKEN` when exposing beyond localhost. Paths in API requests are confined to `--repo`.
- **GitHub App** (`forgebench github-app serve`): requires `FORGEBENCH_GITHUB_WEBHOOK_SECRET`. Posture enforcement accepts GitHub Check Run events or HMAC-signed attestations only — not spoofable JSON fields.
- **Bind hardening**: non-loopback binds require `FORGEBENCH_ALLOW_INSECURE_BIND=1`.

## Policy Path Confinement

`extends`, `include`, and `fpl:` references resolve relative to the containing policy file and must stay within the repository root (detected via `.git`). Paths cannot escape to arbitrary filesystem locations.

## Audit and Retention

- Tamper-evident audit chain: `forgebench audit verify`
- Data retention: `forgebench data retention --max-age-days 90`

## Secrets

Required for production self-hosted deployments:

- `FORGEBENCH_GITHUB_WEBHOOK_SECRET` — GitHub App webhooks (min 16 chars)
- `FORGEBENCH_POLICY_ADMIN_TOKEN` — policy service mutations
- `FORGEBENCH_POLICY_READONLY_TOKEN` — policy service read-only (optional)

Do not put secrets, API keys, or credentials in ForgeBench fixtures, guardrails, reports, or calibration cases.

See [docs/security/](docs/security/) and [docs/air-gapped.md](docs/air-gapped.md).
