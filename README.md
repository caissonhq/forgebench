# ForgeBench

ForgeBench reviews AI-generated diffs before they hit main.

Adversarial pre-merge QA for coding-agent output.

SWE-Bench asks whether an agent solved a task. ForgeBench asks whether a serious engineer would merge the diff.

ForgeBench turns an AI-generated diff, the original task prompt, optional repo guardrails, and optional local check results into a sober merge-risk report, machine-readable JSON, and a repair prompt that can be pasted back into Codex, Claude Code, or Cursor.

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.

## What ForgeBench Is

- A local CLI for reviewing AI-generated patches before merge.
- A deterministic static-signal pass over unified git diffs.
- Optional local build/test/lint/typecheck command execution when explicitly requested.
- A sober report that classifies the patch as `BLOCK`, `REVIEW`, or `LOW_CONCERN`.
- A focused repair prompt for tightening the original patch without expanding scope.

## What ForgeBench Is Not

- Not a web app or dashboard.
- Not a hosted service.
- Not a generic eval platform.
- Not a source-code hosting integration.
- Not a replacement for human review.
- Not connected to GitHub, billing, user accounts, or external LLM APIs.

## Quickstart

Install locally from this repo:

```bash
pip install -e .
```

Run the minimum local review:

```bash
forgebench review --repo . --diff ./patch.diff --task ./task.md
```

ForgeBench writes:

- `forgebench-output/forgebench-report.md`
- `forgebench-output/forgebench-report.json`
- `forgebench-output/repair-prompt.md`

## CLI Usage

```bash
forgebench review \
  --repo . \
  --diff ./patch.diff \
  --task ./task.md \
  --guardrails ./forgebench.yml \
  --run-checks \
  --out ./forgebench-output
```

Arguments:

- `--repo`: repository being reviewed.
- `--diff`: unified git diff to inspect.
- `--task`: original coding-agent task prompt.
- `--guardrails`: optional project guardrails file.
- `--run-checks`: optional flag that executes configured local verification commands.
- `--out`: optional output directory. Defaults to `./forgebench-output/`.

No LLM or network dependency is required in the current version.

## Guardrails File

ForgeBench supports `project`, `protected_behavior`, `risk_files.high`, `risk_files.medium`, `forbidden_patterns`, `checks`, and `check_timeout_seconds`.

```yaml
project: Quarterly

protected_behavior:
  - Federal + California only
  - No feature creep beyond estimated quarterly tax payments
  - Tax calculation trust must be preserved
  - Paid state must distinguish Federal and California payments

risk_files:
  high:
    - "**/TaxEngine/**"
    - "**/Persistence/**"
    - "**/*Migration*"
  medium:
    - "**/Views/**"
    - "**/Settings/**"

forbidden_patterns:
  - subscription
  - external checkout
  - brokered account linking
  - crypto

checks:
  build: "python -m compileall forgebench"
  test: "python -m unittest discover -s tests"
  lint: null
  typecheck: null

check_timeout_seconds: 120
```

Guardrails are applied by matching changed file paths and searching added lines for forbidden patterns.

## Deterministic Checks

ForgeBench can run configured local verification commands, but only when `--run-checks` is passed. By default, ForgeBench does not execute commands.

Commands are read from `forgebench.yml` and run from the repo root supplied by `--repo`. They are user-controlled local shell commands, so only run checks from a repo/config you trust. Results are included as deterministic evidence in the Markdown report, JSON report, and repair prompt.

Failed build, test, and typecheck commands can produce `BLOCK` merge posture. Failed lint commands usually produce `REVIEW`. Timed out commands are reported separately so the reviewer can tell the difference between a failure and incomplete verification.

ForgeBench does not install dependencies or infer how to build your project. Configure commands that already work locally.

Example:

```yaml
checks:
  build: "python -m compileall forgebench"
  test: "python -m unittest discover -s tests"
  lint: null
  typecheck: null
```

Run with checks:

```bash
forgebench review --repo . --diff ./patch.diff --task ./task.md --guardrails ./forgebench.yml --run-checks
```

## Calibration Corpus

ForgeBench includes a small golden corpus under `examples/golden_cases/`. Each case describes a realistic review scenario with:

- `patch.diff`: input diff.
- `task.md`: original coding-agent task.
- `forgebench.yml`: optional guardrails and check commands.
- `expected.json`: expected merge posture and finding IDs.
- `rationale.md`: why the expected result is reasonable.

Run calibration:

```bash
forgebench calibrate --cases examples/golden_cases
```

Write calibration artifacts to a specific directory:

```bash
forgebench calibrate --cases examples/golden_cases --out forgebench-calibration-output
```

Calibration is not a benchmark. It is a local product-quality regression suite for checking that ForgeBench judges realistic diffs the way a serious engineer would expect.

To add a new golden case:

1. Create a new directory under `examples/golden_cases/`.
2. Add `patch.diff`, `task.md`, and `expected.json`.
3. Add `forgebench.yml` if the case needs guardrails or deterministic checks.
4. Add `rationale.md` explaining the expected posture.
5. Run `forgebench calibrate --cases examples/golden_cases`.

Example `expected.json`:

```json
{
  "case_name": "implementation_without_tests_review",
  "run_checks": false,
  "expected_posture": "REVIEW",
  "required_finding_ids": ["implementation_without_tests"],
  "allowed_extra_finding_ids": [],
  "forbidden_finding_ids": ["deleted_tests"],
  "allow_unlisted_findings": false,
  "rationale": "A source behavior change without test updates should require review before merge."
}
```

## Merge Postures

`BLOCK` means ForgeBench found a high-confidence merge risk that should be addressed before merge. Examples include a failed build/test/typecheck command, a deleted test file, a forbidden pattern introduced in added lines, dependency changes without test coverage, or likely persistence/schema changes without test coverage.

`REVIEW` means the patch may be valid, but deterministic or static signals indicate it needs deliberate human review before merge. Examples include lint failures, timed out checks, implementation changes without tests, high-risk project files, build/config changes, broad file surface changes, generated file noise, or guardrail hits.

`LOW_CONCERN` means ForgeBench found no high-confidence merge blockers and no major static risk pattern. Examples include small docs-only changes, test-only additions, advisory-only findings, or patches where configured deterministic checks pass.

## Static Signals

ForgeBench detects:

- Implementation changes without corresponding test updates.
- Deleted or weakened tests.
- Dependency and lockfile changes.
- Build or configuration changes.
- Persistence, schema, model, or migration changes.
- Broad patches touching more than 10 files.
- Generated output, cache, or local machine files in the diff.
- User-facing copy, documentation, or UI surface changes.
- Guardrail high-risk and medium-risk file matches.
- Forbidden patterns introduced in added lines.
- Binary files shown by git diff metadata.

## Dogfood on a Real Local Diff

1. Save the current diff:

```bash
git diff > patch.diff
```

2. Save the original coding-agent task:

```bash
echo "Add paid-state tracking for Federal and California quarterly tax payments." > task.md
```

3. Run ForgeBench:

```bash
forgebench review --repo . --diff ./patch.diff --task ./task.md
```

To include configured local checks:

```bash
forgebench review --repo . --diff ./patch.diff --task ./task.md --guardrails ./forgebench.yml --run-checks
```

4. Open the report:

```bash
open forgebench-output/forgebench-report.md
```

For manual product learning, copy the outcome into `DOGFOOD_LOG.md`. Track whether the posture was right, which findings were useful, which were noisy, and whether the repair prompt helped.

## Development Commands

Install locally:

```bash
python -m pip install -e .
```

Show CLI help:

```bash
forgebench --help
forgebench review --help
forgebench calibrate --help
```

Run tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests
```

Run calibration:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m forgebench calibrate --cases examples/golden_cases
```

## Known Limitations

- The diff parser targets common local `git diff` output, not every possible patch format.
- The guardrails parser supports the documented Sprint 2 YAML shape, not arbitrary YAML.
- Command execution is opt-in and limited to commands you configure locally.
- ForgeBench does not understand full program behavior.
- Current output is local files only. There is no GitHub integration, hosted service, dashboard, or external LLM call.
