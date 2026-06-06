# ForgeBench v1.0.0 — Launch Announcements

Ready-to-post copies. Replace `[GIF]` with demo asset when captured.

---

## X / Twitter (thread)

**Tweet 1 (hook)**

> Would a serious engineer merge this AI-generated diff?
>
> ForgeBench v1.0 is live — local merge-risk review for Cursor, Codex, Claude Code & Copilot output.
>
> `pipx install forgebench && forgebench quickstart`
>
> https://forgebench.dev

**Tweet 2 (what it does)**

> ForgeBench reads your agent's diff + original task prompt and returns:
> • Posture: BLOCK / REVIEW / LOW_CONCERN
> • Evidence-backed findings
> • Repair prompt to paste back into your agent
>
> No hosted review. Your code stays local.

**Tweet 3 (demo)**

> Try it in 60 seconds:
> ```
> forgebench demo
> forgebench doctor --checklist
> ```
> [GIF: demo terminal output]

**Tweet 4 (teams)**

> Engineering teams: `forgebench team init` sets up org policy, CI workflow, and onboarding docs in one wizard.
>
> Design Partner program open — priority support + Team license during pilot.
> https://github.com/caissonhq/forgebench/discussions

**Tweet 5 (CTA)**

> ⭐ Star us: https://github.com/caissonhq/forgebench
> VS Code: search "ForgeBench"
> Feedback: `forgebench feedback --share`

---

## Hacker News (Show HN)

**Title:** Show HN: ForgeBench – merge-risk review for AI-generated diffs (local CLI, v1.0)

**Body:**

Hi HN — we built ForgeBench to answer one question before merge: *would a serious engineer ship this patch?*

Agents (Cursor, Codex, Claude Code) ship diffs fast. Generic linters miss task drift, missing tests on behavior changes, and scope creep. ForgeBench is a local CLI that produces a cited merge posture (BLOCK / REVIEW / LOW_CONCERN), SARIF, and a repair prompt you paste back into your agent.

**Try it:**

```bash
pipx install forgebench
forgebench quickstart
```

**How it works (evidence hierarchy):**

1. Deterministic checks (optional `--run-checks`)
2. Static risk signals on the diff
3. Repo guardrails (`forgebench.yml`)
4. Heuristic review lenses (scope, tests, contracts)
5. Optional LLM review (advisory only)

Deterministic failures are never downgraded. No hosted service — runs on your machine.

**v1.0 includes:** team init wizard, presets gallery, VS Code sidebar extension, self-hosted GitHub App kit, Merge Risk Benchmark (47+ golden cases).

Open source core CLI. Team/Enterprise adds licensing, analytics dashboard, org policy serve.

https://forgebench.dev · https://github.com/caissonhq/forgebench

We'd love feedback — especially false positives from real agent PRs. `forgebench feedback --share` generates a Discussion template.

ForgeBench does not prove code is safe.

---

## Reddit (r/devtools, r/LocalLLaMA, r/programming)

**Title:** [Tool] ForgeBench v1.0 — local merge-risk review before you merge AI-generated code

**Body:**

I shipped v1.0 of ForgeBench — a CLI that reviews coding-agent diffs locally before merge.

**Problem:** Agents solve the task but ship broad diffs, weak tests, or scope creep. "LGTM" isn't enough.

**What ForgeBench does:**
- Takes a unified git diff + original task prompt
- Returns BLOCK / REVIEW / LOW_CONCERN with findings
- Writes a repair prompt for your agent
- Optional GitHub PR review via `gh`

**Quick start:**
```bash
pipx install forgebench
forgebench demo
```

Free for local review. Team tier adds org policy, CI kit, analytics.

GitHub: https://github.com/caissonhq/forgebench  
Docs: https://forgebench.dev/docs/installation/

Happy to answer questions about the architecture or false-positive tuning.

---

## LinkedIn

**ForgeBench v1.0 — merge-risk governance for AI-assisted engineering**

Your team ships faster with Cursor, Codex, and Claude Code. Who reviews the diffs before `main`?

ForgeBench v1.0 is a local CLI + IDE extensions that classify merge risk with evidence — not vibes. Posture: BLOCK, REVIEW, or LOW_CONCERN. Repair loop built in.

✅ Solo developers: `forgebench quickstart` in ~2 minutes  
✅ Engineering teams: org policy, CI workflow, GitHub App kit  
✅ Security-minded leads: SOC2-style controls documentation

We're opening a Design Partner program for teams adopting agent-assisted development at scale.

Learn more: https://forgebench.dev  
Install: `pipx install forgebench`

#DevTools #AI #CodeReview #DeveloperExperience