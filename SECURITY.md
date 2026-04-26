# Security

ForgeBench is a local CLI. By default it reads diffs, task files, and optional guardrails without executing project commands.

`--run-checks` executes local shell commands from `forgebench.yml`. Only run `--run-checks` against trusted repositories and trusted `forgebench.yml` files.

`--llm-review --llm-provider command` executes a user-supplied local command. Only use command providers you trust. See [docs/llm-threat-model.md](docs/llm-threat-model.md) for the LLM threat model and mitigations.

Do not put secrets, API keys, or credentials in ForgeBench fixtures, guardrails, reports, or calibration cases.
