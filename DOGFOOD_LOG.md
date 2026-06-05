# ForgeBench Dogfood Log

Manual product learning from real agent-generated pull requests.

## EO-002 batch — 2026-06-05

**Scope:** 10 real PRs via `forgebench review-pr` (generic mode).  
**Artifacts:** `dogfood_runs/eo002-2026-06-05/` (`runs.json`, `feedback.jsonl`, `feedback-summary.md`, `METRICS.md`).  
**Golden cases:** 10 new `dogfood_*` entries in `examples/golden_cases/`.  
**Public examples:** `examples/real_reports/` (3 anonymized reports).

### Aggregate metrics

See [dogfood_runs/eo002-2026-06-05/METRICS.md](dogfood_runs/eo002-2026-06-05/METRICS.md).

| Metric | Result |
|--------|--------|
| PRs reviewed | 10 |
| Postures | 6 LOW_CONCERN, 4 REVIEW, 0 BLOCK |
| Labeled false-positive rate | **63.2%** (10 dismissed + 2 wrong / 19 findings) |
| Reviewer noise | 4 reviewer findings across 3 PRs; useful when fired, silent on 7 PRs |

---

### 1. caissonhq/forgebench#1 — Docs-only PR intake smoke

- Date: 2026-06-05
- Repo: caissonhq/forgebench (public)
- Original coding agent: internal smoke
- Original task: Docs-only ForgeBench PR intake smoke test
- Diff size: 1 file, +2/-0
- ForgeBench posture: **LOW_CONCERN**
- Findings that were useful: none required
- Findings that were noisy: `ui_copy_changed` on README (dismissed)
- Was the posture right? **Yes**
- Did the repair prompt help? N/A
- Would I have missed anything without ForgeBench? No
- Follow-up: generic-mode markdown suppression

### 2. caissonhq/24hragent#1 — Codex API key cleanup

- Date: 2026-06-05
- Repo: caissonhq/24hragent (private)
- Original coding agent: Codex
- Original task: Load Gemini key from environment; remove hardcoded key pattern
- Diff size: 4 files, +71/-0
- ForgeBench posture: **LOW_CONCERN**
- Findings that were useful: none (clean run)
- Findings that were noisy: none
- Was the posture right? **Yes** — tests updated in same PR
- Did the repair prompt help? N/A
- Would I have missed anything without ForgeBench? Unlikely
- Follow-up: published as `examples/real_reports/agent_env_secret_cleanup_low_concern/`

### 3. vercel/workflow#2238 — Codex environment TOML

- Date: 2026-06-05
- Repo: vercel/workflow (public)
- Original coding agent: Codex
- Original task: Add Codex environment setup
- Diff size: 2 files, +10/-0
- ForgeBench posture: **LOW_CONCERN**
- Findings that were noisy: `ui_copy_changed` (dismissed)
- Was the posture right? **Yes**

### 4. officebeats/beats-pm-kit#15 — Codex browser-first policy

- Date: 2026-06-05
- Repo: officebeats/beats-pm-kit (public)
- Original coding agent: Codex
- Original task: Add Codex browser-first policy + tests (per PR body)
- Diff size: 4 files, +99/-0
- ForgeBench posture: **LOW_CONCERN**
- Findings that were noisy: `ui_copy_changed` (dismissed)
- Was the posture right? **Yes**

### 5. Mohammed-Abdelhady/hyperflow#5 — Codex docs + script drift

- Date: 2026-06-05
- Repo: Mohammed-Abdelhady/hyperflow (public)
- Original coding agent: Codex
- Original task: Clarify Codex Hyperflow invocation
- Diff size: 4 files, +15/-13
- ForgeBench posture: **REVIEW**
- Findings that were useful: `scope_auditor_task_scope_expansion` (accepted); Test Skeptic framing (accepted)
- Findings that were noisy: `ui_copy_changed`; `implementation_without_tests` (no test files in diff, but PR is mostly docs)
- Was the posture right? **Yes** — script path change is worth human eyes
- Did the repair prompt help? Useful as review checklist
- Follow-up: published as `examples/real_reports/agent_docs_scope_review/`

### 6. getbourdon/bourdon#113 — Codex L5 publisher freshness

- Date: 2026-06-05
- Repo: getbourdon/bourdon (public)
- Original coding agent: Codex
- Original task: Separate Codex L5 publisher freshness from manifest staleness
- Diff size: 2 files, +81/-13 (tests per PR body)
- ForgeBench posture: **LOW_CONCERN**
- Findings: none
- Was the posture right? **Yes**

### 7. pingdotgg/t3code#2973 — Cursor Electron fetch

- Date: 2026-06-05
- Repo: pingdotgg/t3code (public)
- Original coding agent: Cursor
- Original task: Use Electron fetch for Clerk IPC proxying
- Diff size: 2 files, +100/-85
- ForgeBench posture: **LOW_CONCERN**
- Findings that were noisy: `ui_copy_changed` (dismissed)
- Was the posture right? **Yes**

### 8. pingdotgg/t3code#2968 — Cursor Effect orElseSucceed refactor

- Date: 2026-06-05
- Repo: pingdotgg/t3code (public)
- Original coding agent: Cursor
- Original task: Refactor recoverable Effect fallbacks
- Diff size: 42 files, +182/-318
- ForgeBench posture: **REVIEW**
- Findings that were useful: `dependency_surface_changed`, `broad_file_surface` (accepted)
- Findings that were wrong: `persistence_schema_changed` (TS/package edits)
- Findings that were noisy: `test_skeptic_weak_test_signal` (tests updated)
- Was the posture right? **Yes**
- Follow-up: published as `examples/real_reports/monorepo_effect_refactor_review/`

### 9. pingdotgg/t3code#2955 — Codex workspace skill autocomplete

- Date: 2026-06-05
- Repo: pingdotgg/t3code (public)
- Original coding agent: Codex
- Original task: Fix Codex workspace skill autocomplete cwd
- Diff size: 22 files, +460/-68
- ForgeBench posture: **REVIEW**
- Findings that were useful: `broad_file_surface` (accepted)
- Findings that were noisy: `ui_copy_changed`, `test_skeptic_weak_test_signal` (dismissed)
- Was the posture right? **Yes**

### 10. tsumi233/cc-switch#1 — Codex chat tool name fallback

- Date: 2026-06-05
- Repo: tsumi233/cc-switch (public)
- Original coding agent: Codex
- Original task: Fix Codex chat tool name fallback in Rust
- Diff size: 22 files, +895/-28
- ForgeBench posture: **REVIEW**
- Findings that were useful: `broad_file_surface` (accepted)
- Findings that were wrong: `persistence_schema_changed` (dismissed as wrong)
- Was the posture right? **Yes**

---

## Entry template (future runs)

- Date:
- Repo:
- Original coding agent:
- Original task:
- Diff size:
- ForgeBench posture:
- Findings that were useful:
- Findings that were noisy:
- Was the posture right?
- Did the repair prompt help?
- Would I have missed anything without ForgeBench?
- Follow-up changes needed:

## Local feedback commands

```bash
forgebench feedback fnd_example123 \
  --status accepted \
  --kind implementation_without_tests \
  --note "caught missing test coverage" \
  --feedback-log dogfood_runs/eo002-2026-06-05/feedback.jsonl
```

```bash
python3 scripts/dogfood_summary.py dogfood_runs/eo002-2026-06-05/feedback.jsonl
```