# First 30 Days Traction Plan

Post–v1.0.0 launch execution plan for ForgeBench initial adoption.

## Week 1 — Launch pulse

| Day | Action | Owner | Metric |
|-----|--------|-------|--------|
| 1 | Post X + HN + Reddit (see `docs/launch/announcements.md`) | GTM | Impressions, click-through |
| 1–2 | Monitor and respond to launch threads (`docs/launch/LAUNCH_FOLLOWUP.md`) | GTM | Response time <2h |
| 2 | Update `examples/launch/public-stats.json` with real GitHub/PyPI/VS Code numbers | GTM | Dashboard accuracy |
| 3 | Send Tier 1 outreach (5 emails, 10 X DMs) | GTM | 3 discovery calls booked |
| 4–5 | Onboard first 2 Design Partners (`forgebench partner onboard`) | CS | 2 kits delivered |
| 7 | Publish first success story (anonymized) | Marketing | 1 Discussion post |

## Week 2 — Activation

| Action | Command / artifact |
|--------|-------------------|
| Track install → first review funnel | `forgebench analytics adoption-dashboard` |
| Weekly feedback digest | `forgebench feedback digest --days 7` |
| CRM pipeline review | `forgebench crm list` |
| False-positive triage | `forgebench feedback --suggest-guardrails` |
| Deliver 3 more pilot license keys | `forgebench partner keys` |

**Target:** 10 `first_review` milestones (local + partner reports), 5 Design Partner intakes.

## Week 3 — Conversion experiments

| Action | Notes |
|--------|-------|
| Test paid flow end-to-end | subscribe → license activate → team init |
| A/B upgrade CTAs | Post-first-review banner vs doctor checklist |
| Partner weekly syncs | Review `feedback digest` + roadmap candidates |
| Second success story | Team with CI integration |

**Target:** 2 pilots → paid conversion conversations, 1 `subscribe team` checkout started.

## Week 4 — Iterate & publish

| Action | Notes |
|--------|-------|
| Update ROADMAP from feedback | Top 3 user-requested items |
| Refresh adoption dashboard | Public stats + funnel narrative |
| Launch follow-up post on X | "What we learned from first 20 reviews" |
| Design Partner cohort retro | NPS + false-positive rate |

**Target:** 8 active Design Partners, 3 paying Team customers or committed POs.

## KPI dashboard

| KPI | Week 1 | Week 2 | Week 3 | Week 4 |
|-----|--------|--------|--------|--------|
| GitHub stars | — | — | — | — |
| PyPI installs (weekly) | — | — | — | — |
| Design Partner intakes | 2 | 5 | 8 | 10 |
| Pilots active | 2 | 5 | 8 | 8 |
| Paid conversions | 0 | 0 | 1 | 3 |
| Success stories published | 1 | 1 | 2 | 3 |

Fill actuals weekly in [DESIGN_PARTNER_STATUS_TRACKER.md](DESIGN_PARTNER_STATUS_TRACKER.md).

## Commands cheat sheet

```bash
forgebench partner onboard --organization "Acme" --out forgebench-output/partner-kit
forgebench feedback digest --days 7 --out forgebench-output/weekly-digest.txt
forgebench analytics adoption-dashboard --public-stats examples/launch/public-stats.json
forgebench crm list
forgebench upgrade --tier team
```