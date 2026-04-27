# ForgeBench Dogfood Log

Use this template when running ForgeBench against a real local AI-generated diff.

## Entry Template

- Date:
- Repo:
- Original coding agent:
- Original task:
- Diff size:
- ForgeBench posture:
- Findings that were useful:
- Findings that were noisy:
- Was the posture right?
- Did the repair prompt help?
- Would I have missed anything without ForgeBench?
- Follow-up changes needed:

## Notes

This file is intentionally manual. The goal is product learning from real local review situations, not benchmark scoring.

## Local Feedback Summary

ForgeBench feedback stays local. Record finding-level feedback during dogfood runs:

```bash
forgebench feedback fnd_example123 \
  --status accepted \
  --kind implementation_without_tests \
  --note "caught missing test coverage"
```

Summarize one or more local feedback logs as Markdown:

```bash
python3 scripts/dogfood_summary.py forgebench-output/feedback.jsonl
```

The script prints a summary to stdout. It does not append to this log automatically; copy only the conclusions that are useful for product learning.
