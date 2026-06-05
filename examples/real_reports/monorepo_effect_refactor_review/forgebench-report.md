# ForgeBench Merge Risk Report

## Merge Posture

REVIEW BEFORE MERGE
- Pre-LLM posture: REVIEW
- Final posture: REVIEW

## Summary

Review before merge. The patch may be valid, but ForgeBench found high-severity risk that needs human review. Deterministic checks were not run.

## Suggested Next Action

Review the listed risks before merge. If the patch was agent-generated, paste repair-prompt.md back into your coding agent.

## Inputs

- Repo: /tmp/example-repo/pingdotgg-t3code
- Diff: dogfood-runs/eo002/t3code-2968-effect/forgebench-output/patch.diff
- Task: dogfood-runs/eo002/t3code-2968-effect/forgebench-output/task.md
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
    - UID: fnd_cabf1ac29888
    - Kind: test_skeptic_weak_test_signal
    - Files: apps/server/src/telemetry/Layers/AnalyticsService.test.ts, apps/server/src/workspace/Layers/WorkspaceFileSystem.test.ts
    - Explanation: The patch changes tests, but the added lines do not show obvious assertion or expectation tokens. That may be fine, but it is a weak static signal for behavior coverage.
    - Suggested fix: Review the tests for real assertions, or add focused assertions for the changed behavior.

### Contract Keeper

- Status: completed
- Summary: Contract risk is already represented by existing static findings.
- Referenced evidence: persistence_schema_changed
- Findings:
  - None.

### Product / Guardrail Reviewer

- Status: completed
- Summary: No additional product or guardrail concern found.
- Findings:
  - None.

### Test Skeptic v2

- Status: skipped
- Summary: LLM review is disabled; Test Skeptic v2 is opt-in.
- Findings:
  - None.

### Regression Hunter

- Status: skipped
- Summary: No removed test assertion lines were present.
- Findings:
  - None.

Skipped LLM-assisted lenses:
- test_skeptic_v2: LLM review is disabled; Test Skeptic v2 is opt-in.
- regression_hunter: No removed test assertion lines were present.


## LLM Review

LLM findings are advisory and do not override deterministic evidence.

LLM review was not run.

## Static Signals

- Changed file count: 42
- Added lines: 182
- Deleted lines: 319
- Tests changed: yes
- Finding counts by severity: HIGH=1, MEDIUM=3, LOW=1

## Changed Files

- apps/desktop/src/app/DesktopAppIdentity.ts
- apps/desktop/src/backend/tailscaleEndpointProvider.ts
- apps/desktop/src/settings/DesktopAppSettings.ts
- apps/desktop/src/settings/DesktopClientSettings.ts
- apps/desktop/src/settings/DesktopSavedEnvironments.ts
- apps/desktop/src/shell/DesktopShellEnvironment.ts
- apps/desktop/src/updates/DesktopUpdates.ts
- apps/server/package.json
- apps/server/src/checkpointing/Layers/CheckpointStore.ts
- apps/server/src/cloud/ManagedEndpointRuntime.ts
- apps/server/src/git/GitManager.ts
- apps/server/src/http.ts
- apps/server/src/orchestration/Layers/ProjectionPipeline.ts
- apps/server/src/project/Layers/ProjectFaviconResolver.ts
- apps/server/src/provider/providerMaintenance.ts
- apps/server/src/review/ReviewService.ts
- apps/server/src/sourceControl/BitbucketApi.ts
- apps/server/src/sourceControl/SourceControlProviderDiscovery.ts
- apps/server/src/sourceControl/SourceControlRepositoryService.ts
- apps/server/src/telemetry/Layers/AnalyticsService.test.ts
- apps/server/src/terminal/Layers/Manager.ts
- apps/server/src/textGeneration/CodexTextGeneration.ts
- apps/server/src/vcs/GitVcsDriver.ts
- apps/server/src/vcs/GitVcsDriverCore.ts
- apps/server/src/workspace/Layers/WorkspaceEntries.ts
- apps/server/src/workspace/Layers/WorkspaceFileSystem.test.ts
- apps/server/src/workspace/Layers/WorkspacePaths.ts
- apps/server/src/ws.ts
- apps/server/tsconfig.json
- infra/relay/scripts/deploy.ts
- infra/relay/src/auth/RelayTokens.ts
- infra/relay/src/environments/ManagedEndpointProvider.ts
- oxlint-plugin-t3code/package.json
- oxlint-plugin-t3code/tsconfig.json
- package.json
- packages/tailscale/src/tailscale.ts
- pnpm-lock.yaml
- pnpm-workspace.yaml
- scripts/build-desktop-artifact.ts
- scripts/mobile-native-static-check.ts
- scripts/package.json
- apps/server/src/terminal/Layers/BunPTY.ts

## High-Confidence Issues

### Dependency surface changed

- Severity: MEDIUM
- Confidence: HIGH
- Evidence: STATIC
- UID: fnd_cfcc7657c16a
- Kind: dependency_surface_changed
- Files: apps/server/package.json, oxlint-plugin-t3code/package.json, package.json, pnpm-lock.yaml, scripts/package.json
- Evidence snippets:
  - Dependency manifest or lockfile changed: apps/server/package.json
  - Dependency manifest or lockfile changed: oxlint-plugin-t3code/package.json
  - Dependency manifest or lockfile changed: package.json
  - Dependency manifest or lockfile changed: pnpm-lock.yaml
  - Dependency manifest or lockfile changed: scripts/package.json
- Explanation: The patch changes dependency manifests or lockfiles. Dependency changes can affect install behavior, runtime behavior, and supply-chain exposure.
- Suggested fix: Confirm the dependency change is required, review the lockfile impact, and run the relevant build and tests.

### Patch touches a broad file surface

- Severity: MEDIUM
- Confidence: HIGH
- Evidence: STATIC
- UID: fnd_220507fdc273
- Kind: broad_file_surface
- Files: apps/desktop/src/app/DesktopAppIdentity.ts, apps/desktop/src/backend/tailscaleEndpointProvider.ts, apps/desktop/src/settings/DesktopAppSettings.ts, apps/desktop/src/settings/DesktopClientSettings.ts, apps/desktop/src/settings/DesktopSavedEnvironments.ts, apps/desktop/src/shell/DesktopShellEnvironment.ts, apps/desktop/src/updates/DesktopUpdates.ts, apps/server/package.json, apps/server/src/checkpointing/Layers/CheckpointStore.ts, apps/server/src/cloud/ManagedEndpointRuntime.ts, apps/server/src/git/GitManager.ts, apps/server/src/http.ts, apps/server/src/orchestration/Layers/ProjectionPipeline.ts, apps/server/src/project/Layers/ProjectFaviconResolver.ts, apps/server/src/provider/providerMaintenance.ts, apps/server/src/review/ReviewService.ts, apps/server/src/sourceControl/BitbucketApi.ts, apps/server/src/sourceControl/SourceControlProviderDiscovery.ts, apps/server/src/sourceControl/SourceControlRepositoryService.ts, apps/server/src/telemetry/Layers/AnalyticsService.test.ts, apps/server/src/terminal/Layers/Manager.ts, apps/server/src/textGeneration/CodexTextGeneration.ts, apps/server/src/vcs/GitVcsDriver.ts, apps/server/src/vcs/GitVcsDriverCore.ts, apps/server/src/workspace/Layers/WorkspaceEntries.ts, apps/server/src/workspace/Layers/WorkspaceFileSystem.test.ts, apps/server/src/workspace/Layers/WorkspacePaths.ts, apps/server/src/ws.ts, apps/server/tsconfig.json, infra/relay/scripts/deploy.ts, infra/relay/src/auth/RelayTokens.ts, infra/relay/src/environments/ManagedEndpointProvider.ts, oxlint-plugin-t3code/package.json, oxlint-plugin-t3code/tsconfig.json, package.json, packages/tailscale/src/tailscale.ts, pnpm-lock.yaml, pnpm-workspace.yaml, scripts/build-desktop-artifact.ts, scripts/mobile-native-static-check.ts, scripts/package.json, apps/server/src/terminal/Layers/BunPTY.ts
- Evidence snippets:
  - 42 files changed
- Explanation: The patch changes more than 10 files. Broad patches are harder to review and more likely to contain unrelated changes.
- Suggested fix: Split unrelated changes, reduce the patch scope, or provide a clear review map for the touched areas.


## Medium / Low Confidence Risks

### Build or configuration surface changed

- Severity: MEDIUM
- Confidence: MEDIUM
- Evidence: STATIC
- UID: fnd_a6f6d281a486
- Kind: build_config_changed
- Files: apps/server/tsconfig.json, oxlint-plugin-t3code/tsconfig.json
- Evidence snippets:
  - Build or configuration file changed: apps/server/tsconfig.json
  - Build or configuration file changed: oxlint-plugin-t3code/tsconfig.json
- Explanation: The patch changes build, CI, package, or platform configuration. These files can change behavior outside the code paths touched by the task.
- Suggested fix: Review the configuration change separately and run the build or CI path it affects.

### Persistence or schema behavior may have changed

- Severity: HIGH
- Confidence: MEDIUM
- Evidence: STATIC
- UID: fnd_850d53d119f3
- Kind: persistence_schema_changed
- Files: apps/desktop/src/app/DesktopAppIdentity.ts, apps/server/src/checkpointing/Layers/CheckpointStore.ts
- Evidence snippets:
  - Persistence, schema, model, or migration file changed: apps/desktop/src/app/DesktopAppIdentity.ts
  - Persistence, schema, model, or migration file changed: apps/server/src/checkpointing/Layers/CheckpointStore.ts
- Explanation: The patch changes a likely persistence, schema, model, or migration file. If no corresponding test file changed, data behavior may have changed without regression coverage.
- Suggested fix: Review the data model impact, verify migration behavior, and add tests around persistence compatibility.

### Test changes do not show a clear assertion signal

- Severity: LOW
- Confidence: LOW
- Evidence: REVIEWER
- UID: fnd_cabf1ac29888
- Kind: test_skeptic_weak_test_signal
- Files: apps/server/src/telemetry/Layers/AnalyticsService.test.ts, apps/server/src/workspace/Layers/WorkspaceFileSystem.test.ts
- Evidence snippets:
  - Test files changed, but added test lines do not include common assertion tokens.
  - Weak assertion signal in test file: apps/server/src/telemetry/Layers/AnalyticsService.test.ts
  - Weak assertion signal in test file: apps/server/src/workspace/Layers/WorkspaceFileSystem.test.ts
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
