# ForgeBench Policy Language (FPL) v1

FPL is a safe, line-oriented policy DSL that compiles into the `policy:` section of `forgebench.yml`. It does not execute code, shell commands, or network calls at parse time.

## Why FPL

YAML guardrails are fine for static configuration. FPL adds:

- Readable policy intent for reviewers
- Versioned policy documents (`.fpl`)
- Compile-time checks before simulation or review
- A path toward richer policy testing without YAML indentation pain

## Syntax

- Comments start with `#`
- One directive per line
- Paths are glob patterns (same semantics as `forgebench.yml`)

### Directives

```fpl
version 1.0.0
name docs-policy

category docs paths README.md docs/** **/*.md severity advisory
advisory_only README.md docs/** **/*.md

suppress ui_copy_changed paths README.md docs/** **/*.md reason "Docs-only copy is advisory."
ceiling docs_only_changes posture LOW_CONCERN reason "Docs-only diffs stay low concern."
override implementation_without_tests severity medium confidence medium applies **/fixtures/**
```

## Compile and attach to guardrails

```bash
forgebench policy compile examples/fpl/docs_policy.fpl
```

Reference from `forgebench.yml`:

```yaml
project: My Repo
policy_version: 1.0.0
fpl: policies/docs_policy.fpl
```

ForgeBench merges compiled FPL policy into the loaded guardrails payload at read time.

## Safety

- No `eval`, `exec`, or embedded scripting
- Parse + compile only; simulation and review remain local
- FPL is optional; plain YAML policies remain fully supported