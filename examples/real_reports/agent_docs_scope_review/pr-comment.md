## ForgeBench Merge Risk Report

Posture: REVIEW

Summary:
Review before merge. Multiple static signals indicate risk even though ForgeBench did not find a deterministic blocker. Deterministic checks were not run.

High-confidence issues:
- None.

Configuration:
- Generic mode: no forgebench.yml found. Add guardrails with `forgebench init` to reduce noise.

Deterministic checks:
- Not run.

Guardrails:
- No guardrail hits.

Heuristic review lenses:
- Scope Auditor: Patch changes files outside the apparent task scope
- Test Skeptic: Changed implementation files need coverage review
- Contract Keeper: no additional concern
- Product / Guardrail Reviewer: no additional concern
- Test Skeptic v2: no additional concern
- Regression Hunter: no additional concern

LLM review:
- Not run.

Suggested next action:
Review the listed risks before merge. If the patch was agent-generated, use the repair prompt locally.

Artifacts:
- Full report generated locally
- Repair prompt generated locally

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.
