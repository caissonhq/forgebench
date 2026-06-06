# SOC 2 Evidence Mapping

Maps ForgeBench controls to auditor-requested evidence artifacts.

| Control ID | Auditor request | Evidence artifact | Owner |
|------------|-----------------|-------------------|-------|
| AC-01 | Prove no mandatory SaaS | README, `docs/air-gapped.md`, architecture diagram | Eng |
| AC-02 | Telemetry opt-in proof | `forgebench telemetry status`, SECURITY.md | Eng |
| AC-03 | Safe policy parsing | `yaml.safe_load` grep, FPL parser tests | Eng |
| AC-04 | Check execution gate | `tests/test_security_invariants.py`, CLI defaults | Eng |
| AC-13 | Path confinement | `tests/test_security_hardening.py` | Eng |
| AC-14 | Webhook authenticity | `FORGEBENCH_GITHUB_WEBHOOK_SECRET`, signature tests | Ops |
| AC-15 | Tamper-evident audit | `forgebench audit verify`, `audit-chain.jsonl` | Ops |
| AC-16 | RBAC for policy API | `FORGEBENCH_POLICY_*_TOKEN`, rbac tests | Ops |
| AC-17 | Dependency scanning | `.github/workflows/security.yml`, SBOM artifact | Eng |
| AC-18 | Data retention | `forgebench data retention --dry-run` | Ops |
| AC-19 | Supply chain | `requirements-lock.txt`, dependabot.yml | Eng |

## Collection cadence

- **Per release**: SBOM, pip-audit report, calibration run, security test suite
- **Quarterly**: Audit chain verification, retention purge dry-run, controls matrix review
- **On change**: Update evidence mapping when new controls ship