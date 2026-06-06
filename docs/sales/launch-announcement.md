# ForgeBench v1.0.0 Launch Announcement

**Subject:** ForgeBench v1.0 — merge-risk review for AI-generated code is live

---

**ForgeBench v1.0.0** is now publicly available — local merge-risk review for teams shipping AI-generated diffs.

ForgeBench answers one question before merge: *Would a serious engineer ship this patch?*

**What's included in Early Access:**

- Local CLI + VS Code / JetBrains extensions
- `forgebench demo` — realistic first review in 60 seconds
- `forgebench init --enterprise` — org policy, CI workflow, team onboarding kit
- Merge Risk Benchmark (47+ golden cases)
- Team tier: shared policy, analytics dashboard, license seat management

**Free forever:** core `review`, `review-pr`, calibration, MCP, GitHub Action.

**Try it:**

```bash
pipx install forgebench
forgebench quickstart
```

Docs: https://forgebench.dev · Pricing: [docs/pricing.md](../pricing.md)

Teams: hello@forgebench.dev for EA pricing and onboarding.

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.