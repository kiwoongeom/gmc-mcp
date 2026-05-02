"""Smoke-test that your credentials work and the API is reachable.

Usage:
    python examples/quickstart.py
"""

from __future__ import annotations

from gmc_mcp.audit import AuditLog
from gmc_mcp.auth import load_auth
from gmc_mcp.client import MerchantClient
from gmc_mcp.config import load_config


def main() -> None:
    config = load_config()
    auth = load_auth(
        service_account_key=config.service_account_key,
        oauth_token=config.oauth_token,
    )
    audit = AuditLog(config.audit_log)

    with MerchantClient(config, auth, audit) as client:
        print(f"Account: {config.account_id}  Auth: {auth.account_label}")

        account = client.request("GET", f"accounts/v1/{client.account_path()}")
        print(f"Account name : {account.get('name')}")
        print(f"Time zone    : {(account.get('timeZone') or {}).get('id')}")

        print("\nFirst 5 products:")
        page = client.request(
            "GET",
            f"products/v1/{client.account_path()}/products",
            params={"pageSize": 5},
        )
        for p in page.get("products", []):
            attrs = p.get("productAttributes") or {}
            print(f"  - {p.get('offerId', ''):42}  {attrs.get('title', '')}")

        issues_page = client.request(
            "GET",
            f"accounts/v1/{client.account_path()}/issues",
            params={"languageCode": "en"},
        )
        n_issues = len(issues_page.get("accountIssues") or [])
        print(f"\nAccount issues: {n_issues}")


if __name__ == "__main__":
    main()
