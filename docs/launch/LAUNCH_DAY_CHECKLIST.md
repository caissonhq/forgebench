# Launch Day Execution Checklist — v1.0.0

**Executive Order 020 · Last updated: 2026-06-06**

Status: ✅ Done · 🟡 Ready (manual) · ⬜ Pending · 🔴 Blocker

Run automated checks: `forgebench launch verify` · `forgebench launch checklist`

---

## 1. Final release & versioning

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1.1 | Version `1.0.0` in `pyproject.toml` | ✅ | Verified |
| 1.2 | `CHANGELOG.md` v1.0.0 section | ✅ | |
| 1.3 | `docs/launch/RELEASE_v1.0.0.md` | ✅ | |
| 1.4 | Git tag `v1.0.0` pushed | 🟡 | `git tag v1.0.0 && git push origin v1.0.0` |
| 1.5 | Release pipeline (PyPI, wheels, SBOM) | 🟡 | Triggered by tag via `.github/workflows/release.yml` |
| 1.6 | Binary bundles + macOS `.pkg` | 🟡 | Automatic on tag |
| 1.7 | Homebrew tap update | 🟡 | Needs `HOMEBREW_TAP_TOKEN` |
| 1.8 | Local wheel smoke | ✅ | `dist/forgebench-1.0.0*.whl` present |

## 2. Marketing site & documentation

| # | Item | Status | Notes |
|---|------|--------|-------|
| 2.1 | `docs/marketing-home.md` polished | ✅ | Hero + CTAs |
| 2.2 | `site-docs/index.md` launch CTAs | ✅ | quickstart · team init · Design Partner |
| 2.3 | MkDocs build `--strict` | ✅ | `mkdocs build --strict` |
| 2.4 | GitHub Pages deploy | 🟡 | Set `PAGES_DEPLOY=true` + enable Pages |
| 2.5 | forgebench.dev DNS → Pages | 🟡 | Point CNAME to GitHub Pages |
| 2.6 | Demo GIF | 🟡 | Capture `forgebench demo` terminal recording |

## 3. Public announcements

| # | Item | Status | Notes |
|---|------|--------|-------|
| 3.1 | X thread finalized | ✅ | `docs/launch/announcements-final.md` |
| 3.2 | Post X thread | ⬜ | Launch window: 9–11 AM PT |
| 3.3 | Show HN posted | ⬜ | `announcements-final.md` title + body |
| 3.4 | Reddit r/programming | ⬜ | Schedule T+2h after HN |
| 3.5 | Reddit r/devtools + r/LocalLLaMA | ⬜ | `announcements.md` |
| 3.6 | LinkedIn post | ⬜ | Launch day AM |
| 3.7 | Blog announcement | ✅ | `docs/launch/BLOG_ANNOUNCEMENT.md` |

## 4. Traction & monitoring

| # | Item | Status | Notes |
|---|------|--------|-------|
| 4.1 | Monitoring playbook active | ✅ | `docs/launch/LAUNCH_FOLLOWUP.md` |
| 4.2 | Respond GitHub Issues/Discussions | ⬜ | <2h during launch day |
| 4.3 | Respond HN/X/Reddit | ⬜ | Use LAUNCH_FOLLOWUP templates |
| 4.4 | Update `public-stats.json` | 🟡 | `forgebench launch stats --stars N` |
| 4.5 | Adoption dashboard refresh | 🟡 | `forgebench analytics adoption-dashboard` |
| 4.6 | Seed Discussions (3 posts) | ✅ | `forgebench launch seed-discussions` |

## 5. Design Partner activation

| # | Item | Status | Notes |
|---|------|--------|-------|
| 5.1 | Outreach templates ready | ✅ | `docs/design-partner/OUTREACH_TEMPLATES.md` |
| 5.2 | 8 pilot license keys | ✅ | `examples/design-partner/pilot-license-keys.json` |
| 5.3 | Send Tier 1 outreach (5+) | ⬜ | Log in `OUTREACH_DAY1.md` |
| 5.4 | First partner onboarded | ⬜ | `forgebench partner onboard` |
| 5.5 | Status tracker updated | 🟡 | `DESIGN_PARTNER_STATUS_TRACKER.md` |

## 6. Post-launch day review

| # | Item | Status | Notes |
|---|------|--------|-------|
| 6.1 | Day-1 review | 🟡 | `forgebench launch day1-review` |
| 6.2 | Weekly review | 🟡 | `forgebench weekly-review --period 7d` |
| 6.3 | ROADMAP update | 🟡 | `forgebench roadmap update --apply` |
| 6.4 | Launch retrospective | ✅ | `docs/launch/launch-retrospective.md` |

---

## Launch sequence (recommended)

```
T-24h   forgebench launch verify
T-1h    mkdocs build --strict · final README check
T+0     Post X thread (tweet 1–6, 5 min apart)
T+15m   Show HN
T+30m   GitHub Discussions seed posts
T+2h    Reddit r/programming
T+4h    forgebench launch stats --stars <N> --hn-points <N>
T+EOD   forgebench launch day1-review
T+1d    forgebench weekly-review · launch-retrospective fill-in
```

## Quick commands

```bash
forgebench launch verify
forgebench launch announce
forgebench launch seed-discussions --out forgebench-output/discussions-seed.txt
forgebench launch stats --stars 42 --partners 2 --reviews 15
forgebench analytics adoption-dashboard --public-stats examples/launch/public-stats.json
forgebench partner onboard --organization "Acme" --out forgebench-output/partner-kit
```