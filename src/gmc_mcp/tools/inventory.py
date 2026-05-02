from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def _price_obj(amount_micros: int | None, currency: str | None) -> dict[str, str] | None:
    if amount_micros is None or not currency:
        return None
    return {"amountMicros": str(amount_micros), "currencyCode": currency}


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    @mcp.tool()
    def gmc_update_regional_inventory(
        product_id: str,
        region: str,
        price_amount_micros: int | None = None,
        price_currency: str | None = None,
        sale_price_amount_micros: int | None = None,
        sale_price_currency: str | None = None,
        availability: str | None = None,
    ) -> dict[str, Any]:
        """Insert or update regional inventory for a product (Merchant API v1).

        product_id: full product ID (channel~lang~feedLabel~offerId).
        region: region code matching a configured region in the account.
        availability: 'IN_STOCK' | 'OUT_OF_STOCK' | 'PREORDER' | 'BACKORDER'
            (v1 expects ENUM in upper-case; v1beta lowercase strings are no longer accepted).

        Prices use the micros format: $19.99 → price_amount_micros=19990000, currency='USD'.

        Note: in v1 all attributes are nested under `regionalInventoryAttributes`.
        `customAttributes` was removed. This function builds the v1 shape automatically.
        """
        attrs: dict[str, Any] = {}
        price = _price_obj(price_amount_micros, price_currency)
        if price:
            attrs["price"] = price
        sale = _price_obj(sale_price_amount_micros, sale_price_currency)
        if sale:
            attrs["salePrice"] = sale
        if availability:
            attrs["availability"] = availability.upper()

        body: dict[str, Any] = {"region": region}
        if attrs:
            body["regionalInventoryAttributes"] = attrs

        return client.request(
            "POST",
            f"inventories/v1/{acct}/products/{product_id}/regionalInventories:insert",
            json_body=body,
            op="update_regional_inventory",
        )

    @mcp.tool()
    def gmc_update_local_inventory(
        product_id: str,
        store_code: str,
        price_amount_micros: int | None = None,
        price_currency: str | None = None,
        sale_price_amount_micros: int | None = None,
        sale_price_currency: str | None = None,
        availability: str | None = None,
        quantity: int | None = None,
        pickup_method: str | None = None,
        pickup_sla: str | None = None,
        instore_product_location: str | None = None,
    ) -> dict[str, Any]:
        """Insert or update local (in-store) inventory for a product (Merchant API v1).

        store_code: must match a store registered via Business Profile / store codes.
        availability: 'IN_STOCK' | 'OUT_OF_STOCK' | 'LIMITED_AVAILABILITY' | 'ON_DISPLAY_TO_ORDER' (enum).
        pickup_method: 'BUY' | 'RESERVE' | 'SHIP_TO_STORE' | 'NOT_SUPPORTED'.
        pickup_sla: 'SAME_DAY' | 'NEXT_DAY' | 'MULTI_DAY' etc.

        Note: in v1 all attributes are nested under `localInventoryAttributes`.
        """
        attrs: dict[str, Any] = {}
        price = _price_obj(price_amount_micros, price_currency)
        if price:
            attrs["price"] = price
        sale = _price_obj(sale_price_amount_micros, sale_price_currency)
        if sale:
            attrs["salePrice"] = sale
        if availability:
            attrs["availability"] = availability.upper()
        if quantity is not None:
            attrs["quantity"] = str(quantity)
        if pickup_method:
            attrs["pickupMethod"] = pickup_method.upper()
        if pickup_sla:
            attrs["pickupSla"] = pickup_sla.upper()
        if instore_product_location:
            attrs["instoreProductLocation"] = instore_product_location

        body: dict[str, Any] = {"storeCode": store_code}
        if attrs:
            body["localInventoryAttributes"] = attrs

        return client.request(
            "POST",
            f"inventories/v1/{acct}/products/{product_id}/localInventories:insert",
            json_body=body,
            op="update_local_inventory",
        )

    @mcp.tool()
    def gmc_list_regional_inventories(
        product_id: str, max_pages: int = 5
    ) -> dict[str, Any]:
        """List regional inventories for a product."""
        items = list(
            client.paginate(
                "GET",
                f"inventories/v1/{acct}/products/{product_id}/regionalInventories",
                items_key="regionalInventories",
                max_pages=max_pages,
            )
        )
        return {"product_id": product_id, "count": len(items), "regional_inventories": items}

    @mcp.tool()
    def gmc_list_local_inventories(
        product_id: str, max_pages: int = 5
    ) -> dict[str, Any]:
        """List local inventories for a product."""
        items = list(
            client.paginate(
                "GET",
                f"inventories/v1/{acct}/products/{product_id}/localInventories",
                items_key="localInventories",
                max_pages=max_pages,
            )
        )
        return {"product_id": product_id, "count": len(items), "local_inventories": items}
