# Feedback Health Scorecard

Track post-launch feedback loop health. Update weekly after `forgebench weekly-review`.

Last updated: **2026-06-06**

## Current period (7d)

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Feedback volume | — | ≥5/week at launch | |
| False positive rate | — | <40% | |
| Resolution rate | — | >50% | |
| Avg NPS (optional) | — | ≥7 | |
| Sentiment score | — | ≥0 | |
| Critical triage items | — | 0 open >7d | |
| Roadmap items added | — | ≥1/week if volume ≥5 | |

```bash
forgebench feedback digest --period 7d
forgebench analytics adoption-dashboard
```

## Triage backlog

| Priority | Open | Oldest | Theme |
|----------|------|--------|-------|
| Critical | 0 | — | |
| High | 0 | — | |
| Medium | 0 | — | |
| Low | 0 | — | |

## Top issues (30d)

| Kind / theme | Count | Priority | Resolution |
|--------------|-------|----------|------------|
| — | — | — | — |

## Post-launch health signals

| Signal | This week | Last week | Notes |
|--------|-----------|-----------|-------|
| False positive reports | — | — | |
| Upgrade prompts shown | — | — | product analytics |
| Design partner digests | — | — | |
| Golden cases promoted | — | — | `feedback promote` |
| Success stories | — | — | `feedback --share` |

## Commands

```bash
forgebench weekly-review --period 7d
forgebench roadmap update --period 7d --apply
forgebench feedback promote --uid <UID>
```