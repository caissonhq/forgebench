# Launch Follow-up — Social & Community Monitoring

Post–v1.0.0 response playbook for X, Hacker News, and Reddit.

## Monitoring checklist

| Channel | URL / search | Check frequency |
|---------|--------------|-----------------|
| X | `@forgebench`, `#ForgeBench`, launch post thread | 2× daily (week 1) |
| Hacker News | Algolia: "ForgeBench", show HN replies | Daily |
| Reddit | r/programming, r/cursor, r/LocalLLaMA | Daily |
| GitHub | Issues, Discussions, stars | Daily |
| PyPI | Download stats | Weekly |

## Response templates

### X — thank you + CTA

> Thanks for trying ForgeBench! 🙌 First review: `forgebench quickstart` (~2 min). Feedback welcome: `forgebench feedback --share` or GitHub Discussions. Design Partners: 50% off Team → forgebench.dev/docs/design-partner/

### X — technical question

> Great question. ForgeBench is local-first — review runs on your machine, no diff upload. Evidence hierarchy: checks → static signals → guardrails → lenses. Docs: forgebench.dev · Happy to dig in via DM if you hit a false positive (`forgebench feedback`).

### HN — thoughtful reply

> Thanks for the feedback. [Specific answer to their point.] ForgeBench deliberately does not claim safety — it's merge-risk routing (BLOCK/REVIEW/LOW_CONCERN) with repair prompts for coding agents. We're actively calibrating false positives via Design Partner pilots; `forgebench feedback --suggest-guardrails` drafts local policy tuning. Issue/discussion links welcome.

### Reddit — indie hacker angle

> ForgeBench is free for solo devs (pipx install). Paid Team tier is for org policy + CI — but the core review is always local. Try `forgebench demo` for a 60s realistic run. I'm collecting Design Partners if you want white-glove setup.

### False positive report

> Sorry that burned you — that's exactly what we optimize in pilots. Please run `forgebench feedback FINDING_UID --status dismissed --kind <kind> --note "context"` and optionally `forgebench feedback --suggest-guardrails`. We'll use it for calibration, not auto-tuning your repo.

## Escalation

| Signal | Action |
|--------|--------|
| Security vulnerability report | SECURITY.md process |
| Viral negative thread | Founder response within 2h, offer 1:1 |
| Press inquiry | `docs/launch/press-one-pager.md` |
| Design Partner interest | `forgebench partner onboard` + license key |

## Metrics update ritual

Weekly, update `examples/launch/public-stats.json`:

```bash
forgebench analytics adoption-dashboard --public-stats examples/launch/public-stats.json
```

Fields: `github_stars`, `pypi_downloads_monthly`, `vscode_installs`, `design_partners_active`, `success_stories_published`.