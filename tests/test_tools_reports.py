from __future__ import annotations

import httpx
import respx
from mcp.server.fastmcp import FastMCP

from gmc_mcp.client import BASE_URL, MerchantClient
from gmc_mcp.tools import reports


def _build(client: MerchantClient) -> dict:
    mcp = FastMCP("test")
    reports.register(mcp, client)
    return {name: tool.fn for name, tool in mcp._tool_manager._tools.items()}


@respx.mock
def test_query_report(client: MerchantClient) -> None:
    respx.post(
        f"{BASE_URL}/reports/v1/accounts/1234567890/reports:search"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"productView": {"offerId": "SKU1"}}]},
        )
    )
    fns = _build(client)
    out = fns["gmc_query_report"](query="SELECT offer_id FROM product_view LIMIT 1")
    assert out["count"] == 1
    assert out["results"][0]["productView"]["offerId"] == "SKU1"


@respx.mock
def test_zero_click_products(client: MerchantClient) -> None:
    respx.post(
        f"{BASE_URL}/reports/v1/accounts/1234567890/reports:search"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"results": [{"productPerformanceView": {"offerId": "DUD"}}]},
        )
    )
    fns = _build(client)
    out = fns["gmc_zero_click_products"](min_impressions=50)
    assert out["count"] == 1
    assert "impressions >= 50" in out["query"]
    assert "clicks = 0" in out["query"]
