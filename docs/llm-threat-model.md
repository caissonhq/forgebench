# ForgeBench LLM Threat Model

ForgeBench can run optional LLM-assisted review. No LLM calls happen by default.

ForgeBench does not prove code is safe. It highlights merge risk before AI-generated code reaches main.

## Threat Surface

### Prompt Injection From Task Text

The original task prompt may contain instructions that try to redirect the LLM reviewer. ForgeBench treats task text as evidence, not as trusted instructions.

### Prompt Injection From PR Body

GitHub PR title/body text can contain prompt injection attempts. PR metadata is included only as context for review and must not override ForgeBench instructions.

### Malicious Diff Content

Code comments, string literals, docs, fixtures, or generated files in a diff may contain instructions aimed at the LLM. Diff content is untrusted evidence.

### Command Provider Shell Risk

The command LLM provider runs a user-supplied local shell command. This is intentionally explicit and local, but it has the same trust requirements as running any shell command.

Do not point `--llm-command` at scripts supplied by an untrusted PR. Treat the command provider as trusted local code execution.

### Structured Output Attacks

An LLM may attempt finding-ID forgery, severity forgery, confidence forgery, or output extra fields that imply stronger authority than ForgeBench allows.

### Oversized Bundles

Large tasks, diffs, and reports can hide relevant details or dilute instructions. ForgeBench caps bundle sizes and marks truncation.

## Mitigations

- LLM review is opt-in with `--llm-review`.
- No real hosted LLM provider is configured by default.
- The command provider is local and user-controlled.
- JSON output is parsed strictly.
- LLM-assisted lens output is reduced to a narrow schema before findings are created.
- Severity and confidence are hard-capped in code.
- LLM findings cannot emit deterministic finding IDs as deterministic evidence.
- LLM findings cannot create `BLOCKER` findings.
- LLM findings cannot create `BLOCK` posture by themselves.
- LLM findings cannot downgrade posture.
- LLM review cannot override deterministic checks.
- LLM review cannot post PR comments.
- Bundle size caps are enforced for task text, diff excerpts, and lens-specific evidence.
- PR comments still require explicit `--post-comment`.
- Feedback remains local JSONL and is not uploaded.

## Test Skeptic v2

Test Skeptic v2 is the first LLM-assisted review lens. It runs only when deterministic triggers indicate a narrow weak-test scenario:

- source files changed
- test files changed
- added test lines exist
- added test lines lack common assertion tokens
- `--llm-review` is enabled
- a usable LLM provider is configured

The lens asks for a strict JSON verdict:

```json
{
  "verdict": "weak",
  "rationale": "short rationale",
  "evidence_lines": ["line from evidence"]
}
```

Only `verdict: "weak"` creates a finding. `adequate` and `uncertain` do not.

The LLM does not choose severity or confidence. ForgeBench caps Test Skeptic v2 findings at `MEDIUM` severity and `MEDIUM` confidence. These findings are advisory review tasks, not proof.

## Evidence Hierarchy

1. Deterministic checks
2. Static risk signals
3. Guardrails policy
4. Heuristic review lenses
5. Optional LLM review

Deterministic checks outrank LLM review. A failing build, test, or typecheck remains a blocker regardless of LLM output.
