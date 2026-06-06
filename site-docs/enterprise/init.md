# Enterprise init wizard

```bash
forgebench init --enterprise
```

Interactive prompts (TTY) or non-interactive defaults with `--yes`.

## Generated artifacts

| Path | Purpose |
|------|---------|
| `org-policy/forgebench-org.yml` | Org-wide policy layer |
| `forgebench.yml` | Repo guardrails extending org policy |
| `.github/forgebench.yml` | Trusted CI guardrails (base branch) |
| `.github/workflows/forgebench.yml` | GitHub Actions PR review |
| `docs/forgebench-onboarding.md` | Team onboarding guide |
| `docs/forgebench-readme-snippet.md` | README section to paste |

## Flags

```bash
forgebench init --enterprise --yes \
  --org-name "Acme Engineering" \
  --team-slug platform \
  --preset auto \
  --manifest forgebench-output/enterprise-init-manifest.json
```

## GitHub App

See onboarding doc for webhook secret, `forgebench github-app serve`, and Helm deployment under `deployments/helm/forgebench/`.