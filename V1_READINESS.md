# ForgeBench V1 Readiness

ForgeBench reviews AI-generated diffs before they hit main.

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.

## Current Capabilities

- Local diff review from a unified git patch and original task prompt.
- GitHub PR URL intake through the local GitHub CLI.
- Docker-based GitHub Action wrapper for pull request workflows.
- Optional safe PR worktree checkout for deterministic checks.
- Optional deterministic local build/test/lint/typecheck/custom checks.
- Static risk findings for tests, dependencies, config, persistence/schema, generated files, UI/copy, and broad file surface.
- Generic first-run mode when no `forgebench.yml` is present, with visible report guidance and less punitive unconfigured path heuristics.
- `forgebench init` presets for Python, Node, Next.js, Swift, and Rust starter guardrails.
- Guardrails v2 policy calibration with path categories, suppressions, severity/confidence overrides, and posture ceilings.
- Phase 1 heuristic review lenses:
  - Scope Auditor
  - Test Skeptic
  - Contract Keeper
  - Product / Guardrail Reviewer
- Phase 1.5 Test Skeptic v2 LLM-assisted lens, gated by deterministic weak-test triggers and `--llm-review`.
- Narrow Phase 2 Regression Hunter lens for potentially load-bearing assertion removal.
- Optional evidence-constrained LLM review through a local command provider.
- Markdown report, JSON report, repair prompt, and PR-comment-ready summary.
- Stable finding UIDs for local dogfood feedback.
- Local-only feedback logging, dogfood feedback summaries, and guardrail tuning suggestions.
- Golden corpus calibration with posture distribution, finding-kind counts, and review-lens fire-rate summaries.
- Synthetic, human-approved sample reports for first-run UX.
- Shared policy layers (`extends`, `include`, `FORGEBENCH_ORG_POLICY`) for Team/Enterprise guardrails.
- Local policy dashboard skeleton export via `forgebench dashboard`.
- CI recipes for GitLab, CircleCI, and Jenkins; production-grade VS Code extension and JetBrains plugin with onboarding wizards, findings sidebar/tool window, and repair prompts.
- EO-012 (2026-06-05): Professional UX — `forgebench demo`, `forgebench status`, `forgebench init --enterprise`, rich CLI output with `--explain`, doctor onboarding checklist, MkDocs Material docs site (`mkdocs.yml` + `site-docs/`).
- EO-013 (2026-06-05): Go-to-market — `forgebench license` (activate/check/status/report), product analytics (`forgebench analytics`), usage dashboard, quota hooks, release automation (multi-platform wheels, SBOM, attestations, Homebrew formula, VS Code Marketplace workflow), sales + customer success kits.
- EO-014 (2026-06-06): Adoption velocity — `forgebench quickstart`, `forgebench team init`, presets gallery (`forgebench presets`), `forgebench share-report`, doctor adoption checklist, milestone analytics, GitHub App install auto-config, install-methods + design-partner docs, GitHub Discussions templates.
- Self-hosted GitHub App kit for org-level policy enforcement (`forgebench github-app`).
- SOC 2-style security documentation pack (`docs/security/`) with controls matrix and evidence mapping.
- Enterprise security hardening (EO-011): path confinement, trusted guardrails for checks, webhook attestation, RBAC, tamper-evident audit chain, data retention.
- Self-hosted deployment skeletons (`deployments/`) and air-gapped install guide.
- Supply chain security: pip-audit CI, SBOM generation, dependabot, locked requirements.
- Structured JSON logging and optional OTEL/Sentry hooks.
- Public roadmap, contribution program, Early Access launch prep, and pricing tiers.
- Semantic AST diff analysis (Python/TypeScript/Rust) with cross-file behavioral signals.
- Behavioral Skeptic reviewer, mutation plan skeleton, LLM ensemble, and prove-it mode skeleton.

## Evidence Hierarchy

1. Deterministic checks
2. Static risk signals
3. Guardrails policy
4. Heuristic review lenses
5. Optional LLM review

Deterministic failures are never downgraded by lens or policy calibration. Heuristic review lenses add framing and extra review tasks; they do not approve merges.

## Supported Inputs

- Local repository path.
- Unified git diff file.
- Original task prompt file.
- Optional `forgebench.yml` guardrails.
- Optional GitHub PR URL through `gh`.
- Optional local command-provider LLM review.

## Phase 1 Review Lenses

Phase 1 review lenses are deterministic heuristics. They route attention to risk. They do not perform semantic human-level code review.

Scope Auditor checks whether the patch appears to change more than the task required.

Test Skeptic checks whether behavior changes have meaningful test coverage and distinguishes deleted test files from assertion-removal or weak-test signals.

Contract Keeper checks API, type, route, public interface, schema, migration, and read-model contract surfaces. Read/view models are treated as contract risk, not persistence/schema risk, unless policy explicitly marks them high risk.

Product / Guardrail Reviewer checks configured protected behavior, forbidden patterns, and high/medium risk guardrail paths.

Test Skeptic v2 is an opt-in LLM-assisted lens. It runs only when deterministic triggers show source changes plus tests with added lines but no common assertion tokens. Its findings are advisory, capped at medium severity/confidence, and cannot block merge by themselves.

## Phase 2 Review Lenses

Regression Hunter is the first narrow Phase 2 lens. It only checks for potentially load-bearing assertion removal when source files also change and no obvious replacement assertion is present. It does not perform broad regression detection.

## Deliberate Non-Goals

- No hosted review service (self-hosted GitHub App kit only).
- No hosted GitHub App or OAuth flow for core review.
- No hosted dashboard SaaS (local policy dashboard export skeleton only).
- No billing.
- No auto-fix.
- No auto-merge.
- No numeric safety score.
- No claim that ForgeBench certifies a diff.

## Known Limitations

- The diff parser is pragmatic and targets common local git diffs.
- Static analysis is path and line-pattern based.
- Guardrails v2 is deterministic policy, not semantic product reasoning.
- Phase 1 review lenses are calibrated heuristics, not the full CAI-7 reviewer set.
- `review-pr --run-checks` needs `--checkout-pr` to run checks against the PR worktree.
- Optional LLM review is command-provider only and advisory.
- LLM-assisted lenses are limited to Test Skeptic v2 and optional Regression Hunter refinement when `--llm-review` is configured.
- The GitHub Action wrapper packages the local CLI for workflows. The GitHub App kit is self-hosted; ForgeBench does not operate a hosted App for customer code.
- EO-002 (2026-06-05): 10 real agent PRs dogfooded; 3 anonymized reports in `examples/real_reports/`; 10 `dogfood_*` golden cases added (47 total calibration cases).
- EO-004 (2026-06-05): OpenAI-compatible LLM provider, `FORGEBENCH_LLM_COMMAND` env default, Dependency Watcher v0, Repo Convention Reviewer, improved Test Skeptic, `review_scope` monorepo path filters, richer repair prompts.
- EO-005 (2026-06-05): Cursor rule + MCP server, Merge Risk Benchmark page, GitHub Marketplace Action prep, beta structured feedback export and `forgebench repair`.
- EO-006 (2026-06-05): Shared policy layers, `forgebench dashboard` skeleton, GitLab/CircleCI/Jenkins CI recipes, VS Code/JetBrains scaffolds, public roadmap and contribution templates.
- EO-007 (2026-06-05): Tree-sitter/stdlib AST semantic diff, Behavioral Skeptic, mutation plan skeleton, multi-model LLM ensemble, prove-it mode skeleton.
- EO-008 (2026-06-05): Opt-in anonymized telemetry, PR outcomes in Merge Risk Benchmark, Review Arena leaderboard, feedback v3, golden case generation from feedback, `forgebench benchmark-dashboard`.
- EO-011 (2026-06-05): Enterprise readiness — security hardening (H1–H4, M1/M4/M5/M6), tamper-evident audit, RBAC, air-gapped deploy skeletons, pip-audit/SBOM CI, data retention.
- EO-013 (2026-06-05): Free/Team/Enterprise packaging in docs/pricing.md; HMAC license keys with seat enforcement; self-hosted analytics dashboard; automated release notes + attestations.
- EO-012 (2026-06-05): VS Code sidebar + onboarding wizard; JetBrains tool window + settings; demo script and GIF capture guide; enterprise init generates org policy, CI, and team onboarding docs.
- EO-010 (2026-06-05): Production IDE extensions, self-hosted GitHub App org enforcement, SOC 2 readiness pack, marketing/Early Access docs, contribution program, pricing tiers.
- EO-009 (2026-06-05): FPL v1, `forgebench policy test/simulate/verify/serve`, formal verification hooks, Grok API integration, policy audit log, and policy versioning.
- EO-003 (2026-06-05): SARIF output, GitHub Check Run annotations, `forgebench validate`, Security Reviewer v0, and `docs/trust-model.md`.
- EO-002 generic-mode noise fixes: suppress markdown/agent-policy `ui_copy_changed`, exclude package/tsconfig/Rust-only persistence misfires.
- Labeled false-positive rate in generic mode: **63.2%** on EO-002 findings before EO-003 noise fixes (dominated by `ui_copy_changed` on markdown/agent-policy PRs).
- Synthetic sample reports remain in `examples/sample_report/` for first-run UX.
- Generic mode is intentionally less strict for unconfigured repos; teams should still add `forgebench.yml` before relying on strict posture decisions.
- Feedback is local-only and useful for alpha dogfood, but ForgeBench does not aggregate or upload feedback anywhere. Feedback suggestions do not automatically tune future runs.

## Distribution (Executive Order 001)

- PyPI package: `forgebench==0.9.0` (`pip install forgebench`)
- First-run check: `forgebench doctor`
- GitHub Action: `run-checks: "true"` automatically enables PR worktree checkout
- CI: `smoke-install` job builds the wheel and verifies install + doctor

## Required Before CAI-5 Done

- CAI-7 Phase 1 dogfood accepted.
- CAI-9 CLI alpha intake considered complete or explicitly split from hosted OAuth.
- README and public site updated to match current CLI capabilities.
- At least one real PR review with `--checkout-pr --run-checks` completed.
- Reviewer noise judged acceptable on real local diffs.

## Deferred To Phase 2 Reviewers

- Security Reviewer beyond v0 pattern matching (dataflow, dependency CVEs, sandboxed execution).
- Dependency Watcher beyond v0 manifest heuristics (CVE lookup, license policy).
- Broader regression analysis beyond load-bearing assertion removal.
- Repo Convention Reviewer beyond debug/TODO pattern matching.
- Any fuller reviewer/persona system.

## Recommended Next Dogfood Plan

- Run ForgeBench on one active AI-generated app diff per week.
- Compare reviewer-enabled output with `--no-reviewers` for the next few serious patches.
- Log noisy static findings separately from noisy reviewer findings.
- Record accepted/dismissed/wrong finding feedback locally and summarize it with `scripts/dogfood_summary.py`.
- Use `forgebench feedback --suggest-guardrails` to draft candidate suppressions, then review them manually before editing `forgebench.yml`.
- Add golden cases whenever dogfood exposes a false positive or missed review concern.
- Keep deterministic check coverage explicit in `forgebench.yml` for repos where build/test commands are cheap and trusted.
