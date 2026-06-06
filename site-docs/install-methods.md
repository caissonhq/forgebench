# Install ForgeBench

ForgeBench is a local CLI. Pick the install path that fits your environment.

```bash
forgebench install          # detect platform & recommend best method
forgebench install methods  # full comparison table
```

See the [Installation & Getting Started](https://forgebench.dev/docs/installation/) guide on the docs site.

## Comparison

| Method | One-command install | Best for | Upgrade |
|--------|---------------------|----------|---------|
| **pipx** | `pipx install forgebench` | Solo developers | `pipx upgrade forgebench` |
| **pip** | `pip install forgebench` | CI, Docker, venvs | `pip install --upgrade forgebench` |
| **Homebrew** | `brew tap caissonhq/tap && brew install forgebench` | macOS/Linux workstations | `brew upgrade forgebench` |
| **Binary** | GitHub Releases `.tar.gz` | Air-gapped / no pip | Replace bundle |
| **macOS .pkg** | GitHub Releases `.pkg` | Enterprise Mac fleets | Re-run installer |
| **VS Code** | Marketplace `caissonhq.forgebench` | IDE sidebar (CLI required) | Extension auto-update |
| **JetBrains** | Marketplace plugin | IntelliJ/PyCharm (CLI required) | Plugin update |
| **Source** | `pip install -e .` | Contributors | `git pull && pip install -e .` |

## pipx (recommended for CLI)

```bash
pipx install forgebench
forgebench quickstart
```

## pip

```bash
pip install forgebench
forgebench doctor --checklist
```

## Homebrew

```bash
brew tap caissonhq/tap
brew install forgebench
forgebench doctor
```

Formula auto-updated via `.github/workflows/homebrew-tap.yml` on each release.

## Binary bundle

Official per-platform `.tar.gz` artifacts are attached to [GitHub Releases](https://github.com/caissonhq/forgebench/releases). Built by `scripts/build_binary_bundle.py` in CI.

## macOS .pkg

macOS `.pkg` installers are built on release (see `packaging/macos/build_pkg.sh`).

## Shell completions

```bash
eval "$(forgebench install completions --shell bash)"
eval "$(forgebench install completions --shell zsh)"
```

## IDE extensions

- **VS Code**: [Marketplace listing](https://marketplace.visualstudio.com/items?itemName=caissonhq.forgebench) · `integrations/vscode-forgebench/MARKETPLACE.md`
- **JetBrains**: `docs/jetbrains-marketplace-listing.md`

## GitHub App (self-hosted)

Not a hosted service — deploy in your infrastructure. See [GitHub App listing](github-app-listing.md).

## First run

```bash
forgebench quickstart
forgebench doctor --checklist
forgebench team init           # teams (Team license)
```