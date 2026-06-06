# Beta → Early Access Launch

ForgeBench is moving from **public beta** (local CLI) to **Early Access** (Team/Enterprise adoption package) while keeping the core OSS CLI free.

## Launch checklist

### Product

- [x] VS Code extension v1.0 (`integrations/vscode-forgebench`)
- [x] JetBrains plugin v1.0 (`integrations/jetbrains-forgebench`)
- [x] Self-hosted GitHub App kit (`forgebench github-app`)
- [x] FPL v1 + policy tests + audit/versioning (EO-009)
- [x] SOC2-style security documentation pack

### Go-to-market

- [x] Marketing home refresh — see GitHub `docs/marketing-home.md`
- [x] Pricing tiers — [enterprise/pricing.md](enterprise/pricing.md)
- [x] Contribution program — see GitHub `docs/contribution-program.md`
- [x] Public roadmap — [ROADMAP on GitHub](https://github.com/caissonhq/forgebench/blob/main/ROADMAP.md)

### Customer onboarding path

```bash
pip install forgebench
forgebench doctor
forgebench init --repo . --out forgebench.yml
forgebench policy test --tests examples/policy_tests
forgebench github-app manifest --out forgebench-output/github-app-manifest.json
```

## Beta vs Early Access

| Capability | Beta | Early Access |
|------------|------|--------------|
| Local CLI review | Yes | Yes |
| Structured feedback v3 | Yes | Yes |
| VS Code / JetBrains | Scaffold | Production plugins |
| GitHub App | Action only | Self-hosted app kit + org enforcement |
| Security audit pack | Trust model | SOC2-style controls matrix |
| Commercial support | Community | Team / Enterprise |

## Rollout communications

1. Announce Early Access on forgebench.dev with technical positioning (merge-risk, not agent scores).
2. Publish VS Code + JetBrains marketplace listings.
3. Share SOC2 readiness doc with design partners.
4. Open Team EA signup via hello@forgebench.dev with repo count + policy maturity survey.

ForgeBench does not prove code is safe. Early Access sells **adoption infrastructure** for merge-risk governance.