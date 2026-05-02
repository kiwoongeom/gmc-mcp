"""Bulk operations that don't fit cleanly into a single sub-API tool."""

from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    @mcp.tool()
    def gmc_bulk_update_regional_prices(
        updates: list[dict[str, Any]],
        confirm: str = "",
        stop_on_error: bool = False,
    ) -> dict[str, Any]:
        """Bulk-update regional inventory prices.

        confirm: must be exactly 'APPLY' to execute (case-sensitive).
        updates: list of dicts. Required keys per item:
            {
              "product_id": "online~en~US~SKU1",   # full product ID
              "region": "US",
              "price_amount_micros": 19990000,
              "price_currency": "USD",
              "availability": "IN_STOCK"            # optional
            }
        stop_on_error: if True, halt on first failure. If False, continue and report.
        """
        if confirm != "APPLY":
            return {
                "error": "Refused: pass confirm='APPLY' (case-sensitive) to execute.",
                "would_update_count": len(updates),
            }

        applied: list[str] = []
        failed: list[dict[str, Any]] = []
        for u in updates:
            pid = u.get("product_id")
            region = u.get("region")
            if not pid or not region:
                failed.append({"item": u, "reason": "missing product_id or region"})
                if stop_on_error:
                    break
                continue

            attrs: dict[str, Any] = {}
            if u.get("price_amount_micros") is not None and u.get("price_currency"):
                attrs["price"] = {
                    "amountMicros": str(u["price_amount_micros"]),
                    "currencyCode": u["price_currency"],
                }
            if u.get("sale_price_amount_micros") is not None and u.get("sale_price_currency"):
                attrs["salePrice"] = {
                    "amountMicros": str(u["sale_price_amount_micros"]),
                    "currencyCode": u["sale_price_currency"],
                }
            if u.get("availability"):
                attrs["availability"] = u["availability"].upper()

            body: dict[str, Any] = {"region": region}
            if attrs:
                body["regionalInventoryAttributes"] = attrs

            try:
                client.request(
                    "POST",
                    f"inventories/v1/{acct}/products/{pid}/regionalInventories:insert",
                    json_body=body,
                    op="bulk_update_regional_price",
                )
                applied.append(f"{pid}@{region}")
            except Exception as e:
                failed.append({"item": u, "reason": str(e)[:200]})
                if stop_on_error:
                    break

        return {
            "applied_count": len(applied),
            "failed_count": len(failed),
            "first_failed": failed[:10],
        }

    @mcp.tool()
    def gmc_bulk_set_availability(
        product_ids: list[str],
        region: str,
        availability: str,
        confirm: str = "",
    ) -> dict[str, Any]:
        """Bulk-set availability ('IN_STOCK', 'OUT_OF_STOCK', etc.) for many products.

        confirm: must be exactly 'APPLY'.
        """
        if confirm != "APPLY":
            return {
                "error": "Refused: pass confirm='APPLY' (case-sensitive) to execute.",
                "would_update_count": len(product_ids),
            }
        applied: list[str] = []
        failed: list[dict[str, Any]] = []
        for pid in product_ids:
            try:
                client.request(
                    "POST",
                    f"inventories/v1/{acct}/products/{pid}/regionalInventories:insert",
                    json_body={
                        "region": region,
                        "regionalInventoryAttributes": {
                            "availability": availability.upper()
                        },
                    },
                    op="bulk_set_availability",
                )
                applied.append(pid)
            except Exception as e:
                failed.append({"product_id": pid, "reason": str(e)[:200]})
        return {
            "applied_count": len(applied),
            "failed_count": len(failed),
            "first_failed": failed[:10],
        }
