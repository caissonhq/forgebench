# Contributing

ForgeBench is a local CLI for adversarial pre-merge QA on coding-agent diffs.

## Quick links

- [ROADMAP.md](ROADMAP.md) — public priorities
- [docs/team-enterprise.md](docs/team-enterprise.md) — shared policy layers
- [docs/ci-integrations.md](docs/ci-integrations.md) — CI recipes
- [docs/ide-integrations.md](docs/ide-integrations.md) — editor scaffolds

## Local setup

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

## Contribution process

1. **Check the roadmap** — open a [feature request](.github/ISSUE_TEMPLATE/feature_request.md) or comment on [ROADMAP.md](ROADMAP.md) if scope is unclear.
2. **Reproduce with evidence** — include commands, expected posture, and redacted artifacts.
3. **Prefer golden cases** — false positives and missed concerns should become `examples/golden_cases/` entries ([template](.github/ISSUE_TEMPLATE/golden_case.md)).
4. **Keep it local-first** — do not add hosted OAuth, remote telemetry, auto-merge, or numeric safety scores unless explicitly in scope.
5. **Run tests** — all PRs should pass `python -m unittest discover -s tests`.
6. **Update docs** — user-facing CLI or schema changes need README / `docs/` updates.

### Good first contributions

- Golden cases from your dogfood runs (anonymized)
- CI recipe improvements for GitLab, CircleCI, or Jenkins
- Policy layer examples under `examples/org-policy/`
- IDE scaffold hardening (VS Code / JetBrains)
- Doc clarity fixes with runnable command snippets

### Review expectations

- Deterministic behavior must stay reproducible
- New reviewers remain evidence-constrained
- Policy layering must not execute commands while parsing YAML
- Marketing copy must not imply hosted SaaS for core review

## Dogfood feedback

```bash
forgebench feedback fnd_example --status dismissed --kind ui_copy_changed
forgebench feedback export --out forgebench-output/beta-feedback.json
```

Feedback stays local unless you choose to attach an export to an issue.

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

ForgeBench does not prove code is safe. Keep changes evidence-backed and honest about limitations.