# ForgeBench Pricing & Packaging

ForgeBench core review stays **local and free forever**. Team and Enterprise tiers add org policy governance, analytics, and supported self-hosted integrations.

## Tier comparison

| | **Free** | **Team** | **Enterprise** |
|---|----------|----------|----------------|
| **Price** | $0 | $29 / developer / month (EA) | Custom annual |
| **Best for** | Individuals, OSS | Multi-repo engineering teams | Regulated / platform orgs |
| **License key** | Not required | `FB-TEAM-...` | `FB-ENTERPRISE-...` |
| **Seats** | Unlimited machines | Per-seat activation | Org-wide or unlimited |

## Feature matrix

| Capability | Free | Team | Enterprise |
|------------|:----:|:----:|:----------:|
| `forgebench review` / `review-pr` | ✓ | ✓ | ✓ |
| Golden benchmark & calibration | ✓ | ✓ | ✓ |
| Cursor rule + MCP server | ✓ | ✓ | ✓ |
| GitHub Action (Docker) | ✓ | ✓ | ✓ |
| VS Code + JetBrains extensions | ✓ | ✓ | ✓ |
| `forgebench init` (basic guardrails) | ✓ | ✓ | ✓ |
| Review telemetry (opt-in, local) | ✓ | ✓ | ✓ |
| Self-hosted analytics dashboard | ✓ | ✓ | ✓ |
| `forgebench init --enterprise` | | ✓ | ✓ |
| Org policy layers + dashboard export | | ✓ | ✓ |
| Policy tests in CI | | ✓ | ✓ |
| Cloud analytics export quota | | ✓ | ✓ |
| Usage reporting (`license report`) | | ✓ | ✓ |
| `forgebench policy serve` | | | ✓ |
| `forgebench github-app serve` | | | ✓ |
| Grok policy verification quota | | 50/day | 1000/day |
| SOC2 audit pack + dedicated onboarding | | | ✓ |

## Purchase & subscribe

```bash
# Start Stripe checkout (Team subscription or Enterprise payment)
forgebench subscribe team --seats 10 --email team@company.com --open

# Upgrade path when hitting a paid feature
forgebench upgrade --feature policy_serve

# Customer portal — license, usage, quotas
forgebench portal --open
```

Configure live billing with `STRIPE_SECRET_KEY`, `STRIPE_PRICE_TEAM_MONTHLY`, and `STRIPE_WEBHOOK_SECRET`.

## License management

```bash
# Activate a Team or Enterprise key on this machine
forgebench license activate FB-TEAM-...

# Check tier and feature access
forgebench license status
forgebench license check --feature policy_serve
forgebench license verify --online   # optional seat check via license server

# Customer success usage report (Team+)
forgebench license report --out forgebench-output/license-report.json
```

### Self-hosted license server

```bash
forgebench billing-serve license --port 8793
export FORGEBENCH_LICENSE_SERVER_URL=http://127.0.0.1:8793
```

Seat activations are tracked server-side; customers can validate with `license verify --online`.

License files are stored at `~/.config/forgebench/license.json` (override with `FORGEBENCH_LICENSE_PATH`).

Seat enforcement counts distinct machine activations per license ID. Enterprise tier supports unlimited seats when `unlimited_seats` is included in the key.

## Product analytics (distinct from review telemetry)

| Stream | Purpose | Default |
|--------|---------|---------|
| **Review telemetry** (`forgebench telemetry`) | Review posture distributions, benchmark runs | Off |
| **Product analytics** (`forgebench analytics`) | CLI adoption, license events, onboarding | Off |

```bash
forgebench analytics enable
forgebench analytics dashboard --out forgebench-output/analytics-dashboard
```

No automatic cloud upload. Teams may export bundles manually for customer success review.

## What stays free

- All core merge-risk review workflows
- Local feedback and repair prompts
- Merge Risk Benchmark reproduction
- Community roadmap and golden case contributions

## Early Access (2026 H1)

- Team pricing is introductory during Beta → Early Access
- No hosted review SaaS required for any tier
- Enterprise GitHub App is **customer-hosted**
- Annual billing and volume discounts: hello@forgebench.dev
- Design Partner → paid conversion: `forgebench crm convert`

## CRM & first customer

```bash
forgebench crm add "Acme Corp" --stage design_partner --seats 15
forgebench crm welcome --organization "Acme Corp"
forgebench crm checklist
```

Optional Linear sync: set `LINEAR_API_KEY` and `LINEAR_TEAM_ID`.

See [customer-onboarding-playbook.md](customer-onboarding-playbook.md) and [revenue/REVENUE_READINESS_SCORECARD.md](revenue/REVENUE_READINESS_SCORECARD.md).

## Honest limits

ForgeBench does not prove code is safe. Pricing covers **merge-risk workflow, policy governance, integration support, and operational readiness** — not certification of correctness.