# ForgeBench

**Adversarial pre-merge QA for coding-agent output.**

ForgeBench reviews AI-generated diffs before they hit main. It produces a sober merge-risk report (`BLOCK`, `REVIEW`, or `LOW_CONCERN`), machine-readable JSON, and a repair prompt you can paste back into Cursor, Codex, or Claude Code.

## Get started in 60 seconds

```bash
pip install forgebench
forgebench doctor
forgebench demo
forgebench status
```

## Professional onboarding

| Step | Command |
|------|---------|
| Verify install | `forgebench doctor` |
| See a realistic review | `forgebench demo` |
| Health summary | `forgebench status` |
| Team starter kit | `forgebench init --enterprise` |
| IDE integration | VS Code or JetBrains ForgeBench extension |

## Evidence hierarchy

1. Deterministic checks
2. Static risk signals
3. Guardrails policy
4. Heuristic review lenses
5. Optional LLM review

Deterministic failures are never downgraded by lenses or policy calibration.

## Deploy this site

```bash
pip install mkdocs-material
mkdocs serve    # local preview at http://127.0.0.1:8000
mkdocs build    # static site in site/
```

Publish `site/` to GitHub Pages or Vercel.