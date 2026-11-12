"""A preview must never be presented to MCP clients as an applied deletion/update."""

import re
from types import SimpleNamespace

import httpx
import pytest
import respx

from gmc_mcp.tools import (
    account_config,
    accounts,
    bulk,
    conversions,
    feeds,
    lfp,
    notifications,
    products,
    regions,
    return_policies,
    reviews,
)


def functions(module, client):
    result = {}
    module.register(
        SimpleNamespace(tool=lambda: lambda f: result.setdefault(f.__name__, f)), client
    )
    return result


@pytest.mark.parametrize(
    "module,name,args",
    [
        (
            products,
            "gmc_delete_product",
            {"product_id": "online~en~US~one", "data_source": "accounts/123/dataSources/1"},
        ),
        (accounts, "gmc_remove_user", {"email": "test@example.com"}),
        (notifications, "gmc_unsubscribe", {"subscription_id": "1"}),
        (feeds, "gmc_delete_datasource", {"datasource_id": "1"}),
        (return_policies, "gmc_delete_return_policy", {"policy_id": "1"}),
        (account_config, "gmc_delete_checkout_settings", {}),
        (reviews, "gmc_delete_merchant_review", {"review_id": "1"}),
        (reviews, "gmc_delete_product_review", {"review_id": "1"}),
        (conversions, "gmc_delete_conversion_source", {"source_id": "1"}),
        (lfp, "gmc_lfp_delete_store", {"store_code": "123~one"}),
        (regions, "gmc_delete_region", {"region_id": "one"}),
    ],
)
@respx.mock
@pytest.mark.parametrize("dry_run", [True, False])
def test_delete_preview_does_not_claim_remote_deletion(client, module, name, args, dry_run):
    client.config.dry_run = dry_run
    respx.get(re.compile(r"https://merchantapi.googleapis.com/.*")).mock(
        return_value=httpx.Response(200, json={})
    )
    respx.delete(re.compile(r"https://merchantapi.googleapis.com/.*")).mock(
        return_value=httpx.Response(204)
    )
    result = functions(module, client)[name](**args)
    if not dry_run:
        assert result.get("_dry_run") is not True
        assert any(k.startswith(("deleted", "removed")) for k in result)
        assert any(call.request.method == "DELETE" for call in respx.calls)
        return
    assert result.get("_dry_run") is True
    assert not any(k.startswith(("deleted", "removed")) for k in result)
    assert all(call.request.method == "GET" for call in respx.calls)


@pytest.mark.parametrize(
    "name,args,count_key",
    [
        (
            "gmc_bulk_update_regional_prices",
            {
                "updates": [
                    {
                        "product_id": "one",
                        "region": "US",
                        "price_amount_micros": 100,
                        "price_currency": "USD",
                    }
                ],
                "confirm": "APPLY",
            },
            "applied_count",
        ),
        (
            "gmc_bulk_set_availability",
            {
                "product_ids": ["one"],
                "region": "US",
                "availability": "IN_STOCK",
                "confirm": "APPLY",
            },
            "applied_count",
        ),
        ("gmc_bulk_delete_products", {"confirm": "DELETE", "max_delete": 1}, "deleted_count"),
    ],
)
@respx.mock
@pytest.mark.parametrize("dry_run", [True, False])
def test_bulk_preview_has_zero_applied_count(client, name, args, count_key, dry_run):
    client.config.dry_run = dry_run
    respx.get(re.compile(r"https://merchantapi.googleapis.com/.*")).mock(
        return_value=httpx.Response(
            200,
            json={
                "products": [
                    {
                        "name": "accounts/123/products/one",
                        "dataSource": "accounts/123/dataSources/1",
                    }
                ]
            },
        )
    )
    respx.post(re.compile(r"https://merchantapi.googleapis.com/.*")).mock(
        return_value=httpx.Response(200, json={})
    )
    respx.delete(re.compile(r"https://merchantapi.googleapis.com/.*")).mock(
        return_value=httpx.Response(204)
    )
    result = functions(products if name == "gmc_bulk_delete_products" else bulk, client)[name](
        **args
    )
    assert result[count_key] == (0 if dry_run else 1)
    assert result["preview_count"] == (1 if dry_run else 0)
    assert result["_dry_run"] is dry_run
    if dry_run:
        assert all(call.request.method == "GET" for call in respx.calls)
