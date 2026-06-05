# Agent security cleanup (LOW_CONCERN)

- Source: anonymized real PR (Codex)
- Real merged PR that removed a hardcoded API key pattern and added env-var tests.

Reproduce locally:

```bash
forgebench review \
  --repo . \
  --diff examples/real_reports/agent_env_secret_cleanup_low_concern/patch.diff \
  --task examples/real_reports/agent_env_secret_cleanup_low_concern/task.md
```
