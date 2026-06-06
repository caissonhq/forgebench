# Semantic Analysis (EO-007)

ForgeBench adds optional AST-backed semantic diff analysis for Python, TypeScript, and Rust.

## Parsers

| Language | Primary parser | Fallback |
|----------|----------------|----------|
| Python | `tree-sitter-python` (optional extra) | stdlib `ast` |
| TypeScript | `tree-sitter-typescript` (optional extra) | regex symbol extraction |
| Rust | `tree-sitter-rust` (optional extra) | regex symbol extraction |

Install optional grammars:

```bash
pip install "forgebench[semantic]"
```

Without extras, Python still analyzes via stdlib `ast`; TypeScript and Rust use conservative regex fallbacks.

## Cross-file behavioral diff

During review, ForgeBench:

1. Extracts changed symbols from source-file hunks
2. Scans changed test files for symbol references
3. Records cross-file edges and symbols lacking test references

Signals are written to `static_signals` in `forgebench-report.json`:

- `semantic_analysis_enabled`
- `semantic_parsers_used`
- `changed_symbols`
- `cross_file_behavior_edges`
- `symbols_without_test_reference`

Disable with:

```bash
forgebench review ... --no-semantic-analysis
```

## Behavioral Skeptic reviewer

The **Behavioral Skeptic** lens consumes semantic signals and raises `behavioral_skeptic_uncovered_symbols` when changed implementation symbols lack cross-file test references in the patch.

## Mutation testing skeleton

```bash
forgebench review --repo . --diff patch.diff --task task.md --prove-it
forgebench mutation plan --report forgebench-output/forgebench-report.json
```

Writes `mutation-plan.json` with candidate symbols and suggested mutation kinds. ForgeBench does not execute mutants yet.

## Multi-model LLM ensemble

```bash
export FORGEBENCH_LLM_ENSEMBLE_MODELS=gpt-4o-mini,claude-sonnet-4
forgebench review ... --llm-review --llm-provider openai
```

Or:

```bash
forgebench review ... --llm-review --llm-ensemble gpt-4o-mini,mock-model --llm-provider mock
```

Strategies: `consensus` (default), `first_success`.

## Prove-it mode skeleton

```bash
forgebench review --repo . --diff patch.diff --task task.md --prove-it
forgebench prove-it --report forgebench-output/forgebench-report.json
```

Exports:

- `prove-it-plan.json` — behavioral diff, mutation plan, ensemble metadata, checklist
- `prove-it-checklist.md` — human-readable proof tasks before merge

Prove-it mode structures evidence gathering. It does not certify a diff as safe.