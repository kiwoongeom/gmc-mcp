from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    @mcp.tool()
    def gmc_list_datasources(max_pages: int = 5) -> dict[str, Any]:
        """List all data sources (primary, supplemental, file-based, API-based)."""
        items = list(
            client.paginate(
                "GET",
                f"datasources/v1/{acct}/dataSources",
                items_key="dataSources",
                max_pages=max_pages,
            )
        )
        return {"count": len(items), "data_sources": items}

    @mcp.tool()
    def gmc_get_datasource(datasource_id: str) -> dict[str, Any]:
        """Get a single data source by its ID (numeric)."""
        return client.request(
            "GET", f"datasources/v1/{acct}/dataSources/{datasource_id}"
        )

    @mcp.tool()
    def gmc_create_supplemental_feed(
        display_name: str,
        content_language: str,
        feed_label: str,
    ) -> dict[str, Any]:
        """Create an API-based supplemental product feed.

        display_name: human-readable name shown in the Merchant Center UI
        content_language: e.g. 'en', 'ko'
        feed_label: usually a country code like 'US', 'KR'

        Use the returned data source name when calling gmc_insert_product to write into this feed.
        """
        body = {
            "displayName": display_name,
            "supplementalProductDataSource": {
                "contentLanguage": content_language,
                "feedLabel": feed_label,
            },
        }
        return client.request(
            "POST",
            f"datasources/v1/{acct}/dataSources",
            json_body=body,
            op="create_supplemental_feed",
        )

    @mcp.tool()
    def gmc_create_primary_feed(
        display_name: str,
        content_language: str,
        feed_label: str,
        countries: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create an API-based primary product feed.

        countries: list of ISO country codes the feed targets (e.g. ['US', 'CA'])
        """
        primary: dict[str, Any] = {
            "contentLanguage": content_language,
            "feedLabel": feed_label,
        }
        if countries:
            primary["countries"] = countries
        body = {
            "displayName": display_name,
            "primaryProductDataSource": primary,
        }
        return client.request(
            "POST",
            f"datasources/v1/{acct}/dataSources",
            json_body=body,
            op="create_primary_feed",
        )

    @mcp.tool()
    def gmc_delete_datasource(datasource_id: str) -> dict[str, Any]:
        """Delete a data source. Cannot delete a primary feed if products depend on it."""
        before = None
        try:
            before = client.request(
                "GET", f"datasources/v1/{acct}/dataSources/{datasource_id}"
            )
        except Exception:
            pass
        client.request(
            "DELETE",
            f"datasources/v1/{acct}/dataSources/{datasource_id}",
            op="delete_datasource",
            before=before,
        )
        return {"deleted": datasource_id}

    @mcp.tool()
    def gmc_fetch_datasource(datasource_id: str) -> dict[str, Any]:
        """Trigger an immediate fetch of a file-based data source (must have a fetch URL)."""
        return client.request(
            "POST",
            f"datasources/v1/{acct}/dataSources/{datasource_id}:fetch",
            op="fetch_datasource",
        )
