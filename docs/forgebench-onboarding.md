# ForgeBench development repository

This repo is the **ForgeBench CLI source**, not a consumer project. Quick orientation for contributors.

## First run

```bash
pip install -e ".[dev]"
forgebench doctor
python -m pytest -q
bash scripts/smoke_install.sh
```

## CI in this repo

Primary CI is `.github/workflows/ci.yml` (pytest, calibration, wheel smoke). Consumer projects use `.github/workflows/forgebench.yml` from `forgebench init --enterprise` — see [customer-onboarding-playbook.md](customer-onboarding-playbook.md).

## Guardrails

Root `forgebench.yml` dogfoods the tool on this codebase. Edit `checks.test` or policy paths as needed.

## Docs & health

- [ci-health.md](ci-health.md) — workflow versions, Dependabot, local CI parity
- [V1_READINESS.md](../V1_READINESS.md) — capability matrix

Support: hello@forgebench.dev