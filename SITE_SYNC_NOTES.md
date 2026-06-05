# Site Sync Notes

Use this as a concise Lovable update prompt for the public alpha site. Do not imply hosted SaaS, OAuth, or the full 8-reviewer set.

## EO-006 marketing refresh (2026-06-05)

Full home page copy: [docs/marketing-home.md](docs/marketing-home.md)

Add or refresh:

- **Team & Enterprise** section — shared `forgebench.yml` layers (`extends`, `include`, `FORGEBENCH_ORG_POLICY`), link [docs/team-enterprise.md](docs/team-enterprise.md)
- **Policy dashboard skeleton** — local `forgebench dashboard` HTML export; frame as preview/skeleton, not hosted SaaS
- **CI integrations grid** — GitHub Action (existing) + GitLab CI, CircleCI, Jenkins → [docs/ci-integrations.md](docs/ci-integrations.md)
- **IDE integrations** — Cursor/MCP (existing) + VS Code & JetBrains scaffolds → [docs/ide-integrations.md](docs/ide-integrations.md)
- **Public roadmap** — link [ROADMAP.md](ROADMAP.md) in nav/footer
- **Contribute** — link [CONTRIBUTING.md](CONTRIBUTING.md), golden-case issue template, community process

Visual polish:

- Three-column value props: posture / guardrails / agent loop
- Integration logo row (GitHub, GitLab, CircleCI, Jenkins, Cursor, VS Code)
- Sample report carousel: synthetic + 3 EO-002 anonymized reports
- Benchmark callout with `forgebench benchmark` CTA

Still do not claim:

- Hosted policy dashboard SaaS (skeleton export only)
- OAuth or GitHub App for core review
- Numeric safety score or auto-merge

## EO-005 additions (2026-06-05)

- Add a **Merge Risk Benchmark** page using [docs/merge-risk-benchmark.md](docs/merge-risk-benchmark.md)
- Add **Cursor integration** callout linking to [docs/cursor-integration.md](docs/cursor-integration.md) and the review → repair paste workflow
- Add **Public beta** section from [docs/beta-launch.md](docs/beta-launch.md)
- Add **GitHub Action** marketplace CTA pointing to [action/README.md](action/README.md)
- Mention MCP server for IDE tool integrations ([docs/mcp-server.md](docs/mcp-server.md))

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
- First runs may use generic mode when no `forgebench.yml` exists
- Generic mode is useful for initial review but may be noisier than repo-specific guardrails
- `forgebench init` creates a starter local guardrails file
- `forgebench init --preset auto|python|node|nextjs|swift|rust` helps users generate starter guardrails
- Local diff review
- GitHub PR URL review through local GitHub CLI
- Optional `--checkout-pr --run-checks`
- Optional `--llm-review`
- Local artifacts: Markdown, JSON, repair prompt, PR-ready comment
- Repair prompts now include relevant diff hunk context
- Local feedback can suggest guardrail tuning, but it never auto-tunes future runs
- Link to synthetic, human-approved sample reports and label them clearly as synthetic examples, not real customer reports
- Add a "Real anonymized reports" section linking to three EO-002 examples (redacted paths/authors):
  - `agent_env_secret_cleanup_low_concern` → LOW_CONCERN, Codex security/env cleanup with tests
  - `agent_docs_scope_review` → REVIEW, Codex docs task with Scope Auditor + Test Skeptic
  - `monorepo_effect_refactor_review` → REVIEW, Cursor broad refactor with dependency/broad-surface signals
- Publish metrics callout from EO-002: ~63% labeled false-positive rate in generic mode (mostly `ui_copy_changed` on markdown PRs); reviewers fired on 3/10 PRs

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
