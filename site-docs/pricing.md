# Pricing

ForgeBench core review is **free forever**. Team and Enterprise add org governance, analytics, and supported self-hosted integrations.

## Compare tiers

| | **Free** | **Team** | **Enterprise** |
|---|----------|----------|----------------|
| **Price** | $0 | $29 / dev / mo (EA) | Custom annual |
| **Best for** | Solo devs, OSS | Engineering teams | Regulated / platform orgs |
| **Seats** | Unlimited machines | Per-seat activation | Org-wide |

## Buy Team

```bash
forgebench subscribe team --seats 10 --open
forgebench license activate FB-TEAM-...
forgebench portal
```

Enterprise: contact [hello@forgebench.dev](mailto:hello@forgebench.dev) or `forgebench subscribe enterprise`.

## What's included

### Free (always)

- `review`, `review-pr`, `demo`, calibration, MCP, IDE extensions
- Local telemetry and analytics dashboard export

### Team

- `forgebench team init`, org policy layers, policy tests in CI
- Cloud analytics export quota (10/day)
- Grok verify quota (50/day)
- Usage reporting (`forgebench license report`)

### Enterprise

- `forgebench policy serve`, `forgebench github-app serve`
- Grok verify (1000/day), policy serve requests (100k/day)
- SOC2-style security pack, dedicated onboarding

## Usage-based quotas

| Quota | Free | Team | Enterprise |
|-------|:----:|:----:|:----------:|
| Grok verify / day | 0 | 50 | 1000 |
| Cloud analytics export / day | 0 | 10 | 1000 |
| Policy serve requests / day | 0 | 0 | 100,000 |

## Commands

```bash
forgebench subscribe team --seats 5
forgebench upgrade --feature policy_serve
forgebench license status
forgebench license verify --online
forgebench portal --open
forgebench crm checklist
```

[Full pricing matrix](https://github.com/caissonhq/forgebench/blob/main/docs/pricing.md) · [Customer onboarding playbook](https://github.com/caissonhq/forgebench/blob/main/docs/customer-onboarding-playbook.md)

ForgeBench does not prove code is safe.