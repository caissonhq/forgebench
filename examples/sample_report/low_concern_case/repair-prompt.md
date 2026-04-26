You are repairing an AI-generated code change after ForgeBench review.

Original task:
Synthetic sample task:

Clarify the README quickstart wording.

This is a synthetic ForgeBench sample case designed to demonstrate output shape.

ForgeBench merge posture:
LOW_CONCERN

No required repair was identified. Use this only to tighten tests or advisory concerns.

Deterministic check failures:
- Deterministic checks were not run.

Static and guardrail findings:
- No static or guardrail findings.

Heuristic review lens findings:
- No heuristic review lens findings.

LLM reviewer notes:
- LLM review was not run.

Suppressed or policy-calibrated findings:
- ui_copy_changed was suppressed by policy.suppress_findings[0].paths: Docs-only copy changes are advisory in this sample. Do not repair this unless the policy is wrong.
- Merge posture was capped at LOW_CONCERN: Docs-only changes should not escalate unless a blocker is present.

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
- Keep the CLI-first alpha framing clear
