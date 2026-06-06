# Launch Execution Checklist — v1.0.0

Status key: ✅ Done · 🟡 Ready (needs manual action) · ⬜ Pending

## 1. Final release preparation

| Item | Status | Notes |
|------|--------|-------|
| Version bumped to 1.0.0 | ✅ | `pyproject.toml`, tests |
| CHANGELOG finalized | ✅ | `CHANGELOG.md` |
| Release notes drafted | ✅ | `docs/launch/RELEASE_v1.0.0.md` |
| Git tag `v1.0.0` | 🟡 | Push tag to trigger pipeline |
| PyPI publish | 🟡 | Automatic on tag via `release.yml` |
| Binary bundles + SBOM | 🟡 | Automatic on tag |
| Homebrew tap update | 🟡 | Needs `HOMEBREW_TAP_TOKEN` |

## 2. Marketing site

| Item | Status | Notes |
|------|--------|-------|
| Marketing home refreshed | ✅ | `docs/marketing-home.md` |
| Docs site index updated | ✅ | `site-docs/index.md` |
| Installation guide | ✅ | `site-docs/installation.md` |
| MkDocs build CI | ✅ | `.github/workflows/docs.yml` |
| Deploy to forgebench.dev | 🟡 | Publish `site/` to hosting |
| Demo GIF / screenshots | 🟡 | Capture `forgebench demo` terminal recording |

## 3. Public announcements

| Item | Status | Notes |
|------|--------|-------|
| X/Twitter thread | ✅ | `docs/launch/announcements.md` |
| Hacker News Show HN | ✅ | Copy ready |
| Reddit posts | ✅ | Copy ready |
| LinkedIn post | ✅ | Copy ready |
| Press one-pager | ✅ | `docs/launch/press-one-pager.md` |

## 4. Traction engine

| Item | Status | Notes |
|------|--------|-------|
| Design Partner program | ✅ | `docs/design-partner.md` enhanced |
| GitHub Discussions templates | ✅ | feature-request, general, success-story |
| `forgebench feedback --share` | ✅ | Success story template |
| Post-review share prompt | ✅ | In `next_actions_after_review` |
| Funnel analytics | ✅ | `funnel_stage` events |
| Adoption dashboard | ✅ | `forgebench analytics adoption-dashboard` |
| Early access signup | ✅ | GitHub Discussions + hello@forgebench.dev |

## 5. Marketplace

| Item | Status | Notes |
|------|--------|-------|
| VS Code publish | 🟡 | Run workflow with `VSCE_PAT` |
| JetBrains upload | 🟡 | `gradlew buildPlugin` |
| GitHub App Marketplace | 🟡 | `docs/github-marketplace-listing.md` |

## 6. Launch day

| Item | Status | Notes |
|------|--------|-------|
| README links verified | ✅ | Badges, install table |
| Monitor GitHub Issues/Discussions | ⬜ | Day-of |
| Respond to HN/Reddit comments | ⬜ | Day-of |
| Update `public-stats.json` weekly | ⬜ | Stars, installs |