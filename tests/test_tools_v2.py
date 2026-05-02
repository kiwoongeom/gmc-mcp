"""Smoke tests for the v0.2.0 tool modules. Verifies each module registers
without errors and one representative call hits the right URL."""

from __future__ import annotations

import httpx
import respx
from mcp.server.fastmcp import FastMCP

from gmc_mcp.client import BASE_URL, MerchantClient
from gmc_mcp.tools import (
    account_config,
    bulk,
    conversions,
    diagnostics,
    homepage,
    lfp,
    mca,
    omnichannel,
    quotas,
    return_policies,
    reviews,
)


def _build(module, client: MerchantClient) -> dict:
    mcp = FastMCP("test")
    module.register(mcp, client)
    return {name: tool.fn for name, tool in mcp._tool_manager._tools.items()}


@respx.mock
def test_return_policies_list(client: MerchantClient) -> None:
    respx.get(
        f"{BASE_URL}/accounts/v1/accounts/1234567890/onlineReturnPolicies"
    ).mock(return_value=httpx.Response(200, json={"onlineReturnPolicies": [{"name": "x"}]}))
    fns = _build(return_policies, client)
    out = fns["gmc_list_return_policies"]()
    assert out["count"] == 1


@respx.mock
def test_homepage_claim(client: MerchantClient) -> None:
    respx.post(
        f"{BASE_URL}/accounts/v1/accounts/1234567890/homepage:claim"
    ).mock(return_value=httpx.Response(200, json={"claimed": True}))
    fns = _build(homepage, client)
    out = fns["gmc_claim_homepage"](overwrite=True)
    assert out == {"claimed": True}


@respx.mock
def test_account_config_get_automatic_improvements(client: MerchantClient) -> None:
    respx.get(
        f"{BASE_URL}/accounts/v1/accounts/1234567890/automaticImprovements"
    ).mock(return_value=httpx.Response(200, json={"itemUpdates": {}}))
    fns = _build(account_config, client)
    out = fns["gmc_get_automatic_improvements"]()
    assert "itemUpdates" in out


@respx.mock
def test_account_config_get_business_identity(client: MerchantClient) -> None:
    respx.get(
        f"{BASE_URL}/accounts/v1/accounts/1234567890/businessIdentity"
    ).mock(return_value=httpx.Response(200, json={"name": "x"}))
    fns = _build(account_config, client)
    assert fns["gmc_get_business_identity"]()["name"] == "x"


@respx.mock
def test_quotas_list(client: MerchantClient) -> None:
    respx.get(
        f"{BASE_URL}/quota/v1/accounts/1234567890/quotas"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"quotaGroups": [{"quotaUsage": "10", "quotaLimit": "1000"}]},
        )
    )
    fns = _build(quotas, client)
    out = fns["gmc_list_quotas"]()
    assert out["count"] == 1


@respx.mock
def test_reviews_list_merchant(client: MerchantClient) -> None:
    respx.get(
        f"{BASE_URL}/accounts/v1/accounts/1234567890/merchantReviews"
    ).mock(return_value=httpx.Response(200, json={"merchantReviews": [{"id": "1"}]}))
    fns = _build(reviews, client)
    assert fns["gmc_list_merchant_reviews"]()["count"] == 1


@respx.mock
def test_conversions_list(client: MerchantClient) -> None:
    respx.get(
        f"{BASE_URL}/conversions/v1/accounts/1234567890/conversionSources"
    ).mock(return_value=httpx.Response(200, json={"conversionSources": []}))
    fns = _build(conversions, client)
    assert fns["gmc_list_conversion_sources"]()["count"] == 0


@respx.mock
def test_omnichannel_list(client: MerchantClient) -> None:
    respx.get(
        f"{BASE_URL}/accounts/v1/accounts/1234567890/omnichannelSettings"
    ).mock(return_value=httpx.Response(200, json={"omnichannelSettings": []}))
    fns = _build(omnichannel, client)
    assert fns["gmc_list_omnichannel_settings"]()["count"] == 0


@respx.mock
def test_lfp_get_merchant_state(client: MerchantClient) -> None:
    respx.get(
        f"{BASE_URL}/lfp/v1/accounts/1234567890/lfpMerchantStates/9999"
    ).mock(return_value=httpx.Response(200, json={"linkedGbpShortCode": "LCO123"}))
    fns = _build(lfp, client)
    out = fns["gmc_lfp_get_merchant_state"](target_account="9999")
    assert out["linkedGbpShortCode"] == "LCO123"


@respx.mock
def test_mca_list_relationships(client: MerchantClient) -> None:
    respx.get(
        f"{BASE_URL}/accounts/v1/accounts/1234567890/accountRelationships"
    ).mock(return_value=httpx.Response(200, json={"accountRelationships": []}))
    fns = _build(mca, client)
    assert fns["gmc_list_relationships"]()["count"] == 0


def test_bulk_refuses_without_confirm(client: MerchantClient) -> None:
    fns = _build(bulk, client)
    out = fns["gmc_bulk_update_regional_prices"](updates=[{"product_id": "x", "region": "US"}])
    assert "Refused" in out["error"]


def test_bulk_set_availability_refuses_without_confirm(client: MerchantClient) -> None:
    fns = _build(bulk, client)
    out = fns["gmc_bulk_set_availability"](
        product_ids=["x"], region="US", availability="OUT_OF_STOCK"
    )
    assert "Refused" in out["error"]


def test_diagnostics_rollback_refuses_without_confirm(client: MerchantClient) -> None:
    fns = _build(diagnostics, client)
    out = fns["gmc_rollback"](audit_id="abc")
    assert "Refused" in out["error"]


@respx.mock
def test_diagnostics_health_check(client: MerchantClient) -> None:
    # Mock all probed endpoints
    respx.get(f"{BASE_URL}/accounts/v1/accounts/1234567890").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.get(f"{BASE_URL}/accounts/v1/accounts/1234567890/issues").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.get(f"{BASE_URL}/products/v1/accounts/1234567890/products").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.get(f"{BASE_URL}/datasources/v1/accounts/1234567890/dataSources").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.post(f"{BASE_URL}/reports/v1/accounts/1234567890/reports:search").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.get(f"{BASE_URL}/accounts/v1/accounts/1234567890/homepage").mock(
        return_value=httpx.Response(200, json={})
    )
    respx.get(
        f"{BASE_URL}/accounts/v1/accounts/1234567890/automaticImprovements"
    ).mock(return_value=httpx.Response(200, json={}))
    fns = _build(diagnostics, client)
    out = fns["gmc_health_check"]()
    assert out["ok"] == 7
    assert out["total"] == 7
