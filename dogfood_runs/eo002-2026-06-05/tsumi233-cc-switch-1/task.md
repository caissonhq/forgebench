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
