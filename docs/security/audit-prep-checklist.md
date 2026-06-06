# Audit Prep Checklist (Customer + Vendor)

Use this checklist when preparing a SOC 2-style review of ForgeBench in your organization.

## Policy & governance

- [ ] Org policy file under version control (`examples/org-policy/`)
- [ ] `forgebench policy test` passing in CI for shared policy repos
- [ ] `forgebench validate --strict` on policy changes
- [ ] Policy version recorded: `forgebench policy version --record`
- [ ] FPL sources reviewed when used (`forgebench policy compile`)

## CI/CD

- [ ] ForgeBench Action pinned to tagged release
- [ ] `review-pr --checkout-pr` used with `--run-checks`
- [ ] SARIF uploaded to code scanning (optional)
- [ ] Check runs enabled only with explicit tokens

## GitHub App (self-hosted)

- [ ] Manifest exported: `forgebench github-app manifest --out manifest.json`
- [ ] Webhook secret configured
- [ ] TLS termination on webhook endpoint
- [ ] Org enforcement config reviewed (`examples/github-app/org-enforcement.json`)
- [ ] Audit log retention policy for `policy-audit.jsonl`

## IDE & developer workstations

- [ ] VS Code / JetBrains plugins use local CLI only
- [ ] `forgebench doctor` in onboarding docs
- [ ] LLM keys stored in OS secret store / CI secrets

## Evidence to collect

- Calibration CI run logs
- Sample `forgebench-report.json` (redacted)
- Policy audit export (`forgebench policy audit --export`)
- Telemetry export if enabled (`forgebench telemetry export`)
- Org enforcement dry-run outputs

ForgeBench does not prove code is safe. This checklist supports **merge-risk governance**, not code certification.