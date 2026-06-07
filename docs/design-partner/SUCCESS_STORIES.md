# ForgeBench Success Stories

Published and draft success stories from early adopters. Generate new templates with `forgebench feedback --share`.

## Story 1 — Solo developer, Python API (anonymized)

**Published:** 2026-06-06 · [Show and Tell Discussion](https://github.com/caissonhq/forgebench/discussions)

### Summary

A solo developer running Cursor on a FastAPI side project ran `forgebench quickstart` after seeing the v1.0 launch post. First review returned **REVIEW** with 3 findings — including `implementation_without_tests` on a new endpoint handler.

### What happened

- Agent generated a PATCH with route + handler but only updated an existing test file superficially
- ForgeBench Test Skeptic flagged weak coverage; repair prompt pasted back into Cursor
- Re-review dropped to **LOW_CONCERN** after tests added

### Impact

- Caught missing test coverage before push to main
- ~20 minutes saved vs discovering in production
- User joined Design Partner waitlist for Team CI kit

### Quote (paraphrased)

> "Finally something that treats agent PRs like a skeptical senior engineer, not a linter."

### Commands used

```bash
pipx install forgebench
forgebench quickstart
forgebench feedback --share --posture REVIEW --finding-count 3 --agent cursor
```

---

## Submit yours

```bash
forgebench feedback --share --posture REVIEW --finding-count N --note "Your story"
```

Post to [GitHub Discussions — Show and Tell](https://github.com/caissonhq/forgebench/discussions/new?category=show-and-tell).