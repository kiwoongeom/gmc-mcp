from __future__ import annotations

import json

import httpx
import pytest
import respx
from mcp.server.fastmcp import FastMCP

from gmc_mcp.client import BASE_URL, MerchantAPIError, MerchantClient
from gmc_mcp.tools import reports


def _build(client: MerchantClient) -> dict:
    mcp = FastMCP("test")
    reports.register(mcp, client)
    return {name: tool.fn for name, tool in mcp._tool_manager._tools.items()}


@respx.mock
def test_query_report(client: MerchantClient) -> None:
    respx.post(f"{BASE_URL}/reports/v1/accounts/1234567890/reports:search").mock(
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
    respx.post(f"{BASE_URL}/reports/v1/accounts/1234567890/reports:search").mock(
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


@respx.mock
def test_dry_run_report_follows_pages(client: MerchantClient) -> None:
    client.config.dry_run = True
    route = respx.post(f"{BASE_URL}/reports/v1/accounts/1234567890/reports:search").mock(
        side_effect=[
            httpx.Response(
                200, json={"results": [{"productView": {"offerId": "A"}}], "nextPageToken": "next"}
            ),
            httpx.Response(200, json={"results": [{"productView": {"offerId": "B"}}]}),
        ]
    )
    out = _build(client)["gmc_query_report"](query="SELECT offer_id FROM product_view")
    assert out["count"] == 2
    assert route.call_count == 2
    assert json.loads(route.calls.last.request.content)["pageToken"] == "next"
    assert not client.audit.path.exists()


@pytest.mark.parametrize("status", [400, 403, 503])
@respx.mock
def test_dry_run_report_surfaces_api_errors(
    client: MerchantClient, monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    client.config.dry_run = True
    monkeypatch.setattr("gmc_mcp.client.time.sleep", lambda *_: None)
    body = {"error": {"message": "report request failed"}}
    route = respx.post(f"{BASE_URL}/reports/v1/accounts/1234567890/reports:search").mock(
        return_value=httpx.Response(status, json=body)
    )
    with pytest.raises(MerchantAPIError) as error:
        _build(client)["gmc_query_report"](query="SELECT invalid FROM nonexistent_view_xyz")
    assert error.value.status == status
    assert error.value.body == body
    assert route.called
