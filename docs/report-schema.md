# ForgeBench JSON Report Schema

Current schema version: `1.2.0`

ForgeBench writes `forgebench-report.json` as a stable machine-readable report for local tooling and future integrations.

ForgeBench will only break this schema with a major schema version bump.

## Top-Level Fields

- `schema_version`: string. Current value is `1.2.0`.
- `config_mode`: string enum. `configured` when a guardrails file was provided or discovered, `generic` when ForgeBench used generic heuristics only.
- `guardrails_source`: string or null. Path to the guardrails file used for the run, or null in generic mode.
- `first_run_guidance`: boolean. True when the report should show first-run generic-mode guidance.
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

## Finding Objects

Each object in `findings`, `llm_review.findings`, and `specialized_reviewers.findings` includes:

- `uid`: string. Stable finding UID, such as `fnd_3a91c0e88d12`.
- `kind`: string. Logical finding type, such as `implementation_without_tests`.
- `id`: string. Historical alias for `kind` in schema `1.x`.
- `title`: string.
- `severity`: string enum.
- `confidence`: string enum.
- `evidence_type`: string enum.
- `files`: array of changed file paths from the patch.
- `evidence`: array of evidence snippets.
- `reviewer`: string or null.
- `supporting_finding_ids`: array of logical finding kinds referenced by this finding.
- `explanation`: string.
- `suggested_fix`: string.

Stable finding UIDs are deterministic for the same logical kind, file set, evidence type, and reviewer/lens source. They do not include timestamps, output directories, or absolute local machine paths. Logical finding types remain available as `kind` and through the historical `id` alias.

Local feedback recorded with `forgebench feedback` is not part of the report schema. Feedback is stored separately as local JSONL.

## Enum Values

`config_mode`:

- `configured`
- `generic`

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

`specialized_reviewers.metadata.skipped_lenses` records trigger-gated LLM-assisted lenses that did not run and the reason they were skipped. This keeps opt-in LLM behavior auditable without changing the top-level schema.

Test Skeptic v2 findings use `evidence_type: LLM`, are capped at `MEDIUM` severity and `MEDIUM` confidence, and cannot block merge by themselves.

## Stability

Within schema `1.x`, consumers can rely on the documented top-level keys continuing to exist. New nested fields may be added when they do not change the meaning of existing fields.
