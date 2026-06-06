# Customer Success Onboarding Playbook

## Week 0 — Kickoff

- [ ] Send Team license keys (`forgebench license activate`)
- [ ] Share [docs/forgebench-onboarding.md](../../site-docs/onboarding/checklist.md) checklist
- [ ] Schedule 30-min demo: `doctor` → `demo` → `review-pr`
- [ ] Identify pilot repo and CODEOWNERS for `forgebench.yml`

## Week 1 — Technical setup

- [ ] Run `forgebench init --enterprise --yes` on pilot repo
- [ ] Validate guardrails: `forgebench validate --strict`
- [ ] Add `.github/workflows/forgebench.yml` to default branch
- [ ] Install VS Code or JetBrains extension on pilot squad
- [ ] Enable product analytics (opt-in): `forgebench analytics enable`

## Week 2 — Policy calibration

- [ ] Run `forgebench policy test --tests examples/policy_tests`
- [ ] Dogfood 3 real agent PRs; log feedback locally
- [ ] Tune `protected_behavior` and `risk_files`
- [ ] Export policy dashboard for stakeholder review

## Week 3 — CI gate

- [ ] Enable `--checkout-pr --run-checks` in CI with trusted `.github/forgebench.yml`
- [ ] Optional: GitHub Check Run annotations
- [ ] Document repair loop for agents

## Week 4 — Expand

- [ ] Roll out to additional repos via org policy (`extends`)
- [ ] Export `forgebench license report` for health review
- [ ] Quarterly policy regression review

## Success metrics

| Metric | Target |
|--------|--------|
| Pilot engineers with `doctor` passing | 100% |
| Repos with `forgebench.yml` | pilot + 2 |
| Agent PRs with posture report | >80% |
| Policy test CI green | 100% |