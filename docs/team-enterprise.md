# Team and Enterprise Policy

ForgeBench stays local-first. Team and Enterprise features focus on **shared policy** and a **local policy dashboard skeleton** you can preview or host yourself.

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.

## Shared `forgebench.yml`

Repos can layer policy from multiple files:

- `extends`: inherit one base file, then overlay repo-specific keys.
- `include`: merge multiple shared policy files before applying the current file.
- `FORGEBENCH_ORG_POLICY`: optional environment variable pointing at an org-wide policy file merged on top of the repo file.

Merge rules:

1. Base layers load first (`extends` / `include` order).
2. The current repo file overlays matching keys.
3. Org policy from `FORGEBENCH_ORG_POLICY` overlays repo policy when the file exists.

Lists such as `protected_behavior`, `forbidden_patterns`, and risk paths are unioned with de-duplication. Mappings such as `checks` and `policy.finding_overrides` are shallow-merged with overlay winning on conflicts.

## Example layout

```text
org-policy/
  forgebench-org.yml
services/
  payments/
    forgebench.yml
  search/
    forgebench.yml
```

Org policy (`org-policy/forgebench-org.yml`):

```yaml
team:
  name: Acme Platform
protected_behavior:
  - No direct production database writes from agent patches
forbidden_patterns:
  - eval(
risk_files:
  high:
    - "**/auth/**"
```

Service repo (`services/payments/forgebench.yml`):

```yaml
extends: ../../org-policy/forgebench-org.yml
project: Payments
checks:
  test: pytest -q
forbidden_patterns:
  - stripe.charges.create
```

CI can set org policy without editing every repo:

```bash
export FORGEBENCH_ORG_POLICY=/opt/forgebench/org/forgebench-org.yml
forgebench review-pr "$PR_URL" --guardrails forgebench.yml --checkout-pr --run-checks
```

## Policy dashboard skeleton

Export a static HTML preview and JSON manifest:

```bash
forgebench dashboard --repo . --out forgebench-output/policy-dashboard
open forgebench-output/policy-dashboard/index.html
```

The export includes:

- Policy source inventory (layered files)
- Protected behavior, risk paths, forbidden patterns
- Deterministic check commands
- Policy calibration counts
- Placeholder cards for future hosted sections (adoption, posture trends, audit log)

This is a **skeleton**, not a hosted SaaS. Host the exported `index.html` on internal static hosting if you want a team preview page.

## Validation

```bash
forgebench validate --repo . --file forgebench.yml
```

Use `--strict` in CI to reject unknown top-level keys on shared policy files.

## Trust boundaries

- Treat org policy files as trusted configuration, same as repo `forgebench.yml`.
- Do not run `--run-checks` against untrusted PR-head guardrails unless you intentionally trust that branch.
- See [trust-model.md](trust-model.md) for check execution and PR worktree guidance.

## Related docs

- Schema: [forgebench-yml-schema.md](forgebench-yml-schema.md)
- CI recipes: [ci-integrations.md](ci-integrations.md)
- Public roadmap: [../ROADMAP.md](../ROADMAP.md)