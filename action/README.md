# ForgeBench GitHub Action

Review AI-generated pull request diffs for merge risk before they reach main.

## Usage

```yaml
name: ForgeBench
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  forgebench:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: caissonhq/forgebench@v0.9.0
        with:
          guardrails-path: forgebench.yml
          run-checks: "true"
          post-comment: "false"
          post-check-run: "false"
```

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `pr-url` | event PR URL | GitHub pull request URL |
| `guardrails-path` | `forgebench.yml` | Repo guardrails file |
| `run-checks` | `false` | Run configured checks (auto-enables PR worktree checkout) |
| `post-comment` | `false` | Post ForgeBench PR comment |
| `post-check-run` | `false` | Post GitHub Check Run with inline annotations |
| `llm-review` | `false` | Optional advisory LLM review |
| `llm-command` | `""` | Command provider for LLM review |

## Outputs

| Output | Description |
|--------|-------------|
| `posture` | Merge posture: `BLOCK`, `REVIEW`, or `LOW_CONCERN` |
| `report-path` | Path to `forgebench-report.md` |
| `pr-comment-path` | Path to `pr-comment.md` |
| `sarif-path` | Path to `forgebench-report.sarif.json` |

## Safe defaults

- PR comments and Check Runs are opt-in.
- Missing `forgebench.yml` uses generic review rules.
- `run-checks: true` checks out PR code into a temporary worktree before running commands from guardrails.

## Repair workflow

Download action artifacts or read `repair-prompt.md` from the job workspace, then paste it into your coding agent.

## Documentation

- Repository: https://github.com/caissonhq/forgebench
- Website: https://forgebench.dev
- Marketplace prep: [docs/github-marketplace-listing.md](../docs/github-marketplace-listing.md)

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.