# Weekly Iteration Playbook

Post-launch feedback loop for ForgeBench maintainers. Run every Friday (or after a release).

## One-command weekly review

```bash
forgebench weekly-review --period 7d --out forgebench-output/weekly-review
```

Produces:
- `digest-7d.txt` — prioritized insights + health metrics
- `roadmap-suggestions-7d.txt` — proposed ROADMAP items
- `whats-new-7d.md` — changelog draft from feedback
- `WEEKLY_REVIEW.md` — index + thank-you template

## Step-by-step

### 1. Collect feedback

```bash
forgebench feedback import discussion-export.md --format discussion
forgebench feedback import pilot-feedback.json --format json
forgebench feedback import support-thread.eml --format email
```

### 2. Triage (Critical / High / Medium / Low)

Auto-triage runs on record. Override manually:

```bash
forgebench feedback fnd_xyz --status dismissed --kind ui_copy_changed \
  --category false_positive --triage high --context "docs-only agent PR"
```

### 3. Digest + health check

```bash
forgebench feedback digest --period 7d
```

Review: false_positive_rate, resolution_rate, avg_nps, top_issues.

### 4. Roadmap sync

```bash
forgebench roadmap update --period 7d          # preview
forgebench roadmap update --period 7d --apply  # write ROADMAP.md
```

### 5. Rapid fixes

| Feedback type | Action |
|---------------|--------|
| False positive | `forgebench feedback --suggest-guardrails` → preset/policy PR |
| Calibration gap | `forgebench feedback promote --uid fnd_...` |
| Feature request | ROADMAP.md + Discussion reply |
| Missed concern | Golden case + reviewer lens review (P0) |

### 6. Communicate

```bash
forgebench feedback thank --name "Alex" --summary "ui_copy_changed false positive"
```

- Post What's New section to CHANGELOG.md
- Reply on GitHub Discussions / email
- Update [FEEDBACK_HEALTH_SCORECARD.md](FEEDBACK_HEALTH_SCORECARD.md)

### 7. Dashboard

```bash
forgebench analytics adoption-dashboard --public-stats examples/launch/public-stats.json
```

## SLA targets

| Priority | Response | Ship target |
|----------|----------|-------------|
| Critical | Same day | Next patch |
| High | 2 business days | This sprint |
| Medium | Weekly digest | Next minor |
| Low | Batched | Backlog |