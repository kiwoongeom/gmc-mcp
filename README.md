# Google Merchant Center MCP (`gmc-mcp`)

[![PyPI](https://img.shields.io/pypi/v/gmc-mcp.svg)](https://pypi.org/project/gmc-mcp/)
[![CI](https://github.com/kiwoongeom/gmc-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/kiwoongeom/gmc-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/gmc-mcp.svg)](https://pypi.org/project/gmc-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

> **The first MCP server for Google Merchant Center (GMC).**
> Drive your Google Shopping feed, products, inventory, Reports, promotions,
> returns, and account configuration in natural language from Claude Desktop,
> Claude Code, or any MCP-compatible client.

Built on **Merchant API v1** (replaces Content API for Shopping; v1beta was
discontinued 2026-02-28). Safe by default: every write is recorded to an
append-only audit log with `before` snapshots, dry-run is one toggle away, and
destructive bulk operations require an explicit `confirm` parameter.

## Why this exists

Google Merchant Center (GMC) is what powers Google Shopping listings, Free
Listings, Shopping Ads, Buy on Google checkout, YouTube Shopping, and more.
Until now there was no MCP server for it — managing a feed of thousands of
products through the GMC web UI is tedious, and writing one-off Python scripts
against the Merchant API REST endpoints is slow.

This package gives Claude (or any MCP client) **126 tools** that map directly
onto the Merchant API v1 surface, so you can do things like:

- *"Show me every disapproved product, grouped by issue code."*
- *"Bump US prices 5% on these 40 SKUs."*
- *"Which products had impressions but zero clicks last week?"*
- *"Roll back audit ID 8fc8dc42… — that update broke something."*
- *"Compare this Shopify CSV against my GMC feed; what's missing?"*

## What's exposed

**126 tools across 19 modules + 4 meta tools.**

| Module | Tools |
|---|---|
| **products** | `gmc_list_products`, `gmc_get_product`, `gmc_insert_product`, `gmc_update_product`, `gmc_delete_product`, `gmc_bulk_delete_products`, `gmc_list_disapproved_products` |
| **inventory** | `gmc_update_regional_inventory`, `gmc_update_local_inventory`, `gmc_list_regional_inventories`, `gmc_list_local_inventories` |
| **issues** | `gmc_list_account_issues`, `gmc_get_product_status`, `gmc_summarize_product_issues` |
| **reports** | `gmc_query_report`, `gmc_product_performance`, `gmc_price_competitiveness`, `gmc_best_sellers`, `gmc_zero_click_products`, `gmc_revenue_by_brand`, `gmc_category_performance`, `gmc_competitive_visibility_top_merchants`, `gmc_price_insights`, `gmc_demoted_products` |
| **promotions** | `gmc_list_promotions`, `gmc_get_promotion`, `gmc_insert_promotion` |
| **accounts** | `gmc_get_account`, `gmc_get_business_info`, `gmc_update_business_info`, `gmc_list_users`, `gmc_add_user`, `gmc_remove_user`, `gmc_get_shipping_settings`, `gmc_update_shipping_settings`, `gmc_list_programs`, `gmc_request_program_review`, `gmc_get_program_review` |
| **regions** | `gmc_list_regions`, `gmc_get_region`, `gmc_create_region`, `gmc_update_region`, `gmc_delete_region` |
| **notifications** | `gmc_list_subscriptions`, `gmc_subscribe`, `gmc_unsubscribe` |
| **feeds** | `gmc_list_datasources`, `gmc_get_datasource`, `gmc_create_supplemental_feed`, `gmc_create_primary_feed`, `gmc_delete_datasource`, `gmc_fetch_datasource` |
| **return_policies** | `gmc_list_return_policies`, `gmc_get_return_policy`, `gmc_create_return_policy`, `gmc_update_return_policy`, `gmc_delete_return_policy` |
| **homepage** | `gmc_get_homepage`, `gmc_update_homepage`, `gmc_claim_homepage`, `gmc_unclaim_homepage` |
| **account_config** | `gmc_get_business_identity`, `gmc_update_business_identity`, `gmc_get_checkout_settings`, `gmc_create_checkout_settings`, `gmc_update_checkout_settings`, `gmc_delete_checkout_settings`, `gmc_get_automatic_improvements`, `gmc_update_automatic_improvements`, `gmc_get_autofeed_settings`, `gmc_update_autofeed_settings`, `gmc_get_account_tax`, `gmc_update_account_tax`, `gmc_get_email_preferences`, `gmc_update_email_preferences`, `gmc_get_latest_tos`, `gmc_list_tos_agreement_states`, `gmc_accept_tos` |
| **quotas** | `gmc_list_quotas` |
| **reviews** | `gmc_list_merchant_reviews`, `gmc_get_merchant_review`, `gmc_insert_merchant_review`, `gmc_delete_merchant_review`, `gmc_list_product_reviews`, `gmc_get_product_review`, `gmc_insert_product_review`, `gmc_delete_product_review` |
| **conversions** | `gmc_list_conversion_sources`, `gmc_get_conversion_source`, `gmc_create_conversion_source`, `gmc_update_conversion_source`, `gmc_delete_conversion_source`, `gmc_undelete_conversion_source` |
| **omnichannel** | `gmc_list_omnichannel_settings`, `gmc_get_omnichannel_settings`, `gmc_create_omnichannel_settings`, `gmc_update_omnichannel_settings`, `gmc_request_inventory_verification`, `gmc_link_gbp_account`, `gmc_list_gbp_accounts` |
| **lfp** | `gmc_lfp_list_stores`, `gmc_lfp_get_store`, `gmc_lfp_insert_store`, `gmc_lfp_delete_store`, `gmc_lfp_insert_inventory`, `gmc_lfp_insert_sale`, `gmc_lfp_get_merchant_state` |
| **mca** | `gmc_list_relationships`, `gmc_get_relationship`, `gmc_update_relationship`, `gmc_create_aggregation`, `gmc_delete_aggregation`, `gmc_list_account_services`, `gmc_propose_account_service`, `gmc_approve_account_service`, `gmc_reject_account_service` |
| **bulk** | `gmc_bulk_update_regional_prices`, `gmc_bulk_set_availability` |
| **diagnostics** | `gmc_health_check`, `gmc_rollback`, `gmc_export_all`, `gmc_diff_with_shopify` |
| **meta** | `gmc_describe_server`, `gmc_audit_lookup`, `gmc_audit_tail`, `gmc_set_dry_run` |

CLI also exposes: `gmc-mcp run`, `auth-init`, `register-gcp`, `webhook`, `describe`, `version`.

## Install

```bash
pip install gmc-mcp
```

For development:

```bash
git clone https://github.com/kiwoongeom/gmc-mcp
cd gmc-mcp
pip install -e ".[dev,test]"
pre-commit install
```

## Quick start

### 1. Enable the Merchant API and create a service account

1. [console.cloud.google.com](https://console.cloud.google.com) → create / pick a project.
2. **APIs & Services → Library** → enable **Merchant API**.
3. **IAM & Admin → Service Accounts → Create service account** named `gmc-mcp`.
4. Open the new service account → **Keys → Add key → Create new key → JSON**. Save it somewhere safe.

### 2. Add the service account to your Merchant Center

1. [merchants.google.com](https://merchants.google.com) → top-right gear → **Account access → People**.
2. **Add user** → enter the `gmc-mcp@PROJECT.iam.gserviceaccount.com` email → grant **Admin**.
3. Note the 10-digit Merchant Center ID in the top-right.

### 3. Configure

```bash
cp .env.example .env
# edit:
#   GMC_ACCOUNT_ID=1234567890
#   GMC_SERVICE_ACCOUNT_KEY=/abs/path/to/service-account.json
```

### 4. One-time GCP registration

Required before any v1 Merchant API call works for a new project.

```bash
gmc-mcp register-gcp --developer-email you@example.com
```

### 5. Smoke-test

```bash
gmc-mcp describe              # prints the resolved config
python examples/quickstart.py  # makes one read against the Merchant API
```

### 6. Wire into Claude

Drop this into `%APPDATA%/Claude/claude_desktop_config.json` (Desktop) or `~/.claude/settings.json` (Code):

```json
{
  "mcpServers": {
    "gmc": {
      "command": "gmc-mcp",
      "args": ["run"],
      "env": {
        "GMC_ACCOUNT_ID": "1234567890",
        "GMC_SERVICE_ACCOUNT_KEY": "/abs/path/to/service-account.json"
      }
    }
  }
}
```

Restart Claude. Ask: *"What account am I connected to?"* — it should call `gmc_describe_server`.

## OAuth instead of a service account

For acting on behalf of an end user (e.g. multi-tenant SaaS):

```bash
# 1. In GCP, create OAuth client credentials (type: Desktop), download client_secret.json.
gmc-mcp auth-init --client-secrets ./client_secret.json
# follow the browser flow; a token JSON is saved to secrets/oauth-token.json.

# 2. Use it
export GMC_OAUTH_TOKEN=./secrets/oauth-token.json
gmc-mcp run
```

## Transports

```bash
gmc-mcp run                              # stdio (Claude Desktop default)
gmc-mcp run --transport sse --port 8000  # SSE / HTTP (remote, Docker, hosted)
```

Or via Docker:

```bash
docker build -t gmc-mcp .
docker run --rm -p 8000:8000 \
    -e GMC_ACCOUNT_ID=1234567890 \
    -v $PWD/secrets:/secrets \
    -e GMC_SERVICE_ACCOUNT_KEY=/secrets/service-account.json \
    gmc-mcp
```

## Audit log + rollback

Every write logs a JSONL entry to `GMC_AUDIT_LOG` (default: `./logs/audit.jsonl`). Each entry contains:

- `audit_id` — UUID for lookup
- `op`, `method`, `url`, `request_body`, `response_status`, `response_body`
- `before` — pre-write snapshot when the tool fetched it (used by `update_*` and `delete_*`)
- `dry_run` — whether the request was actually sent

Inspect from inside Claude:

```
> Show me my last 5 GMC writes.
[gmc_audit_tail(limit=5) → ...]

> Look up audit ID abc123.
[gmc_audit_lookup(audit_id="abc123") → ...]

> Roll back audit ID abc123, that update was wrong.
[gmc_rollback(audit_id="abc123", confirm="ROLLBACK") → ...]
```

## Dry-run

Two ways to enable:

```bash
GMC_DRY_RUN=true gmc-mcp run
```

```
> Set dry-run on and update the price of SKU1 to $19.99.
[gmc_set_dry_run(enabled=True) → ok]
[gmc_update_regional_inventory(...) → {"_dry_run": true, ...}]
```

Reads always go through; only writes are skipped.

## Reports query examples

Paste into `gmc_query_report`:

```sql
-- Top 50 by clicks last 7 days
SELECT offer_id, title, clicks, impressions, ctr
FROM product_performance_view
WHERE date BETWEEN '2026-04-23' AND '2026-04-30'
ORDER BY clicks DESC LIMIT 50

-- Disapproved products with reason codes
SELECT id, offer_id, title, item_issues
FROM product_view
WHERE aggregated_reporting_context_status = 'NOT_ELIGIBLE_OR_DISAPPROVED'

-- You're priced higher than the benchmark
SELECT offer_id, title, price, benchmark_price
FROM price_competitiveness_product_view
WHERE price > benchmark_price LIMIT 100
```

## Configuration reference

All config is via env vars (or `.env`). CLI flags `--transport`, `--host`, `--port`, `--env` override.

| Var | Required | Default | Notes |
|---|---|---|---|
| `GMC_ACCOUNT_ID` | yes | — | 10-digit Merchant Center ID |
| `GMC_SERVICE_ACCOUNT_KEY` | one of | — | Path to service-account JSON |
| `GMC_OAUTH_TOKEN` | one of | — | Path to OAuth token JSON |
| `GMC_SUBACCOUNT_ID` | no | — | When using an MCA |
| `GMC_AUDIT_LOG` | no | `./logs/audit.jsonl` | Append-only JSONL |
| `GMC_PAGE_SIZE` | no | `100` | Default list page size |
| `GMC_TIMEOUT` | no | `30` | Per-request seconds |
| `GMC_DRY_RUN` | no | `false` | Writes go to audit only |
| `GMC_LOG_LEVEL` | no | `INFO` | DEBUG/INFO/WARNING/ERROR |
| `GMC_TRANSPORT` | no | `stdio` | `stdio` or `sse` |
| `GMC_HOST` | no | `127.0.0.1` | SSE only |
| `GMC_PORT` | no | `8000` | SSE only |

## Architecture

```
Claude (any MCP client)
    │  JSON-RPC over stdio or SSE
    ▼
gmc-mcp server  ──►  audit.jsonl
    │
    │  HTTP + Bearer token
    ▼
merchantapi.googleapis.com  ──►  Google Merchant Center
```

- `auth.py` — `ServiceAccountAuth` and `OAuthUserAuth` share an `Auth` protocol.
- `client.py` — single `MerchantClient` with retries (5x w/ jitter), pagination helper, and write-audit hook.
- `tools/*.py` — each module exposes a `register(mcp, client)` that registers `@mcp.tool()` functions.
- `audit.py` — append-only JSONL, lookup by ID, supports `before` snapshots.
- `cli.py` — `gmc-mcp run | auth-init | register-gcp | webhook | describe | version`.

## Testing

```bash
pytest                       # 100% offline; uses respx to mock HTTP
pytest --cov=gmc_mcp         # with coverage
ruff check src tests
mypy src/gmc_mcp
```

## Roadmap

- v0.3: webhook handler scaffolding (auto-respond to `gmc_subscribe` callbacks)
- v0.3: native Merchant API v1 GA migration when Google releases it
- v0.4: BigQuery export of Reports queries
- v0.4: rule-based auto-fixers ("on disapproval, retry with corrected attribute")

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). PRs and issues welcome — this is the
first MCP for Google Merchant Center, so there's a lot of room for community
input on which workflows deserve dedicated tools.

## License

MIT — see [LICENSE](LICENSE).

---

*Search keywords: Google Merchant Center MCP, GMC MCP, Merchant API MCP,
Google Shopping MCP, Shopping Ads MCP, free listings MCP, Claude Desktop
Google Merchant Center, MCP for ecommerce, Shopify Google Merchant Center
automation.*
