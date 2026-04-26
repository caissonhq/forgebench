# BLOCK Sample Case

This is a synthetic ForgeBench sample case.

It demonstrates a `BLOCK` posture for a migration/schema change without
corresponding tests. The example is human-approved synthetic data and is not a
real customer report.

Regenerate from the repo root:

```bash
forgebench review \
  --repo . \
  --diff examples/sample_report/block_case/patch.diff \
  --task examples/sample_report/block_case/task.md \
  --guardrails examples/sample_report/block_case/forgebench.yml \
  --out examples/sample_report/block_case
```
