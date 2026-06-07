# How We Iterate

ForgeBench is local-first, but we iterate in public. Here's how your feedback becomes improvements.

## Submit feedback

```bash
# Structured finding feedback
forgebench feedback fnd_abc123 --status dismissed --kind ui_copy_changed \
  --category false_positive --triage medium --note "docs-only noise"

# Import from Discussion export or email
forgebench feedback import my-post.md --format discussion

# Paid / Design Partner structured prompts
forgebench feedback --paid
```

Nothing uploads automatically. You choose what to share via export, Discussions, or email.

## What happens next

1. **Auto-triage** — Critical / High / Medium / Low based on outcome, severity, and recurrence
2. **Weekly digest** — Maintainers run `forgebench weekly-review`
3. **Roadmap** — High-priority themes sync to [ROADMAP.md](../../ROADMAP.md)
4. **Golden cases** — False positives become calibration cases via `forgebench feedback promote`
5. **Changelog** — Shipped fixes appear in [CHANGELOG.md](../../CHANGELOG.md)

## Transparency

| Artifact | Where |
|----------|-------|
| Public roadmap | [ROADMAP.md](../../ROADMAP.md) — user-requested improvements table |
| Release notes | [CHANGELOG.md](../../CHANGELOG.md) |
| Success stories | [design-partner/SUCCESS_STORIES.md](../design-partner/SUCCESS_STORIES.md) |
| Adoption metrics | `forgebench analytics adoption-dashboard` |

## Response expectations

| Your feedback | Typical response |
|---------------|------------------|
| False positive | Guardrail suggestion or preset fix; thank-you within a week |
| Missed concern | P0 triage; golden case + patch target |
| Feature idea | ROADMAP entry; Discussion reply |
| Bug | Issue + patch in CHANGELOG |

## Thank you

We reply with:

```bash
forgebench feedback thank --name "Your Name" --summary "your ui_copy_changed report"
```

Design Partners get priority via `forgebench feedback digest --period 7d` in weekly syncs.

See [WEEKLY_ITERATION_PLAYBOOK.md](WEEKLY_ITERATION_PLAYBOOK.md) for the maintainer workflow.