# Broad monorepo refactor (REVIEW)

- Source: anonymized real PR (Cursor)
- Real merged PR refactoring Effect fallbacks across 42 files; dependency and broad-surface signals.

Reproduce locally:

```bash
forgebench review \
  --repo . \
  --diff examples/real_reports/monorepo_effect_refactor_review/patch.diff \
  --task examples/real_reports/monorepo_effect_refactor_review/task.md
```
