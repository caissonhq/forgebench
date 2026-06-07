from __future__ import annotations


def format_thank_you_response(
    *,
    name: str = "",
    issue_summary: str = "",
    tracking_ref: str = "",
) -> str:
    who = name.strip() or "there"
    summary = issue_summary.strip() or "your ForgeBench feedback"
    ref = tracking_ref.strip() or "ROADMAP.md user-requested improvements"
    return "\n".join(
        [
            f"Hi {who},",
            "",
            f"Thank you for {summary} — it directly shapes our post-launch priorities.",
            "",
            "What we did:",
            "  • Triaged and logged your report locally (or via import)",
            f"  • Added to our public tracking: {ref}",
            "  • If calibration-related: golden case candidate via `forgebench feedback promote`",
            "",
            "What to expect:",
            "  • Critical/High items: target next patch or weekly digest",
            "  • You'll see updates in CHANGELOG.md and forgebench.dev/docs/how-we-iterate",
            "",
            "Help us iterate faster:",
            "  forgebench feedback FINDING_UID --status dismissed --kind <kind> --triage high --note \"context\"",
            "  forgebench feedback export --out forgebench-output/shared-feedback.json",
            "",
            "— The ForgeBench team",
        ]
    )