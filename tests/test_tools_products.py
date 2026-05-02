from __future__ import annotations

import httpx
import respx
from mcp.server.fastmcp import FastMCP

from gmc_mcp.client import BASE_URL, MerchantClient
from gmc_mcp.tools import products


def _build(client: MerchantClient) -> dict:
    """Register tools onto a temp FastMCP and return the underlying functions."""
    mcp = FastMCP("test")
    products.register(mcp, client)
    # FastMCP stores tools in mcp._tool_manager._tools (private but stable enough for unit tests).
    return {name: tool.fn for name, tool in mcp._tool_manager._tools.items()}


@respx.mock
def test_list_products_paginates(client: MerchantClient) -> None:
    page1 = {"products": [{"name": "a"}, {"name": "b"}], "nextPageToken": "x"}
    page2 = {"products": [{"name": "c"}]}
    respx.get(f"{BASE_URL}/products/v1/accounts/1234567890/products").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    fns = _build(client)
    out = fns["gmc_list_products"](max_pages=5)
    assert out["count"] == 3
    assert [p["name"] for p in out["products"]] == ["a", "b", "c"]


@respx.mock
def test_get_product(client: MerchantClient) -> None:
    pid = "online~en~US~SKU1"
    respx.get(
        f"{BASE_URL}/products/v1/accounts/1234567890/products/{pid}"
    ).mock(return_value=httpx.Response(200, json={"name": pid, "title": "Widget"}))
    fns = _build(client)
    out = fns["gmc_get_product"](product_id=pid)
    assert out["title"] == "Widget"


@respx.mock
def test_insert_product_writes_audit(client: MerchantClient) -> None:
    respx.post(
        f"{BASE_URL}/products/v1/accounts/1234567890/productInputs:insert"
    ).mock(return_value=httpx.Response(200, json={"name": "ok"}))
    fns = _build(client)
    fns["gmc_insert_product"](
        product={"offerId": "SKU1", "title": "Widget"},
        data_source="accounts/1234567890/dataSources/42",
    )
    text = client.audit.path.read_text(encoding="utf-8")
    assert "insert_product" in text


@respx.mock
def test_update_product_captures_before(client: MerchantClient) -> None:
    pid = "online~en~US~SKU1"
    respx.get(
        f"{BASE_URL}/products/v1/accounts/1234567890/products/{pid}"
    ).mock(return_value=httpx.Response(200, json={"name": pid, "title": "Old"}))
    respx.post(
        f"{BASE_URL}/products/v1/accounts/1234567890/productInputs:insert"
    ).mock(return_value=httpx.Response(200, json={"name": "ok"}))

    fns = _build(client)
    fns["gmc_update_product"](
        product_id=pid,
        product={"offerId": "SKU1", "title": "New"},
        data_source="accounts/1234567890/dataSources/42",
    )
    import json
    line = client.audit.path.read_text(encoding="utf-8").strip().splitlines()[-1]
    entry = json.loads(line)
    assert entry["before"]["title"] == "Old"
    assert entry["op"] == "update_product"


@respx.mock
def test_delete_product(client: MerchantClient) -> None:
    pid = "online~en~US~SKU1"
    respx.get(
        f"{BASE_URL}/products/v1/accounts/1234567890/products/{pid}"
    ).mock(return_value=httpx.Response(200, json={"name": pid}))
    respx.delete(
        f"{BASE_URL}/products/v1/accounts/1234567890/productInputs/{pid}"
    ).mock(return_value=httpx.Response(204))
    fns = _build(client)
    out = fns["gmc_delete_product"](
        product_id=pid, data_source="accounts/1234567890/dataSources/42"
    )
    assert out == {"deleted": pid}
