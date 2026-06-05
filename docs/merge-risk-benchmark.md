# Merge Risk Benchmark

ForgeBench's **Merge Risk Benchmark** measures whether a serious engineer would merge an AI-generated diff.

SWE-Bench asks whether an agent solved the task. This benchmark asks whether the resulting patch is safe to merge.

## Snapshot (2026-06-05)

- Golden cases: **47**
- Calibration pass rate: **47/47 (100%)**
- Corpus: `examples/golden_cases/`

### Posture distribution

| Posture | Cases |
|---------|------:|
| BLOCK | 13 |
| REVIEW | 18 |
| LOW_CONCERN | 16 |

### Top finding kinds

| Finding kind | Cases |
|--------------|------:|
| implementation_without_tests | 10 |
| test_skeptic_missing_behavior_coverage | 10 |
| ui_copy_changed | 8 |
| persistence_schema_changed | 5 |
| scope_auditor_task_scope_expansion | 5 |
| dependency_surface_changed | 4 |
| dependency_watcher_major_version_bump | 4 |
| dependency_watcher_new_runtime_dependency | 4 |
| broad_file_surface | 3 |
| dependency_watcher_manifest_without_tests | 3 |

### Review lens fire-rate

Lenses that produced findings on at least one case include Test Skeptic, Scope Auditor, Contract Keeper, Product / Guardrail Reviewer, Dependency Watcher, and Repo Convention Reviewer.

## Methodology

1. Each golden case includes a realistic unified diff, original task prompt, and expected merge posture.
2. ForgeBench runs the full local review pipeline: static signals, guardrails, heuristic lenses, and optional LLM cases.
3. Calibration passes when posture, required findings, and artifact shape match the case contract.
4. This is a **product-quality regression suite**, not a public leaderboard. It guards merge-judgment drift as reviewers evolve.

## Reproduce locally

```bash
pip install forgebench
forgebench benchmark --cases examples/golden_cases
forgebench calibrate --cases examples/golden_cases --repo .
```

Regenerate this page from live calibration:

```bash
forgebench benchmark --cases examples/golden_cases --out-markdown docs/merge-risk-benchmark.md
```

## Comparison to SWE-Bench

| Dimension | SWE-Bench | Merge Risk Benchmark |
|-----------|-----------|----------------------|
| Question | Did the agent solve the task? | Would a serious engineer merge this diff? |
| Input | Issue + repo state | Task prompt + unified diff (+ optional guardrails) |
| Output | Pass/fail on tests | BLOCK / REVIEW / LOW_CONCERN posture |
| Scope | Agent capability eval | Pre-merge QA regression for ForgeBench itself |
| Hosting | Public benchmark harness | Local CLI; no hosted submission portal |

## What this is not

- Not a hosted leaderboard or public submission portal.
- Not a proof that ForgeBench certifies code as safe.
- Not a replacement for repo-specific guardrails or human review.

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.