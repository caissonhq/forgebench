# JetBrains Marketplace — ForgeBench Plugin

## Listing metadata

| Field | Value |
|-------|-------|
| **Name** | ForgeBench |
| **Plugin ID** | `dev.forgebench.jetbrains` |
| **Category** | Developer Tools |
| **Vendor** | ForgeBench (hello@forgebench.dev) |

## Description

Professional merge-risk review for AI-generated diffs via the local ForgeBench CLI.

- **Onboarding wizard** — doctor, demo, and status checklist
- **Findings tool window** — posture and review output
- **Repair prompts** — open `repair-prompt.md` for your coding agent
- **Policy tools** — validate guardrails, run policy tests, enterprise init

Requires `forgebench` on PATH (`pipx install forgebench`).

## Screenshots to capture

1. ForgeBench tool window with findings
2. Tools menu with ForgeBench actions
3. Onboarding wizard notification
4. Repair prompt editor tab

## Build & publish

```bash
cd integrations/jetbrains-forgebench
./gradlew buildPlugin
```

Upload `build/distributions/*.zip` to JetBrains Marketplace.

## Keywords

`code review`, `ai`, `merge risk`, `quality`, `guardrails`, `forgebench`