from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()
    base = f"accounts/v1/{acct}/homepage"

    @mcp.tool()
    def gmc_get_homepage() -> dict[str, Any]:
        """Get the registered homepage URI and its claim status."""
        return client.request("GET", base)

    @mcp.tool()
    def gmc_update_homepage(uri: str, update_mask: str = "uri") -> dict[str, Any]:
        """Update the homepage URI. update_mask defaults to 'uri'."""
        before = None
        try:
            before = client.request("GET", base)
        except Exception:
            pass
        return client.request(
            "PATCH",
            base,
            params={"updateMask": update_mask},
            json_body={"uri": uri},
            op="update_homepage",
            before=before,
        )

    @mcp.tool()
    def gmc_claim_homepage(overwrite: bool = False) -> dict[str, Any]:
        """Claim ownership of the homepage. Set overwrite=True to take over from
        another claimant on the same domain."""
        return client.request(
            "POST",
            f"{base}:claim",
            json_body={"overwrite": overwrite},
            op="claim_homepage",
        )

    @mcp.tool()
    def gmc_unclaim_homepage() -> dict[str, Any]:
        """Release the homepage claim."""
        return client.request("POST", f"{base}:unclaim", op="unclaim_homepage")
