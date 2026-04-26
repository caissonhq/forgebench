# ForgeBench Merge Risk Report

## Merge Posture

BLOCK MERGE
- Pre-LLM posture: BLOCK
- Final posture: BLOCK

## Summary

Do not merge yet. The patch changes likely persistence or schema behavior without corresponding test coverage. Deterministic checks were not run.

## Suggested Next Action

Do not merge yet. Run the repair prompt, regenerate the diff, and rerun ForgeBench.

## Inputs

- Repo: .
- Diff: examples/sample_report/block_case/patch.diff
- Task: examples/sample_report/block_case/task.md
- Guardrails: examples/sample_report/block_case/forgebench.yml

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
- Summary: No additional scope concern found from task text and changed files.
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
- Summary: Found guardrail-related review concerns grounded in configured project policy.
- Referenced evidence: high_risk_guardrail_file
- Findings:
  - MEDIUM: Patch touches protected product or architecture behavior
    - Confidence: HIGH
    - Evidence: REVIEWER
    - Files: db/migrations/20260426_add_payment_receipts.sql
    - Explanation: The patch touches files that this repo marks as tied to protected product or architecture behavior. This needs review against the guardrails; it is not automatically a violation.
    - Suggested fix: Review the changed files against the protected behavior list and add focused tests or reduce scope if needed.

### Test Skeptic v2

- Status: skipped
- Summary: No test files with added lines were present.
- Findings:
  - None.

Skipped LLM-assisted lenses:
- test_skeptic_v2: No test files with added lines were present.


## LLM Review

LLM findings are advisory and do not override deterministic evidence.

LLM review was not run.

## Static Signals

- Changed file count: 1
- Added lines: 19
- Deleted lines: 0
- Tests changed: no
- Finding counts by severity: HIGH=2, MEDIUM=1

## Changed Files

- db/migrations/20260426_add_payment_receipts.sql

## High-Confidence Issues

### Persistence or schema behavior may have changed

- Severity: HIGH
- Confidence: HIGH
- Evidence: STATIC
- Files: db/migrations/20260426_add_payment_receipts.sql
- Evidence snippets:
  - Persistence, schema, model, or migration file changed: db/migrations/20260426_add_payment_receipts.sql
  - No likely test file changed in this patch.
- Explanation: The patch changes a likely persistence, schema, model, or migration file. If no corresponding test file changed, data behavior may have changed without regression coverage.
- Suggested fix: Review the data model impact, verify migration behavior, and add tests around persistence compatibility.

### High-risk project area changed

- Severity: HIGH
- Confidence: HIGH
- Evidence: STATIC
- Files: db/migrations/20260426_add_payment_receipts.sql
- Evidence snippets:
  - High-risk guardrail pattern '**/migrations/**' matched db/migrations/20260426_add_payment_receipts.sql
- Explanation: The patch changes files matched by high-risk project guardrails. These areas usually encode protected behavior or fragile architecture and need deliberate review before merge.
- Suggested fix: Review the changed high-risk files against the original task and add focused tests or reduce the patch scope if the changes are not required.

### Patch touches protected product or architecture behavior

- Severity: MEDIUM
- Confidence: HIGH
- Evidence: REVIEWER
- Files: db/migrations/20260426_add_payment_receipts.sql
- Evidence snippets:
  - Project protected_behavior is configured.
  - Patch hit configured high- or medium-risk guardrail paths.
  - Protected behavior: Tax calculation trust must be preserved
  - Protected behavior: Paid state must distinguish Federal and California payments
- Explanation: The patch touches files that this repo marks as tied to protected product or architecture behavior. This needs review against the guardrails; it is not automatically a violation.
- Suggested fix: Review the changed files against the protected behavior list and add focused tests or reduce scope if needed.


## Medium / Low Confidence Risks

No medium, low, or advisory findings found.

## Guardrail Review

Protected behavior:
- Tax calculation trust must be preserved
- Paid state must distinguish Federal and California payments

Guardrail hits:
- High-risk guardrail pattern '**/migrations/**' matched db/migrations/20260426_add_payment_receipts.sql

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
