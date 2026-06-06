# JetBrains plugin

Path: `integrations/jetbrains-forgebench/`

## Features

- **Tool window** — demo, status, repair prompt viewer
- **Onboarding wizard** — doctor → demo → status checklist
- **Settings** — guardrails path, output dir, run checks
- **Actions** — review, validate, init/enterprise, policy test, dashboard export

## Build

```bash
cd integrations/jetbrains-forgebench
./gradlew buildPlugin
```

Set `FORGEBENCH_BIN` if the CLI is not on PATH.

## Settings

Stored in `forgebench.xml` per project:

- `guardrailsFile`
- `outputDir`
- `policyTestsDir`
- `runChecks`
- `showOnboardingOnFirstRun`