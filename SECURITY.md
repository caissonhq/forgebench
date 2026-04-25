# Security

ForgeBench is a local CLI. By default it reads diffs, task files, and optional guardrails without executing project commands.

`--run-checks` executes local shell commands from `forgebench.yml`. Only run `--run-checks` against trusted repositories and trusted `forgebench.yml` files.

Do not put secrets, API keys, or credentials in ForgeBench fixtures, guardrails, reports, or calibration cases.
