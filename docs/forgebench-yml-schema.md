# `forgebench.yml` Schema

ForgeBench reads optional repo guardrails from `forgebench.yml` using `yaml.safe_load` from PyYAML. ForgeBench never uses `eval`, never uses `exec`, and never executes commands while parsing YAML.

Checks declared in `forgebench.yml` are only run when `--run-checks` is explicitly passed.

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

## Unknown Keys

Unknown top-level keys are non-fatal. ForgeBench records a warning and ignores them.

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
