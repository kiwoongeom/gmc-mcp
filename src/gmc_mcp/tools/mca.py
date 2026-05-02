"""Multi-Client-Account (MCA) features: relationships, aggregation, services.

For agencies and SaaS that manage multiple client Merchant Center accounts
under one parent."""

from __future__ import annotations

from typing import Any

from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    # ---- Relationships ----

    @mcp.tool()
    def gmc_list_relationships(max_pages: int = 5) -> dict[str, Any]:
        """List parent / child / aggregator relationships involving this account."""
        items = list(
            client.paginate(
                "GET",
                f"accounts/v1/{acct}/accountRelationships",
                items_key="accountRelationships",
                max_pages=max_pages,
            )
        )
        return {"count": len(items), "relationships": items}

    @mcp.tool()
    def gmc_get_relationship(relationship_id: str) -> dict[str, Any]:
        return client.request(
            "GET", f"accounts/v1/{acct}/accountRelationships/{relationship_id}"
        )

    @mcp.tool()
    def gmc_update_relationship(
        relationship_id: str,
        relationship: dict[str, Any],
        update_mask: str | None = None,
    ) -> dict[str, Any]:
        before = None
        try:
            before = client.request(
                "GET", f"accounts/v1/{acct}/accountRelationships/{relationship_id}"
            )
        except Exception:
            pass
        params = {"updateMask": update_mask} if update_mask else None
        return client.request(
            "PATCH",
            f"accounts/v1/{acct}/accountRelationships/{relationship_id}",
            params=params,
            json_body=relationship,
            op="update_relationship",
            before=before,
        )

    # ---- Aggregation ----

    @mcp.tool()
    def gmc_create_aggregation(provider_account: str) -> dict[str, Any]:
        """Aggregate this account under a provider (typically an MCA/aggregator).

        provider_account: full name like 'accounts/PROVIDER_ID'.
        """
        return client.request(
            "POST",
            f"accounts/v1/{acct}/accountAggregation:create",
            json_body={"providerAccount": provider_account},
            op="create_aggregation",
        )

    @mcp.tool()
    def gmc_delete_aggregation() -> dict[str, Any]:
        """Remove the current aggregation from a provider."""
        client.request(
            "DELETE",
            f"accounts/v1/{acct}/accountAggregation",
            op="delete_aggregation",
        )
        return {"deleted_aggregation_for": acct}

    # ---- Account services (delegation) ----

    @mcp.tool()
    def gmc_list_account_services(max_pages: int = 5) -> dict[str, Any]:
        """List service relationships (where someone delegates account management)."""
        items = list(
            client.paginate(
                "GET",
                f"accounts/v1/{acct}/services",
                items_key="services",
                max_pages=max_pages,
            )
        )
        return {"count": len(items), "services": items}

    @mcp.tool()
    def gmc_propose_account_service(
        provider: str, service_type: str
    ) -> dict[str, Any]:
        """Propose a service relationship (e.g. account management delegation).

        provider: full account name like 'accounts/PROVIDER_ID'.
        service_type: 'ACCOUNT_MANAGEMENT' | 'ACCOUNT_AGGREGATION' | 'CAMPAIGNS_MANAGEMENT'
        """
        return client.request(
            "POST",
            f"accounts/v1/{acct}/services:propose",
            json_body={"provider": provider, "type": service_type},
            op="propose_service",
        )

    @mcp.tool()
    def gmc_approve_account_service(service_id: str) -> dict[str, Any]:
        """Approve a proposed service relationship."""
        return client.request(
            "POST",
            f"accounts/v1/{acct}/services/{service_id}:approve",
            op="approve_service",
        )

    @mcp.tool()
    def gmc_reject_account_service(service_id: str) -> dict[str, Any]:
        """Reject a proposed service relationship."""
        return client.request(
            "POST",
            f"accounts/v1/{acct}/services/{service_id}:reject",
            op="reject_service",
        )
