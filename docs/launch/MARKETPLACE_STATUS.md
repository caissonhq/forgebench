# Marketplace Listings Status — v1.0.0 Launch

Last updated: **2026-06-06**

| Marketplace | Status | Kit / workflow | Action to go live |
|-------------|--------|----------------|-------------------|
| **PyPI** | 🟡 Tag-triggered | `.github/workflows/release.yml` | Push `v1.0.0` tag |
| **GitHub Releases** | 🟡 Tag-triggered | `release.yml` (binaries, SBOM) | Push tag |
| **Homebrew tap** | 🟡 CI ready | `.github/workflows/homebrew-tap.yml` | Set `HOMEBREW_TAP_TOKEN` |
| **VS Code** | 🟡 Kit ready | `integrations/vscode-forgebench/MARKETPLACE.md`, `vscode-marketplace.yml` | Run workflow with `VSCE_PAT` |
| **JetBrains** | 🟡 Plugin built | `integrations/jetbrains-forgebench/` | `gradlew buildPlugin` + upload |
| **GitHub Marketplace (Action)** | 🟡 Listing doc | `docs/github-marketplace-listing.md` | Publish tagged Action release |
| **GitHub App** | 🟡 Self-hosted kit | `docs/github-app-listing.md` | Org installs self-hosted; no hosted App |

## VS Code publish

```bash
# CI (preferred)
gh workflow run vscode-marketplace.yml

# Manual
cd integrations/vscode-forgebench
vsce publish -p $VSCE_PAT
```

## Verification

```bash
forgebench launch verify
```

See `LAUNCH_DAY_CHECKLIST.md` §1 and §5.