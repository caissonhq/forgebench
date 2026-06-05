You are repairing an AI-generated code change after ForgeBench review.

Original task:
GitHub PR Review

PR:
https://github.com/tsumi233/cc-switch/pull/1

Title:
[codex] Fix Codex chat tool name fallback

Body:
## What changed

- Infer missing Chat Completions `tool_call.function.name` values from the original Codex Responses tool schema when the upstream provider omits the name.
- Buffer streamed Chat tool calls until a usable name is available, then restore the proper Responses tool call item.
- Keep safe Codex completion summary logs for diagnosing empty outputs and tool-call issues without logging request content or secrets.
- Disable updater artifact generation so local unsigned macOS/Windows builds do not require private updater signing keys.

## Why

With CC Switch local route mapping enabled for Codex through Chat Completions providers, some upstream responses produced tool-call arguments such as `cmd`, `workdir`, and `yield_time_ms` but omitted `function.name`. Codex then received `function_call.name = ""` and returned `unsupported call`, so the model kept saying it would call tools but nothing actually executed.

## Validation

- `cargo test tool_call_name_from_arguments`
- `cargo test transform_codex_chat::tests::`
- `cargo test streaming_codex_chat::tests::`
- `cargo check`
- `pnpm tauri build`

Built local macOS artifacts successfully under `src-tauri/target/release/bundle/`.

Author:
tsumi233

Base:
main

Head:
codex/codex-tool-name-fallback

Changed files:
22

Additions:
895

Deletions:
28

This task context was generated from GitHub PR metadata.

ForgeBench merge posture:
REVIEW

Address the issues below or explain why each is acceptable.

Configuration note:
This review ran with generic heuristics. Do not broaden scope based on low-confidence generic findings.

Deterministic check failures:
- Deterministic checks were not run.

Static and guardrail findings:
- HIGH: Persistence or schema behavior may have changed
  UID: fnd_e3046b7a523b
  Kind: persistence_schema_changed
  Confidence: MEDIUM
  Evidence: STATIC
  Files: src-tauri/src/database/dao/proxy.rs, src-tauri/src/database/mod.rs, src-tauri/src/database/schema.rs, src-tauri/src/database/tests.rs
  Evidence snippets:
  - Persistence, schema, model, or migration file changed: src-tauri/src/database/dao/proxy.rs
  - Persistence, schema, model, or migration file changed: src-tauri/src/database/mod.rs
  - Persistence, schema, model, or migration file changed: src-tauri/src/database/schema.rs
  - Persistence, schema, model, or migration file changed: src-tauri/src/database/tests.rs
  Explanation: The patch changes a likely persistence, schema, model, or migration file. If no corresponding test file changed, data behavior may have changed without regression coverage.
  Suggested fix: Review the data model impact, verify migration behavior, and add tests around persistence compatibility.
  Diff hunk context:
  ```diff
  diff -- src-tauri/src/database/dao/proxy.rs
  @@ -224,7 +224,7 @@ impl Database {
                   "SELECT app_type, enabled, auto_failover_enabled,
                           max_retries, streaming_first_byte_timeout, streaming_idle_timeout, non_streaming_timeout,
                           circuit_failure_threshold, circuit_success_threshold, circuit_timeout_seconds,
  -                        circuit_error_rate_threshold, circuit_min_requests
  +                        circuit_error_rate_threshold, circuit_min_requests, filter_unsupported_response_tools
                    FROM proxy_config WHERE app_type = ?1",
                   [app_type],
                   |row| {
  diff -- src-tauri/src/database/dao/proxy.rs
  @@ -241,6 +241,7 @@ impl Database {
                           circuit_timeout_seconds: row.get::<_, i32>(9)? as u32,
                           circuit_error_rate_threshold: row.get(10)?,
                           circuit_min_requests: row.get::<_, i32>(11)? as u32,
  +                        filter_unsupported_response_tools: row.get::<_, i32>(12)? != 0,
                       })
                   },
               )
  diff -- src-tauri/src/database/dao/proxy.rs
  @@ -265,6 +266,7 @@ impl Database {
                       circuit_timeout_seconds: 60,
                       circuit_error_rate_threshold: 0.6,
                       circuit_min_requests: 10,
  +                    filter_unsupported_response_tools: true,
                   })
               }
               Err(e) => Err(AppError::Database(e.to_string())),
  diff -- src-tauri/src/database/dao/proxy.rs
  @@ -291,6 +293,7 @@ impl Database {
                   circuit_timeout_seconds = ?10,
                   circuit_error_rate_threshold = ?11,
                   circuit_min_requests = ?12,
  +                filter_unsupported_response_tools = ?13,
                   updated_at = datetime('now')
                WHERE app_type = ?1",
               rusqlite::params![
  diff -- src-tauri/src/database/dao/proxy.rs
  @@ -306,6 +309,11 @@ impl Database {
                   config.circuit_timeout_seconds as i32,
  ```
  ... (truncated, see patch.diff for full context)
- MEDIUM: Patch touches a broad file surface
  UID: fnd_1f8d591373be
  Kind: broad_file_surface
  Confidence: HIGH
  Evidence: STATIC
  Files: pnpm-workspace.yaml, src-tauri/src/database/dao/proxy.rs, src-tauri/src/database/mod.rs, src-tauri/src/database/schema.rs, src-tauri/src/database/tests.rs, src-tauri/src/proxy/body_filter.rs, src-tauri/src/proxy/forwarder.rs, src-tauri/src/proxy/handler_context.rs, src-tauri/src/proxy/server.rs, src-tauri/src/proxy/types.rs, src/components/proxy/AutoFailoverConfigPanel.tsx, src/components/proxy/ProxyPanel.tsx, src/i18n/locales/en.json, src/i18n/locales/ja.json, src/i18n/locales/zh-TW.json, src/i18n/locales/zh.json, src/types/proxy.ts, src-tauri/src/proxy/handlers.rs, src-tauri/src/proxy/providers/streaming_codex_chat.rs, src-tauri/src/proxy/providers/transform_codex_chat.rs, src-tauri/src/proxy/response_processor.rs, src-tauri/tauri.conf.json
  Evidence snippets:
  - 22 files changed
  Explanation: The patch changes more than 10 files. Broad patches are harder to review and more likely to contain unrelated changes.
  Suggested fix: Split unrelated changes, reduce the patch scope, or provide a clear review map for the touched areas.
  Diff hunk context:
  ```diff
  diff -- pnpm-workspace.yaml
  @@ -1,4 +1,8 @@
   packages: []
   
  +allowBuilds:
  +  esbuild: true
  +  msw: true
  +
   onlyBuiltDependencies:
     - '@tailwindcss/oxide'
  diff -- src-tauri/src/database/dao/proxy.rs
  @@ -224,7 +224,7 @@ impl Database {
                   "SELECT app_type, enabled, auto_failover_enabled,
                           max_retries, streaming_first_byte_timeout, streaming_idle_timeout, non_streaming_timeout,
                           circuit_failure_threshold, circuit_success_threshold, circuit_timeout_seconds,
  -                        circuit_error_rate_threshold, circuit_min_requests
  +                        circuit_error_rate_threshold, circuit_min_requests, filter_unsupported_response_tools
                    FROM proxy_config WHERE app_type = ?1",
                   [app_type],
                   |row| {
  diff -- src-tauri/src/database/dao/proxy.rs
  @@ -241,6 +241,7 @@ impl Database {
                           circuit_timeout_seconds: row.get::<_, i32>(9)? as u32,
                           circuit_error_rate_threshold: row.get(10)?,
                           circuit_min_requests: row.get::<_, i32>(11)? as u32,
  +                        filter_unsupported_response_tools: row.get::<_, i32>(12)? != 0,
                       })
                   },
               )
  diff -- src-tauri/src/database/dao/proxy.rs
  @@ -265,6 +266,7 @@ impl Database {
                       circuit_timeout_seconds: 60,
                       circuit_error_rate_threshold: 0.6,
                       circuit_min_requests: 10,
  +                    filter_unsupported_response_tools: true,
                   })
               }
               Err(e) => Err(AppError::Database(e.to_string())),
  diff -- src-tauri/src/database/dao/proxy.rs
  @@ -291,6 +293,7 @@ impl Database {
  ```
  ... (truncated, see patch.diff for full context)
- ADVISORY: User-facing copy or UI surface changed
  UID: fnd_2f6bf3bbbda7
  Kind: ui_copy_changed
  Confidence: LOW
  Evidence: STATIC
  Files: src/components/proxy/AutoFailoverConfigPanel.tsx, src/components/proxy/ProxyPanel.tsx
  Evidence snippets:
  - Likely user-facing, documentation, or UI file changed: src/components/proxy/AutoFailoverConfigPanel.tsx
  - Likely user-facing, documentation, or UI file changed: src/components/proxy/ProxyPanel.tsx
  Explanation: The patch touches files that often affect user-facing copy, documentation, or UI. This is not automatically a defect, but it deserves product review when relevant.
  Suggested fix: Review the changed UI or copy for accuracy, tone, and unintended product behavior.
  Diff hunk context:
  ```diff
  diff -- src/components/proxy/AutoFailoverConfigPanel.tsx
  @@ -172,6 +172,7 @@ export function AutoFailoverConfigPanel({
           circuitTimeoutSeconds: raw.circuitTimeoutSeconds,
           circuitErrorRateThreshold: raw.circuitErrorRateThreshold / 100,
           circuitMinRequests: raw.circuitMinRequests,
  +        filterUnsupportedResponseTools: config.filterUnsupportedResponseTools,
         });
         toast.success(
           t("proxy.autoFailover.configSaved", "自动故障转移配置已保存"),
  diff -- src/components/proxy/ProxyPanel.tsx
  @@ -25,6 +25,8 @@ import {
     useSetProxyTakeoverForApp,
     useGlobalProxyConfig,
     useUpdateGlobalProxyConfig,
  +  useAppProxyConfig,
  +  useUpdateAppProxyConfig,
   } from "@/lib/query/proxy";
   import type { ProxyStatus } from "@/types/proxy";
   import { useTranslation } from "react-i18next";
  diff -- src/components/proxy/ProxyPanel.tsx
  @@ -53,6 +55,8 @@ export function ProxyPanel({
     // 获取全局代理配置
     const { data: globalConfig } = useGlobalProxyConfig();
     const updateGlobalConfig = useUpdateGlobalProxyConfig();
  +  const { data: codexProxyConfig } = useAppProxyConfig("codex");
  +  const updateAppProxyConfig = useUpdateAppProxyConfig();
   
     // 监听地址/端口的本地状态（端口用字符串以支持完全清空）
     const [listenAddress, setListenAddress] = useState("127.0.0.1");
  diff -- src/components/proxy/ProxyPanel.tsx
  @@ -116,6 +120,32 @@ export function ProxyPanel({
       }
     };
   
  +  const handleCodexToolFilterChange = async (enabled: boolean) => {
  +    if (!codexProxyConfig) return;
  +    try {
  +      await updateAppProxyConfig.mutateAsync({
  +        ...codexProxyConfig,
  +        filterUnsupportedResponseTools: enabled,
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
