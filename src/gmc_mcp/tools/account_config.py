"""Account-level configuration: business identity, checkout, automatic improvements,
autofeed, account tax, email preferences, terms of service."""

from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    # ---------------- Business identity ----------------

    @mcp.tool()
    def gmc_get_business_identity() -> dict[str, Any]:
        """Get business identity (women-owned, minority-owned, veteran-owned, etc.).
        Google can show badges on your listings based on these attributes."""
        return client.request("GET", f"accounts/v1/{acct}/businessIdentity")

    @mcp.tool()
    def gmc_update_business_identity(
        identity: dict[str, Any], update_mask: str | None = None
    ) -> dict[str, Any]:
        """Patch business identity. Body example:
            {
              "blackOwned": {"identityDeclaration": "SELF_IDENTIFIES_AS"},
              "womenOwned": {"identityDeclaration": "SELF_IDENTIFIES_AS"},
              "promotionsConsent": "PROMOTIONS_CONSENT_GIVEN_FOR_PROMOTIONS"
            }
        """
        before = None
        try:
            before = client.request("GET", f"accounts/v1/{acct}/businessIdentity")
        except Exception:
            pass
        params = {"updateMask": update_mask} if update_mask else None
        return client.request(
            "PATCH",
            f"accounts/v1/{acct}/businessIdentity",
            params=params,
            json_body=identity,
            op="update_business_identity",
            before=before,
        )

    # ---------------- Checkout settings ----------------

    @mcp.tool()
    def gmc_get_checkout_settings(program: str = "checkout") -> dict[str, Any]:
        """Get URI checkout settings.

        program: only `'checkout'` is supported by Merchant API v1 (this is the
        Buy-on-Google / URI checkout program, NOT free-listings or shopping-ads).
        """
        return client.request(
            "GET",
            f"accounts/v1/{acct}/programs/{program}/checkoutSettings",
        )

    @mcp.tool()
    def gmc_create_checkout_settings(
        checkout_settings: dict[str, Any], program: str = "checkout"
    ) -> dict[str, Any]:
        """Create URI checkout settings (program is always 'checkout' in v1).

        Body example:
            {
              "uriSettings": {
                "checkoutUriTemplate": "https://your-store.com/cart?items={item_ids}"
              }
            }
        """
        return client.request(
            "POST",
            f"accounts/v1/{acct}/programs/{program}/checkoutSettings",
            json_body=checkout_settings,
            op="create_checkout_settings",
        )

    @mcp.tool()
    def gmc_update_checkout_settings(
        checkout_settings: dict[str, Any],
        program: str = "checkout",
        update_mask: str | None = None,
    ) -> dict[str, Any]:
        """Patch URI checkout settings (program is always 'checkout' in v1)."""
        before = None
        try:
            before = client.request(
                "GET", f"accounts/v1/{acct}/programs/{program}/checkoutSettings"
            )
        except Exception:
            pass
        params = {"updateMask": update_mask} if update_mask else None
        return client.request(
            "PATCH",
            f"accounts/v1/{acct}/programs/{program}/checkoutSettings",
            params=params,
            json_body=checkout_settings,
            op="update_checkout_settings",
            before=before,
        )

    @mcp.tool()
    def gmc_delete_checkout_settings(program: str = "checkout") -> dict[str, Any]:
        """Delete URI checkout settings (program defaults to 'checkout')."""
        client.request(
            "DELETE",
            f"accounts/v1/{acct}/programs/{program}/checkoutSettings",
            op="delete_checkout_settings",
        )
        return {"deleted_program_checkout": program}

    # ---------------- Automatic improvements ----------------

    @mcp.tool()
    def gmc_get_automatic_improvements() -> dict[str, Any]:
        """Get current automatic-improvements settings (item updates, image, shipping, prices)."""
        return client.request("GET", f"accounts/v1/{acct}/automaticImprovements")

    @mcp.tool()
    def gmc_update_automatic_improvements(
        improvements: dict[str, Any], update_mask: str | None = None
    ) -> dict[str, Any]:
        """Toggle automatic improvements. Body example:
            {
              "itemUpdates": {"accountItemUpdatesSettings": {
                "allowPriceUpdates": True,
                "allowAvailabilityUpdates": True,
                "allowConditionUpdates": True,
                "allowStrictAvailabilityUpdates": True
              }},
              "imageImprovements": {"accountImageImprovementsSettings": {
                "allowAutomaticImageImprovements": True
              }},
              "shippingImprovements": {"allowShippingImprovements": True}
            }
        """
        before = None
        try:
            before = client.request("GET", f"accounts/v1/{acct}/automaticImprovements")
        except Exception:
            pass
        params = {"updateMask": update_mask} if update_mask else None
        return client.request(
            "PATCH",
            f"accounts/v1/{acct}/automaticImprovements",
            params=params,
            json_body=improvements,
            op="update_automatic_improvements",
            before=before,
        )

    # ---------------- Autofeed settings ----------------

    @mcp.tool()
    def gmc_get_autofeed_settings() -> dict[str, Any]:
        """Get autofeed (Google crawls your site to build a feed) settings."""
        return client.request("GET", f"accounts/v1/{acct}/autofeedSettings")

    @mcp.tool()
    def gmc_update_autofeed_settings(
        enable_products: bool, update_mask: str = "enableProducts"
    ) -> dict[str, Any]:
        """Enable / disable autofeed product crawling."""
        before = None
        try:
            before = client.request("GET", f"accounts/v1/{acct}/autofeedSettings")
        except Exception:
            pass
        return client.request(
            "PATCH",
            f"accounts/v1/{acct}/autofeedSettings",
            params={"updateMask": update_mask},
            json_body={"enableProducts": enable_products},
            op="update_autofeed_settings",
            before=before,
        )

    # ---------------- Account tax ----------------

    @mcp.tool()
    def gmc_get_account_tax() -> dict[str, Any]:
        """Get US account tax settings."""
        return client.request("GET", f"accounts/v1/{acct}/accountTax")

    @mcp.tool()
    def gmc_update_account_tax(
        tax_rules: list[dict[str, Any]], update_mask: str = "taxRules"
    ) -> dict[str, Any]:
        """Update US tax rules. Body example:
            [
              {"region": "US-CA", "useGoogleRate": True, "shippingTaxed": False},
              {"region": "US-NY", "ratePercent": 8.0, "shippingTaxed": True}
            ]
        """
        before = None
        try:
            before = client.request("GET", f"accounts/v1/{acct}/accountTax")
        except Exception:
            pass
        return client.request(
            "PATCH",
            f"accounts/v1/{acct}/accountTax",
            params={"updateMask": update_mask},
            json_body={"taxRules": tax_rules},
            op="update_account_tax",
            before=before,
        )

    # ---------------- Email preferences ----------------

    @mcp.tool()
    def gmc_get_email_preferences(email: str) -> dict[str, Any]:
        """Get email-notification preferences for a user.
        email: the user's email exactly as it appears in Account Access."""
        return client.request(
            "GET", f"accounts/v1/{acct}/users/{email}/emailPreferences"
        )

    @mcp.tool()
    def gmc_update_email_preferences(
        email: str, preferences: dict[str, Any], update_mask: str | None = None
    ) -> dict[str, Any]:
        """Update email preferences. preferences example:
            {"newsAndTips": "OPTED_IN"}  # or OPTED_OUT
        """
        before = None
        try:
            before = client.request(
                "GET", f"accounts/v1/{acct}/users/{email}/emailPreferences"
            )
        except Exception:
            pass
        params = {"updateMask": update_mask} if update_mask else None
        return client.request(
            "PATCH",
            f"accounts/v1/{acct}/users/{email}/emailPreferences",
            params=params,
            json_body=preferences,
            op="update_email_preferences",
            before=before,
        )

    # ---------------- Terms of Service ----------------

    @mcp.tool()
    def gmc_get_latest_tos(region_code: str = "US", kind: str = "MERCHANT_CENTER") -> dict[str, Any]:
        """Retrieve the latest TermsOfService document.

        kind: 'MERCHANT_CENTER' (default).
        """
        return client.request(
            "GET",
            f"termsOfService/v1/termsOfService:retrieveLatest",
            params={"regionCode": region_code, "kind": kind},
        )

    @mcp.tool()
    def gmc_list_tos_agreement_states(max_pages: int = 3) -> dict[str, Any]:
        """List the TOS agreement states for the current account."""
        items = list(
            client.paginate(
                "GET",
                f"accounts/v1/{acct}/termsOfServiceAgreementStates",
                items_key="termsOfServiceAgreementStates",
                max_pages=max_pages,
            )
        )
        return {"count": len(items), "states": items}

    @mcp.tool()
    def gmc_accept_tos(tos_name: str, agreement_state: str | None = None) -> dict[str, Any]:
        """Accept a TermsOfService.

        tos_name: full name of the TermsOfService resource (from gmc_get_latest_tos.name).
        agreement_state: optional name of an existing agreement-state resource.
        """
        params = {"name": tos_name}
        if agreement_state:
            params["agreementState"] = agreement_state
        return client.request(
            "POST",
            f"termsOfService/v1/{tos_name}:accept",
            params=params,
            op="accept_tos",
        )
