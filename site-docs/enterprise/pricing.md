# Pricing & Licensing

See the full tier matrix in [docs/pricing.md](https://github.com/caissonhq/forgebench/blob/main/docs/pricing.md).

## Quick reference

| Tier | Price | License |
|------|-------|---------|
| Free | $0 | None |
| Team | $29/dev/mo (EA) | `FB-TEAM-...` |
| Enterprise | Custom | `FB-ENTERPRISE-...` |

## Commands

```bash
forgebench subscribe team --seats 10 --open
forgebench license activate FB-TEAM-...
forgebench license status
forgebench license verify --online
forgebench upgrade --feature init_enterprise
forgebench portal --open
forgebench license report

forgebench analytics enable
forgebench analytics dashboard
```

Full page: [Pricing](../pricing.md)

## Analytics streams

- **Review telemetry** — posture and benchmark events (`forgebench telemetry`)
- **Product analytics** — CLI adoption and license events (`forgebench analytics`)

Both are opt-in and local-only by default.