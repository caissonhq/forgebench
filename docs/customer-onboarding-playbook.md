# Customer Onboarding Playbook — Paid Tiers

Premium onboarding for Team and Enterprise customers. Local-first, no hosted code review required.

## Tier overview

| Tier | Price (EA) | Activation |
|------|------------|------------|
| **Team** | $29 / developer / month | `forgebench subscribe team` → `license activate` |
| **Enterprise** | Custom annual | Contact hello@forgebench.dev |

## Purchase flow

```bash
# 1. Customer selects tier
forgebench subscribe team --seats 10 --email team@company.com --open

# 2. After payment, deliver license key (email or portal)
forgebench license activate FB-TEAM-...

# 3. Verify
forgebench license verify --online   # optional seat check against license server
forgebench license status
```

## Self-hosted infrastructure (optional)

```bash
# License validation server (seat registry)
forgebench billing-serve license --port 8793

# Stripe webhook receiver
export STRIPE_WEBHOOK_SECRET=whsec_...
forgebench billing-serve stripe-webhook --port 8794
```

Set `FORGEBENCH_LICENSE_SERVER_URL` for online validation in customer environments.

## Customer portal

```bash
forgebench portal --out forgebench-output/portal --open
```

Shows license status, daily quotas (Grok verify, cloud export, policy serve), CRM pipeline, and policy management commands.

## Design Partner → paying customer

1. Complete 4–6 week pilot (see `docs/design-partner.md`)
2. Export metrics: `forgebench license report --out report.json`
3. Offer EA pricing lock-in via `forgebench subscribe`
4. Update CRM: `forgebench crm add "Org" --stage paid`
5. Send welcome: `forgebench crm welcome --organization "Org" --tier team`
6. Track checklist: `forgebench crm checklist`

## Upgrade prompts (free users)

When a free user hits a paid feature, ForgeBench shows:

```
Feature 'policy_serve' requires enterprise tier or higher.
Run `forgebench upgrade --tier enterprise` or `forgebench subscribe enterprise`
```

## Customer success touchpoints

| Day | Action |
|-----|--------|
| 0 | License delivery + welcome sequence |
| 1 | Team init + first review |
| 3 | CI wiring review |
| 7 | Usage report + false-positive tuning |
| 30 | Renewal check-in + success story |

## CRM + Linear (optional)

```bash
forgebench crm add "Acme" --stage design_partner --seats 15
export LINEAR_API_KEY=...
export LINEAR_TEAM_ID=...
# Pipeline updates auto-sync to Linear when configured
```

ForgeBench does not prove code is safe.