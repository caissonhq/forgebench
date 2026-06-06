# Usage Reporting for Paid Customers

## CLI report

```bash
forgebench license report --out monthly-usage.json
```

Bundle includes:

- License tier, seats, expiry
- Quota consumption (Grok verify, cloud export)
- Product analytics summary (opt-in)
- Review telemetry summary (opt-in, separate stream)

## Recommended cadence

| Tier | Cadence | Owner |
|------|---------|-------|
| Team | Monthly self-serve export | Engineering lead |
| Enterprise | Weekly automated export to CS | CSM |

## Health check for paid customers

```bash
forgebench doctor
forgebench status
forgebench license check --feature init_enterprise
forgebench analytics dashboard
```

Share `license report` JSON with hello@forgebench.dev for adoption review calls.

## Privacy

Reports contain no diff content. Paths and repos are hashed in analytics streams. Review telemetry is opt-in and separate from product analytics.