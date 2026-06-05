You are repairing an AI-generated code change after ForgeBench review.

Original task:
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

ForgeBench merge posture:
REVIEW

Address the issues below or explain why each is acceptable.

Configuration note:
This review ran with generic heuristics. Do not broaden scope based on low-confidence generic findings.

Deterministic check failures:
- Deterministic checks were not run.

Static and guardrail findings:
- MEDIUM: Patch touches a broad file surface
  UID: fnd_2b622c6c09b6
  Kind: broad_file_surface
  Confidence: HIGH
  Evidence: STATIC
  Files: apps/server/src/provider/Drivers/ClaudeDriver.ts, apps/server/src/provider/Drivers/CodexDriver.ts, apps/server/src/provider/Drivers/CursorDriver.ts, apps/server/src/provider/Drivers/OpenCodeDriver.ts, apps/server/src/provider/Layers/CodexProvider.ts, apps/server/src/provider/Layers/ProviderAdapterRegistry.test.ts, apps/server/src/provider/Layers/ProviderRegistry.test.ts, apps/server/src/provider/Layers/ProviderRegistry.ts, apps/server/src/provider/Services/ProviderRegistry.ts, apps/server/src/provider/Services/ServerProvider.ts, apps/server/src/provider/makeManagedServerProvider.test.ts, apps/server/src/provider/makeManagedServerProvider.ts, apps/server/src/ws.ts, apps/web/src/components/ChatView.tsx, apps/web/src/localApi.test.ts, apps/web/src/localApi.ts, packages/contracts/src/ipc.ts, packages/contracts/src/rpc.ts, apps/server/src/provider/Drivers/OpenCodeDriver.ts, apps/web/src/components/ChatView.logic.test.ts, apps/web/src/components/ChatView.logic.ts, apps/web/src/components/ChatView.tsx, apps/web/src/components/ChatView.logic.test.ts, apps/web/src/components/ChatView.logic.ts, apps/web/src/components/ChatView.tsx, apps/web/src/components/ChatView.browser.tsx, apps/web/src/components/ChatView.tsx, apps/web/src/environmentApi.ts, apps/web/src/localApi.test.ts, packages/contracts/src/ipc.ts
  Evidence snippets:
  - 30 files changed
  Explanation: The patch changes more than 10 files. Broad patches are harder to review and more likely to contain unrelated changes.
  Suggested fix: Split unrelated changes, reduce the patch scope, or provide a clear review map for the touched areas.
  Diff hunk context:
  ```diff
  diff -- apps/server/src/provider/Drivers/ClaudeDriver.ts
  @@ -170,7 +170,7 @@ export const ClaudeDriver: ProviderDriver<ClaudeSettings, ClaudeDriverEnv> = {
           haveSettingsChanged: () => false,
           initialSnapshot: (settings) =>
             makePendingClaudeProvider(settings).pipe(Effect.map(stampIdentity)),
  -        checkProvider,
  +        checkProvider: () => checkProvider,
           enrichSnapshot: ({ snapshot, publishSnapshot }) =>
             enrichProviderSnapshotWithVersionAdvisory(snapshot, maintenanceCapabilities).pipe(
               Effect.provideService(HttpClient.HttpClient, httpClient),
  diff -- apps/server/src/provider/Drivers/CodexDriver.ts
  @@ -112,6 +112,7 @@ export const CodexDriver: ProviderDriver<CodexSettings, CodexDriverEnv> = {
         const spawner = yield* ChildProcessSpawner.ChildProcessSpawner;
         const httpClient = yield* HttpClient.HttpClient;
         const eventLoggers = yield* ProviderEventLoggers;
  +      const serverConfig = yield* ServerConfig;
         const processEnv = mergeProviderInstanceEnvironment(environment);
         const homeLayout = yield* resolveCodexHomeLayout(config);
         const continuationIdentity = codexContinuationIdentity(homeLayout);
  diff -- apps/server/src/provider/Drivers/CodexDriver.ts
  @@ -159,10 +160,16 @@ export const CodexDriver: ProviderDriver<CodexSettings, CodexDriverEnv> = {
         // in as instance rebuilds from the registry rather than in-place
         // updates. Pre-provide `ChildProcessSpawner` so the check fits
         // `makeManagedServerProvider.checkProvider`'s `R = never`.
  -      const checkProvider = checkCodexProviderStatus(effectiveConfig, undefined, processEnv).pipe(
  -        Effect.map(stampIdentity),
  -        Effect.provideService(ChildProcessSpawner.ChildProcessSpawner, spawner),
  -      );
  +      const checkProvider = (refreshInput?: { readonly cwd?: string | undefined }) =>
  +        checkCodexProviderStatus(
  +          effectiveConfig,
  +          undefined,
  +          processEnv,
  +          refreshInput?.cwd ?? serverConfig.cwd,
  +        ).pipe(
  +          Effect.map(stampIdentity),
  +          Effect.provideService(ChildProcessSpawner.ChildProcessSpawner, spawner),
  +        );
         const snapshot = yield* makeManagedServerProvider<CodexSettings>({
           maintenanceCapabilities,
  ```
  ... (truncated, see patch.diff for full context)
- ADVISORY: User-facing copy or UI surface changed
  UID: fnd_b2956cd24d9d
  Kind: ui_copy_changed
  Confidence: LOW
  Evidence: STATIC
  Files: apps/web/src/components/ChatView.browser.tsx, apps/web/src/components/ChatView.tsx
  Evidence snippets:
  - Likely user-facing, documentation, or UI file changed: apps/web/src/components/ChatView.browser.tsx
  - Likely user-facing, documentation, or UI file changed: apps/web/src/components/ChatView.tsx
  Explanation: The patch touches files that often affect user-facing copy, documentation, or UI. This is not automatically a defect, but it deserves product review when relevant.
  Suggested fix: Review the changed UI or copy for accuracy, tone, and unintended product behavior.
  Diff hunk context:
  ```diff
  diff -- apps/web/src/components/ChatView.tsx
  @@ -202,6 +202,7 @@ const EMPTY_PROPOSED_PLANS: Thread["proposedPlans"] = [];
   const EMPTY_PROVIDERS: ServerProvider[] = [];
   const EMPTY_PROVIDER_SKILLS: ServerProvider["skills"] = [];
   const EMPTY_PENDING_USER_INPUT_ANSWERS: Record<string, PendingUserInputDraftAnswer> = {};
  +const CODEX_PROVIDER_DRIVER = ProviderDriverKind.make("codex");
   type EnvironmentUnavailableState = {
     readonly environmentId: EnvironmentId;
     readonly label: string;
  diff -- apps/web/src/components/ChatView.tsx
  @@ -844,6 +845,7 @@ export default function ChatView(props: ChatViewProps) {
     const composerImagesRef = useRef<ComposerImageAttachment[]>([]);
     const composerTerminalContextsRef = useRef<TerminalContextDraft[]>([]);
     const localComposerRef = useRef<ChatComposerHandle | null>(null);
  +  const codexWorkspaceProviderRefreshKeyRef = useRef<string | null>(null);
     const composerRef = useComposerHandleContext() ?? localComposerRef;
     const [showScrollToBottom, setShowScrollToBottom] = useState(false);
     const [expandedImage, setExpandedImage] = useState<ExpandedImagePreview | null>(null);
  diff -- apps/web/src/components/ChatView.tsx
  @@ -1859,6 +1861,34 @@ export default function ChatView(props: ChatViewProps) {
     const activeProjectCwd = activeProject?.cwd ?? null;
     const activeThreadWorktreePath = activeThread?.worktreePath ?? null;
     const activeWorkspaceRoot = activeThreadWorktreePath ?? activeProjectCwd ?? undefined;
  +  useEffect(() => {
  +    if (!activeWorkspaceRoot) return;
  +    const refreshProviderInstanceId =
  +      activeProviderInstanceId ?? defaultInstanceIdForDriver(selectedProvider);
  +    const refreshProviderDriver = activeProviderStatus?.driver ?? selectedProvider;
  +    if (refreshProviderDriver !== CODEX_PROVIDER_DRIVER) return;
  +
  +    const refreshKey = `${environmentId}\u0000${refreshProviderInstanceId}\u0000${activeWorkspaceRoot}`;
  +    if (codexWorkspaceProviderRefreshKeyRef.current === refreshKey) return;
  +
  +    const api = readLocalApi();
  +    if (!api) return;
  +    codexWorkspaceProviderRefreshKeyRef.current = refreshKey;
  +    void api.server
  +      .refreshProviders({
  +        instanceId: refreshProviderInstanceId,
  +        cwd: activeWorkspaceRoot,
  ```
  ... (truncated, see patch.diff for full context)

Heuristic review lens findings:
- Test Skeptic:
  - LOW: Test changes do not show a clear assertion signal
    UID: fnd_3e8b76cc7439
    Kind: test_skeptic_weak_test_signal
    Confidence: LOW
    Files: apps/server/src/provider/Layers/ProviderAdapterRegistry.test.ts
    Evidence snippets:
    - Test files changed, but added test lines do not include common assertion tokens.
    - Weak assertion signal in test file: apps/server/src/provider/Layers/ProviderAdapterRegistry.test.ts
    Explanation: The patch changes tests, but the added lines do not show obvious assertion or expectation tokens. That may be fine, but it is a weak static signal for behavior coverage.
    Suggested fix: Review the tests for real assertions, or add focused assertions for the changed behavior.
    Diff hunk context:
    ```diff
    diff -- apps/server/src/provider/Layers/ProviderAdapterRegistry.test.ts
    @@ -120,7 +120,7 @@ const makeFakeInstance = (
             packageName: null,
           }),
           getSnapshot: Effect.succeed({} as unknown as ServerProvider),
    -      refresh: Effect.succeed({} as unknown as ServerProvider),
    +      refresh: () => Effect.succeed({} as unknown as ServerProvider),
           streamChanges: Stream.empty,
         },
         adapter,
    ```

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
