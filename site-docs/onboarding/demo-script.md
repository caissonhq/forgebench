# Demo video script

**Duration:** ~3 minutes  
**Audience:** Engineering leads evaluating ForgeBench for team adoption

## Scene 1 — Install (0:00–0:30)

```bash
pip install forgebench
forgebench doctor
```

Narration: "ForgeBench doctor verifies your environment and prints an onboarding checklist."

## Scene 2 — Guided demo (0:30–1:15)

```bash
forgebench demo
```

Show terminal output with posture `REVIEW` and findings list. Open `forgebench-output/demo/forgebench-report.md`.

Narration: "Demo runs a realistic dependency-change review with no repo setup."

## Scene 3 — Status and enterprise init (1:15–2:00)

```bash
forgebench status
forgebench init --enterprise --yes
```

Show generated `org-policy/`, `.github/workflows/forgebench.yml`, and `docs/forgebench-onboarding.md`.

## Scene 4 — IDE extension (2:00–2:45)

VS Code: open ForgeBench sidebar → Run demo → Open repair prompt (clipboard).

Narration: "The extension mirrors CLI workflows with a findings sidebar and onboarding wizard."

## Scene 5 — Repair loop (2:45–3:00)

```bash
forgebench repair --out forgebench-output/demo
```

Paste into coding agent. Re-run review.

## GIF capture targets

| Flow | Suggested filename |
|------|-------------------|
| `forgebench demo` terminal | `demo-cli.gif` |
| VS Code sidebar findings | `demo-vscode-sidebar.gif` |
| Repair prompt copy | `demo-repair.gif` |
| `forgebench init --enterprise` tree | `demo-enterprise-init.gif` |

Place assets under `docs/onboarding/gifs/` when recorded.