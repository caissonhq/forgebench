You are repairing an AI-generated code change after ForgeBench review.

Original task:
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

ForgeBench merge posture:
REVIEW

Address the issues below or explain why each is acceptable.

Configuration note:
This review ran with generic heuristics. Do not broaden scope based on low-confidence generic findings.

Deterministic check failures:
- Deterministic checks were not run.

Static and guardrail findings:
- MEDIUM: Dependency surface changed
  UID: fnd_cfcc7657c16a
  Kind: dependency_surface_changed
  Confidence: HIGH
  Evidence: STATIC
  Files: apps/server/package.json, oxlint-plugin-t3code/package.json, package.json, pnpm-lock.yaml, scripts/package.json
  Evidence snippets:
  - Dependency manifest or lockfile changed: apps/server/package.json
  - Dependency manifest or lockfile changed: oxlint-plugin-t3code/package.json
  - Dependency manifest or lockfile changed: package.json
  - Dependency manifest or lockfile changed: pnpm-lock.yaml
  - Dependency manifest or lockfile changed: scripts/package.json
  Explanation: The patch changes dependency manifests or lockfiles. Dependency changes can affect install behavior, runtime behavior, and supply-chain exposure.
  Suggested fix: Confirm the dependency change is required, review the lockfile impact, and run the relevant build and tests.
  Diff hunk context:
  ```diff
  diff -- apps/server/package.json
  @@ -38,7 +38,7 @@
       "@t3tools/shared": "workspace:*",
       "@t3tools/tailscale": "workspace:*",
       "@t3tools/web": "workspace:*",
  -    "@types/bun": "catalog:",
  +    "@types/bun": "1.3.14",
       "@types/node": "catalog:",
       "effect-acp": "workspace:*",
       "effect-codex-app-server": "workspace:*",
  diff -- oxlint-plugin-t3code/package.json
  @@ -13,7 +13,6 @@
     },
     "devDependencies": {
       "@effect/vitest": "catalog:",
  -    "@types/bun": "catalog:",
       "vite-plus": "catalog:"
     }
   }
  diff -- package.json
  @@ -17,6 +17,7 @@
       "build:marketing": "vp run --filter @t3tools/marketing build",
       "build:desktop": "vp run --filter @t3tools/desktop --filter t3 build",
       "typecheck": "vp run -r --concurrency-limit 2 typecheck",
  +    "tc": "vp run -r --concurrency-limit 2 typecheck",
       "lint": "vp lint --report-unused-disable-directives",
       "lint:mobile": "node scripts/mobile-native-static-check.ts",
       "test": "vp run -r test",
  diff -- pnpm-lock.yaml
  @@ -10,8 +10,8 @@ catalogs:
         specifier: 4.0.0-beta.78
         version: 4.0.0-beta.78
       '@effect/tsgo':
  -      specifier: 0.11.4
  -      version: 0.11.4
  +      specifier: 0.13.2
  +      version: 0.13.2
       '@noble/curves':
         specifier: 1.9.1
         version: 1.9.1
  ```
  ... (truncated, see patch.diff for full context)
- MEDIUM: Build or configuration surface changed
  UID: fnd_a6f6d281a486
  Kind: build_config_changed
  Confidence: MEDIUM
  Evidence: STATIC
  Files: apps/server/tsconfig.json, oxlint-plugin-t3code/tsconfig.json
  Evidence snippets:
  - Build or configuration file changed: apps/server/tsconfig.json
  - Build or configuration file changed: oxlint-plugin-t3code/tsconfig.json
  Explanation: The patch changes build, CI, package, or platform configuration. These files can change behavior outside the code paths touched by the task.
  Suggested fix: Review the configuration change separately and run the build or CI path it affects.
  Diff hunk context:
  ```diff
  diff -- apps/server/tsconfig.json
  @@ -1,7 +1,7 @@
   {
     "extends": "../../tsconfig.base.json",
     "compilerOptions": {
  -    "types": ["node", "bun"],
  +    "types": ["node"],
       "lib": ["ESNext", "esnext.disposable"]
     },
     "include": ["src", "vite.config.ts", "scripts", "integration", "../../scripts/lib"]
  diff -- oxlint-plugin-t3code/tsconfig.json
  @@ -2,7 +2,7 @@
     "extends": "../tsconfig.base.json",
     "compilerOptions": {
       "composite": true,
  -    "types": ["bun", "node"],
  +    "types": ["node"],
       "lib": ["ESNext", "esnext.disposable"]
     },
     "include": ["**/*.ts"]
  ```
- HIGH: Persistence or schema behavior may have changed
  UID: fnd_850d53d119f3
  Kind: persistence_schema_changed
  Confidence: MEDIUM
  Evidence: STATIC
  Files: apps/desktop/src/app/DesktopAppIdentity.ts, apps/server/src/checkpointing/Layers/CheckpointStore.ts
  Evidence snippets:
  - Persistence, schema, model, or migration file changed: apps/desktop/src/app/DesktopAppIdentity.ts
  - Persistence, schema, model, or migration file changed: apps/server/src/checkpointing/Layers/CheckpointStore.ts
  Explanation: The patch changes a likely persistence, schema, model, or migration file. If no corresponding test file changed, data behavior may have changed without regression coverage.
  Suggested fix: Review the data model impact, verify migration behavior, and add tests around persistence compatibility.
  Diff hunk context:
  ```diff
  diff -- apps/desktop/src/app/DesktopAppIdentity.ts
  @@ -52,7 +52,7 @@ const make = Effect.gen(function* () {
             Effect.map((parsed) =>
               Option.fromNullishOr(parsed.t3codeCommitHash).pipe(Option.flatMap(normalizeCommitHash)),
             ),
  -          Effect.catch(() => Effect.succeed(Option.none<string>())),
  +          Effect.orElseSucceed(() => Option.none<string>()),
           ),
       });
     });
  diff -- apps/server/src/checkpointing/Layers/CheckpointStore.ts
  @@ -35,7 +35,7 @@ const makeCheckpointStore = Effect.gen(function* () {
     const isGitRepository: CheckpointStoreShape["isGitRepository"] = (cwd) =>
       vcsRegistry.resolve({ cwd, requestedKind: "git" }).pipe(
         Effect.map(() => true),
  -      Effect.catch(() => Effect.succeed(false)),
  +      Effect.orElseSucceed(() => false),
       );
   
     const captureCheckpoint: CheckpointStoreShape["captureCheckpoint"] = Effect.fn(
  ```
- MEDIUM: Patch touches a broad file surface
  UID: fnd_220507fdc273
  Kind: broad_file_surface
  Confidence: HIGH
  Evidence: STATIC
  Files: apps/desktop/src/app/DesktopAppIdentity.ts, apps/desktop/src/backend/tailscaleEndpointProvider.ts, apps/desktop/src/settings/DesktopAppSettings.ts, apps/desktop/src/settings/DesktopClientSettings.ts, apps/desktop/src/settings/DesktopSavedEnvironments.ts, apps/desktop/src/shell/DesktopShellEnvironment.ts, apps/desktop/src/updates/DesktopUpdates.ts, apps/server/package.json, apps/server/src/checkpointing/Layers/CheckpointStore.ts, apps/server/src/cloud/ManagedEndpointRuntime.ts, apps/server/src/git/GitManager.ts, apps/server/src/http.ts, apps/server/src/orchestration/Layers/ProjectionPipeline.ts, apps/server/src/project/Layers/ProjectFaviconResolver.ts, apps/server/src/provider/providerMaintenance.ts, apps/server/src/review/ReviewService.ts, apps/server/src/sourceControl/BitbucketApi.ts, apps/server/src/sourceControl/SourceControlProviderDiscovery.ts, apps/server/src/sourceControl/SourceControlRepositoryService.ts, apps/server/src/telemetry/Layers/AnalyticsService.test.ts, apps/server/src/terminal/Layers/Manager.ts, apps/server/src/textGeneration/CodexTextGeneration.ts, apps/server/src/vcs/GitVcsDriver.ts, apps/server/src/vcs/GitVcsDriverCore.ts, apps/server/src/workspace/Layers/WorkspaceEntries.ts, apps/server/src/workspace/Layers/WorkspaceFileSystem.test.ts, apps/server/src/workspace/Layers/WorkspacePaths.ts, apps/server/src/ws.ts, apps/server/tsconfig.json, infra/relay/scripts/deploy.ts, infra/relay/src/auth/RelayTokens.ts, infra/relay/src/environments/ManagedEndpointProvider.ts, oxlint-plugin-t3code/package.json, oxlint-plugin-t3code/tsconfig.json, package.json, packages/tailscale/src/tailscale.ts, pnpm-lock.yaml, pnpm-workspace.yaml, scripts/build-desktop-artifact.ts, scripts/mobile-native-static-check.ts, scripts/package.json, apps/server/src/terminal/Layers/BunPTY.ts
  Evidence snippets:
  - 42 files changed
  Explanation: The patch changes more than 10 files. Broad patches are harder to review and more likely to contain unrelated changes.
  Suggested fix: Split unrelated changes, reduce the patch scope, or provide a clear review map for the touched areas.
  Diff hunk context:
  ```diff
  diff -- apps/desktop/src/app/DesktopAppIdentity.ts
  @@ -52,7 +52,7 @@ const make = Effect.gen(function* () {
             Effect.map((parsed) =>
               Option.fromNullishOr(parsed.t3codeCommitHash).pipe(Option.flatMap(normalizeCommitHash)),
             ),
  -          Effect.catch(() => Effect.succeed(Option.none<string>())),
  +          Effect.orElseSucceed(() => Option.none<string>()),
           ),
       });
     });
  diff -- apps/desktop/src/backend/tailscaleEndpointProvider.ts
  @@ -116,11 +116,11 @@ export const resolveTailscaleAdvertisedEndpoints = Effect.fn("resolveTailscaleAd
         input.statusJson === undefined
           ? yield* readTailscaleStatus.pipe(
               Effect.map((status) => status.magicDnsName),
  -            Effect.catch(() => Effect.succeed(null)),
  +            Effect.orElseSucceed(() => null),
             )
           : input.statusJson
             ? yield* parseTailscaleMagicDnsName(input.statusJson).pipe(
  -              Effect.catch(() => Effect.succeed(null)),
  +              Effect.orElseSucceed(() => null),
               )
             : null;
       const magicDnsEndpoint = yield* resolveTailscaleMagicDnsAdvertisedEndpoint({
  diff -- apps/desktop/src/settings/DesktopAppSettings.ts
  @@ -209,7 +209,7 @@ function readSettings(
           onSome: (raw) =>
             decodeDesktopSettingsJson(raw).pipe(
               Effect.map((parsed) => normalizeDesktopSettingsDocument(parsed, appVersion)),
  -            Effect.catch(() => Effect.succeed(defaultSettings)),
  +            Effect.orElseSucceed(() => defaultSettings),
             ),
         }),
       ),
  diff -- apps/desktop/src/settings/DesktopClientSettings.ts
  @@ -63,7 +63,7 @@ const readClientSettings = (
           onSome: (raw) =>
             decodeClientSettingsJson(raw).pipe(
               Effect.map((settings) => Option.some(settings)),
  ```
  ... (truncated, see patch.diff for full context)

Heuristic review lens findings:
- Test Skeptic:
  - LOW: Test changes do not show a clear assertion signal
    UID: fnd_cabf1ac29888
    Kind: test_skeptic_weak_test_signal
    Confidence: LOW
    Files: apps/server/src/telemetry/Layers/AnalyticsService.test.ts, apps/server/src/workspace/Layers/WorkspaceFileSystem.test.ts
    Evidence snippets:
    - Test files changed, but added test lines do not include common assertion tokens.
    - Weak assertion signal in test file: apps/server/src/telemetry/Layers/AnalyticsService.test.ts
    - Weak assertion signal in test file: apps/server/src/workspace/Layers/WorkspaceFileSystem.test.ts
    Explanation: The patch changes tests, but the added lines do not show obvious assertion or expectation tokens. That may be fine, but it is a weak static signal for behavior coverage.
    Suggested fix: Review the tests for real assertions, or add focused assertions for the changed behavior.
    Diff hunk context:
    ```diff
    diff -- apps/server/src/telemetry/Layers/AnalyticsService.test.ts
    @@ -62,7 +62,7 @@ it.layer(NodeServices.layer)("AnalyticsService test", (it) => {
     
               const payload = yield* request.json.pipe(
                 Effect.map((body) => body as RecordedBatchRequest["body"]),
    -            Effect.catch(() => Effect.succeed(null)),
    +            Effect.orElseSucceed(() => null),
               );
     
               capturedRequests.push({ path: request.url, body: payload });
    diff -- apps/server/src/workspace/Layers/WorkspaceFileSystem.test.ts
    @@ -132,7 +132,7 @@ it.layer(TestLayer)("WorkspaceFileSystemLive", (it) => {
             const escapedPath = path.resolve(cwd, "..", "escape.md");
             const escapedStat = yield* fileSystem
               .stat(escapedPath)
    -          .pipe(Effect.catch(() => Effect.succeed(null)));
    +          .pipe(Effect.orElseSucceed(() => null));
             expect(escapedStat).toBeNull();
           }),
         );
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
