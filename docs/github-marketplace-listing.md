# GitHub Marketplace — ForgeBench App Listing

Self-hosted GitHub App for org-level merge-risk policy enforcement.

## Listing metadata

| Field | Value |
|-------|-------|
| **Name** | ForgeBench |
| **Tagline** | Merge-risk gates for AI-generated pull requests |
| **Category** | Code quality · Security · CI/CD |
| **Pricing** | Free (self-hosted infrastructure) |

## Description (short)

ForgeBench adds merge-risk review and org policy enforcement to AI-assisted development workflows. Deploy the webhook receiver in your infrastructure — no hosted code review service required.

## Description (full)

ForgeBench reviews AI-generated diffs before merge and can gate pull requests based on merge posture (`BLOCK`, `REVIEW`, `LOW_CONCERN`).

**What you get**

- Self-hosted GitHub App webhook receiver (`forgebench github-app serve`)
- Auto-configuration on installation (org enforcement defaults)
- Trusted CI guardrails via `forgebench team init`
- Check Run integration and signed posture attestation

**Permissions (minimum)**

- `checks: write` — post Check Runs
- `pull_requests: read` — PR metadata
- `contents: read` — default branch policy files
- `metadata: read`

**Events**

`pull_request`, `check_run`, `installation`, `organization`

## Screenshots (capture before submit)

1. `forgebench team init` terminal output
2. GitHub Check Run with ForgeBench posture
3. `forgebench doctor --checklist` adoption view
4. VS Code findings sidebar

## Logo

`https://forgebench.dev/assets/forgebench-logo.svg` (128×128 PNG export for upload)

## Setup URL

`https://forgebench.dev/docs/github-app-listing.md`

## Submit checklist

- [ ] Export manifest: `forgebench github-app manifest --out manifest.json`
- [ ] Deploy webhook receiver with `FORGEBENCH_GITHUB_WEBHOOK_SECRET`
- [ ] Pilot repo has `.github/forgebench.yml` on default branch
- [ ] Run `forgebench github-app enforce --config org-enforcement.json --posture REVIEW`
- [ ] Upload screenshots and logo to Marketplace listing