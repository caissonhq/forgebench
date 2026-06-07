# Design Partner Onboarding Kit

White-glove onboarding for ForgeBench Design Partners. Local-first — no hosted code review required.

## Quick start

```bash
forgebench partner onboard --organization "Acme Engineering" --email "lead@acme.com" --out forgebench-output/partner-kit
forgebench license activate <KEY>
forgebench partner presets install agent-pr-strict
forgebench team init --yes --org-name "Acme Engineering"
```

## Kit contents

| Artifact | Command / path |
|----------|----------------|
| Welcome email | `forgebench partner onboard --out …` → `welcome-email.txt` |
| License key | `examples/design-partner/pilot-license-keys.json` or generated key |
| Private presets | `forgebench partner presets list` |
| Priority support | `forgebench partner support` |
| Feedback channel | GitHub Discussions · label `design-partner` |
| Weekly digest | `forgebench feedback digest --days 7` |

## Welcome email template

Run `forgebench partner onboard --organization "Your Team"` to print a personalized welcome email with license activation steps.

## License delivery

1. Pick an unassigned key: `forgebench partner keys`
2. Deliver via secure channel (1Password, email encryption)
3. Update CRM: `forgebench crm add "Your Team" --stage design_partner --seats 15`
4. Mark key assigned in `pilot-license-keys.json`

## Private preset sharing

Design Partner presets live in `examples/design-partner/private-presets/`. They are not listed in the public presets gallery.

```bash
forgebench partner presets install agent-pr-strict
```

## Priority support process

```bash
forgebench partner support
```

- **P0** (CI blocked): <4h response
- **P1** (guardrail tuning): <1 business day
- **P2** (roadmap input): weekly digest

Contact: **hello@forgebench.dev** · subject `[Design Partner] <org>`

## Conversion to paid

```bash
forgebench crm convert
forgebench subscribe team --seats N
forgebench crm welcome --organization "Your Team"
```

See [WHY_JOIN_ONE_PAGER.md](WHY_JOIN_ONE_PAGER.md) and [../customer-onboarding-playbook.md](../customer-onboarding-playbook.md).