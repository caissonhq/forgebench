# Design Partner & Early Adopter Program

Help shape ForgeBench while your team ships faster with AI-assisted development.

## Who it's for

- Engineering teams running Cursor, Codex, Claude Code, or Copilot on production repos
- Platform / developer-experience leads evaluating merge-risk tooling
- Security-minded teams that want policy gates without blocking agent velocity

## Benefits (v1.0 launch)

| Benefit | Details |
|---------|---------|
| **Priority support** | Direct Slack/email channel during 4–6 week pilot |
| **Custom presets** | We help author `forgebench.yml` + policy tests for your stack |
| **License discount** | 50% off Team tier for pilot duration (up to 25 seats) |
| **Roadmap input** | Your workflows influence post-v1 priorities |
| **White-glove onboarding** | Guided `forgebench team init`, CI wiring, guardrail tuning |
| **Benchmark cohort** | Optional anonymized merge-risk benchmark inclusion |
| **Launch recognition** | Logo/testimonial on forgebench.dev (optional) |

## Commitment

- 4–6 week pilot on one repo or squad
- Weekly 30-minute feedback sync (or async via GitHub Discussions)
- Share anonymized posture distributions and false-positive examples

## Apply

1. Run `forgebench quickstart` locally
2. Guided onboarding: `forgebench partner onboard`
3. Open a GitHub Discussion: [Design Partner intake](https://github.com/caissonhq/forgebench/discussions/new?category=general) (use the **Design Partner** template)
4. Or email **hello@forgebench.dev** with team size, stack, and agent tooling

## Onboarding kit

```bash
forgebench partner onboard --organization "Your Team" --out forgebench-output/partner-kit
forgebench partner presets install agent-pr-strict
forgebench feedback --paid
```

Full kit: [ONBOARDING_KIT.md](https://github.com/caissonhq/forgebench/blob/main/docs/design-partner/ONBOARDING_KIT.md) · [Why join one-pager](https://github.com/caissonhq/forgebench/blob/main/docs/design-partner/WHY_JOIN_ONE_PAGER.md)

## What we measure together

- Time-to-first-review
- False-positive rate on dismissed findings (`forgebench feedback`)
- CI pass rate with `--run-checks`
- Engineer NPS after first merge with ForgeBench

See also [Early Access](early-access.md) and [Contribution Program on GitHub](https://github.com/caissonhq/forgebench/blob/main/docs/contribution-program.md).