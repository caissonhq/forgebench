You are repairing an AI-generated code change after ForgeBench review.

Original task:
GitHub PR Review

PR:
https://github.com/pingdotgg/t3code/pull/2973

Title:
fix(cloud): use Electron fetch for proxying Clerk IPC requests

Body:
Fixes #2970

## Summary
- Swaps the desktop waitlist form from direct Clerk client calls to `useWaitlist` so it uses the provider-managed resource.
- Adds Clerk CAPTCHA mount support for the custom desktop waitlist flow.
- Improves submit handling with trimmed emails, provider field error display, and disabled submit state while fetching.
- Adds browser coverage for the CAPTCHA mount point and waitlist submission path.

## Testing
- `Not run`
- Added browser tests in `apps/web/src/components/clerk/DesktopClerkWaitlist.browser.tsx` for the CAPTCHA mount and waitlist submission behavior.
- Per repo requirements, `vp check` and `vp run typecheck` should be run before merge.


<!-- CURSOR_SUMMARY -->
---

> [!NOTE]
> **Medium Risk**
> Changes how authenticated Clerk API traffic is executed in the desktop main process; host allowlisting is unchanged but network behavior and error paths differ from the prior HttpClient default.
> 
> **Overview**
> Routes desktop **Clerk Frontend API** IPC fetches through Electron’s network stack by wiring **`electronNetFetchLayer`**: it resolves **`electron.net.fetch`** when present, logs and falls back to **`globalThis.fetch`**, and supplies that to Effect’s **`FetchHttpClient`**.
> 
> The **`fetchCloudAuth`** handler delegates to a new **`executeCloudAuthFetch`** helper that builds the HTTP request (including optional body with the caller’s content-type), runs it, and maps failures to **`DesktopCloudAuthFetchError`**.
> 
> Tests no longer mock Effect’s **`HttpClient`** layer; they stub **`globalThis.fetch`** with a **`recordedFetch`** helper and assert forwarded URL, method, headers, and body—matching the fallback path the layer uses in non-Electron test runs.
> 
> <sup>Reviewed by [Cursor Bugbot](https://cursor.com/bugbot) for commit 25542d7deacb6092667eacd163f443338c8fcb91. Bugbot is set up for automated code reviews on this repo. Configure [here](https://www.cursor.com/dashboard/bugbot).</sup>
<!-- /CURSOR_SUMMARY -->



<!-- Macroscope's pull request summary starts here -->
<!-- Macroscope will only edit the content between these invisible markers, and the markers themselves will not be visible in the GitHub rendered markdown. -->
<!-- If you delete either of the start / end markers from your PR's description, Macroscope will append its summary at the bottom of the description. -->
> [!NOTE]
> ### Use Electron's `net.fetch` for proxying Clerk IPC requests in the desktop app
> - Introduces `electronNetFetchLayer` in [cloudAuth.ts](https://github.com/pingdotgg/t3code/pull/2973/files#diff-e5ff3c14598dc28813f4a3eb9b753939eeccfb39445c9950dae9fafa9db7f0e8) that provides `electron.net.fetch` as the HTTP client when running in Electron, falling back to `globalThis.fetch` with a warning if unavailable.
> - Adds `executeCloudAuthFetch` to centralize request construction and error mapping, replacing inline request handling in the `fetchCloudAuth` IPC handler.
> - Rewrites tests in [cloudAuth.test.ts](https://github.com/pingdotgg/t3code/pull/2973/files#diff-c4b52563d999054f74b466fe8ecdf8fa67237e79f1e9ce3bd393273bc74dd60f) to record calls against `globalThis.fetch` directly instead of mocking the Effect `HttpClient` layer.
> - Behavioral Change: execution failures now carry the reason `'Desktop cloud auth fetch failed to execute.'` instead of previous error messages.
>
> <!-- Macroscope's review summary starts here -->
>
> <sup><a href="https://app.macroscope.com">Macroscope</a> summarized 25542d7.</sup>
> <!-- Macroscope's review summary ends here -->
>
<!-- macroscope-ui-refresh -->
<!-- Macroscope's pull request summary ends here -->

Author:
juliusmarminge

Base:
main

Head:
t3code/d574c457

Changed files:
2

Additions:
100

Deletions:
85

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
  UID: fnd_c7f699366288
  Kind: ui_copy_changed
  Confidence: LOW
  Evidence: STATIC
  Files: apps/web/src/components/clerk/DesktopClerkWaitlist.browser.tsx, apps/web/src/components/clerk/DesktopClerkWaitlist.tsx
  Evidence snippets:
  - Likely user-facing, documentation, or UI file changed: apps/web/src/components/clerk/DesktopClerkWaitlist.browser.tsx
  - Likely user-facing, documentation, or UI file changed: apps/web/src/components/clerk/DesktopClerkWaitlist.tsx
  Explanation: The patch touches files that often affect user-facing copy, documentation, or UI. This is not automatically a defect, but it deserves product review when relevant.
  Suggested fix: Review the changed UI or copy for accuracy, tone, and unintended product behavior.
  Diff hunk context:
  ```diff
  diff -- apps/web/src/components/clerk/DesktopClerkWaitlist.browser.tsx
  @@ -0,0 +1,62 @@
  +import "../../index.css";
  +
  +import { page, userEvent } from "vite-plus/test/browser";
  +import { afterEach, beforeEach, describe, expect, it, vi } from "vite-plus/test";
  +import { render } from "vitest-browser-react";
  +
  +import { DesktopClerkWaitlist } from "./DesktopClerkWaitlist";
  +
  +const waitlistJoinMock = vi.hoisted(() => vi.fn(async () => ({ error: null })));
  +const useWaitlistMock = vi.hoisted(() =>
  +  vi.fn(() => ({
  +    errors: {
  +      fields: {
  +        emailAddress: null,
  +      },
  +      global: null,
  +      raw: null,
  +    },
  +    fetchStatus: "idle",
  +    waitlist: {
  +      id: "",
  +      join: waitlistJoinMock,
  +    },
  +  })),
  +);
  +
  +vi.mock("@clerk/react", () => ({
  +  useClerk: () => ({}),
  +  useSignIn: () => ({ isLoaded: true, signIn: null }),
  +  useSignUp: () => ({ isLoaded: true, signUp: null }),
  +  useWaitlist: useWaitlistMock,
  +}));
  +
  +describe("DesktopClerkWaitlist", () => {
  +  beforeEach(() => {
  +    waitlistJoinMock.mockReset();
  +    waitlistJoinMock.mockResolvedValue({ error: null });
  +    useWaitlistMock.mockClear();
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
