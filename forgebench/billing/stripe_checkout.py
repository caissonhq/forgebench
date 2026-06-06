from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from forgebench.billing.config import (
    checkout_cancel_url,
    checkout_success_url,
    hosted_portal_url,
    sales_email,
    stripe_price_enterprise_annual,
    stripe_price_team_monthly,
    stripe_secret_key,
)
from forgebench.licensing.tiers import LicenseTier, parse_tier, tier_label


class StripeCheckoutError(RuntimeError):
    pass


@dataclass(frozen=True)
class CheckoutSession:
    tier: str
    seats: int
    mode: str
    url: str
    session_id: str | None
    message: str


def build_checkout_url(*, tier: str, seats: int = 5, customer_email: str = "") -> CheckoutSession:
    tier_enum = parse_tier(tier)
    if tier_enum == LicenseTier.FREE:
        raise StripeCheckoutError("Free tier does not require checkout.")
    secret = stripe_secret_key()
    if secret:
        return _create_stripe_session(tier=tier_label(tier_enum), seats=seats, customer_email=customer_email)
    return _fallback_checkout_url(tier=tier_label(tier_enum), seats=seats)


def _create_stripe_session(*, tier: str, seats: int, customer_email: str) -> CheckoutSession:
    price = stripe_price_team_monthly() if tier == "team" else stripe_price_enterprise_annual()
    mode = "subscription" if tier == "team" else "payment"
    data: dict[str, Any] = {
        "mode": mode,
        "success_url": checkout_success_url(),
        "cancel_url": checkout_cancel_url(),
        "client_reference_id": f"forgebench-{tier}-{seats}",
        "metadata[tier]": tier,
        "metadata[seats]": str(seats),
        "line_items[0][price]": price,
        "line_items[0][quantity]": str(seats if tier == "team" else 1),
    }
    if customer_email:
        data["customer_email"] = customer_email
    payload = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(
        "https://api.stripe.com/v1/checkout/sessions",
        data=payload,
        headers={
            "Authorization": f"Bearer {stripe_secret_key()}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise StripeCheckoutError(f"Stripe checkout failed ({exc.code}): {detail}") from exc
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        raise StripeCheckoutError(f"Stripe checkout unavailable: {exc}") from exc
    url = str(body.get("url") or "")
    if not url:
        raise StripeCheckoutError("Stripe checkout session missing URL.")
    return CheckoutSession(
        tier=tier,
        seats=seats,
        mode=mode,
        url=url,
        session_id=str(body.get("id") or "") or None,
        message="Stripe checkout session created.",
    )


def _fallback_checkout_url(*, tier: str, seats: int) -> CheckoutSession:
    base = hosted_portal_url().rstrip("/")
    query = urllib.parse.urlencode({"tier": tier, "seats": str(seats), "source": "cli"})
    url = f"{base}/subscribe?{query}"
    return CheckoutSession(
        tier=tier,
        seats=seats,
        mode="subscription" if tier == "team" else "payment",
        url=url,
        session_id=None,
        message=(
            f"Stripe not configured. Contact {sales_email()} or visit {url} "
            f"(set STRIPE_SECRET_KEY for live checkout)."
        ),
    )