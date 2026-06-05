# EO-002 Dogfood Metrics (2026-06-05)

## Corpus

- Real agent PRs reviewed: **10**
- Agents represented: Codex (7), Cursor (2), mixed Cursor/Codex metadata (1)
- Repos: public OSS + `caissonhq/*` (authenticated clone)
- Mode: generic (`forgebench.yml` not present in target repos)
- Deterministic checks: not run (PR worktree not required for static/reviewer pass)

## Posture distribution

| Posture | Count | Human agreement |
|---------|------:|-----------------|
| LOW_CONCERN | 6 | 6/6 appropriate |
| REVIEW | 4 | 4/4 appropriate |
| BLOCK | 0 | — |

## Finding volume

- Total findings emitted: **19** (1.9 per PR)
- PRs with zero findings: **2** (`caissonhq/24hragent#1`, `getbourdon/bourdon#113`)
- PRs with Phase 1 reviewer findings: **3** (`hyperflow#5`, `t3code#2955`, `t3code#2968`)

## Reviewer noise

| Metric | Value |
|--------|------:|
| Reviewer finding events | 4 |
| PRs where any reviewer fired | 3/10 (30%) |
| Scope Auditor events | 1 |
| Test Skeptic events | 3 |
| Contract Keeper / Product reviewer events | 0 |

Reviewer signal was **useful when it fired** (scope drift on docs+script PR; weak-test hint on large refactors). It did not dominate noise: most PRs had zero reviewer findings.

## False-positive rate (labeled feedback)

Feedback labels on **19 unique findings** (see `feedback.jsonl`):

| Label | Count | Share |
|-------|------:|------:|
| accepted | 7 | 36.8% |
| dismissed | 10 | 52.6% |
| wrong | 2 | 10.5% |

**False-positive rate (dismissed + wrong): 63.2%**

### Top noisy finding kinds

1. `ui_copy_changed` — 7/7 labeled dismissed (markdown/agent policy/docs PRs)
2. `test_skeptic_weak_test_signal` — 2/2 dismissed (tests present in PR)
3. `implementation_without_tests` — 1/1 dismissed on hyperflow (tests not in diff paths)

### Top wrong finding kinds

1. `persistence_schema_changed` — 2/2 wrong (TS config / Rust transform, not schema)

### Top useful finding kinds

1. `broad_file_surface` — 3/3 accepted
2. `dependency_surface_changed` — 1/1 accepted
3. `scope_auditor_task_scope_expansion` — 1/1 accepted

## Golden corpus

- Added **10** `dogfood_*` cases under `examples/golden_cases/`
- Full calibration: **47/47 PASS** (37 legacy + 10 dogfood)

## Anonymized public artifacts

- `examples/real_reports/` — 3 redacted reports for site/README
- Site sync prompt updated in `SITE_SYNC_NOTES.md`

## Recommended product follow-ups

1. Suppress or downgrade `ui_copy_changed` for `**/*.md` in generic mode (7/10 low-signal findings).
2. Tighten `persistence_schema_changed` heuristics for `package.json` / `tsconfig` / Rust sources.
3. Do not fire `implementation_without_tests` when test files change in the same patch.
4. Ship `forgebench init` + docs-only policy presets on repos that are mostly agent markdown PRs.