# `forgebench.yml` Schema

ForgeBench reads optional repo guardrails from `forgebench.yml` using `yaml.safe_load` from PyYAML. ForgeBench never uses `eval`, never uses `exec`, and never executes commands while parsing YAML.

Checks declared in `forgebench.yml` are only run when `--run-checks` is explicitly passed.

If no guardrails file is passed and no `forgebench.yml` exists in the repo, ForgeBench runs in generic mode. Generic mode uses first-run heuristics and reports that it is unconfigured. Run `forgebench init --repo . --out forgebench.yml` to create local guardrails, then edit the protected behavior, forbidden patterns, risk paths, and checks before relying on strict posture decisions.

Team and Enterprise repos can layer shared policy with `extends`, `include`, and the `FORGEBENCH_ORG_POLICY` environment variable. See [team-enterprise.md](team-enterprise.md).

## Local Trust Note

`forgebench.yml` is local project configuration. Treat check commands as trusted local commands only in repositories you trust. Parsing the file is passive, but running checks executes user-configured shell commands from the repo root.

Do not run checks from an untrusted PR-head `forgebench.yml`. Prefer the base-branch or local trusted guardrails file unless you intentionally trust the PR branch configuration.

## Top-Level Keys

### `project`

- Type: string
- Default: `null`
- Purpose: Human-readable project name.

### `protected_behavior`

- Type: list of strings, or a single string
- Default: `[]`
- Purpose: Product or architecture behavior reviewers should preserve.

### `risk_files`

- Type: mapping
- Default: `{}`
- Supported children:
  - `high`: list of glob patterns
  - `medium`: list of glob patterns
- Purpose: Path-based risk calibration.

### `forbidden_patterns`

- Type: list of strings, or a single string
- Default: `[]`
- Purpose: Added-line substring matches that should create high-confidence guardrail findings.

### `review_scope`

- Type: mapping
- Default: `{}`
- Supported children:
  - `include_paths`: list of glob patterns. Only changed files matching at least one pattern are reviewed.
  - `exclude_paths`: list of glob patterns. Changed files matching any pattern are excluded after include filtering.
- Purpose: Scope reviews to one workspace in monorepos and reduce noise from unrelated packages.

When no `review_scope` is configured, ForgeBench still detects multiple package roots and reports a monorepo hint in review output.

### `checks`

- Type: mapping
- Default: `{}`
- Supported children:
  - `build`: string or `null`
  - `test`: string or `null`
  - `lint`: string or `null`
  - `typecheck`: string or `null`
  - `custom`: mapping of custom check name to string or `null`
- Purpose: Local deterministic commands. They do not run unless `--run-checks` is passed.

### `check_timeout_seconds`

- Type: integer-like value
- Default: `120`
- Purpose: Timeout for configured check commands.

### `extends`

- Type: string
- Default: unset
- Purpose: Path to a base policy file merged before the current file. Relative paths resolve from the current file's directory.

### `include`

- Type: string or list of strings
- Default: unset
- Purpose: One or more shared policy files merged before the current file.

### `team`

- Type: string or mapping with `name`
- Default: `null`
- Purpose: Team or org label surfaced in reports and the policy dashboard export.

### `policy`

- Type: mapping or `null`
- Default: `{}`
- Purpose: Guardrails v2 policy calibration.

Supported policy children:

- `finding_overrides`
- `path_categories`
- `advisory_only`
- `suppress_findings`
- `posture_overrides`

## Org policy environment variable

Set `FORGEBENCH_ORG_POLICY` to an absolute or repo-relative path of a trusted org-wide policy file. ForgeBench merges org policy on top of the repo `forgebench.yml` when the file exists.

## Policy dashboard export

Run `forgebench dashboard --repo .` to export a local HTML policy dashboard skeleton and `policy-manifest.json`. This is not a hosted service.

## Validation

Run `forgebench validate --repo . --file forgebench.yml` to lint a guardrails file against this schema.

- Exit `0`: valid (warnings allowed)
- Exit `1`: valid with warnings
- Exit `2`: errors (malformed YAML or `--strict` unknown keys)

## Unknown Keys

Unknown top-level keys are non-fatal. ForgeBench records a warning and ignores them. Use `--strict` with `forgebench validate` to treat unknown keys as errors.

## `forgebench init` Presets

`forgebench init` writes a starter configuration without running package managers, `git`, `gh`, or network calls.

Supported presets:

- `auto`: default. Detects `pyproject.toml`, `package.json`, `Cargo.toml`, `Package.swift`, and `CODEOWNERS` when present.
- `python`: adds `python3 -m unittest discover -s tests` as the test command and marks common Python source paths as medium risk.
- `node`: uses scripts from `package.json` when present and marks common Node source paths as medium risk.
- `nextjs`: uses scripts from `package.json` when present, treats docs/assets as advisory, and marks `app/**`, `pages/**`, `components/**`, and `src/**` as medium risk.
- `swift`: uses `swift build` / `swift test` only for Swift package repos and marks `Sources/**`, `Tests/**`, and asset paths appropriately.
- `rust`: adds `cargo build` / `cargo test` and marks `src/**` and `tests/**` as medium risk.

Starter files intentionally leave `protected_behavior`, `forbidden_patterns`, and `risk_files.high` empty because those require human repo knowledge.

## Malformed YAML

Malformed YAML raises a clear parse error. When PyYAML provides line/column information, ForgeBench includes it in the error message.

## Example

```yaml
project: Quarterly

protected_behavior:
  - Federal + California only
  - Tax calculation trust must be preserved

risk_files:
  high:
    - "**/TaxEngine/**"
    - "**/Persistence/**"
  medium:
    - "**/Views/**"

forbidden_patterns:
  - Stripe
  - Plaid

checks:
  build: "python -m compileall forgebench"
  test: "python -m unittest discover -s tests"
  lint: null
  typecheck: null
  custom:
    docs: "python scripts/check_docs.py"

check_timeout_seconds: 120

policy:
  path_categories:
    docs:
      patterns:
        - "README.md"
        - "docs/**"
      default_severity: advisory
  suppress_findings:
    - finding_id: ui_copy_changed
      paths:
        - "README.md"
        - "docs/**"
      reason: "Docs-only copy changes are not merge-risk relevant."
```
