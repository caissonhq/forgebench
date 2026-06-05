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
