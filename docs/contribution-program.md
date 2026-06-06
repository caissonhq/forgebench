# ForgeBench Contribution Program

ForgeBench grows through **golden cases**, **policy examples**, and **integration hardening**. This program makes high-quality contributions easy to land.

## Contributor lanes

| Lane | Impact | How to start |
|------|--------|--------------|
| Calibration | Highest | [golden case template](../.github/ISSUE_TEMPLATE/golden_case.md) |
| Policy | High | Add `examples/policy_tests/` or `examples/org-policy/` |
| Integrations | High | VS Code, JetBrains, CI recipes, GitHub App deployments |
| Docs | Medium | Runnable command snippets, security clarifications |
| Benchmarks | Medium | Anonymized PR outcomes (see `examples/benchmark_outcomes/`) |

## Recognition

- Contributors credited in CHANGELOG for merged golden cases
- `dogfood_*` case naming for real anonymized PRs (with approval)
- Early Access design partner list for sustained policy + integration work

## Quality bar

1. **Reproducible** — include exact CLI commands
2. **Anonymized** — no proprietary code without redaction
3. **Tested** — `python -m unittest discover -s tests` passes
4. **Honest** — no hosted-SaaS claims for core review

## Monthly cadence (public)

- Roadmap review — first week ([ROADMAP.md](../ROADMAP.md))
- Calibration office hours — golden case triage
- Integration office hours — IDE + GitHub App self-hosting

## Submit work

```bash
# Golden case from dogfood
forgebench feedback --generate-golden-cases --out forgebench-output/golden-case-candidates

# Policy test from simulation
forgebench policy simulate --diff patch.diff --guardrails forgebench.yml

# Export feedback bundle for maintainers
forgebench feedback export --out forgebench-output/beta-feedback.json
```

Open a PR with the template checklist in [CONTRIBUTING.md](../CONTRIBUTING.md).

ForgeBench does not prove code is safe. Good contributions make merge-risk signals **more calibrated**, not "safe to merge."