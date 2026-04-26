# LOW_CONCERN Sample Case

This is a synthetic ForgeBench sample case.

It demonstrates a `LOW_CONCERN` posture for a docs-only change with policy
calibration that keeps docs copy advisory. The example is human-approved
synthetic data and is not a real customer report.

Regenerate from the repo root:

```bash
forgebench review \
  --repo . \
  --diff examples/sample_report/low_concern_case/patch.diff \
  --task examples/sample_report/low_concern_case/task.md \
  --guardrails examples/sample_report/low_concern_case/forgebench.yml \
  --out examples/sample_report/low_concern_case
```
