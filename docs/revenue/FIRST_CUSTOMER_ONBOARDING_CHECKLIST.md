# First Customer Onboarding Checklist

Use this for the first paying Team or Enterprise customer.

## Pre-sale

- [ ] Design Partner pilot complete (`forgebench crm convert`)
- [ ] ROI summary exported (`forgebench license report`)
- [ ] Seats and tier confirmed
- [ ] Stripe checkout or invoice sent (`forgebench subscribe team --seats N`)

## Day 0 — Purchase → activation

- [ ] `checkout.session.completed` received (webhook or manual)
- [ ] CRM stage updated: `forgebench crm add "Customer Name" --stage paid`
- [ ] License key issued (`FB-TEAM-...` or `FB-ENTERPRISE-...`)
- [ ] Welcome email sent (`forgebench crm welcome --organization "Customer"`)

## Day 1 — Technical onboarding

- [ ] Customer runs `forgebench license activate <KEY>`
- [ ] `forgebench license status` shows valid tier + seats
- [ ] `forgebench team init` completed
- [ ] Preset installed for their stack

## Day 2 — Policy + CI

- [ ] `forgebench init --enterprise` (or team kit)
- [ ] Policy tests wired in CI
- [ ] First `review-pr` with `--run-checks` on a real PR

## Week 1 — Success metrics

- [ ] `forgebench portal` exported — customer sees usage/quota
- [ ] False-positive feedback captured (`forgebench feedback`)
- [ ] 30-minute check-in scheduled
- [ ] Optional: success story (`forgebench feedback --share`)

## Enterprise add-ons

- [ ] `forgebench policy serve` (if Enterprise)
- [ ] `forgebench github-app serve` configured
- [ ] SOC2 pack shared (`docs/security/`)

Support: **hello@forgebench.dev**