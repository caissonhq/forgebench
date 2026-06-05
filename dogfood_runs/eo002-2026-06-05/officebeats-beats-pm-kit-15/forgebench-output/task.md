GitHub PR Review

PR:
https://github.com/officebeats/beats-pm-kit/pull/15

Title:
[codex] Add Codex browser-first policy

Body:
## Summary

Adds a Codex Browser-first policy for browser-dependent work in the kit.

## Changes

- Adds a canonical `.agent/rules/codex-browser-first.md` rule.
- Updates the generated root `AGENTS.md` adapter guidance so Codex users default to the in-app Browser for local apps, rendered UI checks, localhost demos, screenshots, click-through validation, and page inspection.
- Updates `sync_cli_adapters.py` so future adapter regeneration preserves the policy in `AGENTS.md` and `.codex/rules.md`.
- Adds regression tests for the canonical rule and generated Codex adapter text.

## Validation

- `python3 -m unittest system.tests.test_codex_browser_first`
- `python3 -m unittest system.tests.test_codex_skill_adapters`
- Commit hook passed adapter sync, command integrity, command surface audit, py_compile, adapter tests, and privacy guard.

## Notes

The worktree had unrelated pre-existing dirty files. This PR stages and commits only the browser-policy change set.

Author:
officebeats

Base:
main

Head:
codex/codex-browser-first

Changed files:
4

Additions:
99

Deletions:
0

This task context was generated from GitHub PR metadata.
