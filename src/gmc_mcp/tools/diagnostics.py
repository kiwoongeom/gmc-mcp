"""Diagnostic & utility tools: rollback, health-check, export, Shopify diff."""

from __future__ import annotations

import csv
import json
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ..audit import AuditLog
from ..client import MerchantClient


def register(mcp, client: MerchantClient) -> None:
    acct = client.account_path()

    @mcp.tool()
    def gmc_health_check() -> dict[str, Any]:
        """Probe core endpoints and report which respond. Useful first call after setup."""
        checks: list[dict[str, Any]] = []

        def probe(
            name: str,
            method: str,
            path: str,
            params: dict | None = None,
            json_body: Any | None = None,
        ) -> None:
            t0 = time.time()
            try:
                client.request(method, path, params=params, json_body=json_body)
                checks.append({"check": name, "ok": True, "ms": int((time.time() - t0) * 1000)})
            except Exception as e:
                checks.append(
                    {"check": name, "ok": False, "ms": int((time.time() - t0) * 1000), "error": str(e)[:200]}
                )

        probe("account", "GET", f"accounts/v1/{acct}")
        probe("issues", "GET", f"accounts/v1/{acct}/issues", {"languageCode": "en"})
        probe("products", "GET", f"products/v1/{acct}/products", {"pageSize": 1})
        probe("data_sources", "GET", f"datasources/v1/{acct}/dataSources")
        probe(
            "reports",
            "POST",
            f"reports/v1/{acct}/reports:search",
            json_body={"query": "SELECT id FROM product_view LIMIT 1"},
        )
        probe("homepage", "GET", f"accounts/v1/{acct}/homepage")
        probe("automatic_improvements", "GET", f"accounts/v1/{acct}/automaticImprovements")

        ok = sum(1 for c in checks if c["ok"])
        return {"ok": ok, "total": len(checks), "checks": checks}

    @mcp.tool()
    def gmc_rollback(audit_id: str, confirm: str = "") -> dict[str, Any]:
        """Roll back a previous write using its audit `before` snapshot.

        confirm: must be 'ROLLBACK' (case-sensitive).
        Only works for ops that captured a `before` state (update_*, delete_*, etc.)
        """
        if confirm != "ROLLBACK":
            return {
                "error": "Refused: pass confirm='ROLLBACK' (case-sensitive) to execute.",
                "audit_id": audit_id,
            }

        log = AuditLog(client.config.audit_log)
        entry = log.find(audit_id)
        if not entry:
            return {"error": f"Audit ID not found: {audit_id}"}
        before = entry.get("before")
        if not before:
            return {
                "error": f"Audit entry has no `before` snapshot — cannot rollback.",
                "op": entry.get("op"),
            }
        op = entry.get("op", "")
        url = entry.get("url", "")
        method = entry.get("method", "")

        # Strategy by op type
        if op in {"delete_product", "bulk_delete_product"} and "productInputs" in url:
            ds = before.get("dataSource")
            if not ds:
                return {"error": "Original product had no dataSource; cannot recreate."}
            return client.request(
                "POST",
                f"products/v1/{acct}/productInputs:insert",
                params={"dataSource": ds},
                json_body=before,
                op=f"rollback_{op}",
            )

        if op in {"delete_datasource"} and "dataSources" in url:
            return client.request(
                "POST",
                f"datasources/v1/{acct}/dataSources",
                json_body=before,
                op=f"rollback_{op}",
            )

        if op.startswith("update_") and method == "PATCH":
            # Re-PATCH with the before snapshot
            relative = url.split("merchantapi.googleapis.com/")[-1]
            return client.request(
                "PATCH", relative, json_body=before, op=f"rollback_{op}"
            )

        return {
            "error": f"Don't know how to rollback op={op}. before snapshot: {json.dumps(before)[:300]}"
        }

    @mcp.tool()
    def gmc_export_all(output_dir: str, max_per_resource: int = 5000) -> dict[str, Any]:
        """Dump products, issues, datasources, return policies, account info to JSON files.

        Returns a manifest of paths and counts. One file per resource type.
        """
        out = Path(output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)

        manifest: dict[str, Any] = {"output_dir": str(out), "resources": {}}

        def dump_paginated(name: str, path: str, key: str) -> None:
            items: list[Any] = []
            params: dict[str, Any] = {"pageSize": 250}
            for _ in range(max_per_resource // 250 + 1):
                p = client.request("GET", path, params=params)
                items.extend(p.get(key, []) or [])
                token = p.get("nextPageToken")
                if not token or len(items) >= max_per_resource:
                    break
                params["pageToken"] = token
            f = out / f"{name}.json"
            f.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
            manifest["resources"][name] = {"path": str(f), "count": len(items)}

        def dump_single(name: str, path: str, params: dict | None = None) -> None:
            try:
                payload = client.request("GET", path, params=params)
            except Exception as e:
                manifest["resources"][name] = {"error": str(e)[:200]}
                return
            f = out / f"{name}.json"
            f.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            manifest["resources"][name] = {"path": str(f)}

        dump_single("account", f"accounts/v1/{acct}")
        dump_single("business_info", f"accounts/v1/{acct}/businessInfo")
        dump_paginated(
            "account_issues",
            f"accounts/v1/{acct}/issues",
            "accountIssues",
        )
        dump_paginated("products", f"products/v1/{acct}/products", "products")
        dump_paginated(
            "data_sources",
            f"datasources/v1/{acct}/dataSources",
            "dataSources",
        )
        dump_paginated(
            "return_policies",
            f"accounts/v1/{acct}/onlineReturnPolicies",
            "onlineReturnPolicies",
        )
        dump_paginated("users", f"accounts/v1/{acct}/users", "users")
        dump_paginated(
            "promotions",
            f"promotions/v1/{acct}/promotions",
            "promotions",
        )
        return manifest

    @mcp.tool()
    def gmc_diff_with_shopify(
        shopify_csv: str,
        offer_id_column: str = "Variant SKU",
        max_pages: int = 50,
    ) -> dict[str, Any]:
        """Compare a Shopify product CSV (exported from admin) against GMC products.

        Reports which offer_ids exist only in Shopify, only in GMC, or in both.
        Works on the SKU/handle column — pass `offer_id_column` to override.
        """
        path = Path(shopify_csv).expanduser().resolve()
        if not path.exists():
            return {"error": f"Shopify CSV not found: {path}"}

        shopify_ids: set[str] = set()
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                v = (row.get(offer_id_column) or "").strip()
                if v:
                    shopify_ids.add(v)

        gmc_ids: set[str] = set()
        params: dict[str, Any] = {"pageSize": 250}
        for _ in range(max_pages):
            page = client.request("GET", f"products/v1/{acct}/products", params=params)
            for p in page.get("products", []) or []:
                oid = p.get("offerId")
                if oid:
                    gmc_ids.add(oid)
            token = page.get("nextPageToken")
            if not token:
                break
            params["pageToken"] = token

        only_shopify = shopify_ids - gmc_ids
        only_gmc = gmc_ids - shopify_ids
        both = shopify_ids & gmc_ids
        return {
            "shopify_count": len(shopify_ids),
            "gmc_count": len(gmc_ids),
            "in_both": len(both),
            "only_in_shopify": sorted(only_shopify)[:200],
            "only_in_gmc": sorted(only_gmc)[:200],
            "only_in_shopify_count": len(only_shopify),
            "only_in_gmc_count": len(only_gmc),
        }
