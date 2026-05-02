"""Export all disapproved products to a CSV with issue codes.

Usage:
    python examples/audit_disapproved.py [output.csv]
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from gmc_mcp.audit import AuditLog
from gmc_mcp.auth import load_auth
from gmc_mcp.client import MerchantClient
from gmc_mcp.config import load_config

QUERY = (
    "SELECT offer_id, id, title, aggregated_reporting_context_status, item_issues "
    "FROM product_view "
    "WHERE aggregated_reporting_context_status != 'ELIGIBLE'"
)


def main(output: Path) -> None:
    config = load_config()
    auth = load_auth(
        service_account_key=config.service_account_key,
        oauth_token=config.oauth_token,
    )
    with MerchantClient(config, auth, AuditLog(config.audit_log)) as client:
        rows: list[dict[str, str]] = []
        body: dict = {"query": QUERY}
        path = f"reports/v1/{client.account_path()}/reports:search"
        while True:
            payload = client.request("POST", path, json_body=body)
            for item in payload.get("results", []) or []:
                pv = item.get("productView", {})
                issues = pv.get("itemIssues") or []
                rows.append(
                    {
                        "offer_id": pv.get("offerId", ""),
                        "title": pv.get("title", ""),
                        "status": pv.get("aggregatedReportingContextStatus", ""),
                        "issue_codes": "|".join(
                            issue.get("code", "") for issue in issues
                        ),
                        "issue_count": str(len(issues)),
                    }
                )
            token = payload.get("nextPageToken")
            if not token:
                break
            body = {"query": QUERY, "pageToken": token}

    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["offer_id", "title", "status", "issue_codes", "issue_count"]
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output}")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("disapproved.csv")
    main(out)
