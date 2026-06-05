# ForgeBench Public Roadmap

ForgeBench reviews AI-generated diffs before they hit main.

Status key: **Done** · **In progress** · **Planned** · **Exploring**

Last updated: 2026-06-05 (EO-006)

## Now — CLI alpha (Done)

- Local diff and GitHub PR review via `gh`
- Deterministic checks, static signals, guardrails v2 policy
- Phase 1 heuristic lenses + narrow Regression Hunter
- SARIF, GitHub Check Runs, `forgebench validate`
- Cursor rule, MCP server, `forgebench repair`
- Merge Risk Benchmark (`forgebench benchmark`)
- OpenAI-compatible optional LLM provider
- Public beta structured feedback export

## EO-006 — World-Class Polish & Scale (Done)

- **Shared policy layers**: `extends`, `include`, `FORGEBENCH_ORG_POLICY`
- **Policy dashboard skeleton**: `forgebench dashboard` static HTML + JSON manifest
- **CI recipes**: GitLab CI, CircleCI, Jenkins examples
- **IDE scaffolds**: VS Code extension scaffold, JetBrains plugin scaffold
- **Community**: contribution process, issue templates, this roadmap

## Next — Team adoption (Planned)

| Item | Notes |
|------|-------|
| Hosted policy dashboard v1 | Wire skeleton to org inventory + adoption status (opt-in telemetry TBD) |
| VS Code marketplace publish | Harden extension scaffold, diff picker UX |
| JetBrains plugin alpha | Kotlin actions for review + report |
| GitLab / CircleCI shared templates | Publish reusable template repos |
| Policy lint in CI | `--strict` gate on shared org policy repos |

## Depth & intelligence (Planned)

| Item | Notes |
|------|-------|
| Security Reviewer v1 | Beyond pattern matching; sandboxed static probes |
| Dependency Watcher v1 | CVE/license signals with local cache |
| Broader regression lens | Still evidence-constrained; no numeric safety score |
| Monorepo package graph hints | Smarter `review_scope` suggestions from manifests |

## Ecosystem (Exploring)

| Item | Notes |
|------|-------|
| GitHub Marketplace Action GA | Listing live, versioned tags |
| Bitbucket / Azure DevOps recipes | Community-maintained CI snippets |
| ForgeBench policy registry | Git-based org policy distribution (no hosted OAuth) |
| Reviewer plugins | Third-party lens API (design phase) |

## Explicit non-goals

- No claim that ForgeBench certifies a diff as safe
- No auto-merge or auto-fix
- No numeric safety score
- No mandatory hosted SaaS or OAuth for core review
- No remote telemetry without explicit opt-in design review

## How to influence the roadmap

1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Open a [Roadmap discussion](../../discussions) or issue with label `roadmap`
3. Propose golden cases for false positives or missed concerns
4. Share dogfood feedback via `forgebench feedback export`

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.