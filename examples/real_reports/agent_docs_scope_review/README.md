# Docs task with script drift (REVIEW)

- Source: anonymized real PR (Codex)
- Real open PR where documentation edits also touched validation scripts; Scope Auditor and Test Skeptic fired.

Reproduce locally:

```bash
forgebench review \
  --repo . \
  --diff examples/real_reports/agent_docs_scope_review/patch.diff \
  --task examples/real_reports/agent_docs_scope_review/task.md
```
