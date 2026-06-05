# Contributing

ForgeBench is currently a local CLI proof for adversarial pre-merge QA on coding-agent diffs.

## Local Setup

From PyPI:

```bash
python3 -m pip install forgebench
forgebench doctor
```

From source:

```bash
python3 -m pip install -e .
forgebench doctor
```

## Test

```bash
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests
```

## Calibration

```bash
PYTHONDONTWRITEBYTECODE=1 python -m forgebench calibrate --cases examples/golden_cases
```

## Publish to PyPI

Releases are triggered by pushing a `v*` tag. The `Release` workflow runs tests, calibration, builds artifacts, and publishes with PyPI Trusted Publishing.

Before the first publish, configure a trusted publisher on [pypi.org](https://pypi.org) for project `forgebench`:

- Owner: `caissonhq`
- Repository: `forgebench`
- Workflow name: `release.yml`
- Environment name: *(leave empty unless you add a GitHub Environment)*

Then push a tag:

```bash
git tag -a v0.9.0 -m "Release forgebench 0.9.0"
git push origin v0.9.0
```

Local smoke check before tagging:

```bash
./scripts/smoke_install.sh
```

Manual fallback (API token; do not commit tokens):

```bash
python -m build
python -m twine upload dist/*
```

Keep changes local, deterministic, and evidence-backed. Do not add hosted services, external LLM calls, OAuth flows, dashboards, billing, auto-fix, auto-merge, or remote telemetry unless that is explicitly in scope for a future sprint.
