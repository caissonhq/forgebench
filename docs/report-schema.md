# ForgeBench JSON Report Schema

Current schema version: `1.0.0`

ForgeBench writes `forgebench-report.json` as a stable machine-readable report for local tooling and future integrations.

ForgeBench will only break this schema with a major schema version bump.

## Top-Level Fields

- `schema_version`: string. Current value is `1.0.0`.
- `posture`: string enum. Final merge posture.
- `pre_llm_posture`: string enum. Posture before optional LLM review.
- `final_posture`: string enum. Same value as `posture`.
- `summary`: string. Human-readable posture summary.
- `task_summary`: string. Task text supplied to ForgeBench.
- `changed_files`: array of strings. Paths from the parsed diff.
- `findings`: array of finding objects.
- `static_signals`: object. Deterministic static signal summary.
- `guardrail_hits`: array of strings. Guardrail match evidence.
- `deterministic_checks`: object. Check runner request, results, and summary.
- `policy`: object. Guardrails v2 policy decision.
- `specialized_reviewers`: object. Historical field for Phase 1 review-lens results.
- `llm_review`: object. Optional LLM review result.
- `pr_checkout`: object. PR worktree checkout metadata.
- `generated_at`: string. ISO-8601 generation timestamp.

## Enum Values

`posture`, `pre_llm_posture`, and `final_posture`:

- `BLOCK`
- `REVIEW`
- `LOW_CONCERN`

Finding `severity`:

- `BLOCKER`
- `HIGH`
- `MEDIUM`
- `LOW`
- `ADVISORY`

Finding `confidence`:

- `HIGH`
- `MEDIUM`
- `LOW`

Finding `evidence_type`:

- `DETERMINISTIC`
- `STATIC`
- `REVIEWER`
- `LLM`
- `INFERRED`
- `SPECULATIVE`

Deterministic check `status`:

- `PASSED`
- `FAILED`
- `TIMED_OUT`
- `SKIPPED`
- `NOT_CONFIGURED`
- `ERROR`

LLM review `status`:

- `completed`
- `skipped`
- `failed`

Review lens `status` under `specialized_reviewers.results`:

- `completed`
- `skipped`
- `failed`

## Notes On Review Lenses

The JSON field `specialized_reviewers` is historical and will be renamed in schema `2.0`. User-facing copy calls these Heuristic review lenses in schema `1.x`.

Phase 1 review lenses are deterministic heuristics. They route attention to risk. They do not perform semantic human-level code review.

## Stability

Within schema `1.x`, consumers can rely on the documented top-level keys continuing to exist. New nested fields may be added when they do not change the meaning of existing fields.
