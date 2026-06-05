# ForgeBench Trust Model

ForgeBench is a local CLI that reviews diffs before merge. It does not prove code is safe. It highlights merge risk before AI-generated code reaches main.

This document explains what ForgeBench trusts, what it does not trust, and how to run it safely in CI and on pull requests.

## Trust Boundaries

| Surface | Default behavior | Trust assumption |
| --- | --- | --- |
| Unified diff + task prompt | Always read | Diff and task are review inputs only; not executed |
| `forgebench.yml` parsing | Passive `yaml.safe_load` | YAML is data, not code |
| `forgebench.yml` checks | Runs only with `--run-checks` | Check commands are trusted shell execution |
| PR worktree checkout | Optional with `--checkout-pr` | Git operations stay in a temporary worktree |
| PR comments | Off unless `--post-comment` | Writes to GitHub only when explicitly requested |
| GitHub Check Runs | Off unless `--check-run` | Posts annotations only when explicitly requested |
| LLM command provider | Off unless `--llm-review` | User-supplied command may execute arbitrary local code |
| Feedback JSONL | Local append-only file | Never uploaded by ForgeBench |

## Fork and Untrusted Pull Requests

ForgeBench does not authenticate PR authors. Treat fork PRs like any other untrusted input.

### `forgebench.yml` from the PR branch

`forgebench.yml` may contain shell commands under `checks`. Do not run `--run-checks` using a PR-head `forgebench.yml` unless you intentionally trust that branch.

Recommended CI pattern:

1. Keep `forgebench.yml` on the base branch under team review.
2. Pass `--guardrails .github/forgebench.yml` or another trusted path in CI.
3. Use `--checkout-pr` only to run checks against PR code, not to load PR-branch guardrails.

The GitHub Action uses the checked-out repository guardrails path. In fork workflows, pin guardrails to a trusted base-branch file or disable `run-checks`.

### Check execution

`--run-checks` executes commands from the selected guardrails file in the repository checkout used for review. When combined with `--checkout-pr`, commands run in a temporary PR worktree.

Only enable this for repositories and guardrails files you trust.

### LLM review

`--llm-review --llm-provider command` executes a user-supplied local command with review bundle data on stdin. Do not point this at untrusted scripts or PR-provided executables.

See [llm-threat-model.md](llm-threat-model.md) for the LLM threat model.

## Evidence Hierarchy

ForgeBench ranks evidence in this order:

1. Deterministic checks
2. Static risk signals
3. Guardrails policy
4. Heuristic review lenses, including Security Reviewer v0
5. Optional LLM review

Deterministic failures are never downgraded by policy calibration or advisory lenses. Security Reviewer v0 is deterministic pattern matching on added lines; it is not a substitute for secret scanners or SAST.

## Security Reviewer v0

Security Reviewer v0 is a narrow, deterministic lens. It flags:

- Likely secrets or credentials in added lines
- Dangerous imports or dynamic execution patterns in added lines

It does not perform dataflow analysis, dependency CVE lookup, or sandboxed execution. Findings are review signals, not proof of compromise.

## CI Outputs

ForgeBench can emit:

- Markdown report
- JSON report
- SARIF report for code scanning integrations
- GitHub Check Run annotations when `--check-run` is passed

SARIF and Check Runs surface file-level findings for human review. They do not change ForgeBench posture rules by themselves.

## Operator Checklist

Before enabling ForgeBench in CI on external contributions:

- [ ] Pin guardrails to a trusted file path
- [ ] Leave `run-checks` off for fork PRs unless guardrails are trusted
- [ ] Leave `post-comment` and `check-run` opt-in
- [ ] Do not pass untrusted `--llm-command` values
- [ ] Store secrets outside the repo and outside ForgeBench fixtures
- [ ] Review SARIF/Check Run output as signals, not merge gates by default

## Related Docs

- [SECURITY.md](../SECURITY.md)
- [forgebench-yml-schema.md](forgebench-yml-schema.md)
- [llm-threat-model.md](llm-threat-model.md)