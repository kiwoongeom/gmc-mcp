"""Multi-Client-Account (MCA) features: relationships, aggregation, services.

For agencies and SaaS that manage multiple client Merchant Center accounts
under one parent."""

from __future__ import annotations

import contextlib
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
                f"accounts/v1/{acct}/relationships",
                items_key="accountRelationships",
                max_pages=max_pages,
            )
        )
        return {"count": len(items), "relationships": items}

    @mcp.tool()
    def gmc_get_relationship(relationship_id: str) -> dict[str, Any]:
        return client.request("GET", f"accounts/v1/{acct}/relationships/{relationship_id}")

    @mcp.tool()
    def gmc_update_relationship(
        relationship_id: str,
        relationship: dict[str, Any],
        update_mask: str | None = None,
    ) -> dict[str, Any]:
        before = None
        with contextlib.suppress(Exception):
            before = client.request("GET", f"accounts/v1/{acct}/relationships/{relationship_id}")
        params = {"updateMask": update_mask} if update_mask else None
        return client.request(
            "PATCH",
            f"accounts/v1/{acct}/relationships/{relationship_id}",
            params=params,
            json_body=relationship,
            op="update_relationship",
            before=before,
        )

    # ---- Aggregation ----

    @mcp.tool()
    def gmc_create_aggregation(provider_account: str) -> dict[str, Any]:
        """Propose aggregation under a provider; provider approval may be required.

        provider_account: full name like 'accounts/PROVIDER_ID'.
        """
        provider = provider_account.replace("accounts/", "providers/", 1)
        if not provider.startswith("providers/"):
            raise ValueError("provider_account must be accounts/{id} or providers/{id}")
        return client.request(
            "POST",
            f"accounts/v1/{acct}/services:propose",
            json_body={"provider": provider, "accountService": {"accountAggregation": {}}},
            op="create_aggregation",
        )

    @mcp.tool()
    def gmc_delete_aggregation() -> dict[str, Any]:
        """Reject existing aggregation services; return not_configured if none exist."""
        services = list(
            client.paginate("GET", f"accounts/v1/{acct}/services", items_key="services")
        )
        removed = []
        for service in services:
            if "accountAggregation" in service:
                client.request(
                    "POST",
                    f"accounts/v1/{service['name']}:reject",
                    op="delete_aggregation",
                    before=service,
                )
                removed.append(service["name"])
        return {
            "deleted_aggregation_for": acct,
            "services": removed,
            "status": ("dry_run" if client.config.dry_run else "rejected")
            if removed
            else "not_configured",
            "dry_run": client.config.dry_run,
        }

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
    def gmc_propose_account_service(provider: str, service_type: str) -> dict[str, Any]:
        """Propose a service relationship (e.g. account management delegation).

        provider: full account name like 'accounts/PROVIDER_ID'.
        service_type: 'ACCOUNT_MANAGEMENT' | 'ACCOUNT_AGGREGATION' | 'CAMPAIGNS_MANAGEMENT'
        """
        types = {
            "ACCOUNT_MANAGEMENT": "accountManagement",
            "ACCOUNT_AGGREGATION": "accountAggregation",
            "CAMPAIGNS_MANAGEMENT": "campaignsManagement",
            "PRODUCTS_MANAGEMENT": "productsManagement",
        }
        if service_type not in types:
            raise ValueError("Unsupported service_type; choose " + ", ".join(types))
        return client.request(
            "POST",
            f"accounts/v1/{acct}/services:propose",
            json_body={"provider": provider, "accountService": {types[service_type]: {}}},
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
