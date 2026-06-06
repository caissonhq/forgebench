# Troubleshooting

## `forgebench doctor` reports failures

| Check | Fix |
|-------|-----|
| python | Install Python 3.10+ |
| forgebench | `pip install forgebench` |
| git | Install git for worktree checkout |
| github_cli | Install `gh` from https://cli.github.com |
| github_auth | `gh auth login` |
| output_dir | Run from a writable directory |

Use `--explain` on any command for contextual hints:

```bash
forgebench review-pr URL --run-checks --explain
```

## Review errors

**`run_checks requires --checkout-pr`** — Add `--checkout-pr` so checks run against PR code.

**`refusing to overwrite`** — Pass `--force` to `forgebench init`.

**`guardrails file does not exist`** — Run `forgebench init` or `forgebench init --enterprise`.

## Noisy generic mode

Run `forgebench init` and edit `protected_behavior`, `forbidden_patterns`, and `risk_files`.

## CI workflow not running

Ensure `.github/workflows/forgebench.yml` exists (`forgebench init --enterprise`) and guardrails live at `.github/forgebench.yml` on the default branch.

## Still stuck?

```bash
forgebench status --plain
forgebench doctor
```

Open an issue: https://github.com/caissonhq/forgebench/issues