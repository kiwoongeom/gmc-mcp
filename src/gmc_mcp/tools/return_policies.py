from __future__ import annotations

import contextlib
from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()
    base = f"accounts/v1/{acct}/onlineReturnPolicies"

    @mcp.tool()
    def gmc_list_return_policies(max_pages: int = 5) -> dict[str, Any]:
        """List online return policies attached to this account.

        Required by Google in the US/EU — without one, products get demoted.
        """
        items = list(
            client.paginate("GET", base, items_key="onlineReturnPolicies", max_pages=max_pages)
        )
        return {"count": len(items), "return_policies": items}

    @mcp.tool()
    def gmc_get_return_policy(policy_id: str) -> dict[str, Any]:
        """Get a single return policy by ID."""
        return client.request("GET", f"{base}/{policy_id}")

    @mcp.tool()
    def gmc_create_return_policy(policy: dict[str, Any]) -> dict[str, Any]:
        """Create an online return policy.

        Minimal `policy` body example:
            {
              "label": "Standard 30-day",
              "countries": ["US"],
              "policy": {
                "type": "NUMBER_OF_DAYS_AFTER_DELIVERY",
                "days": 30
              },
              "returnShippingFee": {"type": "FREE"},
              "itemConditions": ["NEW"],
              "returnMethods": ["BY_MAIL"],
              "returnPolicyUri": "https://your-store.com/returns"
            }
        """
        return client.request("POST", base, json_body=policy, op="create_return_policy")

    @mcp.tool()
    def gmc_update_return_policy(
        policy_id: str, policy: dict[str, Any], update_mask: str | None = None
    ) -> dict[str, Any]:
        """Unsupported: Merchant API has no online-return-policy update method."""
        raise NotImplementedError(
            "UNSUPPORTED_FEATURE: Merchant API has no onlineReturnPolicies PATCH method. "
            "Edit the existing policy in Merchant Center. No replacement or deletion was performed."
        )

    @mcp.tool()
    def gmc_delete_return_policy(policy_id: str) -> dict[str, Any]:
        """Delete a return policy."""
        before = None
        with contextlib.suppress(Exception):
            before = client.request("GET", f"{base}/{policy_id}")
        result = client.request(
            "DELETE", f"{base}/{policy_id}", op="delete_return_policy", before=before
        )
        if result.get("_dry_run"):
            return result
        return {"deleted": policy_id}
