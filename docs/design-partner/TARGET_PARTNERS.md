# Target Design Partners

Curated outreach list for ForgeBench v1.0 Design Partner pilots. Update status in [DESIGN_PARTNER_STATUS_TRACKER.md](DESIGN_PARTNER_STATUS_TRACKER.md).

## Tier 1 — High fit (agent-native teams)

| Segment | Examples / signals | Why they fit |
|---------|-------------------|--------------|
| Indie hackers shipping with Cursor | Solo founders on X building SaaS with agent PRs | Fast feedback loop, public success stories |
| Small AI-native startups (5–15 eng) | YC-era teams, "AI-first" positioning | Need merge gates without slowing agents |
| Cursor power users | Active in Cursor community, `.cursorrules` repos | Already feel merge-risk pain |
| DevTools / platform teams | Internal DX leads evaluating guardrails | Policy + CI kit buyers |

## Tier 2 — Strong fit (security-minded velocity)

| Segment | Examples / signals | Why they fit |
|---------|-------------------|--------------|
| Fintech / healthtech squads | Regulated but using Copilot/Cursor | BLOCK/REVIEW posture maps to compliance |
| Open-source maintainers | High agent PR volume on GitHub | Calibration feedback + golden cases |
| Agency dev shops | Multiple client stacks, agent workflows | Presets gallery + per-repo guardrails |

## Tier 3 — Exploratory

| Segment | Notes |
|---------|-------|
| Enterprise platform engineering | Longer sales cycle; route to Early Access |
| Security consultancies | Benchmark cohort + anonymized reports |
| AI coding tool builders | Integration feedback, MCP server users |

## Discovery channels

- X: `#Cursor`, `#ClaudeCode`, `#AIcoding`, merge-risk / agent PR threads
- Hacker News: Show HN posts mentioning AI code review
- GitHub: Repos with `forgebench.yml`, Cursor rules, agent PR templates
- Discord: Cursor, Latent Space, indie hacker communities
- Personal network: CaissonHQ contacts, former colleagues on agent-heavy teams

## Qualification criteria

1. Runs Cursor, Codex, Claude Code, or Copilot on production code
2. Willing to run `forgebench quickstart` before kickoff
3. Can commit to 4–6 week pilot + weekly async feedback
4. One repo or squad scope (not full enterprise rollout)

## CRM intake

```bash
forgebench crm add "Acme Engineering" --stage design_partner --seats 12
forgebench partner onboard --organization "Acme Engineering" --email "lead@acme.com"
```