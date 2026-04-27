# Contributing

ForgeBench is currently a local CLI proof for adversarial pre-merge QA on coding-agent diffs.

## Local Setup

```bash
python3 -m pip install -e .
```

## Test

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests
```

## Calibration

```bash
PYTHONDONTWRITEBYTECODE=1 python -m forgebench calibrate --cases examples/golden_cases
```

Keep changes local, deterministic, and evidence-backed. Do not add hosted services, external LLM calls, OAuth flows, dashboards, billing, auto-fix, auto-merge, or remote telemetry unless that is explicitly in scope for a future sprint.
