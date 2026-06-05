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

- Repo: /tmp/forgebench-eo002-clones/tsumi233-cc-switch
- Diff: /Users/davidhorton/Developer/caissonhq/projects/forgebench/dogfood_runs/eo002-2026-06-05/tsumi233-cc-switch-1/forgebench-output/patch.diff
- Task: /Users/davidhorton/Developer/caissonhq/projects/forgebench/dogfood_runs/eo002-2026-06-05/tsumi233-cc-switch-1/forgebench-output/task.md
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
- Summary: No additional test coverage concern found.
- Findings:
  - None.

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
- Summary: Added test lines already include common assertion tokens.
- Findings:
  - None.

### Regression Hunter

- Status: skipped
- Summary: No removed test assertion lines were present.
- Findings:
  - None.

Skipped LLM-assisted lenses:
- test_skeptic_v2: Added test lines already include common assertion tokens.
- regression_hunter: No removed test assertion lines were present.


## LLM Review

LLM findings are advisory and do not override deterministic evidence.

LLM review was not run.

## Static Signals

- Changed file count: 22
- Added lines: 895
- Deleted lines: 29
- Tests changed: yes
- Finding counts by severity: HIGH=1, MEDIUM=1, ADVISORY=1

## Changed Files

- pnpm-workspace.yaml
- src-tauri/src/database/dao/proxy.rs
- src-tauri/src/database/mod.rs
- src-tauri/src/database/schema.rs
- src-tauri/src/database/tests.rs
- src-tauri/src/proxy/body_filter.rs
- src-tauri/src/proxy/forwarder.rs
- src-tauri/src/proxy/handler_context.rs
- src-tauri/src/proxy/server.rs
- src-tauri/src/proxy/types.rs
- src/components/proxy/AutoFailoverConfigPanel.tsx
- src/components/proxy/ProxyPanel.tsx
- src/i18n/locales/en.json
- src/i18n/locales/ja.json
- src/i18n/locales/zh-TW.json
- src/i18n/locales/zh.json
- src/types/proxy.ts
- src-tauri/src/proxy/handlers.rs
- src-tauri/src/proxy/providers/streaming_codex_chat.rs
- src-tauri/src/proxy/providers/transform_codex_chat.rs
- src-tauri/src/proxy/response_processor.rs
- src-tauri/tauri.conf.json

## High-Confidence Issues

### Patch touches a broad file surface

- Severity: MEDIUM
- Confidence: HIGH
- Evidence: STATIC
- UID: fnd_1f8d591373be
- Kind: broad_file_surface
- Files: pnpm-workspace.yaml, src-tauri/src/database/dao/proxy.rs, src-tauri/src/database/mod.rs, src-tauri/src/database/schema.rs, src-tauri/src/database/tests.rs, src-tauri/src/proxy/body_filter.rs, src-tauri/src/proxy/forwarder.rs, src-tauri/src/proxy/handler_context.rs, src-tauri/src/proxy/server.rs, src-tauri/src/proxy/types.rs, src/components/proxy/AutoFailoverConfigPanel.tsx, src/components/proxy/ProxyPanel.tsx, src/i18n/locales/en.json, src/i18n/locales/ja.json, src/i18n/locales/zh-TW.json, src/i18n/locales/zh.json, src/types/proxy.ts, src-tauri/src/proxy/handlers.rs, src-tauri/src/proxy/providers/streaming_codex_chat.rs, src-tauri/src/proxy/providers/transform_codex_chat.rs, src-tauri/src/proxy/response_processor.rs, src-tauri/tauri.conf.json
- Evidence snippets:
  - 22 files changed
- Explanation: The patch changes more than 10 files. Broad patches are harder to review and more likely to contain unrelated changes.
- Suggested fix: Split unrelated changes, reduce the patch scope, or provide a clear review map for the touched areas.


## Medium / Low Confidence Risks

### Persistence or schema behavior may have changed

- Severity: HIGH
- Confidence: MEDIUM
- Evidence: STATIC
- UID: fnd_e3046b7a523b
- Kind: persistence_schema_changed
- Files: src-tauri/src/database/dao/proxy.rs, src-tauri/src/database/mod.rs, src-tauri/src/database/schema.rs, src-tauri/src/database/tests.rs
- Evidence snippets:
  - Persistence, schema, model, or migration file changed: src-tauri/src/database/dao/proxy.rs
  - Persistence, schema, model, or migration file changed: src-tauri/src/database/mod.rs
  - Persistence, schema, model, or migration file changed: src-tauri/src/database/schema.rs
  - Persistence, schema, model, or migration file changed: src-tauri/src/database/tests.rs
- Explanation: The patch changes a likely persistence, schema, model, or migration file. If no corresponding test file changed, data behavior may have changed without regression coverage.
- Suggested fix: Review the data model impact, verify migration behavior, and add tests around persistence compatibility.

### User-facing copy or UI surface changed

- Severity: ADVISORY
- Confidence: LOW
- Evidence: STATIC
- UID: fnd_2f6bf3bbbda7
- Kind: ui_copy_changed
- Files: src/components/proxy/AutoFailoverConfigPanel.tsx, src/components/proxy/ProxyPanel.tsx
- Evidence snippets:
  - Likely user-facing, documentation, or UI file changed: src/components/proxy/AutoFailoverConfigPanel.tsx
  - Likely user-facing, documentation, or UI file changed: src/components/proxy/ProxyPanel.tsx
- Explanation: The patch touches files that often affect user-facing copy, documentation, or UI. This is not automatically a defect, but it deserves product review when relevant.
- Suggested fix: Review the changed UI or copy for accuracy, tone, and unintended product behavior.


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
