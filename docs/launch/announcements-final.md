# ForgeBench v1.0.0 — Final Launch Posts

**Ready to post · 2026-06-06**

Also generated via: `forgebench launch announce --out forgebench-output/launch-posts.txt`

---

## X / Twitter Thread (6 tweets)

### Tweet 1/6 — Hook

Would a serious engineer merge this AI-generated diff?

ForgeBench v1.0 is live — local merge-risk review for Cursor, Codex, Claude Code & Copilot.

```bash
pipx install forgebench && forgebench quickstart
```

https://forgebench.dev

### Tweet 2/6 — What you get

ForgeBench reads your agent diff + original task prompt and returns:

- Posture: `BLOCK` / `REVIEW` / `LOW_CONCERN`
- Evidence-backed findings
- Repair prompt → paste back into your agent

No hosted review. Your code stays on your machine.

### Tweet 3/6 — 60-second demo

Try it in 60 seconds:

```
forgebench demo
forgebench doctor --checklist
```

### Tweet 4/6 — Teams & Design Partners

Engineering teams:

```
forgebench team init
```

Org policy · CI workflow · onboarding docs — one wizard.

**Design Partner program open** → 50% Team discount + white-glove onboarding  
https://github.com/caissonhq/forgebench/discussions

### Tweet 5/6 — Integrations

Also shipping:

- VS Code sidebar extension
- GitHub Action + self-hosted App kit
- Merge Risk Benchmark (47+ golden cases)

https://github.com/caissonhq/forgebench

### Tweet 6/6 — CTA

Star us if merge-risk gates for agent PRs resonate

Share your first review: `forgebench feedback --share`

ForgeBench does not prove code is safe.

---

## Hacker News — Show HN

**Title (paste exactly):**

```
Show HN: ForgeBench – merge-risk review for AI-generated diffs (local CLI, v1.0)
```

**Body:**

Hi HN — we built ForgeBench to answer one question before merge: *would a serious engineer ship this patch?*

Coding agents (Cursor, Codex, Claude Code, Copilot) ship diffs fast. Generic linters miss task drift, weak tests on behavior changes, and scope creep. ForgeBench is a local CLI that returns a cited merge posture (BLOCK / REVIEW / LOW_CONCERN), SARIF, and a repair prompt you paste back into your agent.

**Try it:**

```bash
pipx install forgebench
forgebench quickstart
```

**Evidence hierarchy:**

1. Deterministic checks (optional `--run-checks`)
2. Static risk signals on the diff
3. Repo guardrails (`forgebench.yml`)
4. Heuristic review lenses (scope, tests, contracts)
5. Optional LLM review (advisory only)

Deterministic failures are never downgraded. No hosted SaaS — runs on your machine.

**v1.0 includes:** team init wizard, presets gallery, VS Code extension, self-hosted GitHub App kit, Merge Risk Benchmark (47+ golden cases).

Open source core CLI. Team/Enterprise adds licensing, analytics dashboard, org policy serve.

https://forgebench.dev · https://github.com/caissonhq/forgebench

We'd love feedback — especially false positives from real agent PRs. `forgebench feedback --share` generates a Discussion template.

ForgeBench does not prove code is safe.

---

## Reddit — r/programming (schedule T+2h after HN)

**Title:** `[Tool] ForgeBench v1.0 — local merge-risk review before you merge AI-generated code`

**Body:** See `docs/launch/announcements.md` Reddit section.

---

## LinkedIn (schedule launch day AM)

See `docs/launch/announcements.md` LinkedIn section.