GitHub PR Review

PR:
https://github.com/getbourdon/bourdon/pull/113

Title:
[codex] separate Codex L5 publisher freshness

Body:
## Summary
- expose Codex L5 staleness as shared derived snapshot data instead of HTML-only state
- rename the dashboard blocker to 'Codex L5 publisher not recently run' so it does not imply the publisher code is broken
- split Codex L5 publisher and manifest cards, and include the publisher command in evidence drawers
- add regression coverage for snapshot staleness fields and dashboard copy

## Local automation
Created active Codex automation `codex-l5-publisher` to run the Codex L5 export every 24 hours and refresh the metrics dashboard afterward. This automation writes only `/Users/radman/agent-library/agents/codex.l5.yaml` plus metrics/report artifacts; it does not inspect `~/.codex/auth.json` or mutate Codex SQLite.

## Validation
- `./.venv/bin/ruff check scripts/codex_memory_metrics.py tests/test_codex_memory_metrics.py`
- `./.venv/bin/pytest -q -p no:cacheprovider tests/test_codex_memory_metrics.py` run 3x
- `./.venv/bin/pytest -q -p no:cacheprovider tests/test_cli.py tests/test_codex_adapter.py tests/test_codex_memory_metrics.py` -> 123 passed
- `./.venv/bin/pytest -q -p no:cacheprovider tests` -> 771 passed, 1 skipped
- live Codex L5 publish + dashboard refresh: latest snapshot now reports `codex_l5_stale: false`, `518` entities, `81` sessions

## Notes
The native-memory heartbeat remains read-only. Publication freshness is now handled by the separate publisher automation and reported as a distinct signal.

Author:
ryandavispro1-cmyk

Base:
main

Head:
codex/l5-publisher-freshness

Changed files:
2

Additions:
81

Deletions:
13

This task context was generated from GitHub PR metadata.
