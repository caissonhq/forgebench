# ForgeBench Public Roadmap

ForgeBench reviews AI-generated diffs before they hit main.

Status key: **Done** · **In progress** · **Planned** · **Exploring**

Last updated: 2026-06-05 (EO-011)

## EO-011 — Enterprise Readiness & Compliance (Done)

- **Security hardening**: Trusted guardrails for `--run-checks`, repo-root path confinement, webhook secret + attestation, HTTP/MCP body limits, shell-free LLM commands
- **Compliance**: Expanded controls matrix, evidence mapping, tamper-evident audit chain (`forgebench audit verify`), data retention CLI
- **Supply chain**: pip-audit workflow, SBOM artifact, dependabot, `requirements-lock.txt`
- **Self-hosted / air-gapped**: Docker Compose + Helm skeleton, [docs/air-gapped.md](docs/air-gapped.md)
- **RBAC + observability**: Policy service admin/readonly tokens, structured JSON logging, OTEL/Sentry hook env vars

## EO-010 — World-Class Delivery & Adoption (Done)

- **IDE extensions v1**: Production-grade VS Code extension (`forgebenchRunner`, diff review, policy test, SARIF) and JetBrains plugin (Kotlin actions + Gradle build)
- **GitHub App kit**: Self-hosted org policy enforcement — `forgebench github-app manifest|enforce|serve`, webhook handler, check-run output
- **SOC 2 readiness pack**: `docs/security/` controls matrix, audit prep checklist, SOC 2 overview
- **Marketing refresh**: Early Access positioning in [docs/marketing-home.md](docs/marketing-home.md)
- **Public roadmap + contribution program**: [contribution-program.md](docs/contribution-program.md), refreshed [CONTRIBUTING.md](CONTRIBUTING.md)
- **Early Access launch prep**: [docs/early-access.md](docs/early-access.md), [docs/pricing.md](docs/pricing.md)

## EO-009 — Policy & Verification Platform (Done)

- **FPL v1**: `.fpl` policy language compiling into `forgebench.yml` policy (`fpl:` reference)
- **Policy tests**: `forgebench policy test` over `examples/policy_tests/`
- **Simulation**: `forgebench policy simulate` for fast posture/suppression checks
- **Verification**: Formal-ish local hooks + optional Grok API (`forgebench policy verify --grok`)
- **Audit + versions**: `forgebench-output/policy-audit.jsonl` and `policy-versions.jsonl`
- **Self-hosted service**: `forgebench policy serve` HTTP skeleton on localhost

## EO-008 — Data Flywheel & Trust at Scale (Done)

- **Opt-in telemetry**: `forgebench telemetry enable|disable|status|export` — local JSONL, anonymized, no auto-upload
- **PR outcomes**: Anonymized dogfood outcomes wired into `forgebench benchmark --outcomes`
- **Review Arena**: Leaderboard ranking calibration pass rate, lens activity, and human agreement
- **Feedback v3**: Outcome labels, severity/confidence, files, expected posture, reviewer lens
- **Golden case automation**: Draft candidates from dismissed/wrong feedback with human review gate
- **Benchmark dashboard**: `forgebench benchmark-dashboard` static HTML + manifest for public sharing

## Now — CLI alpha (Done)

- Local diff and GitHub PR review via `gh`
- Deterministic checks, static signals, guardrails v2 policy
- Phase 1 heuristic lenses + narrow Regression Hunter
- SARIF, GitHub Check Runs, `forgebench validate`
- Cursor rule, MCP server, `forgebench repair`
- Merge Risk Benchmark (`forgebench benchmark`)
- OpenAI-compatible optional LLM provider
- Public beta structured feedback export

## EO-007 — Semantic Depth & Reasoning Engine (Done)

- **AST parsing**: Python stdlib `ast` + optional tree-sitter for Python/TypeScript/Rust (`pip install forgebench[semantic]`)
- **Cross-file behavioral diff**: changed symbols, test-reference edges, uncovered symbols in `static_signals`
- **Behavioral Skeptic** reviewer lens
- **Mutation testing skeleton**: `forgebench mutation plan`
- **LLM ensemble**: multi-model merge via `FORGEBENCH_LLM_ENSEMBLE_MODELS`
- **Prove-it mode skeleton**: `--prove-it`, `forgebench prove-it`

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
| VS Code marketplace publish | Package v1.0.0 extension; diff picker UX polish |
| JetBrains Marketplace publish | Package Kotlin plugin; sign and list |
| GitHub App hosted option | Managed webhook receiver (self-hosted kit ships in EO-010) |
| GitLab / CircleCI shared templates | Publish reusable template repos |
| Policy lint in CI | `--strict` gate on shared org policy repos |

## Depth & intelligence (Planned)

| Item | Notes |
|------|-------|
| Mutation runner integration | Wire skeleton to mutmut, cargo-mutants, Stryker in CI |
| Prove-it execution | Run mutation + ensemble automatically, not export-only |
| Full tree-sitter default | Ship grammars in core wheel or prebuilt language packs |
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
- No remote telemetry upload without explicit user action (local opt-in export only)

## How to influence the roadmap

1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Open a [Roadmap discussion](../../discussions) or issue with label `roadmap`
3. Propose golden cases for false positives or missed concerns
4. Share dogfood feedback via `forgebench feedback export`

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.