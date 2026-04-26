# ForgeBench V1 Readiness

ForgeBench reviews AI-generated diffs before they hit main.

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.

## Current Capabilities

- Local diff review from a unified git patch and original task prompt.
- GitHub PR URL intake through the local GitHub CLI.
- Optional safe PR worktree checkout for deterministic checks.
- Optional deterministic local build/test/lint/typecheck/custom checks.
- Static risk findings for tests, dependencies, config, persistence/schema, generated files, UI/copy, and broad file surface.
- Guardrails v2 policy calibration with path categories, suppressions, severity/confidence overrides, and posture ceilings.
- Phase 1 heuristic review lenses:
  - Scope Auditor
  - Test Skeptic
  - Contract Keeper
  - Product / Guardrail Reviewer
- Optional evidence-constrained LLM review through a local command provider.
- Markdown report, JSON report, repair prompt, and PR-comment-ready summary.
- Golden corpus calibration.

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

## Required Before CAI-5 Done

- CAI-7 Phase 1 dogfood accepted.
- CAI-9 CLI alpha intake considered complete or explicitly split from hosted OAuth.
- README and public site updated to match current CLI capabilities.
- At least one real PR review with `--checkout-pr --run-checks` completed.
- Reviewer noise judged acceptable on real local diffs.

## Deferred To Phase 2 Reviewers

- Security Reviewer.
- Dependency Watcher as a standalone reviewer.
- Regression Hunter.
- Repo Convention Reviewer.
- Any fuller reviewer/persona system.

## Recommended Next Dogfood Plan

- Run ForgeBench on one active AI-generated app diff per week.
- Compare reviewer-enabled output with `--no-reviewers` for the next few serious patches.
- Log noisy static findings separately from noisy reviewer findings.
- Add golden cases whenever dogfood exposes a false positive or missed review concern.
- Keep deterministic check coverage explicit in `forgebench.yml` for repos where build/test commands are cheap and trusted.
