from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    @mcp.tool()
    def gmc_get_account() -> dict[str, Any]:
        """Get the current Merchant Center account information."""
        return client.request("GET", f"accounts/v1/{acct}")

    @mcp.tool()
    def gmc_get_business_info() -> dict[str, Any]:
        """Get business identity info (address, phone, customer service)."""
        return client.request("GET", f"accounts/v1/{acct}/businessInfo")

    @mcp.tool()
    def gmc_update_business_info(
        business_info: dict[str, Any], update_mask: str | None = None
    ) -> dict[str, Any]:
        """Patch business info. Body example:
            {
              "address": {
                "regionCode": "US",
                "postalCode": "94043",
                "administrativeArea": "CA",
                "locality": "Mountain View",
                "addressLines": ["1600 Amphitheatre Pkwy"]
              },
              "phone": {"e164Number": "+14155551234"},
              "customerService": {
                "uri": "https://store.com/contact",
                "email": "support@store.com",
                "phone": {"e164Number": "+18005551234"}
              },
              "koreanBusinessRegistrationNumber": "123-45-67890"
            }
        update_mask: comma-separated FieldMask, e.g. 'address,phone'.
        """
        before = None
        try:
            before = client.request("GET", f"accounts/v1/{acct}/businessInfo")
        except Exception:
            pass
        params = {"updateMask": update_mask} if update_mask else None
        return client.request(
            "PATCH",
            f"accounts/v1/{acct}/businessInfo",
            params=params,
            json_body=business_info,
            op="update_business_info",
            before=before,
        )

    @mcp.tool()
    def gmc_list_users(max_pages: int = 5) -> dict[str, Any]:
        """List users with access to this Merchant Center account."""
        items = list(
            client.paginate(
                "GET",
                f"accounts/v1/{acct}/users",
                items_key="users",
                max_pages=max_pages,
            )
        )
        return {"count": len(items), "users": items}

    @mcp.tool()
    def gmc_add_user(email: str, access_rights: list[str]) -> dict[str, Any]:
        """Add a user to the Merchant Center account.

        access_rights: list of strings, e.g. ['ADMIN'] or ['STANDARD', 'PERFORMANCE_REPORTING']
        """
        return client.request(
            "POST",
            f"accounts/v1/{acct}/users",
            params={"userId": email},
            json_body={"accessRights": access_rights},
            op="add_user",
        )

    @mcp.tool()
    def gmc_remove_user(email: str) -> dict[str, Any]:
        """Remove a user from the Merchant Center account."""
        before = None
        try:
            before = client.request(
                "GET", f"accounts/v1/{acct}/users/{email}"
            )
        except Exception:
            pass
        client.request(
            "DELETE",
            f"accounts/v1/{acct}/users/{email}",
            op="remove_user",
            before=before,
        )
        return {"removed": email}

    @mcp.tool()
    def gmc_get_shipping_settings() -> dict[str, Any]:
        """Get shipping settings (services, rate groups, delivery times)."""
        return client.request(
            "GET", f"accounts/v1/{acct}/shippingSettings"
        )

    @mcp.tool()
    def gmc_update_shipping_settings(shipping_settings: dict[str, Any]) -> dict[str, Any]:
        """Update shipping settings. Body must be a complete ShippingSettings object."""
        before = None
        try:
            before = client.request(
                "GET", f"accounts/v1/{acct}/shippingSettings"
            )
        except Exception:
            pass
        return client.request(
            "POST",
            f"accounts/v1/{acct}/shippingSettings:insert",
            json_body=shipping_settings,
            op="update_shipping_settings",
            before=before,
        )

    @mcp.tool()
    def gmc_list_programs(max_pages: int = 3) -> dict[str, Any]:
        """List participation in Merchant Center programs (Shopping Ads, Free Listings, etc.)."""
        items = list(
            client.paginate(
                "GET",
                f"accounts/v1/{acct}/programs",
                items_key="programs",
                max_pages=max_pages,
            )
        )
        return {"count": len(items), "programs": items}

    @mcp.tool()
    def gmc_request_program_review(
        program_id: str, region_code: str = "US"
    ) -> dict[str, Any]:
        """Request a manual review of a program after fixing disapproval issues.

        program_id: e.g. 'shopping-ads', 'free-listings'.
        region_code: country to request review in.

        Use after you've resolved the policy / quality issues that caused suspension.
        Limited to a few requests per period.
        """
        return client.request(
            "POST",
            f"accounts/v1/{acct}/programs/{program_id}:requestReview",
            json_body={"regionCode": region_code},
            op="request_program_review",
        )

    @mcp.tool()
    def gmc_get_program_review(program_id: str) -> dict[str, Any]:
        """Get the current review state of a program (pending/approved/disapproved/etc.)."""
        return client.request(
            "GET", f"accounts/v1/{acct}/programs/{program_id}/review"
        )
