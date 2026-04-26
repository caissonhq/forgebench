# ForgeBench

ForgeBench reviews AI-generated diffs before they hit main.

Adversarial pre-merge QA for coding-agent output.

SWE-Bench asks whether an agent solved a task. ForgeBench asks whether a serious engineer would merge the diff.

ForgeBench turns an AI-generated diff, the original task prompt, optional repo guardrails, optional local check results, and optional advisory LLM review into a sober merge-risk report, machine-readable JSON, and a repair prompt that can be pasted back into Codex, Claude Code, or Cursor.

Site: https://merge-posture-guard.lovable.app

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.

## What ForgeBench Is

- A local CLI for reviewing AI-generated patches before merge.
- A deterministic static-signal pass over unified git diffs.
- Optional local build/test/lint/typecheck command execution when explicitly requested.
- Optional evidence-constrained LLM review when explicitly requested.
- Optional GitHub PR URL intake through the local `gh` CLI.
- A sober report that classifies the patch as `BLOCK`, `REVIEW`, or `LOW_CONCERN`.
- A focused repair prompt for tightening the original patch without expanding scope.

## What ForgeBench Is Not

- Not a web app or dashboard.
- Not a hosted service.
- Not a generic eval platform.
- Not a GitHub App or hosted PR review service.
- Not an automatic PR commenter unless `--post-comment` is explicitly passed.
- Not a replacement for human review.
- Not connected to billing, user accounts, hosted GitHub OAuth, or built-in external LLM APIs.

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
- `--llm-review`: optional flag that runs an advisory LLM review layer.
- `--llm-provider`: optional LLM provider. Sprint 4 supports `command` and test-only `mock`.
- `--llm-command`: local command used by the command provider.
- `--out`: optional output directory. Defaults to `./forgebench-output/`.

No LLM or network dependency is required by default.

## GitHub PR Intake

ForgeBench can fetch a GitHub pull request through the local `gh` CLI, derive task context from the PR title/body, run the normal ForgeBench review, and write the same local artifacts.

```bash
forgebench review-pr https://github.com/OWNER/REPO/pull/123
```

This keeps PR review local by default while producing a comment-ready summary for manual use.

ForgeBench requires the GitHub CLI for this flow. Install `gh`, run `gh auth login`, and make sure your local auth can read the target PR.

The default output directory is PR-scoped:

```text
forgebench-output/pr-OWNER-REPO-NUMBER/
```

Inside it, ForgeBench writes:

- `patch.diff`
- `task.md`
- `forgebench-report.md`
- `forgebench-report.json`
- `repair-prompt.md`
- `pr-comment.md`

To include configured local checks:

```bash
forgebench review-pr https://github.com/OWNER/REPO/pull/123 --run-checks
```

Important: without `--checkout-pr`, deterministic checks run against the current local repo checkout, not the PR branch.

To run configured checks against the actual PR code, ask ForgeBench to prepare a temporary git worktree:

```bash
forgebench review-pr https://github.com/OWNER/REPO/pull/123 --checkout-pr --run-checks
```

ForgeBench fetches the PR head into a temporary namespaced ref, creates a detached worktree, runs checks from that worktree, and removes the worktree/ref by default. It does not mutate your current checkout.

To keep the worktree for inspection:

```bash
forgebench review-pr https://github.com/OWNER/REPO/pull/123 --checkout-pr --run-checks --keep-worktree
```

You can choose the parent directory for temporary worktrees:

```bash
forgebench review-pr https://github.com/OWNER/REPO/pull/123 --checkout-pr --worktree-dir /tmp/forgebench-worktrees
```

PR checkout depends on local `git`, GitHub CLI auth, the local repo remote, and permissions to fetch the PR ref.

To write the PR comment Markdown somewhere specific:

```bash
forgebench review-pr https://github.com/OWNER/REPO/pull/123 --comment-file /tmp/forgebench-pr-comment.md
```

To post the generated comment back to the PR, pass `--post-comment` explicitly:

```bash
forgebench review-pr https://github.com/OWNER/REPO/pull/123 --post-comment
```

PR comments are never posted by default. `--dry-run` can be passed explicitly when you want local artifacts only. ForgeBench does not store GitHub tokens or secrets.

## Guardrails File

ForgeBench supports `project`, `protected_behavior`, `risk_files.high`, `risk_files.medium`, `forbidden_patterns`, `checks`, `check_timeout_seconds`, and optional Guardrails v2 policy rules.

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

Guardrails are applied by matching changed file paths, searching added lines for forbidden patterns, and applying repo-specific policy calibration.

## Guardrails v2 Policy

Guardrails v2 lets a repo tune generic static findings into project-specific review policy. The intent is not to hide risk. It is to explain when a finding is suppressed, downgraded, or capped because the repo has declared a path category or review rule.

Supported policy controls:

- `path_categories`: classify paths such as `docs`, `assets`, `read_models`, or `persistence`.
- `finding_overrides`: adjust severity/confidence for a finding on matching paths.
- `suppress_findings`: suppress specific findings on matching paths or when all changed files match a pattern set.
- `advisory_only`: mark paths that should not escalate posture on their own.
- `posture_overrides`: cap posture for docs-only or asset-only changes.

Example docs-only policy:

```yaml
policy:
  path_categories:
    docs:
      patterns:
        - "README.md"
        - "docs/**"
        - "**/*.md"
      default_severity: advisory

  advisory_only:
    - "README.md"
    - "docs/**"
    - "**/*.md"

  suppress_findings:
    - finding_id: ui_copy_changed
      paths:
        - "README.md"
        - "docs/**"
        - "**/*.md"
      reason: "Docs-only copy changes are not merge-risk relevant."

  posture_overrides:
    docs_only_changes:
      posture_ceiling: LOW_CONCERN
      reason: "Docs-only changes should not escalate unless a blocker is present."
```

Example asset-only policy:

```yaml
policy:
  path_categories:
    assets:
      patterns:
        - "**/*.png"
        - "**/*.jpg"
        - "**/*.svg"
        - "**/*.ico"
        - "**/Assets.xcassets/**"
      default_severity: advisory

  suppress_findings:
    - finding_id: broad_file_surface
      when_all_changed_files_match:
        - "**/*.png"
        - "**/*.jpg"
        - "**/*.svg"
        - "**/*.ico"
        - "**/Assets.xcassets/**"
      reason: "Asset-only large diffs should not be treated as broad code risk."

  posture_overrides:
    asset_only_changes:
      posture_ceiling: LOW_CONCERN
      reason: "Asset-only changes should not escalate unless a blocker is present."
```

Example read-model refinement:

```yaml
policy:
  path_categories:
    read_models:
      patterns:
        - "**/read_model.py"
        - "**/view_model.py"
        - "**/*ReadModel*"
        - "**/*ViewModel*"
      default_severity: low

  finding_overrides:
    persistence_schema_changed:
      suppress_paths:
        - "**/read_model.py"
        - "**/view_model.py"
      reason: "Read/view models are not persistence schema changes."
```

Deterministic blockers are not suppressed by posture ceilings. A failing configured build, test, or typecheck command can still produce `BLOCK` even when the diff is docs-only or asset-only. Forbidden patterns, deleted tests, and explicit high-risk guardrail hits also bypass docs/assets posture ceilings.

Policy decisions appear in the Markdown report under `Guardrails Policy`, in JSON under `policy`, and in the repair prompt as suppressed or calibrated findings. Suppressed findings are not listed as required repairs.

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

## Specialized Reviewers

ForgeBench runs four deterministic specialized reviewers by default. They are evidence-constrained checks over the task text, parsed diff, static findings, deterministic check results, and guardrails. They do not call an LLM, approve merges, assign scores, or override deterministic failures.

Phase 1 reviewers:

- Scope Auditor: checks whether the patch appears to change more than the task required.
- Test Skeptic: checks whether changed behavior has meaningful regression coverage.
- Contract Keeper: checks whether API, schema, type, route, persistence, or public interface surfaces changed without clear coverage.
- Product / Guardrail Reviewer: checks whether configured product or architecture guardrails were touched or violated.

Reviewer findings are lower in the evidence hierarchy than deterministic checks, static risk signals, and Guardrails v2 policy. A reviewer finding can raise concern, for example moving a low-concern patch to `REVIEW`, but it cannot downgrade `BLOCK`, claim code is safe, or approve a merge.

Disable the layer when you need a static-only baseline:

```bash
forgebench review --repo . --diff ./patch.diff --task ./task.md --no-reviewers
```

The same flag is available for PR intake:

```bash
forgebench review-pr https://github.com/OWNER/REPO/pull/123 --no-reviewers
```

Reviewer output appears in Markdown under `Specialized Reviewers`, in JSON under `specialized_reviewers`, in the repair prompt as reviewer findings, and as a concise summary in `pr-comment.md`.

Sprint 6.1 calibration tightened the Phase 1 reviewers around real dogfood noise:

- Test Skeptic no longer treats every deleted test line as weakened coverage. Deleted test files remain serious; removed assertions without replacement produce review-level risk; assertion refactors with replacement coverage stay low concern.
- Contract Keeper separates read/view-model contract changes from persistence/schema changes. Read models can still require review when their public shape changes, but they should not block as schema risk unless policy marks them high risk.
- Scope Auditor focuses on task-scope drift, such as README-only tasks that also change code or CI/config.
- Product / Guardrail Reviewer adds product-review framing to configured guardrail hits without claiming semantic violations unless forbidden patterns match.

## Optional LLM Review

ForgeBench can run an advisory LLM reviewer when `--llm-review` is passed. LLM review is off by default.

The evidence hierarchy remains:

1. Deterministic checks
2. Static risk signals
3. Guardrails policy
4. Specialized reviewers
5. LLM review

LLM findings can raise concern, for example by moving a `LOW_CONCERN` patch to `REVIEW` when a medium advisory finding is returned. LLM findings cannot downgrade posture, approve a merge, erase static findings, override deterministic failures, create a blocker finding, or assign a numeric score.

ForgeBench does not ship a hosted LLM integration in Sprint 4. The `command` provider is a local escape hatch: ForgeBench writes an evidence bundle to stdin and expects structured JSON on stdout.

Example:

```bash
forgebench review \
  --repo . \
  --diff ./patch.diff \
  --task ./task.md \
  --guardrails ./forgebench.yml \
  --llm-review \
  --llm-provider command \
  --llm-command "python scripts/mock_reviewer.py"
```

The command must return JSON like:

```json
{
  "reviewer_name": "General LLM Reviewer",
  "summary": "No additional LLM findings beyond existing deterministic/static evidence.",
  "findings": []
}
```

Or with findings:

```json
{
  "reviewer_name": "General LLM Reviewer",
  "summary": "The reviewer found one advisory edge case.",
  "findings": [
    {
      "id": "llm_missing_edge_case",
      "title": "Missing edge case review",
      "severity": "medium",
      "confidence": "medium",
      "files": ["src/example.py"],
      "explanation": "The diff changes behavior but does not show coverage for an empty-input case.",
      "suggested_fix": "Add a focused test for the empty-input path or explain why it is covered elsewhere."
    }
  ]
}
```

The `mock` provider is used by tests and golden corpus calibration. It is deterministic and local; it does not make a network call.

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
- Deleted test files.
- Test assertions or test cases removed without clear replacement.
- Dependency and lockfile changes.
- Build or configuration changes.
- Persistence, schema, entity, store, database, ORM, or migration changes.
- Read/view-model contract changes through Contract Keeper without treating them as persistence/schema by default.
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

## V1 Readiness

See `V1_READINESS.md` for the current V1 readiness assessment, evidence hierarchy, Phase 1 reviewer scope, known limitations, and what remains before CAI-5 should be considered done.

See `SITE_SYNC_NOTES.md` for the Lovable update prompt that keeps the public alpha site aligned with current CLI capabilities without implying hosted SaaS or the full reviewer set.

## Known Limitations

- The diff parser targets common local `git diff` output, not every possible patch format.
- The guardrails parser supports the documented ForgeBench YAML shapes, not arbitrary YAML.
- Guardrails v2 policy is path-pattern based. It does not interpret copy intent or program semantics.
- Specialized reviewers are Phase 1 deterministic heuristics only; they are not the full CAI-7 reviewer set.
- Command execution is opt-in and limited to commands you configure locally.
- LLM review is opt-in and advisory. The command provider can run any command you configure, so only use it with trusted local commands.
- GitHub PR intake depends on the local `gh` CLI and network/auth state. It is not a GitHub App.
- ForgeBench does not understand full program behavior.
- Current output is local files unless `--post-comment` is explicitly passed. There is no hosted service, dashboard, or built-in external LLM call.
