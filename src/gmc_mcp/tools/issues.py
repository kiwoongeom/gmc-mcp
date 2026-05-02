from __future__ import annotations

from collections import Counter
from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    @mcp.tool()
    def gmc_list_account_issues(language_code: str = "en") -> dict[str, Any]:
        """List all account-level issues (policy, missing settings, etc).

        language_code: BCP-47 code for issue messages (default 'en').
        """
        items = list(
            client.paginate(
                "GET",
                f"accounts/v1/{acct}/issues",
                params={"languageCode": language_code},
                items_key="accountIssues",
            )
        )
        return {"count": len(items), "issues": items}

    @mcp.tool()
    def gmc_get_product_status(product_id: str) -> dict[str, Any]:
        """Get the status (approval, issues, destinations) of a single product.

        product_id: full product ID (channel~lang~feedLabel~offerId)
        """
        product = client.request(
            "GET", f"products/v1/{acct}/products/{product_id}"
        )
        return {
            "product_id": product_id,
            "title": (product.get("productAttributes") or {}).get("title"),
            "status": product.get("productStatus", {}),
        }

    @mcp.tool()
    def gmc_summarize_product_issues(max_products: int = 5000) -> dict[str, Any]:
        """Scan products and aggregate issue codes by frequency.

        Useful for prioritizing fixes — e.g. "1186 products: landing_page_error".
        Each issue is keyed by `type.code` and broken down by `aggregatedSeverity`
        and the affected canonical attribute (e.g. n:link, n:gtin).
        Uses the Reports API for efficiency.
        """
        query = (
            "SELECT id, offer_id, title, "
            "aggregated_reporting_context_status, item_issues "
            "FROM product_view "
            "WHERE aggregated_reporting_context_status != 'ELIGIBLE'"
        )
        items: list[dict[str, Any]] = []
        body: dict[str, Any] = {"query": query}
        path = f"reports/v1/{acct}/reports:search"
        while len(items) < max_products:
            payload = client.request("POST", path, json_body=body)
            items.extend(payload.get("results", []) or [])
            token = payload.get("nextPageToken")
            if not token:
                break
            body = {"query": query, "pageToken": token}

        items = items[:max_products]

        status_counter: Counter[str] = Counter()
        code_counter: Counter[str] = Counter()
        attribute_counter: Counter[str] = Counter()
        severity_counter: Counter[str] = Counter()
        resolution_counter: Counter[str] = Counter()

        for row in items:
            pv = row.get("productView", {})
            status_counter[pv.get("aggregatedReportingContextStatus", "UNKNOWN")] += 1
            for issue in pv.get("itemIssues", []) or []:
                itype = issue.get("type") or {}
                code = itype.get("code") or "unknown"
                code_counter[code] += 1
                if itype.get("canonicalAttribute"):
                    attribute_counter[itype["canonicalAttribute"]] += 1
                sev = (issue.get("severity") or {}).get("aggregatedSeverity", "UNKNOWN")
                severity_counter[sev] += 1
                if issue.get("resolution"):
                    resolution_counter[issue["resolution"]] += 1

        return {
            "scanned": len(items),
            "_query": query,
            "status_breakdown": dict(status_counter.most_common()),
            "severity_breakdown": dict(severity_counter.most_common()),
            "resolution_breakdown": dict(resolution_counter.most_common()),
            "top_issue_codes": dict(code_counter.most_common(30)),
            "top_affected_attributes": dict(attribute_counter.most_common(30)),
        }
