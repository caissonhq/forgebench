You are repairing an AI-generated code change after ForgeBench review.

Original task:
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

ForgeBench merge posture:
LOW_CONCERN

No required repair was identified. Use this only to tighten tests or advisory concerns.

Configuration note:
This review ran with generic heuristics. Do not broaden scope based on low-confidence generic findings.

Deterministic check failures:
- Deterministic checks were not run.

Static and guardrail findings:
- ADVISORY: User-facing copy or UI surface changed
  UID: fnd_4026189d452c
  Kind: ui_copy_changed
  Confidence: LOW
  Evidence: STATIC
  Files: .agent/rules/codex-browser-first.md, AGENTS.md
  Evidence snippets:
  - Likely user-facing, documentation, or UI file changed: .agent/rules/codex-browser-first.md
  - Likely user-facing, documentation, or UI file changed: AGENTS.md
  Explanation: The patch touches files that often affect user-facing copy, documentation, or UI. This is not automatically a defect, but it deserves product review when relevant.
  Suggested fix: Review the changed UI or copy for accuracy, tone, and unintended product behavior.
  Diff hunk context:
  ```diff
  diff -- .agent/rules/codex-browser-first.md
  @@ -0,0 +1,23 @@
  +# Codex Browser First
  +
  +Use this rule whenever Codex needs a browser for local apps, rendered UI checks, localhost demos, screenshots, click-through validation, or web page inspection.
  +
  +## Default
  +
  +1. Use the Codex in-app Browser first.
  +2. Keep browser work contained in the Codex session unless the user explicitly asks to use an external browser.
  +3. For local apps, start the required local server normally, then open and validate the URL in the Codex Browser.
  +4. Capture screenshots, DOM state, console warnings/errors, and interaction evidence through the Codex Browser whenever possible.
  +5. Do not default to macOS `open`, Chrome, Edge, Safari, Computer Use, or standalone Playwright before trying the Codex Browser.
  +
  +## External Browser Fallback
  +
  +Use an external browser only when there is a concrete reason, such as:
  +
  +- The user explicitly asks for an external browser.
  +- The task requires the user's browser profile, cookies, extensions, SSO state, or saved credentials.
  +- The issue is browser-specific and needs Chrome, Edge, Safari, or Firefox reproduction.
  +- The Codex Browser is unavailable, cannot reach the target, or fails after a reasonable attempt.
  +- The workflow requires browser permissions, downloads, or OS integration that the Codex Browser cannot provide.
  +
  +When using an external browser, state the reason briefly and keep the external action scoped to that need.
  diff -- AGENTS.md
  @@ -20,6 +20,18 @@ On a new Codex session:
   6. Translate Antigravity-only primitives into Codex equivalents instead of failing.
   7. Write durable outputs back into the standard repo folders so runtime switching stays lossless.
   
  +## Codex Browser First
  +
  +When a task needs a browser for local apps, rendered UI checks, localhost demos, screenshots, click-through validation, or page inspection:
  +
  +1. Use the Codex in-app Browser first.
  +2. Keep browser work contained in the Codex session whenever possible.
  +3. Start local servers with terminal commands when needed, then open and validate the URL in the Codex Browser.
  +4. Capture screenshots, DOM state, console warnings/errors, and interaction evidence through the Codex Browser whenever possible.
  +5. Do not default to macOS `open`, Chrome, Edge, Safari, Computer Use, or standalone Playwright before trying the Codex Browser.
  +
  ```
  ... (truncated, see patch.diff for full context)

Heuristic review lens findings:
- No heuristic review lens findings.

LLM reviewer notes:
- LLM review was not run.

Suppressed or policy-calibrated findings:
- None.

Instructions:
- Fix only the issues listed above.
- For each issue, either make the smallest necessary repair or clearly explain why the issue is acceptable.
- Do not broaden the scope.
- Do not add unrelated refactors.
- Do not introduce new dependencies unless explicitly necessary.
- Preserve the original product and architecture guardrails.
- Treat heuristic review lens findings as review tasks, not as automatic approval or rejection.
- Add or update tests where ForgeBench identified missing coverage.
- Before returning the repair, run the configured checks that failed if they are available locally. If you cannot run them, explain why.
- After making changes, summarize exactly what changed and why.

Project guardrails:
- No project-specific protected behavior was provided.
