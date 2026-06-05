# Changelog

## 0.9.0 — 2026-06-05

- Published to PyPI as `forgebench==0.9.0` with README-on-PyPI metadata and Apache-2.0 license.
- Added `forgebench doctor` for first-run install and tooling checks.
- `review-pr --run-checks` now requires `--checkout-pr` so checks never run against the wrong checkout.
- GitHub Action: `run-checks: "true"` automatically adds `--checkout-pr`.
- CI: wheel install smoke test verifies `pip install` and `forgebench doctor`.

## Unreleased

- EO-004 (LLM provider): OpenAI-compatible built-in LLM provider (`--llm-provider openai`, `FORGEBENCH_LLM_API_KEY`), and `FORGEBENCH_LLM_COMMAND` default for command provider.
- EO-003: Production hardening and CI polish — SARIF output, GitHub Check Run annotations (`review-pr --check-run`), `forgebench validate`, Security Reviewer v0, trust model docs, and EO-002 generic-mode noise fixes.
- EO-002: Dogfooded 10 real agent PRs; added `dogfood_runs/eo002-2026-06-05/`, 10 golden cases, and `examples/real_reports/` anonymized artifacts.
- Sprint 12A: Bumped package version to `0.8.0`, added the narrow Regression Hunter lens for potentially load-bearing assertion removal, added synthetic Regression Hunter golden cases, and added calibration posture/finding/lens summaries. Real anonymized PR corpus work remains blocked pending approved source material.
- Sprint 11: Bumped package version to `0.7.0`, added a safe-default GitHub Action wrapper, simplified install docs, and hardened security/trust-boundary documentation.
- Sprint 10: Bumped package version to `0.6.0`, bumped JSON schema to `1.1.0`, added stable finding UIDs/kinds, local-only feedback logging, and a dogfood feedback summary script.
- Sprint 9: Added trigger-gated Test Skeptic v2 LLM lens, LLM lens skip metadata, and LLM threat model docs.
- Sprint 8: Added `forgebench init`, synthetic sample reports for first-run UX, and repair prompt diff hunk context.
- Sprint 7: Added Apache-2.0 license metadata, PyPI package metadata, release workflow scaffolding, CLI version support, JSON schema versioning, PyYAML guardrail parsing, and heuristic review lens naming.
- Sprint 6.1: Calibrated Phase 1 review heuristics to reduce test, read-model, asset, and docs noise.
- Sprint 6: Added Phase 1 review routing for scope, tests, contracts, and product guardrails.
- Sprint 5.2: Added optional safe PR worktree checkout for deterministic checks.
- Sprint 5: Added GitHub PR URL intake through the local GitHub CLI and PR-comment-ready output.
- Sprint 4: Added optional evidence-constrained LLM review through local mock/command providers.
- Sprint 3: Added Guardrails v2 policy calibration with path categories, suppressions, and posture ceilings.
- Sprint 1: Added the local `forgebench review` CLI, unified diff parsing, static risk findings, Markdown/JSON reports, and repair prompts.
- Sprint 1.1: Hardened diff parsing, posture rules, report quality, repair prompts, realistic fixtures, and local dogfood documentation.
- Sprint 2: Added opt-in deterministic local check execution for build, test, lint, typecheck, and custom checks.
- Sprint 2.1: Added the golden corpus calibration runner, artifact validation, and manual dogfood log template.
- Sprint 2.2: Added GitHub Actions CI, repo hygiene docs, install validation, and GitHub publication preparation.
