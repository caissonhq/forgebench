# SOC 2 Readiness Overview (ForgeBench EO-010)

ForgeBench is a **local-first** merge-risk CLI. This document frames SOC 2-style controls for customers evaluating Team/Enterprise adoption. It is audit-prep documentation, not a certification claim.

## Trust boundaries

| Boundary | Customer data | ForgeBench default |
|----------|---------------|-------------------|
| Review execution | Repo diffs, task prompts, reports | Stays on customer machine/CI |
| Policy files | `forgebench.yml`, FPL, org policy | Customer-controlled git |
| Feedback / telemetry | Optional local JSONL | Opt-in; no auto-upload |
| GitHub App | Webhook payloads, check runs | **Self-hosted** by customer |
| LLM / Grok | Prompt excerpts when enabled | Customer API keys |

## Control themes (SOC 2 mapping)

| TSC criteria | ForgeBench control |
|--------------|-------------------|
| CC6.1 Logical access | Local CLI; no mandatory OAuth for core review |
| CC6.6 System boundaries | Documented trust model; SARIF/check-run optional |
| CC7.2 Detection | Policy audit JSONL; formal verification hooks |
| CC8.1 Change management | Policy versioning fingerprints; golden corpus CI |
| CC9.2 Risk mitigation | Merge posture gates; org enforcement config |

## Customer responsibilities

- Secure CI secrets (`FORGEBENCH_LLM_API_KEY`, `FORGEBENCH_GROK_API_KEY`, webhook secrets)
- Pin policy versions in org repos
- Run `forgebench policy test` before promoting shared policy
- Host GitHub App webhook receivers on hardened infrastructure

## ForgeBench responsibilities (Early Access)

- Maintain calibration corpus and honest limitation docs
- Publish security advisories via GitHub Security Advisories
- Provide audit artifacts: control matrix, audit checklist, trust model cross-links

## Related docs

- [controls-matrix.md](controls-matrix.md)
- [audit-prep-checklist.md](audit-prep-checklist.md)
- [../trust-model.md](../trust-model.md)