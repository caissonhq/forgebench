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

- No hosted service.
- No GitHub App or OAuth flow.
- No dashboard.
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
- The GitHub Action wrapper packages the local CLI for workflows. It is not a hosted GitHub App.
- Real anonymized sample reports are still required before broader public beta. Sprint 8 includes synthetic sample reports for first-run UX only.
- Real anonymized PR corpus remains blocked pending approved source material. Sprint 12A implements the Regression Hunter lens and calibration summary only.
- Current golden corpus count: 37 synthetic or fixture-based cases, 0 real anonymized PR cases.
- Generic mode is intentionally less strict for unconfigured repos; teams should still add `forgebench.yml` before relying on strict posture decisions.
- Feedback is local-only and useful for alpha dogfood, but ForgeBench does not aggregate or upload feedback anywhere. Feedback suggestions do not automatically tune future runs.

## Required Before CAI-5 Done

- CAI-7 Phase 1 dogfood accepted.
- CAI-9 CLI alpha intake considered complete or explicitly split from hosted OAuth.
- README and public site updated to match current CLI capabilities.
- At least one real PR review with `--checkout-pr --run-checks` completed.
- Reviewer noise judged acceptable on real local diffs.

## Deferred To Phase 2 Reviewers

- Security Reviewer.
- Dependency Watcher as a standalone reviewer.
- Broader regression analysis beyond load-bearing assertion removal.
- Repo Convention Reviewer.
- Any fuller reviewer/persona system.

## Recommended Next Dogfood Plan

- Run ForgeBench on one active AI-generated app diff per week.
- Compare reviewer-enabled output with `--no-reviewers` for the next few serious patches.
- Log noisy static findings separately from noisy reviewer findings.
- Record accepted/dismissed/wrong finding feedback locally and summarize it with `scripts/dogfood_summary.py`.
- Use `forgebench feedback --suggest-guardrails` to draft candidate suppressions, then review them manually before editing `forgebench.yml`.
- Add golden cases whenever dogfood exposes a false positive or missed review concern.
- Keep deterministic check coverage explicit in `forgebench.yml` for repos where build/test commands are cheap and trusted.
