# CI Health

ForgeBench CI/CD status after the stabilization round (2026-06-06).

**Source repo note:** Primary CI is `ci.yml`. The `forgebench.yml` workflow is a **reference consumer template** (manual dispatch); customer repos enable it via `forgebench init --enterprise`.

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | push/PR to `main` | pytest + calibration + wheel smoke |
| `security.yml` | push/PR + weekly Mon | pip-audit + SBOM artifact |
| `docs.yml` | docs path changes | MkDocs build + GitHub Pages deploy |
| `release.yml` | tag `v*` | wheels, binaries, PyPI, GitHub Release |
| `homebrew-tap.yml` | release published | Homebrew formula (needs `HOMEBREW_TAP_TOKEN`) |
| `vscode-marketplace.yml` | manual | VSIX publish (needs `VSCE_PAT`) |
| `dependabot-auto-merge.yml` | Dependabot PRs | Auto-merge safe minor/patch bumps |

## Action versions (pinned)

| Action | Version |
|--------|---------|
| `actions/checkout` | v6 |
| `actions/setup-python` | v6 |
| `actions/setup-node` | v6 |
| `actions/upload-artifact` | v7 |
| `actions/download-artifact` | v8 |

## Dependabot

- Weekly Monday 09:00 PT
- Groups minor/patch for pip and GitHub Actions
- Max 5 open PRs per ecosystem
- Auto-merge: GitHub Actions minor/patch; pip patch only (after CI passes)

## Notification recommendations

In GitHub → **Watch** → Custom:

- ✅ Pull request reviews (your PRs)
- ✅ Actions: only **Failed workflows** on `main`
- ❌ All Actions runs (reduces Dependabot noise)

In repo **Settings → Notifications**, disable email for Dependabot if using auto-merge.

## Known manual steps

- **GitHub Pages**: Settings → Pages → Source: GitHub Actions, then set repository variable `PAGES_DEPLOY=true` to enable deploy job
- **PyPI / release secrets**: Configure for tagged releases
- **HOMEBREW_TAP_TOKEN**, **VSCE_PAT**: Optional; workflows skip push/publish when unset

## Local CI parity

```bash
pip install -e ".[dev]"
python -m pytest -q
python -m forgebench calibrate --cases examples/golden_cases
bash scripts/smoke_install.sh
python -m forgebench doctor
pip install pip-audit && pip-audit
mkdocs build --strict
```

## Production-ready checklist (GitHub settings)

| Item | Status | Action |
|------|--------|--------|
| `main` CI green | ✅ | Required checks: CI / Python 3.12, PyPI wheel smoke |
| Open PRs / stale branches | ✅ | Zero open; only `main` on remote |
| Dependabot | ✅ | Weekly grouped updates + auto-merge workflow |
| GitHub Pages deploy | ⏸ | Settings → Pages → GitHub Actions; set `PAGES_DEPLOY=true` |
| Auto-merge | 🟡 | Settings → General → Allow auto-merge (recommended) |
| Branch protection | 🟡 | Require CI checks before merge on `main` |
| Release secrets | 🟡 | PyPI OIDC, `HOMEBREW_TAP_TOKEN`, `VSCE_PAT` when publishing |
| Repository secrets | 🟡 | Never commit; use GitHub Secrets / Variables |

See [forgebench-onboarding.md](forgebench-onboarding.md) for contributor setup.