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

Only run `--run-checks` against trusted repositories and trusted `forgebench.yml` files.

### `--post-comment`

PR comments are never posted by default. ForgeBench posts to GitHub only when `--post-comment` is explicitly passed.

### `--llm-command`

`--llm-review --llm-provider command` executes a user-supplied local command. This can be dangerous if pointed at untrusted scripts or PR-provided files. Only use command providers you trust.

See [docs/llm-threat-model.md](docs/llm-threat-model.md) for the LLM threat model and mitigations.

### PR Worktrees

`review-pr --checkout-pr` uses a temporary git worktree so deterministic checks can run against PR code without mutating the main checkout.

ForgeBench should not run `git reset`, `git clean`, `git checkout`, `git merge`, or `git rebase` in your main checkout. If ForgeBench is interrupted with Ctrl-C or the process is killed, a temporary worktree or temporary ref may remain and require manual cleanup.

### Feedback

`forgebench feedback` writes local JSONL. No feedback telemetry, analytics, or reports are uploaded anywhere.

## Secrets

Do not put secrets, API keys, or credentials in ForgeBench fixtures, guardrails, reports, or calibration cases.
