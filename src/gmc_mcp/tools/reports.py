from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    @mcp.tool()
    def gmc_query_report(query: str, max_pages: int = 10) -> dict[str, Any]:
        """Run a raw Merchant API Reports query (Google's SQL-like dialect).

        Available views: product_view, price_competitiveness_product_view,
        price_insights_product_view, best_sellers_product_cluster_view,
        best_sellers_brand_view, product_performance_view, competitive_visibility_*

        Example:
        SELECT offer_id, title, clicks, impressions FROM product_performance_view
        WHERE date BETWEEN '2026-04-01' AND '2026-04-30'
        ORDER BY clicks DESC LIMIT 100
        """
        results: list[dict[str, Any]] = []
        params: dict[str, Any] = {}
        page_count = 0
        body = {"query": query}
        while True:
            payload = client.request(
                "POST",
                f"reports/v1/{acct}/reports:search",
                params=params,
                json_body=body,
            )
            results.extend(payload.get("results", []) or [])
            page_count += 1
            token = payload.get("nextPageToken")
            if not token or page_count >= max_pages:
                break
            body = {"query": query, "pageToken": token}

        return {"count": len(results), "query": query, "results": results}

    @mcp.tool()
    def gmc_product_performance(
        start_date: str,
        end_date: str,
        top_n: int = 100,
        order_by: str = "clicks",
    ) -> dict[str, Any]:
        """Top-performing products by clicks/impressions/CTR over a date range.

        start_date / end_date: 'YYYY-MM-DD'
        order_by: clicks | impressions | ctr | conversions | conversion_value_micros
        """
        query = (
            "SELECT offer_id, title, clicks, impressions, ctr, conversions, "
            "conversion_value_micros "
            "FROM product_performance_view "
            f"WHERE date BETWEEN '{start_date}' AND '{end_date}' "
            f"ORDER BY {order_by} DESC "
            f"LIMIT {top_n}"
        )
        return _run(client, acct, query)

    @mcp.tool()
    def gmc_price_competitiveness(top_n: int = 100) -> dict[str, Any]:
        """Compare your prices to benchmark prices (where available)."""
        query = (
            "SELECT offer_id, title, price, benchmark_price "
            "FROM price_competitiveness_product_view "
            f"LIMIT {top_n}"
        )
        return _run(client, acct, query)

    @mcp.tool()
    def gmc_best_sellers(report_country_code: str = "US", top_n: int = 100) -> dict[str, Any]:
        """Top-selling product clusters in a given country."""
        query = (
            "SELECT title, brand, category_l1, rank, previous_rank, relative_demand "
            "FROM best_sellers_product_cluster_view "
            f"WHERE report_country_code = '{report_country_code}' "
            "ORDER BY rank "
            f"LIMIT {top_n}"
        )
        return _run(client, acct, query)

    @mcp.tool()
    def gmc_zero_click_products(min_impressions: int = 100) -> dict[str, Any]:
        """Products that have impressions but zero clicks — usually a CTR/title/image problem."""
        query = (
            "SELECT offer_id, title, impressions, clicks, ctr "
            "FROM product_performance_view "
            f"WHERE impressions >= {min_impressions} AND clicks = 0 "
            "ORDER BY impressions DESC "
            "LIMIT 200"
        )
        return _run(client, acct, query)

    @mcp.tool()
    def gmc_revenue_by_brand(start_date: str, end_date: str, top_n: int = 50) -> dict[str, Any]:
        """Aggregate clicks/conversions/value by brand."""
        query = (
            "SELECT brand, clicks, impressions, conversions, conversion_value_micros "
            "FROM product_performance_view "
            f"WHERE date BETWEEN '{start_date}' AND '{end_date}' "
            f"LIMIT {top_n}"
        )
        return _run(client, acct, query)

    @mcp.tool()
    def gmc_category_performance(start_date: str, end_date: str, top_n: int = 50) -> dict[str, Any]:
        """Performance grouped by Google product category L1/L2."""
        query = (
            "SELECT category_l1, category_l2, clicks, impressions, conversions "
            "FROM product_performance_view "
            f"WHERE date BETWEEN '{start_date}' AND '{end_date}' "
            f"LIMIT {top_n}"
        )
        return _run(client, acct, query)

    @mcp.tool()
    def gmc_competitive_visibility_top_merchants(
        report_country_code: str = "US", top_n: int = 50
    ) -> dict[str, Any]:
        """Who ranks above you on Shopping for the same products."""
        query = (
            "SELECT domain, rank, ads_organic_ratio, page_overlap_rate, higher_position_rate "
            "FROM competitive_visibility_top_merchant_view "
            f"WHERE report_country_code = '{report_country_code}' "
            "ORDER BY rank "
            f"LIMIT {top_n}"
        )
        return _run(client, acct, query)

    @mcp.tool()
    def gmc_price_insights(top_n: int = 100) -> dict[str, Any]:
        """Google's suggested optimal price for each product (where available)."""
        query = (
            "SELECT offer_id, title, suggested_price, predicted_impressions_change_fraction, "
            "predicted_clicks_change_fraction, predicted_conversions_change_fraction "
            "FROM price_insights_product_view "
            f"LIMIT {top_n}"
        )
        return _run(client, acct, query)

    @mcp.tool()
    def gmc_demoted_products(top_n: int = 200) -> dict[str, Any]:
        """Products that are still ELIGIBLE but suppressed (less reach than they could have)."""
        query = (
            "SELECT id, offer_id, title, item_issues "
            "FROM product_view "
            "WHERE aggregated_reporting_context_status = 'ELIGIBLE_LIMITED' "
            f"LIMIT {top_n}"
        )
        return _run(client, acct, query)


def _run(client: MerchantClient, acct: str, query: str) -> dict[str, Any]:
    payload = client.request(
        "POST",
        f"reports/v1/{acct}/reports:search",
        json_body={"query": query},
    )
    return {
        "query": query,
        "count": len(payload.get("results", []) or []),
        "results": payload.get("results", []),
        "next_page_token": payload.get("nextPageToken"),
    }
