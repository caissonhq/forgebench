GitHub PR Review

PR:
https://github.com/pingdotgg/t3code/pull/2968

Title:
Refactor recoverable Effect fallbacks to orElseSucceed

Body:
## Summary
- Replaced recoverable `Effect.catch` fallbacks with `Effect.orElseSucceed` across desktop, server, relay, and shared runtime code.
- Simplified a large number of error-handling paths that intentionally degrade to safe defaults like `null`, `false`, empty arrays, or cached fallback values.
- Tightened the server package TypeScript setup by removing the Bun type dependency from `apps/server` and pinning `@types/bun` where needed.
- Updated a small set of tests and build scripts to match the new fallback style and workspace configuration.

## Testing
- Not run.
- Expected checks for this branch: `vp check`, `vp run typecheck`.
- If native mobile code is affected, also run `vp run lint:mobile`.

<!-- CURSOR_SUMMARY -->
---

> [!NOTE]
> **Low Risk**
> Behavior-preserving API style change with no auth or data-model changes; minor TS config risk around Bun types in the server PTY layer.
> 
> **Overview**
> Replaces recoverable **`Effect.catch(() => Effect.succeed(...))`** fallbacks with **`Effect.orElseSucceed(() => ...)`** across desktop, server, relay, shared Tailscale, and build scripts. Fallback values and degradation behavior stay the same (defaults like `null`, `false`, empty collections, and safe HTTP error responses).
> 
> **TypeScript / workspace:** `apps/server` drops global **`bun`** types from `tsconfig.json` and pins **`@types/bun@1.3.14`** in devDependencies; **`BunPTY.ts`** adds a local `/// <reference types="bun" />`. **`oxlint-plugin-t3code`** and **`scripts`** remove catalog **`@types/bun`**; **`scripts`** also drops **`@anthropic-ai/claude-agent-sdk`**. Root **`package.json`** adds a **`tc`** alias for typecheck; lockfile bumps **`@effect/tsgo`** and **`@typescript/native-preview`** and trims unused catalog entries.
> 
> <sup>Reviewed by [Cursor Bugbot](https://cursor.com/bugbot) for commit caa0e02a7c02707c799329b2032d829c12baabaa. Bugbot is set up for automated code reviews on this repo. Configure [here](https://www.cursor.com/dashboard/bugbot).</sup>
<!-- /CURSOR_SUMMARY -->

<!-- Macroscope's pull request summary starts here -->
<!-- Macroscope will only edit the content between these invisible markers, and the markers themselves will not be visible in the GitHub rendered markdown. -->
<!-- If you delete either of the start / end markers from your PR's description, Macroscope will append its summary at the bottom of the description. -->
> [!NOTE]
> ### Replace `Effect.catch` fallbacks with `Effect.orElseSucceed` across the codebase
> Replaces all instances of `Effect.catch(() => Effect.succeed(value))` with the equivalent `Effect.orElseSucceed(() => value)` across desktop, server, relay, and script code. This is a pure refactor with no behavioral change — `Effect.orElseSucceed` is the idiomatic Effect-TS API for recovering from any failure with a success value.
>
> <!-- Macroscope's review summary starts here -->
>
> <sup><a href="https://app.macroscope.com">Macroscope</a> summarized caa0e02.</sup>
> <!-- Macroscope's review summary ends here -->
>
<!-- macroscope-ui-refresh -->
<!-- Macroscope's pull request summary ends here -->

Author:
juliusmarminge

Base:
main

Head:
feature/effect-fallback-refactor

Changed files:
42

Additions:
182

Deletions:
318

This task context was generated from GitHub PR metadata.
