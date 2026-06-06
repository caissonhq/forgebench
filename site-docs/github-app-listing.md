# GitHub App — Public Listing Readiness

ForgeBench ships a **self-hosted** GitHub App kit. Customers deploy the webhook receiver in their own infrastructure.

## Manifest export

```bash
forgebench github-app manifest --out forgebench-output/github-app-manifest.json
```

The manifest includes:

- Minimum permissions (`checks: write`, `pull_requests: read`, `contents: read`, `metadata: read`)
- Events: `pull_request`, `pull_request_review`, `check_run`, `organization`, `installation`
- Org policy enforcement defaults
- Public listing metadata (tagline, logo URL, documentation links)

## Auto-configuration on install

When the app is installed, the webhook receiver auto-generates:

- `forgebench-output/github-app-installs/installation-<id>/installation.json`
- `org-enforcement.json` with sensible defaults
- `README.md` with next-step commands

Run the receiver:

```bash
export FORGEBENCH_GITHUB_WEBHOOK_SECRET="<16+ characters>"
forgebench github-app serve --config path/to/org-enforcement.json
```

## Post-install checklist

1. `forgebench team init` on pilot repos (CI workflow + trusted `.github/forgebench.yml`)
2. `forgebench doctor --repo .`
3. `forgebench github-app enforce --config org-enforcement.json --posture REVIEW`
4. Open a test PR and confirm Check Run + policy gate

## Marketplace page copy

**Name:** ForgeBench  
**Tagline:** Merge-risk review for AI-generated PRs  
**Description:** Org-level merge-risk policy enforcement for AI-generated pull requests. Self-hosted webhook receiver; ForgeBench review runs in your infrastructure.  
**Logo:** `https://forgebench.dev/assets/forgebench-logo.svg`

## Privacy

ForgeBench does not operate a hosted review service for customer code by default. Webhook payloads are processed on infrastructure you control.