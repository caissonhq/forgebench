GitHub PR Review

PR:
https://github.com/pingdotgg/t3code/pull/2955

Title:
[codex] Fix Codex workspace skill autocomplete

Body:
## Summary
Fix Codex `$skill` autocomplete for project/worktree-local skills.

## Root cause
Codex provider status was probed from the server process cwd, so `codex app-server skills/list` did not receive the active project or worktree cwd. Project-local `.agents/skills` entries could be parsed by Codex, but T3 Code's provider snapshot did not include them for the active workspace, leaving `$create-st` and similar skill queries with no matches.

## Changes
- Thread optional `cwd` context through `server.refreshProviders`, the WebSocket contract, provider registry refreshes, and managed provider snapshots.
- Make managed providers remember an explicit refresh context so later background refreshes keep using the active workspace cwd.
- Probe Codex provider status with the active project/worktree cwd, falling back to the configured server cwd.
- Refresh the active Codex provider when the active workspace root changes so the existing `## Summary
Fix Codex `$skill` autocomplete for project/worktree-local skills.

## Root cause
Codex provider status was probed from the server process cwd, so `codex app-server skills/list` did not receive the active project or worktree cwd. Project-local `.agents/skills` entries could be parsed by Codex, but T3 Code's provider snapshot did not include them for the active workspace, leaving `$create-st` and similar skill queries with no matches.

## Changes
- Thread optional `cwd` context through `server.refreshProviders`, the WebSocket contract, provider registry refreshes, and managed provider snapshots.
- Make managed providers remember an explicit refresh context so later background refreshes keep using the active workspace cwd.
- Probe Codex provider status with the active project/worktree cwd, falling back to the configured server cwd.
 skill autocomplete has the right skill list.
- Route workspace provider refreshes through the environment-specific API so remote workspace paths refresh the matching backend environment.
- Keep OpenCode's provider refresh wrapper aligned with the new cwd contract by honoring the same optional refresh cwd fallback.
- Preserve custom Codex instance targeting while provider status is catching up, falling back to the default Codex instance only if the requested instance no longer exists.
- Avoid stale provider instance ids no-oping the workspace refresh, and clear the refresh de-dupe key after failed refreshes so the request can retry.
- Add regression coverage for Codex cwd forwarding, registry refresh context, managed-provider context reuse, local API forwarding, and workspace refresh target selection.

## Related
Related to #2637, but this PR intentionally does not change `/` command suggestions or close that issue.
Related to #2048, but this PR only wires the cwd consumer for Codex; Claude project skill discovery remains separate.
Builds on the closed stale approach from #2330, with the cwd coming from the active workspace rather than only the server config cwd.
Supersedes draft #2954 with the requested `pabloszx/` branch prefix.

## Validation
- `mise exec -- pnpm exec vp check`
- `mise exec -- pnpm --filter @t3tools/web exec vp test run --project unit src/components/ChatView.logic.test.ts`
- `mise exec -- pnpm exec vp test run apps/server/src/provider/Layers/OpenCodeProvider.test.ts apps/server/src/provider/makeManagedServerProvider.test.ts apps/server/src/provider/Layers/ProviderRegistry.test.ts apps/web/src/localApi.test.ts`
- `mise exec -- pnpm exec vp run --filter t3 --filter @t3tools/web --filter @t3tools/contracts typecheck`
- `mise exec -- pnpm exec vp run typecheck`


<!-- Macroscope's pull request summary starts here -->
<!-- Macroscope will only edit the content between these invisible markers, and the markers themselves will not be visible in the GitHub rendered markdown. -->
<!-- If you delete either of the start / end markers from your PR's description, Macroscope will append its summary at the bottom of the description. -->
> [!NOTE]
> ### Fix Codex workspace skill autocomplete by passing workspace `cwd` through provider refresh
> - Extends the provider refresh pipeline to accept an optional `cwd` so Codex (and OpenCode) status probes run in the correct workspace directory.
> - `makeManagedServerProvider` now takes `checkProvider` as a function receiving optional `ProviderSnapshotRefreshInput`, and remembers the last refresh input for subsequent background refreshes.
> - `ProviderRegistry.refresh` and `refreshInstance` accept and forward the optional input through to the underlying provider drivers.
> - The `ChatView` component triggers a Codex provider refresh with the active workspace `cwd` when a Codex provider is selected, with a fallback to the default instance if the targeted instance is not found.
> - The `serverRefreshProviders` WS RPC schema and `LocalApi`/`EnvironmentApi` contracts are extended to carry optional `instanceId` and `cwd` fields.
> - Behavioral Change: `ServerProviderShape.refresh` is now a function that must be called rather than a plain `Effect`; all callers have been updated.
>
> <!-- Macroscope's review summary starts here -->
>
> <sup><a href="https://app.macroscope.com">Macroscope</a> summarized 97cd5a8.</sup>
> <!-- Macroscope's review summary ends here -->
>
<!-- macroscope-ui-refresh -->
<!-- Macroscope's pull request summary ends here -->

<!-- CURSOR_SUMMARY -->
---

> [!NOTE]
> **Medium Risk**
> Changes the provider refresh contract and WS/API surfaces across server and web; behavior is well-tested but affects live provider snapshots and multi-instance Codex targeting.
> 
> **Overview**
> Fixes **Codex `$skill` autocomplete** for project/worktree-local skills by probing provider status against the **active workspace directory** instead of the server process cwd.
> 
> The PR adds optional **`cwd` on provider refresh** (`ProviderSnapshotRefreshInput`) and threads it through managed snapshots, the provider registry, WebSocket `serverRefreshProviders`, and local/environment APIs. **`ServerProvider.refresh`** and **`checkProvider`** become callables that accept that context; managed providers **remember** an explicit refresh cwd so later background checks keep using the same workspace. **Codex** (and **OpenCode**) status probes use `refreshInput.cwd ?? serverConfig.cwd`.
> 
> On the web client, **`ChatView`** refreshes the active **Codex** instance when the workspace root (project cwd or thread worktree) changes, using **`resolveProviderRefreshTarget`** to pick the right instance and optionally fall back to the default Codex instance if a custom id is stale. Failed refreshes clear the de-dupe key so retries can run.
> 
> Tests cover cwd forwarding, registry refresh input, managed-provider context reuse, API forwarding, and refresh target selection.
> 
> <sup>Reviewed by [Cursor Bugbot](https://cursor.com/bugbot) for commit 97cd5a8cab71a3366948fc384fe522988af6f4b8. Bugbot is set up for automated code reviews on this repo. Configure [here](https://www.cursor.com/dashboard/bugbot).</sup>
<!-- /CURSOR_SUMMARY -->

Author:
PabloSzx

Base:
main

Head:
pabloszx/workspace-skill-autocomplete-only

Changed files:
22

Additions:
460

Deletions:
68

This task context was generated from GitHub PR metadata.
