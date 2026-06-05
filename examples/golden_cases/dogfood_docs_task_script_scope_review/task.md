GitHub PR Review

PR:
https://github.com/Mohammed-Abdelhady/hyperflow/pull/5

Title:
[codex] clarify Codex Hyperflow invocation

Body:
## Summary

- Clarifies that Codex App/CLI does not expose a bare `/hyperflow` root slash command.
- Moves Codex quick-start examples to the portable `hyperflow <skill>` form while keeping `/hyperflow:<skill>` as an alias form.
- Resolves hook validation commands relative to the plugin root so validation works from any current working directory.

## Validation

- `python3 scripts/validate-plugin.py`
- `python3 /Users/mohammedabdelhady/Documents/coding/projects/hyperflow/scripts/validate-plugin.py` from `/Users/mohammedabdelhady/Documents/coding/projects/forgepath`
- `git diff --check`

Author:
Mohammed-Abdelhady

Base:
main

Head:
codex/fix-codex-hyperflow-command-docs

Changed files:
4

Additions:
15

Deletions:
13

This task context was generated from GitHub PR metadata.
