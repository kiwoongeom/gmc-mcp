from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    @mcp.tool()
    def gmc_list_quotas(max_pages: int = 5) -> dict[str, Any]:
        """List the API quota usage / limits for this account.

        Useful to monitor before hitting rate limits. Returns one entry per
        quota group (e.g. ProductsService, ReportsService).
        """
        items = list(
            client.paginate(
                "GET",
                f"quota/v1/{acct}/quotas",
                items_key="quotaGroups",
                max_pages=max_pages,
            )
        )
        rows = []
        for q in items:
            rows.append(
                {
                    "method": q.get("methodDetails", []),
                    "quota_usage": q.get("quotaUsage"),
                    "quota_limit": q.get("quotaLimit"),
                    "quota_minute_limit": q.get("quotaMinuteLimit"),
                }
            )
        return {"count": len(items), "quotas_raw": items, "summary": rows}
