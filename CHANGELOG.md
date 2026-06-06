# Changelog

## 1.0.0 — 2026-06-06

**Public launch.** ForgeBench v1.0 — production-ready local merge-risk review for AI-generated diffs.

### Launch highlights

- `forgebench quickstart`, `forgebench install`, `forgebench team init`, presets gallery, `forgebench share-report`
- Distribution: pip/pipx/Homebrew, binary bundles, macOS `.pkg`, shell completions, VS Code 1.2
- Adoption: doctor checklist, funnel analytics (`funnel_stage`), `forgebench analytics adoption-dashboard`
- Traction: `forgebench feedback --share`, Design Partner program, GitHub Discussions templates
- Enterprise: Team/Enterprise licensing, self-hosted GitHub App kit, SOC2-style security pack
- Evidence hierarchy: deterministic checks → static signals → guardrails → lenses → optional LLM

### Install

```bash
pipx install forgebench==1.0.0
forgebench quickstart
```

See [docs/launch/RELEASE_v1.0.0.md](docs/launch/RELEASE_v1.0.0.md) for full release notes.

## 0.9.0 — 2026-06-05

- Published to PyPI as `forgebench==0.9.0` with README-on-PyPI metadata and Apache-2.0 license.
- Added `forgebench doctor` for first-run install and tooling checks.
- `review-pr --run-checks` now requires `--checkout-pr` so checks never run against the wrong checkout.
- GitHub Action: `run-checks: "true"` automatically adds `--checkout-pr`.
- CI: wheel install smoke test verifies `pip install` and `forgebench doctor`.

## Unreleased

- EO-017 (revenue): Production licensing with online validation server, `license verify`/`upgrade`, Stripe checkout + webhook handler, `forgebench subscribe`/`upgrade`/`portal`/`crm`, customer portal dashboard, CRM pipeline + Linear sync, paid onboarding playbook, pricing page.

## Development history (pre-1.0)

- EO-015 (distribution): `forgebench install` guidance command (detect environment, methods table, shell completions, upgrade path).
- EO-015 (releases): Official binary `.tar.gz` bundles, macOS `.pkg` installer, Homebrew tap automation workflow.
- EO-015 (doctor): Install method detection, pipx recommendation, upgrade path hints across distribution channels.
- EO-015 (marketplace): VS Code extension 1.2 listing polish (icon, keywords, MARKETPLACE.md), JetBrains plugin.xml, GitHub Marketplace listing doc.
- EO-015 (docs): World-class `site-docs/installation.md`, README install badges and comparison table, pip metadata improvements.
- EO-014 (adoption): `forgebench quickstart`, `forgebench team init`, `forgebench init --team`, `forgebench presets list|install|export`, `forgebench share-report`, `forgebench feedback --suggest`.
- EO-014 (doctor): `forgebench doctor --checklist` adoption success checklist and personalized next-step recommendations.
- EO-014 (analytics): Milestone events (`first_review`, `first_team_init`, `first_paid_feature`, etc.) via local adoption state + product analytics.
- EO-014 (GitHub App): Public listing metadata, installation auto-configuration on webhook `installation` events.
- EO-014 (distribution): Install methods docs (pip, pipx, Homebrew, VS Code), presets gallery, design partner program, GitHub Discussions templates.
- EO-013 (GTM): `forgebench license` commands — activate, check, status, report with HMAC keys and seat enforcement.
- EO-013 (analytics): `forgebench analytics` product telemetry (opt-in, separate from review telemetry); self-hosted usage dashboard.
- EO-013 (quotas): Tier-based daily limits for Grok verify, cloud export, policy serve (Enterprise).
- EO-013 (release): Multi-platform release workflow, SBOM, attestations.json, Homebrew formula, release notes automation, VS Code Marketplace workflow.
- EO-013 (sales): One-pager, deck outline, competitive matrix, case study template, launch announcement copy.
- EO-013 (CS): Onboarding playbook, SLA template, support process, usage reporting guide, GitHub Discussions template.
- EO-012 (UX): `forgebench demo`, `forgebench status`, rich CLI output, global `--explain` flag, doctor onboarding checklist.
- EO-012 (enterprise): `forgebench init --enterprise` wizard — org policy, GitHub Actions workflow, trusted CI guardrails, team onboarding docs.
- EO-012 (IDE): VS Code findings sidebar, onboarding wizard, repair prompt clipboard, status bar posture colors; JetBrains tool window, settings, onboarding/status/repair/init actions.
- EO-012 (docs): MkDocs Material site (`mkdocs.yml`, `site-docs/`), demo video script, onboarding GIF guide.
- EO-011 (security): Trusted guardrails enforcement for `review-pr --run-checks`, repo-root policy path confinement, required webhook secrets, signed posture attestation, HTTP/MCP body limits, shell-free LLM command provider.
- EO-011 (compliance): Tamper-evident audit chain (`forgebench audit verify`), data retention (`forgebench data retention`), expanded SOC 2 controls and evidence mapping.
- EO-011 (enterprise): Policy service RBAC tokens, structured JSON logging, Docker Compose + Helm deploy skeletons, air-gapped install guide.
- EO-011 (supply chain): pip-audit CI workflow, SBOM generation, dependabot, `requirements-lock.txt`.
- EO-010 (IDE): Production-grade VS Code extension v1.0.0 (`forgebenchRunner`, policy test, SARIF) and JetBrains Kotlin plugin with Gradle build.
- EO-010 (GitHub App): Self-hosted org policy enforcement kit — `forgebench github-app manifest|enforce|serve`, webhook handler, check-run output.
- EO-010 (security): SOC 2-style readiness pack — controls matrix, audit prep checklist, SOC 2 overview in `docs/security/`.
- EO-010 (launch): Early Access positioning, pricing tiers, and contribution program docs.
- EO-009 (FPL): ForgeBench Policy Language v1 — line-oriented DSL compiling into guardrails policy.
- EO-009 (testing): `forgebench policy test` simulation framework with `examples/policy_tests/`.
- EO-009 (verification): Formal-ish verification hooks and optional Grok API policy verification.
- EO-009 (platform): Policy audit JSONL, version fingerprints, and self-hosted policy service skeleton.
- EO-008 (telemetry): Opt-in local-only anonymized telemetry via `forgebench telemetry` and `FORGEBENCH_TELEMETRY=1`.
- EO-008 (benchmark): Merge Risk Benchmark expanded with anonymized real PR outcomes (`examples/benchmark_outcomes/`).
- EO-008 (arena): Review Arena leaderboard from calibration + PR outcomes.
- EO-008 (feedback): Structured feedback v3 (`severity`, `confidence`, `files`, `outcome_label`, `expected_posture`).
- EO-008 (golden): `forgebench feedback --generate-golden-cases` drafts calibration cases from local feedback.
- EO-008 (dashboard): `forgebench benchmark-dashboard` exports public static HTML + JSON manifest.
- EO-007 (semantic): Tree-sitter/stdlib AST parsing for Python, TypeScript, and Rust with cross-file behavioral diff signals.
- EO-007 (reviewer): Behavioral Skeptic lens for uncovered changed symbols.
- EO-007 (mutation): `forgebench mutation plan` skeleton exporting mutation candidates from semantic diff.
- EO-007 (ensemble): Multi-model LLM ensemble via `FORGEBENCH_LLM_ENSEMBLE_MODELS` and `--llm-ensemble`.
- EO-007 (prove-it): `--prove-it` and `forgebench prove-it` skeleton for evidence checklist + mutation plan export.
- EO-006 (team): Shared policy layers via `extends`, `include`, and `FORGEBENCH_ORG_POLICY`; `team` metadata and `policy_sources` in review output.
- EO-006 (dashboard): `forgebench dashboard` local policy dashboard skeleton (HTML + JSON manifest).
- EO-006 (integrations): GitLab CI, CircleCI, and Jenkins recipes; VS Code and JetBrains IDE plugin scaffolds.
- EO-006 (community): Public [ROADMAP.md](ROADMAP.md), contribution process refresh, GitHub issue/PR templates.
- EO-006 (marketing): [docs/marketing-home.md](docs/marketing-home.md) and EO-006 [SITE_SYNC_NOTES.md](SITE_SYNC_NOTES.md) refresh.
- EO-005 (integrations): Cursor review rule, MCP server, and `forgebench repair` for review → paste repair prompt workflow.
- EO-005 (benchmark): Merge Risk Benchmark page and `forgebench benchmark` CLI over the golden corpus.
- EO-005 (marketplace): GitHub Marketplace listing prep for the ForgeBench Action.
- EO-005 (beta): Public beta onboarding, structured feedback v2, and `forgebench feedback export`.
- EO-004 (LLM provider): OpenAI-compatible built-in LLM provider (`--llm-provider openai`, `FORGEBENCH_LLM_API_KEY`), and `FORGEBENCH_LLM_COMMAND` default for command provider.
- EO-004 (reviewers): Dependency Watcher v0, Repo Convention Reviewer, and improved Test Skeptic with setup-only and paired-test-path signals.
- EO-004 (path filter): Monorepo `review_scope` include/exclude path filters with package-root detection hints.
- EO-004 (repair prompt): Richer repair prompts with review context, repair priority, reviewer summaries, and diff hunk context.
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
