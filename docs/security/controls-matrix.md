# Security Controls Matrix

| ID | Control | Implementation | Evidence |
|----|---------|----------------|----------|
| AC-01 | Core review requires no hosted account | Local CLI + `gh` for PR intake | README, `forgebench doctor` |
| AC-02 | Opt-in telemetry only | `forgebench telemetry enable` | `forgebench/telemetry.py`, SECURITY.md |
| AC-03 | Policy parse is non-executing | `yaml.safe_load`; FPL line parser | `docs/forgebench-yml-schema.md`, `docs/fpl-v1.md` |
| AC-04 | Checks run only when requested | `--run-checks` explicit | CLI docs, GitHub Action |
| AC-05 | PR comments explicit | `--post-comment` | README, action.yml |
| AC-06 | Policy audit trail | `policy-audit.jsonl` | `forgebench policy audit` |
| AC-07 | Policy version fingerprints | `policy-versions.jsonl` | `forgebench policy version --record` |
| AC-08 | Org policy enforcement | GitHub App self-hosted + config JSON | `examples/github-app/`, `forgebench github-app` |
| AC-09 | Formal verification hooks | `forgebench policy verify` | `forgebench/formal_hooks.py` |
| AC-10 | Secret redaction in telemetry | Path/secret hashing | `tests/test_telemetry.py` |
| AC-11 | SARIF export for CI gates | `forgebench-report.sarif.json` | `tests/test_sarif_writer.py` |
| AC-12 | Calibration regression suite | 47+ golden cases | `forgebench calibrate`, CI workflow |
| AC-13 | Policy path confinement | Repo-root bounded `extends`/`include`/`fpl` | `forgebench/security/path_confinement.py`, `tests/test_security_hardening.py` |
| AC-14 | Trusted guardrails for checks | `--guardrails` required with `--run-checks` | `forgebench/github_pr.py`, action defaults |
| AC-15 | Webhook secret required | `FORGEBENCH_GITHUB_WEBHOOK_SECRET` | `forgebench/github_app/server.py` |
| AC-16 | Posture attestation | Check Run or signed attestation only | `forgebench/github_app/attestation.py` |
| AC-17 | HTTP body size limits | 5 MB policy/GitHub App, 10 MB MCP | `forgebench/security/http_limits.py` |
| AC-18 | LLM command no shell | `shlex` argv parsing | `forgebench/security/command_exec.py` |
| AC-19 | Policy service RBAC | Admin/readonly bearer tokens | `forgebench/security/rbac.py` |
| AC-20 | Tamper-evident audit chain | Hash-linked `audit-chain.jsonl` | `forgebench audit verify` |
| AC-21 | Data retention policy | `forgebench data retention` | `forgebench/data_retention.py` |
| AC-22 | Supply chain scanning | pip-audit + SBOM CI | `.github/workflows/security.yml` |
| AC-23 | Structured logging | JSON logs via `FORGEBENCH_LOG_LEVEL` | `forgebench/observability/logging.py` |
| AC-24 | Air-gapped deployment | Docker Compose + Helm skeleton | `deployments/`, `docs/air-gapped.md` |