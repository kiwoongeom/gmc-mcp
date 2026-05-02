"""Regions CRUD — required for setting up regional inventory targeting.

A region is a named bundle of postal codes / sub-areas you can later target
with `gmc_update_regional_inventory(region=...)`.
"""

from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()
    base = f"accounts/v1/{acct}/regions"

    @mcp.tool()
    def gmc_list_regions(max_pages: int = 5) -> dict[str, Any]:
        """List all regions configured on the account."""
        items = list(
            client.paginate(
                "GET", base, items_key="regions", max_pages=max_pages
            )
        )
        return {"count": len(items), "regions": items}

    @mcp.tool()
    def gmc_get_region(region_id: str) -> dict[str, Any]:
        """Get one region by ID."""
        return client.request("GET", f"{base}/{region_id}")

    @mcp.tool()
    def gmc_create_region(
        region_id: str,
        display_name: str,
        postal_code_prefixes: list[str] | None = None,
        postal_code_ranges: list[dict[str, str]] | None = None,
        geotarget_criteria_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new region.

        region_id: short ID like 'us-west', 'kr-seoul'.
        Provide ONE of:
          - postal_code_prefixes: ['90', '91']  (US ZIPs starting with 90/91)
          - postal_code_ranges: [{'firstPostalCode': '90001', 'lastPostalCode': '92899'}]
          - geotarget_criteria_ids: ['1014044']  (Google Ads geotargets)
        """
        body: dict[str, Any] = {"displayName": display_name}
        if postal_code_prefixes or postal_code_ranges:
            postal: dict[str, Any] = {}
            if postal_code_prefixes:
                postal["postalCodes"] = [{"prefix": p} for p in postal_code_prefixes]
            if postal_code_ranges:
                postal.setdefault("postalCodes", []).extend(postal_code_ranges)
            body["postalCodeArea"] = postal
        if geotarget_criteria_ids:
            body["geotargetArea"] = {"geotargetCriteriaIds": geotarget_criteria_ids}

        return client.request(
            "POST",
            base,
            params={"regionId": region_id},
            json_body=body,
            op="create_region",
        )

    @mcp.tool()
    def gmc_update_region(
        region_id: str, region: dict[str, Any], update_mask: str | None = None
    ) -> dict[str, Any]:
        """Patch a region. update_mask example: 'displayName,postalCodeArea'."""
        before = None
        try:
            before = client.request("GET", f"{base}/{region_id}")
        except Exception:
            pass
        params = {"updateMask": update_mask} if update_mask else None
        return client.request(
            "PATCH",
            f"{base}/{region_id}",
            params=params,
            json_body=region,
            op="update_region",
            before=before,
        )

    @mcp.tool()
    def gmc_delete_region(region_id: str) -> dict[str, Any]:
        """Delete a region (and any regional inventories that reference it)."""
        before = None
        try:
            before = client.request("GET", f"{base}/{region_id}")
        except Exception:
            pass
        client.request(
            "DELETE", f"{base}/{region_id}", op="delete_region", before=before
        )
        return {"deleted_region_id": region_id}
