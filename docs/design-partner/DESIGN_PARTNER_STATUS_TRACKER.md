# Design Partner Status Tracker

Update weekly. Sync with `forgebench crm list` and GitHub Discussions labeled `design-partner`.

Last updated: **2026-06-06**

## Pipeline summary

| Stage | Count | Target (30 days) |
|-------|-------|------------------|
| Lead | 0 | 15 |
| Design Partner (active pilot) | 0 | 8 |
| Paid | 0 | 3 |
| Churned / declined | 0 | — |

## Active pilots

| Organization | Contact | Stack | Agent | Start | License | Status | Next step |
|--------------|---------|-------|-------|-------|---------|--------|-----------|
| *— add rows as partners onboard —* | | | | | | | |

**License column:** `forgebench partner keys` · **Status:** intake / kickoff / week-2 / converting / paid

## Outreach queue (Tier 1)

| Name / org | Channel | Sent | Response | Notes |
|------------|---------|------|----------|-------|
| Indie hacker (TBD) | X DM | | | Template: OUTREACH_TEMPLATES.md |
| Small AI team (TBD) | Email | | | |
| Cursor power user (TBD) | X DM | | | |
| DX lead (TBD) | Email | | | |
| OSS maintainer (TBD) | GitHub | | | |

## Feedback themes (from `forgebench feedback digest`)

| Week | Top dismissed kind | Roadmap candidate | Action |
|------|-------------------|-------------------|--------|
| W1 | — | — | Run first digest after partner feedback |

## Conversion tracker

| Organization | Pilot end | False-positive rate | NPS | Converted | ARR notes |
|--------------|-----------|---------------------|-----|-----------|-----------|
| — | — | — | — | — | — |

## License key inventory

```bash
forgebench partner keys
```

| Slot | Tier | Assigned to | Delivered |
|------|------|-------------|-----------|
| Pilot Alpha | team | unassigned | |
| Pilot Beta | team | unassigned | |
| Pilot Gamma | team | unassigned | |
| Pilot Delta | team | unassigned | |
| Pilot Epsilon | enterprise | unassigned | |
| Pilot Zeta | team | unassigned | |
| Pilot Eta | team | unassigned | |
| Pilot Theta | team | unassigned | |

## Weekly ritual (Fridays)

1. `forgebench feedback digest --days 7 --out forgebench-output/weekly-digest.txt`
2. Update this tracker + `forgebench crm list`
3. Refresh `examples/launch/public-stats.json`
4. Post roadmap candidates to ROADMAP.md if ≥3 partners request same item