from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    @mcp.tool()
    def gmc_list_promotions(max_pages: int = 5) -> dict[str, Any]:
        """List all promotions in the Merchant Center."""
        items = list(
            client.paginate(
                "GET",
                f"promotions/v1/{acct}/promotions",
                items_key="promotions",
                max_pages=max_pages,
            )
        )
        return {"count": len(items), "promotions": items}

    @mcp.tool()
    def gmc_get_promotion(promotion_id: str) -> dict[str, Any]:
        """Get a single promotion by ID."""
        return client.request(
            "GET", f"promotions/v1/{acct}/promotions/{promotion_id}"
        )

    @mcp.tool()
    def gmc_insert_promotion(promotion: dict[str, Any], data_source: str) -> dict[str, Any]:
        """Insert or update a promotion.

        promotion: full Promotion object (promotionId, contentLanguage, targetCountry,
                   redemptionChannel, productApplicability, offerType, longTitle, ...).
        data_source: data source name like 'accounts/123/dataSources/456'
        """
        return client.request(
            "POST",
            f"promotions/v1/{acct}/promotions:insert",
            params={"dataSource": data_source},
            json_body=promotion,
            op="insert_promotion",
        )
