"""Bump prices on a list of SKUs by a percentage.

Reads a CSV of (offer_id, current_price_micros, currency) and writes regional
inventory updates. Pass --dry-run to log the plan without sending requests.

Usage:
    python examples/bulk_price_update.py inputs.csv --region US --bump 1.05 [--dry-run]

CSV format (header required):
    offer_id,current_price_micros,currency
    SKU1,19990000,USD
    SKU2,29990000,USD
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from gmc_mcp.audit import AuditLog
from gmc_mcp.auth import load_auth
from gmc_mcp.client import MerchantClient
from gmc_mcp.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--region", required=True, help="Region code (e.g. US)")
    parser.add_argument("--bump", type=float, required=True, help="Multiplier, e.g. 1.05 for +5%")
    parser.add_argument("--feed-label", default="US", help="Feed label, e.g. US, KR")
    parser.add_argument("--lang", default="en", help="Content language, e.g. en, ko")
    parser.add_argument("--channel", default="online")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    config = load_config()
    if args.dry_run:
        config.dry_run = True
    auth = load_auth(
        service_account_key=config.service_account_key,
        oauth_token=config.oauth_token,
    )

    updates_done = 0
    with MerchantClient(config, auth, AuditLog(config.audit_log)) as client:
        with args.csv.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                offer_id = row["offer_id"]
                current = int(row["current_price_micros"])
                currency = row["currency"]
                new_price = int(round(current * args.bump))
                product_id = (
                    f"{args.channel}~{args.lang}~{args.feed_label}~{offer_id}"
                )
                client.request(
                    "POST",
                    f"inventories/v1/{client.account_path()}/products/{product_id}/regionalInventories:insert",
                    json_body={
                        "region": args.region,
                        "price": {
                            "amountMicros": str(new_price),
                            "currencyCode": currency,
                        },
                    },
                    op="bulk_price_update",
                    before={"price_micros": current, "currency": currency},
                )
                updates_done += 1
                print(f"{offer_id}: {current} -> {new_price} {currency}")

    mode = "DRY-RUN" if config.dry_run else "APPLIED"
    print(f"\n{mode}: {updates_done} price updates")


if __name__ == "__main__":
    main()
