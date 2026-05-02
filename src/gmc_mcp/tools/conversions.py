from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()
    base = f"conversions/v1/{acct}/conversionSources"

    @mcp.tool()
    def gmc_list_conversion_sources(
        include_archived: bool = False, max_pages: int = 5
    ) -> dict[str, Any]:
        """List conversion sources (Google Tag, Google Analytics, Merchant Center
        Destination)."""
        params: dict[str, Any] = {"showDeleted": include_archived}
        items = list(
            client.paginate(
                "GET",
                base,
                params=params,
                items_key="conversionSources",
                max_pages=max_pages,
            )
        )
        return {"count": len(items), "conversion_sources": items}

    @mcp.tool()
    def gmc_get_conversion_source(source_id: str) -> dict[str, Any]:
        return client.request("GET", f"{base}/{source_id}")

    @mcp.tool()
    def gmc_create_conversion_source(source: dict[str, Any]) -> dict[str, Any]:
        """Create a conversion source. Examples:

        Google Analytics 4:
            {"googleAnalyticsLink": {"propertyId": 123456789}}

        Merchant Center destination (free listings):
            {"merchantCenterDestination": {
                "destination": "FREE_LISTINGS",
                "currencyCode": "USD",
                "displayName": "MC Free Listings"
            }}
        """
        return client.request("POST", base, json_body=source, op="create_conversion_source")

    @mcp.tool()
    def gmc_update_conversion_source(
        source_id: str, source: dict[str, Any], update_mask: str | None = None
    ) -> dict[str, Any]:
        before = None
        try:
            before = client.request("GET", f"{base}/{source_id}")
        except Exception:
            pass
        params = {"updateMask": update_mask} if update_mask else None
        return client.request(
            "PATCH",
            f"{base}/{source_id}",
            params=params,
            json_body=source,
            op="update_conversion_source",
            before=before,
        )

    @mcp.tool()
    def gmc_delete_conversion_source(source_id: str) -> dict[str, Any]:
        """Soft-delete a conversion source (recoverable via undelete)."""
        before = None
        try:
            before = client.request("GET", f"{base}/{source_id}")
        except Exception:
            pass
        client.request(
            "DELETE", f"{base}/{source_id}", op="delete_conversion_source", before=before
        )
        return {"deleted": source_id}

    @mcp.tool()
    def gmc_undelete_conversion_source(source_id: str) -> dict[str, Any]:
        """Undelete a soft-deleted conversion source."""
        return client.request(
            "POST",
            f"{base}/{source_id}:undelete",
            op="undelete_conversion_source",
        )
