## ForgeBench Merge Risk Report

Posture: BLOCK

Summary:
Do not merge yet. The patch changes likely persistence or schema behavior without corresponding test coverage. Deterministic checks were not run.

High-confidence issues:
- Persistence or schema behavior may have changed — HIGH/HIGH
- High-risk project area changed — HIGH/HIGH
- Patch touches protected product or architecture behavior — MEDIUM/HIGH

Deterministic checks:
- Not run.

Guardrails:
- 1 guardrail hit(s).

Heuristic review lenses:
- Scope Auditor: no additional concern
- Test Skeptic: no additional concern
- Contract Keeper: no additional concern
- Product / Guardrail Reviewer: Patch touches protected product or architecture behavior
- Test Skeptic v2: no additional concern
- Regression Hunter: no additional concern

LLM review:
- Not run.

Suggested next action:
Do not merge yet. Address the blocking findings, regenerate the diff if needed, and rerun ForgeBench.

Artifacts:
- Full report generated locally
- Repair prompt generated locally

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.
