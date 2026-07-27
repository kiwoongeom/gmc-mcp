from __future__ import annotations

import httpx
import pytest
import respx

from gmc_mcp.client import BASE_URL, MerchantAPIError, MerchantClient


def test_account_path(client: MerchantClient) -> None:
    assert client.account_path() == "accounts/1234567890"
    assert client.account_path("999") == "accounts/999"


@respx.mock
def test_get_attaches_auth_header(client: MerchantClient) -> None:
    route = respx.get(f"{BASE_URL}/foo/v1/test").mock(
        return_value=httpx.Response(200, json={"hello": "world"})
    )
    payload = client.request("GET", "foo/v1/test")
    assert payload == {"hello": "world"}
    assert route.called
    sent = route.calls.last.request
    assert sent.headers["Authorization"] == "Bearer fake-token"


@respx.mock
def test_dry_run_skips_network(client: MerchantClient) -> None:
    client.config.dry_run = True
    route = respx.post(f"{BASE_URL}/foo/v1/test").mock(
        return_value=httpx.Response(200, json={})
    )
    out = client.request("POST", "foo/v1/test", json_body={"a": 1}, op="test_op")
    assert out["_dry_run"] is True
    assert "audit_id" in out
    assert not route.called


@respx.mock
def test_dry_run_does_not_intercept_search_posts(client: MerchantClient) -> None:
    """reports:search is a read-only query that happens to use POST; dry-run
    must let it through, otherwise every reports-based tool silently returns
    0 results (a disapproved feed reads as a clean one)."""
    client.config.dry_run = True
    route = respx.post(
        f"{BASE_URL}/reports/v1/accounts/1234567890/reports:search"
    ).mock(
        return_value=httpx.Response(200, json={"results": [{"productView": {}}]})
    )
    out = client.request(
        "POST",
        "reports/v1/accounts/1234567890/reports:search",
        json_body={"query": "SELECT id FROM product_view"},
    )
    assert out == {"results": [{"productView": {}}]}
    assert route.called


@respx.mock
def test_write_writes_audit_entry(client: MerchantClient) -> None:
    respx.post(f"{BASE_URL}/foo/v1/x:insert").mock(
        return_value=httpx.Response(200, json={"name": "ok"})
    )
    client.request(
        "POST",
        "foo/v1/x:insert",
        json_body={"k": "v"},
        op="insert_x",
    )
    text = client.audit.path.read_text(encoding="utf-8").strip()
    assert text  # not empty
    import json
    entry = json.loads(text.splitlines()[-1])
    assert entry["op"] == "insert_x"
    assert entry["response_status"] == 200
    assert entry["request_body"] == {"k": "v"}


@respx.mock
def test_read_does_not_audit(client: MerchantClient) -> None:
    respx.get(f"{BASE_URL}/foo/v1/x").mock(
        return_value=httpx.Response(200, json={"name": "ok"})
    )
    client.request("GET", "foo/v1/x")
    assert not client.audit.path.exists() or client.audit.path.read_text() == ""


@respx.mock
def test_4xx_raises(client: MerchantClient) -> None:
    respx.get(f"{BASE_URL}/foo/v1/missing").mock(
        return_value=httpx.Response(404, json={"error": {"message": "not found"}})
    )
    with pytest.raises(MerchantAPIError) as ei:
        client.request("GET", "foo/v1/missing")
    assert ei.value.status == 404


@respx.mock
def test_retries_on_503(client: MerchantClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("gmc_mcp.client.time.sleep", lambda *_: None)
    route = respx.get(f"{BASE_URL}/foo/v1/x").mock(
        side_effect=[
            httpx.Response(503, json={}),
            httpx.Response(503, json={}),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    out = client.request("GET", "foo/v1/x")
    assert out == {"ok": True}
    assert route.call_count == 3


@respx.mock
def test_paginate_follows_token(client: MerchantClient) -> None:
    page1 = {"items": [{"id": 1}, {"id": 2}], "nextPageToken": "tok"}
    page2 = {"items": [{"id": 3}]}
    respx.get(f"{BASE_URL}/foo/v1/list").mock(
        side_effect=[
            httpx.Response(200, json=page1),
            httpx.Response(200, json=page2),
        ]
    )
    items = list(client.paginate("GET", "foo/v1/list", items_key="items"))
    assert [i["id"] for i in items] == [1, 2, 3]


@respx.mock
def test_paginate_respects_max_pages(client: MerchantClient) -> None:
    big = {"items": [{"id": 1}], "nextPageToken": "tok"}
    respx.get(f"{BASE_URL}/foo/v1/list").mock(
        return_value=httpx.Response(200, json=big)
    )
    items = list(client.paginate("GET", "foo/v1/list", items_key="items", max_pages=3))
    assert len(items) == 3
