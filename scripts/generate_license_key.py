#!/usr/bin/env python3
"""Generate ForgeBench license keys for Team/Enterprise customers (internal)."""

from __future__ import annotations

import argparse

from forgebench.licensing.keys import generate_license_key


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a ForgeBench license key.")
    parser.add_argument("--tier", required=True, choices=["team", "enterprise"])
    parser.add_argument("--org", required=True, help="Customer organization name")
    parser.add_argument("--seats", type=int, default=10)
    parser.add_argument("--expires", required=False, help="Expiry date YYYY-MM-DD")
    args = parser.parse_args()
    key = generate_license_key(
        tier=args.tier,
        organization=args.org,
        seats=args.seats,
        expires_at=args.expires,
    )
    print(key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())