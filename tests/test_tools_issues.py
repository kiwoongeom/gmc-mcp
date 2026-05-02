from __future__ import annotations

import httpx
import respx
from mcp.server.fastmcp import FastMCP

from gmc_mcp.client import BASE_URL, MerchantClient
from gmc_mcp.tools import issues


def _build(client: MerchantClient) -> dict:
    mcp = FastMCP("test")
    issues.register(mcp, client)
    return {name: tool.fn for name, tool in mcp._tool_manager._tools.items()}


@respx.mock
def test_list_account_issues(client: MerchantClient) -> None:
    respx.get(
        f"{BASE_URL}/accounts/v1/accounts/1234567890/issues"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "accountIssues": [
                    {"title": "Missing return policy", "severity": "ERROR"},
                ]
            },
        )
    )
    fns = _build(client)
    out = fns["gmc_list_account_issues"]()
    assert out["count"] == 1
    assert out["issues"][0]["title"] == "Missing return policy"


@respx.mock
def test_summarize_product_issues(client: MerchantClient) -> None:
    """v1 itemIssues schema: type.code, severity.aggregatedSeverity, resolution."""
    respx.post(
        f"{BASE_URL}/reports/v1/accounts/1234567890/reports:search"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "productView": {
                            "id": "...",
                            "offerId": "A",
                            "aggregatedReportingContextStatus": "NOT_ELIGIBLE_OR_DISAPPROVED",
                            "itemIssues": [
                                {
                                    "type": {
                                        "code": "missing_gtin",
                                        "canonicalAttribute": "n:gtin",
                                    },
                                    "severity": {"aggregatedSeverity": "DISAPPROVED"},
                                    "resolution": "MERCHANT_ACTION",
                                },
                            ],
                        }
                    },
                    {
                        "productView": {
                            "id": "...",
                            "offerId": "B",
                            "aggregatedReportingContextStatus": "PENDING",
                            "itemIssues": [
                                {
                                    "type": {
                                        "code": "missing_gtin",
                                        "canonicalAttribute": "n:gtin",
                                    },
                                    "severity": {"aggregatedSeverity": "DEMOTED"},
                                    "resolution": "MERCHANT_ACTION",
                                },
                                {
                                    "type": {
                                        "code": "image_quality",
                                        "canonicalAttribute": "n:image_link",
                                    },
                                    "severity": {"aggregatedSeverity": "DEMOTED"},
                                    "resolution": "MERCHANT_ACTION",
                                },
                            ],
                        }
                    },
                ]
            },
        )
    )
    fns = _build(client)
    out = fns["gmc_summarize_product_issues"](max_products=10)
    assert out["scanned"] == 2
    assert out["top_issue_codes"]["missing_gtin"] == 2
    assert out["top_issue_codes"]["image_quality"] == 1
    assert out["status_breakdown"]["NOT_ELIGIBLE_OR_DISAPPROVED"] == 1
    assert out["status_breakdown"]["PENDING"] == 1
    assert out["severity_breakdown"]["DISAPPROVED"] == 1
    assert out["severity_breakdown"]["DEMOTED"] == 2
    assert out["resolution_breakdown"]["MERCHANT_ACTION"] == 3
    assert out["top_affected_attributes"]["n:gtin"] == 2
    assert out["top_affected_attributes"]["n:image_link"] == 1
