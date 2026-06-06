# ForgeBench JetBrains Plugin

Production-grade IntelliJ Platform plugin for local ForgeBench CLI workflows.

## Requirements

- IntelliJ IDEA 2023.3+ (IC/Ultimate compatible scaffold)
- `forgebench` on `PATH`

## Actions (Tools → ForgeBench)

- **Review Diff + Task** — file pickers + `forgebench review`
- **Open Markdown Report** — `forgebench-output/forgebench-report.md`
- **Run Policy Tests** — `forgebench policy test`
- **Export Policy Dashboard** — `forgebench dashboard`

## Build

```bash
cd integrations/jetbrains-forgebench
./gradlew buildPlugin
```

## Publish (Early Access)

1. `./gradlew buildPlugin`
2. Upload `build/distributions/*.zip` to JetBrains Marketplace
3. Document org policy + GitHub App self-hosting in listing notes

ForgeBench does not prove code is safe. The plugin shells out to the local CLI only.