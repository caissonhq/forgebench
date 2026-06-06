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

## License management

```bash
# Activate a Team or Enterprise key on this machine
forgebench license activate FB-TEAM-...

# Check tier and feature access
forgebench license status
forgebench license check --feature policy_serve

# Customer success usage report (Team+)
forgebench license report --out forgebench-output/license-report.json
```

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

## Honest limits

ForgeBench does not prove code is safe. Pricing covers **merge-risk workflow, policy governance, integration support, and operational readiness** — not certification of correctness.