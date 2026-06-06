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