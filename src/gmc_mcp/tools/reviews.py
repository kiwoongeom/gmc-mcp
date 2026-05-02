"""Merchant reviews + Product reviews."""

from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()
    mr_base = f"accounts/v1/{acct}/merchantReviews"
    pr_base = f"accounts/v1/{acct}/productReviews"

    # ---- Merchant reviews ----

    @mcp.tool()
    def gmc_list_merchant_reviews(max_pages: int = 5) -> dict[str, Any]:
        """List merchant (store) reviews — used for Trusted Stores / star ratings."""
        items = list(
            client.paginate(
                "GET", mr_base, items_key="merchantReviews", max_pages=max_pages
            )
        )
        return {"count": len(items), "reviews": items}

    @mcp.tool()
    def gmc_get_merchant_review(review_id: str) -> dict[str, Any]:
        return client.request("GET", f"{mr_base}/{review_id}")

    @mcp.tool()
    def gmc_insert_merchant_review(
        review: dict[str, Any], data_source: str
    ) -> dict[str, Any]:
        """Insert / upsert a merchant review.

        review: full MerchantReview body (merchantReviewId, attributes, etc.)
        data_source: data source name like 'accounts/X/dataSources/Y'.
        """
        return client.request(
            "POST",
            mr_base,
            params={"dataSource": data_source},
            json_body=review,
            op="insert_merchant_review",
        )

    @mcp.tool()
    def gmc_delete_merchant_review(review_id: str) -> dict[str, Any]:
        before = None
        try:
            before = client.request("GET", f"{mr_base}/{review_id}")
        except Exception:
            pass
        client.request(
            "DELETE", f"{mr_base}/{review_id}", op="delete_merchant_review", before=before
        )
        return {"deleted": review_id}

    # ---- Product reviews ----

    @mcp.tool()
    def gmc_list_product_reviews(max_pages: int = 10) -> dict[str, Any]:
        """List product reviews."""
        items = list(
            client.paginate(
                "GET", pr_base, items_key="productReviews", max_pages=max_pages
            )
        )
        return {"count": len(items), "reviews": items}

    @mcp.tool()
    def gmc_get_product_review(review_id: str) -> dict[str, Any]:
        return client.request("GET", f"{pr_base}/{review_id}")

    @mcp.tool()
    def gmc_insert_product_review(
        review: dict[str, Any], data_source: str
    ) -> dict[str, Any]:
        """Insert / upsert a product review."""
        return client.request(
            "POST",
            pr_base,
            params={"dataSource": data_source},
            json_body=review,
            op="insert_product_review",
        )

    @mcp.tool()
    def gmc_delete_product_review(review_id: str) -> dict[str, Any]:
        before = None
        try:
            before = client.request("GET", f"{pr_base}/{review_id}")
        except Exception:
            pass
        client.request(
            "DELETE", f"{pr_base}/{review_id}", op="delete_product_review", before=before
        )
        return {"deleted": review_id}
