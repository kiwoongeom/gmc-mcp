"""Local Feed Partnership (LFP) — for POS/inventory partners that push
in-store inventory & sales on behalf of merchants."""

from __future__ import annotations

import contextlib
from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    # LFP resources belong to the approved provider, not its target subaccount.
    acct = client.account_path(client.config.account_id)

    def store_id(store_code: str, target_account: str | None) -> str:
        if "~" in store_code:
            return store_code
        if not target_account or not target_account.isdigit():
            raise ValueError(
                "Pass store_code as {target_merchant_id}~{store_code}, "
                "or supply a numeric target_account; no store was changed."
            )
        return f"{target_account}~{store_code}"

    # ---- LFP stores ----

    @mcp.tool()
    def gmc_lfp_list_stores(target_account: str, max_pages: int = 5) -> dict[str, Any]:
        """List stores LFP-linked to a target merchant account."""
        items = list(
            client.paginate(
                "GET",
                f"lfp/v1/{acct}/lfpStores",
                params={"targetAccount": target_account},
                items_key="lfpStores",
                max_pages=max_pages,
            )
        )
        return {"count": len(items), "stores": items}

    @mcp.tool()
    def gmc_lfp_get_store(store_code: str, target_account: str | None = None) -> dict[str, Any]:
        """Get a provider's store using target_account plus store_code, or a combined target~store ID."""
        return client.request(
            "GET", f"lfp/v1/{acct}/lfpStores/{store_id(store_code, target_account)}"
        )

    @mcp.tool()
    def gmc_lfp_insert_store(store: dict[str, Any]) -> dict[str, Any]:
        """Create / upsert an LFP store. Body example:
        {
          "targetAccount": "1234567890",
          "storeCode": "store-1",
          "storeAddress": "123 Main St, City, ST 00000",
          "storeName": "Main Street Store",
          "phoneNumber": "+1-555-0100",
          "websiteUri": "https://store.com/locations/1"
        }
        """
        return client.request(
            "POST",
            f"lfp/v1/{acct}/lfpStores:insert",
            json_body=store,
            op="lfp_insert_store",
        )

    @mcp.tool()
    def gmc_lfp_delete_store(store_code: str, target_account: str | None = None) -> dict[str, Any]:
        """Delete a provider's store identified by target_account/store_code or a combined ID."""
        identifier = store_id(store_code, target_account)
        before = None
        with contextlib.suppress(Exception):
            before = client.request("GET", f"lfp/v1/{acct}/lfpStores/{identifier}")
        result = client.request(
            "DELETE",
            f"lfp/v1/{acct}/lfpStores/{identifier}",
            op="lfp_delete_store",
            before=before,
        )
        if result.get("_dry_run"):
            return result
        return {"deleted_store_code": store_code}

    # ---- LFP inventories ----

    @mcp.tool()
    def gmc_lfp_insert_inventory(inventory: dict[str, Any]) -> dict[str, Any]:
        """Push one local inventory record. Body example:
        {
          "targetAccount": "1234567890",
          "storeCode": "store-1",
          "offerId": "SKU1",
          "regionCode": "US",
          "contentLanguage": "en",
          "price": {"amountMicros": "19990000", "currencyCode": "USD"},
          "availability": "IN_STOCK",
          "quantity": "12"
        }
        """
        return client.request(
            "POST",
            f"lfp/v1/{acct}/lfpInventories:insert",
            json_body=inventory,
            op="lfp_insert_inventory",
        )

    # ---- LFP sales ----

    @mcp.tool()
    def gmc_lfp_insert_sale(sale: dict[str, Any]) -> dict[str, Any]:
        """Push one local sale event. Body example:
        {
          "targetAccount": "1234567890",
          "storeCode": "store-1",
          "offerId": "SKU1",
          "regionCode": "US",
          "contentLanguage": "en",
          "price": {"amountMicros": "19990000", "currencyCode": "USD"},
          "quantity": "1",
          "saleTime": "2026-04-30T19:30:00Z",
          "uid": "txn-abc123"
        }
        """
        return client.request(
            "POST",
            f"lfp/v1/{acct}/lfpSales:insert",
            json_body=sale,
            op="lfp_insert_sale",
        )

    # ---- LFP merchant states ----

    @mcp.tool()
    def gmc_lfp_get_merchant_state(target_account: str) -> dict[str, Any]:
        """Get the current LFP onboarding/sync state for a target merchant."""
        return client.request("GET", f"lfp/v1/{acct}/lfpMerchantStates/{target_account}")
