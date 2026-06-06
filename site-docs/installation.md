# Installation & Getting Started

ForgeBench is a **local CLI** for merge-risk review of AI-generated diffs. Choose the install path that fits your environment — all methods run the same commands.

## Quick pick

| You are… | Recommended |
|----------|-------------|
| Solo developer on macOS | `brew tap caissonhq/tap && brew install forgebench` |
| Solo developer (any OS) | `pipx install forgebench` |
| CI / Docker | `pip install forgebench` |
| Locked-down laptop | [Binary bundle](installation.md#binary-bundle) from GitHub Releases |
| Contributor | [From source](installation.md#from-source) |

```bash
forgebench install          # detect your environment & recommend a method
forgebench quickstart       # ~2 minute guided first review
forgebench doctor --checklist
```

## Install methods comparison

| Method | Command | Pros | Cons | Best for |
|--------|---------|------|------|----------|
| **pipx** | `pipx install forgebench` | Isolated CLI, clean upgrades | Needs pipx | Daily CLI use |
| **pip** | `pip install forgebench` | Familiar, CI-friendly | Env conflicts possible | CI, venvs |
| **Homebrew** | `brew tap caissonhq/tap && brew install forgebench` | System-wide, managed | macOS/Linux only | Workstations |
| **Binary** | Download `.tar.gz` from Releases | No pip required | Manual PATH | Air-gapped |
| **macOS .pkg** | Download `.pkg` from Releases | GUI installer | macOS only | Enterprise Mac fleets |
| **VS Code** | Marketplace: `caissonhq.forgebench` | IDE sidebar + onboarding | Requires CLI on PATH | Cursor/VS Code users |
| **JetBrains** | Marketplace plugin | Tool window + actions | Requires CLI on PATH | IntelliJ/PyCharm users |
| **Source** | `pip install -e .` | Latest code | Manual updates | Contributors |

## pipx (recommended)

```bash
pipx install forgebench
forgebench quickstart
```

Upgrade: `pipx upgrade forgebench`

## pip

```bash
pip install forgebench
forgebench doctor
```

Upgrade: `pip install --upgrade forgebench`

## Homebrew

```bash
brew tap caissonhq/tap
brew install forgebench
forgebench doctor --checklist
```

Upgrade: `brew upgrade forgebench`

Shell completions:

```bash
eval "$(forgebench install completions --shell bash)"   # or zsh / fish
```

## Binary bundle

Download from [GitHub Releases](https://github.com/caissonhq/forgebench/releases):

```bash
# Linux x86_64 example
curl -fsSL -o forgebench.tar.gz \
  https://github.com/caissonhq/forgebench/releases/latest/download/forgebench-VERSION-linux-x86_64.tar.gz
tar -xzf forgebench.tar.gz
export PATH="$(pwd)/forgebench-VERSION-linux-x86_64/bin:$PATH"
forgebench doctor
```

## macOS .pkg

Enterprise Mac deployments can distribute the signed `.pkg` from GitHub Releases. It installs to `/opt/forgebench` and links `/usr/local/bin/forgebench`.

## VS Code extension

1. Install CLI: `pipx install forgebench`
2. Install extension: search **ForgeBench** in VS Code Marketplace (`caissonhq.forgebench`)
3. Run **ForgeBench: Onboarding Wizard** from the sidebar

## JetBrains plugin

1. Install CLI on PATH
2. Install **ForgeBench** from JetBrains Marketplace
3. **Tools → ForgeBench → Onboarding Wizard**

## From source

```bash
git clone https://github.com/caissonhq/forgebench.git
cd forgebench
python3 -m pip install -e .
forgebench doctor
```

## Verify & upgrade

```bash
forgebench doctor --checklist
forgebench install upgrade
forgebench status
```

## Next steps

- [Quickstart](quickstart.md)
- [Presets gallery](../docs/presets-gallery.md)
- [Team init](enterprise/init.md)
- [Troubleshooting](troubleshooting.md)