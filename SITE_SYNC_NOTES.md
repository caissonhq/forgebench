# Site Sync Notes

Use this as a concise Lovable update prompt for the public alpha site. Do not imply hosted SaaS, OAuth, or the full 8-reviewer set.

## Lovable Prompt

Update the ForgeBench public alpha site to reflect the current CLI alpha.

Positioning:
- ForgeBench reviews AI-generated diffs before they hit main.
- SWE-Bench asks whether an agent solved the task. ForgeBench asks whether a serious engineer would merge the diff.
- Keep the product framed as local-first, CLI-first, evidence-backed pre-merge QA.

Add Heuristic Review Lenses to the homepage and report viewer:
- Scope Auditor
- Test Skeptic
- Contract Keeper
- Product / Guardrail Reviewer

Explain that these are Phase 1 deterministic heuristic lenses only. Do not imply the full 8-reviewer set exists yet.

Make the reviewers evidence-constrained:
- They use the task, diff, deterministic checks, static signals, and guardrails.
- They do not approve merges.
- They do not assign a numeric score.
- They do not override deterministic failures.

Update the example report to include a concise reviewer summary:
- Scope Auditor: no additional concern
- Test Skeptic: changed behavior lacks corresponding test coverage
- Contract Keeper: read-model contract changed without clear coverage
- Product / Guardrail Reviewer: protected area changed

Keep the current CLI alpha framing:
- `forgebench init` creates a starter local guardrails file
- Local diff review
- GitHub PR URL review through local GitHub CLI
- Optional `--checkout-pr --run-checks`
- Optional `--llm-review`
- Local artifacts: Markdown, JSON, repair prompt, PR-ready comment
- Repair prompts now include relevant diff hunk context
- Link to synthetic, human-approved sample reports and label them clearly as synthetic examples, not real customer reports

Do not add:
- hosted SaaS claims
- OAuth claims
- dashboard claims
- billing language
- auto-fix
- auto-merge
- numeric safety score

Keep this footer disclaimer:

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.
