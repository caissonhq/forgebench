GitHub PR Review

PR:
https://github.com/vercel/workflow/pull/2238

Title:
[codex] Add Codex environment setup

Body:
### Description

Add a checked-in Codex environment descriptor so Codex tasks bootstrap the workspace with `pnpm install --frozen-lockfile`.

This keeps environment setup deterministic from the committed lockfile and avoids coupling the bootstrap step to app credentials or target-specific builds. An empty changeset is included because this is internal configuration and does not change a published package.

### How did you test your changes?

- Parsed `.codex/environments/environment.toml` with Python `tomllib`.
- Ran `git diff --check origin/main...HEAD`.
- Verified the signed, signed-off commit is reported as valid by GitHub.

Author:
pranaygp

Base:
main

Head:
pranaygp/codex/add-codex-environment

Changed files:
2

Additions:
10

Deletions:
0

This task context was generated from GitHub PR metadata.
