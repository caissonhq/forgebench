# Feedback → Golden Case Promotion Checklist

Use when `forgebench feedback promote` generates draft candidates.

## 1. Promote from feedback

```bash
forgebench feedback fnd_abc123 --status dismissed --kind ui_copy_changed --outcome-label false_positive --note "docs-only"
forgebench feedback promote --uid fnd_abc123 --out forgebench-output/golden-case-candidates
```

## 2. Human review gate

- [ ] Add anonymized `patch.diff` (rename from `.PLACEHOLDER`)
- [ ] Add `task.md` with original agent prompt
- [ ] Verify `expected.json` posture and finding IDs
- [ ] Run calibration: `forgebench calibrate --cases forgebench-output/golden-case-candidates/<slug>`

## 3. Ship

- [ ] Move approved case to `examples/golden_cases/<slug>/`
- [ ] Open golden case proposal issue
- [ ] Mark feedback resolved: `--resolved` on next export cycle

## 4. Communicate

- [ ] Add CHANGELOG entry via weekly review What's New draft
- [ ] Send thank-you: `forgebench feedback thank --name "..." --summary "false positive on docs"`