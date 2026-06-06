from __future__ import annotations

from dataclasses import dataclass

from forgebench.licensing.store import LicenseRecord, load_license


@dataclass(frozen=True)
class OnboardingStep:
    label: str
    command: str
    completed: bool = False


def build_paid_customer_checklist(*, record: LicenseRecord | None = None) -> list[OnboardingStep]:
    license_record = record or load_license()
    tier = license_record.tier.name.lower() if license_record.valid else "pending"
    return [
        OnboardingStep("License activated", "forgebench license activate FB-TEAM-...", completed=license_record.valid),
        OnboardingStep("Team kit initialized", "forgebench team init"),
        OnboardingStep("Org policy configured", "forgebench init --enterprise"),
        OnboardingStep("CI workflow wired", "forgebench review-pr PR_URL --checkout-pr --run-checks"),
        OnboardingStep("Usage dashboard exported", "forgebench portal --out forgebench-output/portal"),
        OnboardingStep("Customer success report", "forgebench license report --out forgebench-output/license-report.json"),
        OnboardingStep("Share feedback", "forgebench feedback --share"),
    ] + (
        [OnboardingStep("Policy service (Enterprise)", "forgebench policy serve")]
        if tier == "enterprise"
        else []
    )


def format_paid_customer_checklist(steps: list[OnboardingStep] | None = None) -> str:
    items = steps or build_paid_customer_checklist()
    lines = ["Paid customer success checklist:"]
    for step in items:
        mark = "x" if step.completed else " "
        lines.append(f"  [{mark}] {step.label}")
        if not step.completed:
            lines.append(f"      → {step.command}")
    return "\n".join(lines)


def format_welcome_sequence(*, organization: str = "", tier: str = "team") -> str:
    org = organization or "your team"
    return "\n".join(
        [
            f"Welcome to ForgeBench {tier.title()} — {org}",
            "",
            "Thank you for choosing ForgeBench. Your premium merge-risk workflow starts here.",
            "",
            "Day 0 — Activate",
            "  forgebench license activate <KEY>",
            "  forgebench license status",
            "",
            "Day 1 — Team setup",
            "  forgebench team init",
            "  forgebench presets install python  # or your stack",
            "",
            "Day 2 — CI + policy",
            "  forgebench init --enterprise",
            "  forgebench policy test --tests examples/policy_tests",
            "",
            "Ongoing",
            "  forgebench portal              # license, usage, quotas",
            "  forgebench license report      # customer success bundle",
            "  hello@forgebench.dev           # priority support",
            "",
            "ForgeBench does not prove code is safe.",
        ]
    )


def design_partner_conversion_flow() -> str:
    return "\n".join(
        [
            "Design Partner → Paying Customer conversion",
            "",
            "1. Pilot complete — review posture metrics + false-positive rate",
            "2. Present Team ROI summary (`forgebench license report`)",
            "3. Offer EA pricing lock-in: forgebench subscribe team --seats N",
            "4. Deliver license keys + `format_welcome_sequence` onboarding email",
            "5. Move CRM stage: design_partner → paid (`forgebench crm update`)",
            "6. Schedule 30-day check-in; capture success story (`feedback --share`)",
        ]
    )