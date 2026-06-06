from __future__ import annotations

import os


def stripe_secret_key() -> str:
    return os.environ.get("STRIPE_SECRET_KEY", "").strip()


def stripe_webhook_secret() -> str:
    return os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip()


def stripe_price_team_monthly() -> str:
    return os.environ.get("STRIPE_PRICE_TEAM_MONTHLY", "price_team_monthly_ea").strip()


def stripe_price_enterprise_annual() -> str:
    return os.environ.get("STRIPE_PRICE_ENTERPRISE_ANNUAL", "price_enterprise_annual").strip()


def checkout_success_url() -> str:
    return os.environ.get("FORGEBENCH_CHECKOUT_SUCCESS_URL", "https://forgebench.dev/docs/pricing/#activate").strip()


def checkout_cancel_url() -> str:
    return os.environ.get("FORGEBENCH_CHECKOUT_CANCEL_URL", "https://forgebench.dev/docs/pricing/").strip()


def hosted_portal_url() -> str:
    return os.environ.get("FORGEBENCH_CUSTOMER_PORTAL_URL", "https://forgebench.dev/portal").strip()


def sales_email() -> str:
    return os.environ.get("FORGEBENCH_SALES_EMAIL", "hello@forgebench.dev").strip()