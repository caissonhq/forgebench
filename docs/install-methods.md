# Install ForgeBench

ForgeBench is a local CLI. Pick the install path that fits your environment.

## pip (recommended)

```bash
pip install forgebench
forgebench doctor
```

## pipx (isolated CLI)

```bash
pipx install forgebench
forgebench quickstart
```

## Homebrew (macOS / Linux)

```bash
brew tap caissonhq/tap
brew install forgebench
forgebench doctor
```

The formula template lives in `packaging/homebrew/forgebench.rb` and is updated on each release.

## From source (contributors)

```bash
git clone https://github.com/caissonhq/forgebench.git
cd forgebench
python3 -m pip install -e .
forgebench doctor
```

## VS Code extension

Install **ForgeBench** from the VS Code Marketplace (search "ForgeBench") or build from `integrations/vscode/`.

The release workflow in `.github/workflows/vscode-marketplace.yml` publishes on tagged releases.

## JetBrains plugin

Build from `integrations/jetbrains/` or install from the JetBrains Marketplace when listed.

## Docker / CI

See [GitHub Action](github-action.md) and `Dockerfile` for containerized PR review.

## First run

```bash
forgebench quickstart          # solo developers
forgebench team init           # engineering teams (Team license)
forgebench init --enterprise   # full enterprise kit
```

## Verify

```bash
forgebench doctor --checklist
forgebench status
```