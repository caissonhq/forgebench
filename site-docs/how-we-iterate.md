# How We Iterate

Your feedback shapes ForgeBench after v1.0 — transparently and locally.

## Submit

```bash
forgebench feedback fnd_abc123 --status dismissed --kind ui_copy_changed --note "context"
forgebench feedback import discussion.md --format discussion
forgebench feedback --paid   # Design Partner structured prompts
```

No automatic upload. You control what leaves your machine.

## Our loop

1. **Triage** — Critical / High / Medium / Low (auto + manual override)
2. **Weekly review** — `forgebench weekly-review --period 7d`
3. **Roadmap** — Public [ROADMAP.md](https://github.com/caissonhq/forgebench/blob/main/ROADMAP.md) user-requested table
4. **Ship** — Golden cases, presets, patches → [CHANGELOG](https://github.com/caissonhq/forgebench/blob/main/CHANGELOG.md)

## Full playbook

[docs/iteration/how-we-iterate.md](https://github.com/caissonhq/forgebench/blob/main/docs/iteration/how-we-iterate.md) · [Weekly iteration playbook](https://github.com/caissonhq/forgebench/blob/main/docs/iteration/WEEKLY_ITERATION_PLAYBOOK.md)