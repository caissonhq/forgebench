# ForgeBench Merge Risk Report

## Merge Posture

REVIEW BEFORE MERGE
- Pre-LLM posture: REVIEW
- Final posture: REVIEW

## Summary

Review before merge. The patch touches a broad file surface and should be inspected for unrelated changes. Deterministic checks were not run.

## Suggested Next Action

Review the listed risks before merge. If the patch was agent-generated, paste repair-prompt.md back into your coding agent.

## Inputs

- Repo: /tmp/forgebench-eo002-clones/pingdotgg-t3code
- Diff: /Users/davidhorton/Developer/caissonhq/projects/forgebench/dogfood_runs/eo002-2026-06-05/t3code-2955-codex/forgebench-output/patch.diff
- Task: /Users/davidhorton/Developer/caissonhq/projects/forgebench/dogfood_runs/eo002-2026-06-05/t3code-2955-codex/forgebench-output/task.md
- Guardrails: none

## Configuration Mode

Generic review mode.

ForgeBench did not find a forgebench.yml file for this run. Generic heuristics are useful for initial review, but may be noisier than repo-specific guardrails.

Run:

```bash
forgebench init --repo . --out forgebench.yml
```

Then edit the generated guardrails before relying on strict posture decisions.

## PR Checkout

- Status: not requested
- Worktree path: none
- Checks target: not run

## Deterministic Checks

Not run. Re-run with --run-checks to execute configured local verification commands.

## Heuristic Review Lenses

Phase 1 review lenses are deterministic heuristics. They route attention to risk. They do not perform semantic human-level code review.

### Scope Auditor

- Status: completed
- Summary: Broad or scope-sensitive static evidence is already present; no additional scope finding added.
- Referenced evidence: broad_file_surface
- Findings:
  - None.

### Test Skeptic

- Status: completed
- Summary: Found test coverage concerns for the changed behavior.
- Findings:
  - LOW: Test changes do not show a clear assertion signal
    - Confidence: LOW
    - Evidence: REVIEWER
    - UID: fnd_3e8b76cc7439
    - Kind: test_skeptic_weak_test_signal
    - Files: apps/server/src/provider/Layers/ProviderAdapterRegistry.test.ts
    - Explanation: The patch changes tests, but the added lines do not show obvious assertion or expectation tokens. That may be fine, but it is a weak static signal for behavior coverage.
    - Suggested fix: Review the tests for real assertions, or add focused assertions for the changed behavior.

### Contract Keeper

- Status: completed
- Summary: No additional contract-surface concern found.
- Findings:
  - None.

### Product / Guardrail Reviewer

- Status: completed
- Summary: No additional product or guardrail concern found.
- Findings:
  - None.

### Test Skeptic v2

- Status: skipped
- Summary: Added test lines already include common assertion tokens.
- Findings:
  - None.

### Regression Hunter

- Status: skipped
- Summary: Removed test assertions had an obvious assertion replacement in the same file.
- Findings:
  - None.

Skipped LLM-assisted lenses:
- test_skeptic_v2: Added test lines already include common assertion tokens.
- regression_hunter: Removed test assertions had an obvious assertion replacement in the same file.


## LLM Review

LLM findings are advisory and do not override deterministic evidence.

LLM review was not run.

## Static Signals

- Changed file count: 30
- Added lines: 480
- Deleted lines: 92
- Tests changed: yes
- Finding counts by severity: MEDIUM=1, LOW=1, ADVISORY=1

## Changed Files

- apps/server/src/provider/Drivers/ClaudeDriver.ts
- apps/server/src/provider/Drivers/CodexDriver.ts
- apps/server/src/provider/Drivers/CursorDriver.ts
- apps/server/src/provider/Drivers/OpenCodeDriver.ts
- apps/server/src/provider/Layers/CodexProvider.ts
- apps/server/src/provider/Layers/ProviderAdapterRegistry.test.ts
- apps/server/src/provider/Layers/ProviderRegistry.test.ts
- apps/server/src/provider/Layers/ProviderRegistry.ts
- apps/server/src/provider/Services/ProviderRegistry.ts
- apps/server/src/provider/Services/ServerProvider.ts
- apps/server/src/provider/makeManagedServerProvider.test.ts
- apps/server/src/provider/makeManagedServerProvider.ts
- apps/server/src/ws.ts
- apps/web/src/components/ChatView.tsx
- apps/web/src/localApi.test.ts
- apps/web/src/localApi.ts
- packages/contracts/src/ipc.ts
- packages/contracts/src/rpc.ts
- apps/server/src/provider/Drivers/OpenCodeDriver.ts
- apps/web/src/components/ChatView.logic.test.ts
- apps/web/src/components/ChatView.logic.ts
- apps/web/src/components/ChatView.tsx
- apps/web/src/components/ChatView.logic.test.ts
- apps/web/src/components/ChatView.logic.ts
- apps/web/src/components/ChatView.tsx
- apps/web/src/components/ChatView.browser.tsx
- apps/web/src/components/ChatView.tsx
- apps/web/src/environmentApi.ts
- apps/web/src/localApi.test.ts
- packages/contracts/src/ipc.ts

## High-Confidence Issues

### Patch touches a broad file surface

- Severity: MEDIUM
- Confidence: HIGH
- Evidence: STATIC
- UID: fnd_2b622c6c09b6
- Kind: broad_file_surface
- Files: apps/server/src/provider/Drivers/ClaudeDriver.ts, apps/server/src/provider/Drivers/CodexDriver.ts, apps/server/src/provider/Drivers/CursorDriver.ts, apps/server/src/provider/Drivers/OpenCodeDriver.ts, apps/server/src/provider/Layers/CodexProvider.ts, apps/server/src/provider/Layers/ProviderAdapterRegistry.test.ts, apps/server/src/provider/Layers/ProviderRegistry.test.ts, apps/server/src/provider/Layers/ProviderRegistry.ts, apps/server/src/provider/Services/ProviderRegistry.ts, apps/server/src/provider/Services/ServerProvider.ts, apps/server/src/provider/makeManagedServerProvider.test.ts, apps/server/src/provider/makeManagedServerProvider.ts, apps/server/src/ws.ts, apps/web/src/components/ChatView.tsx, apps/web/src/localApi.test.ts, apps/web/src/localApi.ts, packages/contracts/src/ipc.ts, packages/contracts/src/rpc.ts, apps/server/src/provider/Drivers/OpenCodeDriver.ts, apps/web/src/components/ChatView.logic.test.ts, apps/web/src/components/ChatView.logic.ts, apps/web/src/components/ChatView.tsx, apps/web/src/components/ChatView.logic.test.ts, apps/web/src/components/ChatView.logic.ts, apps/web/src/components/ChatView.tsx, apps/web/src/components/ChatView.browser.tsx, apps/web/src/components/ChatView.tsx, apps/web/src/environmentApi.ts, apps/web/src/localApi.test.ts, packages/contracts/src/ipc.ts
- Evidence snippets:
  - 30 files changed
- Explanation: The patch changes more than 10 files. Broad patches are harder to review and more likely to contain unrelated changes.
- Suggested fix: Split unrelated changes, reduce the patch scope, or provide a clear review map for the touched areas.


## Medium / Low Confidence Risks

### User-facing copy or UI surface changed

- Severity: ADVISORY
- Confidence: LOW
- Evidence: STATIC
- UID: fnd_b2956cd24d9d
- Kind: ui_copy_changed
- Files: apps/web/src/components/ChatView.browser.tsx, apps/web/src/components/ChatView.tsx
- Evidence snippets:
  - Likely user-facing, documentation, or UI file changed: apps/web/src/components/ChatView.browser.tsx
  - Likely user-facing, documentation, or UI file changed: apps/web/src/components/ChatView.tsx
- Explanation: The patch touches files that often affect user-facing copy, documentation, or UI. This is not automatically a defect, but it deserves product review when relevant.
- Suggested fix: Review the changed UI or copy for accuracy, tone, and unintended product behavior.

### Test changes do not show a clear assertion signal

- Severity: LOW
- Confidence: LOW
- Evidence: REVIEWER
- UID: fnd_3e8b76cc7439
- Kind: test_skeptic_weak_test_signal
- Files: apps/server/src/provider/Layers/ProviderAdapterRegistry.test.ts
- Evidence snippets:
  - Test files changed, but added test lines do not include common assertion tokens.
  - Weak assertion signal in test file: apps/server/src/provider/Layers/ProviderAdapterRegistry.test.ts
- Explanation: The patch changes tests, but the added lines do not show obvious assertion or expectation tokens. That may be fine, but it is a weak static signal for behavior coverage.
- Suggested fix: Review the tests for real assertions, or add focused assertions for the changed behavior.


## Guardrail Review

Protected behavior:
- None provided.

Guardrail hits:
- None.

## Guardrails Policy

Active categories:
- None.

Suppressed findings:
- None.

Severity/confidence overrides:
- None.

Posture ceiling:
- None.

## Repair Prompt

See repair-prompt.md.
