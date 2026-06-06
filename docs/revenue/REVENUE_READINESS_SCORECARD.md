# Revenue Readiness Scorecard — EO-017

Status key: ✅ Ready · 🟡 Needs configuration · ⬜ Manual

| Area | Item | Status | Notes |
|------|------|--------|-------|
| **Licensing** | Offline HMAC key validation | ✅ | `FB-TEAM-...` / `FB-ENTERPRISE-...` |
| | Online license server skeleton | ✅ | `forgebench billing-serve license` |
| | Seat enforcement | ✅ | Per license ID activation registry |
| | `license activate/status/verify/upgrade/report` | ✅ | CLI complete |
| **Stripe** | Checkout session creation | 🟡 | Set `STRIPE_SECRET_KEY` + price IDs |
| | Webhook handler | ✅ | `forgebench billing-serve stripe-webhook` |
| | Subscription + one-time modes | ✅ | Team subscription, Enterprise payment |
| | `forgebench subscribe` | ✅ | Opens checkout URL |
| **Portal** | Self-hosted customer dashboard | ✅ | `forgebench portal` |
| | Usage + quota visibility | ✅ | Quota report embedded |
| | Invoice placeholder | 🟡 | Stripe Customer Portal when live |
| **Gating** | Upgrade prompts on paid features | ✅ | `LicenseRequired` + `forgebench upgrade` |
| | Value messaging per feature | ✅ | `billing/upgrade.py` |
| **CRM** | Local pipeline tracking | ✅ | `forgebench crm` |
| | Linear sync (optional) | 🟡 | `LINEAR_API_KEY` + `LINEAR_TEAM_ID` |
| | Design Partner → paid flow | ✅ | `forgebench crm convert` |
| | Welcome sequence | ✅ | `forgebench crm welcome` |
| **Pricing** | `docs/pricing.md` finalized | ✅ | Team $29/dev/mo EA, Enterprise custom |
| | MkDocs pricing page | ✅ | `site-docs/pricing.md` |
| **First customer** | Onboarding playbook | ✅ | `docs/customer-onboarding-playbook.md` |
| | Paid success checklist | ✅ | `forgebench crm checklist` |

## Go-live checklist

1. Set production `FORGEBENCH_LICENSE_SECRET`
2. Configure Stripe products/prices and webhook endpoint
3. Smoke test: `forgebench subscribe team --open`
4. Deliver license key after `checkout.session.completed`
5. Run first customer through `forgebench crm welcome` + `portal`