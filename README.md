<!-- mcp-name: io.github.kiwoongeom/gmc-mcp -->

# Google Merchant Center MCP (GMC MCP)

[![PyPI](https://img.shields.io/pypi/v/gmc-mcp.svg)](https://pypi.org/project/gmc-mcp/)
[![Downloads](https://static.pepy.tech/badge/gmc-mcp)](https://pepy.tech/projects/gmc-mcp)
[![Downloads/month](https://static.pepy.tech/badge/gmc-mcp/month)](https://pepy.tech/projects/gmc-mcp)
[![GitHub stars](https://img.shields.io/github/stars/kiwoongeom/gmc-mcp?style=social)](https://github.com/kiwoongeom/gmc-mcp/stargazers)
[![CI](https://github.com/kiwoongeom/gmc-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/kiwoongeom/gmc-mcp/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/gmc-mcp.svg)](https://pypi.org/project/gmc-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

> **Manage Google Merchant Center from your AI assistant.**
> Google Merchant Center MCP (GMC MCP) connects Claude Desktop, Claude Code,
> and other MCP-compatible clients directly to Google's Merchant API v1.
> Inspect product issues, query Shopping reports, update inventory, and manage
> account operations with **134 tools** in one self-hosted Python package.

`gmc-mcp` is MIT-licensed and available as
[Google Merchant Center MCP (GMC MCP) on PyPI](https://pypi.org/project/gmc-mcp/).
Run it locally or on your own server, using your own Google credentials.
No hosted connector is required.

## What you can do

| Workflow | Capabilities |
|---|---|
| Product catalog | List, inspect, insert, update, and delete products; manage product inputs and data sources. |
| Feed diagnostics | Find disapproved products, summarize product issues, and inspect account and feed status. |
| Shopping reports | Query Merchant Center reports and inspect product performance, price benchmarks, and best sellers where the account is eligible. |
| Inventory and bulk operations | Update regional/local inventory, prices, and availability across products. |
| Account operations | Manage promotions, returns, shipping settings, users, regions, and other Merchant Center settings. |
| Auditing and recovery | Record writes in a local JSONL audit log and roll back supported operations when a prior snapshot is available. |
| Storefront policy review | Inspect linked policies and contact information, prioritize fixes, draft an appeal and persist weekly monitoring reports. |

## Built for day-to-day operations

- **Direct Merchant API v1 access.** Use your own Merchant Center account;
  Google permissions and report eligibility apply to each operation.
- **Dry-run before making changes.** Enable `GMC_DRY_RUN=true` to intercept
  and audit writes while product reads and read-only Reports queries still
  reach Google. Destructive bulk operations require explicit confirmation.
- **An audit trail you control.** Inspect request outcomes and captured
  `before` snapshots. Rollback is available for supported changes with the
  required snapshot; it is not a universal undo for every API action.
- **Flexible authentication and clients.** Service-account or OAuth user
  credentials, stdio for desktop clients, and SSE for self-hosted deployments.
- **Standard Python distribution.** Install with `pip install gmc-mcp` or run
  with `uvx gmc-mcp run`; Python 3.10+ and an MIT license.

## Verified operation

The release verification covers the installed package, MCP startup and tool
registration, and live read-only Google Merchant API requests:

- **MCP stdio initialization and all 134 tools registered** in the local 0.3.0 integration check.
- **Live product listing and Reports queries succeeded**, including a Reports
  query with dry-run enabled that returned real account data.
- The **53-test 0.2.7 baseline** is retained, with additional policy and monitoring tests covering public-network restrictions, incomplete audits, evidence files, weekly cadence and draft generation. Baseline coverage includes pagination, API error
  propagation, auditing, and continued interception of writes in dry-run mode.
- The 0.2.7 **CI checks passed on Linux, Windows, and macOS**, across Python 3.10–3.13, with
  Ruff lint/format checks and mypy type checking.

The live checks exercise product listing and report queries. They do not
constitute live validation of every tool or permission combination. Writes
were not executed against the live account during release verification.

## Example requests

- "Show me every disapproved product, grouped by issue code."
- "Which products had impressions but zero clicks last week?"
- "Enable dry-run, then preview a regional inventory update."
- "Look up this audit entry and show the captured previous state."

## What's exposed

**134 registered tools, including 8 policy-audit tools and 4 server and audit-control tools.**

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

Get the Python package and release files from
[Google Merchant Center MCP (GMC MCP) on PyPI](https://pypi.org/project/gmc-mcp/).
This permanent package URL always points to the latest published release.

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

`GMC_DRY_RUN=true` blocks writes, but still sends read requests, including the
read-only Reports API `POST reports:search`. Report tools return real data;
Merchant API errors are surfaced to the caller rather than reported as zero rows.

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

## Storefront policy audit and weekly monitoring (0.3.0)

Eight new MCP tools preserve the existing 126-tool interface:

| Tool | Purpose |
|---|---|
| `gmc_run_policy_audit(url, max_pages=8, include_account=True)` | Fetch public HTTPS pages and account issues, save evidence, and evaluate storefront text. |
| `gmc_list_policy_audits()` / `gmc_get_policy_audit(audit_id)` | Retrieve persisted audit history and full raw download paths. |
| `gmc_get_policy_fix_plan(audit_id)` | Prioritize failed and unknown checks with verification steps. |
| `gmc_generate_policy_appeal(audit_id, merchant_statement="")` | Save an appeal **draft** with unresolved checks and Google-reported issues; never submit it. |
| `gmc_set_policy_monitoring(url, enabled=True)` | Save a weekly schedule; the first audit is due immediately. |
| `gmc_get_policy_monitoring()` | Read next-due times, last reports, risk changes and local alerts. |
| `gmc_run_policy_monitors()` | Execute due monitors on demand. |

**What is checked:** homepage reachability; observed contact methods; linked
business/About, return/refund, delivery, terms and privacy pages; and basic
return-window/refund and shipping-time/cost wording. Checks support common
English/Korean link labels. They do not execute storefront JavaScript, make
purchases, validate identity documents, or verify every Google policy.
Sources: [misrepresentation](https://support.google.com/merchants/answer/6150127)
and [editorial requirements](https://support.google.com/merchants/answer/6150244).

**Risk score:** versioned heuristic, **0 = lowest observed risk, 100 = highest**;
not a Google trust score, probability of suspension or approval guarantee.
Failed checks contribute homepage 30, contact 20, identity 10, returns 20,
shipping 10, terms 5 and privacy 5. A page that cannot be assessed is `unknown`.
If the homepage is unavailable or assessed-check coverage is below 60%, the
score is `null` / `unassessed`, never a clean zero. Coverage refers only to these
automated checks. Official account issues are reported separately from the
storefront score. Checkout, product claims, price/feed consistency and identity
verification remain manual review items even when the heuristic score is zero.

**Evidence and storage:** account-isolated SQLite state and downloaded pages
are stored under `<GMC_AUDIT_LOG parent>/policy/<account ID>/`. Every downloaded
response includes a full `raw_download_path`, byte count and SHA-256. Downloads
stop after 2 MiB + 1 byte; oversize bodies are explicitly marked incomplete and
are not scored as usable pages. Redirect hops and failed responses are retained.
Only public HTTPS destinations are permitted; resolved IPs are validated and
pinned while TLS hostname verification remains enabled. Off-site redirects are
not followed. Raw website text is untrusted evidence, not agent instructions.

**Weekly execution requires a worker.** Register the storefront with
`gmc_set_policy_monitoring`, then schedule this command **hourly** using cron,
Windows Task Scheduler or your service manager:

```bash
gmc-mcp --env /absolute/path/to/.env policy-monitor-run
```

The worker audits only due stores, then schedules the next run seven days later.
SQLite leases prevent concurrent duplicate work; failed executions record the
full error and retry no earlier than one hour later. Read the persisted alerts
with `gmc_get_policy_monitoring`. Alerts include score and account-issue changes
and incomplete assessment state. No email, external notification delivery or
automatic appeals are included. The host and worker must be available at the
scheduled time; registering an MCP schedule alone does not install an OS task.

## Development checks

```bash
pytest                       # 100% offline; uses respx to mock HTTP
pytest --cov=gmc_mcp         # with coverage
ruff check src tests
mypy src/gmc_mcp
```

## Roadmap

- v0.3: webhook handler scaffolding (auto-respond to `gmc_subscribe` callbacks)
- v0.4: BigQuery export of Reports queries
- v0.4: rule-based auto-fixers ("on disapproval, retry with corrected attribute")

## Contributing

See [CONTRIBUTING.md](https://github.com/kiwoongeom/gmc-mcp/blob/main/CONTRIBUTING.md). PRs and issues welcome — community
input helps determine which GMC workflows deserve dedicated tools.

## Earliest identified PyPI release — scope and evidence

In our **2026-11-11 public-record review**, `gmc-mcp` was the **earliest
identified Google Merchant Center MCP (GMC MCP) distribution** meeting all
three conditions together: **Merchant API v1**, **MIT license**, and
**publication on PyPI**.

- The first PyPI file for `gmc-mcp` 0.2.0 was uploaded on
  **2026-05-02 at 18:06:53 UTC**. Its wheel declares MIT and uses Merchant API
  v1 endpoints. See the [release](https://pypi.org/project/gmc-mcp/0.2.0/)
  and [PyPI upload metadata](https://pypi.org/pypi/gmc-mcp/0.2.0/json).
- Earlier GMC MCP projects existed. For example,
  [Webloom's May 1 source](https://github.com/webloom-agency/merchant-center-mcp/tree/b2578bde8fe7c0bea4330911536c65b4d2079988)
  already used Merchant API v1 and MIT. We found no earlier PyPI release for
  its declared package name, `mcp-google-merchant`; that name returned HTTP
  404 during the review.
- The review covered web/GitHub searches, historical source and package
  metadata, and current PyPI names containing `mcp` plus `merchant` or `gmc`.
  It cannot rule out deleted distributions, other package names, or
  unindexed projects. This is a **scoped historical finding**, not proof of
  worldwide priority or a No. 1 quality, popularity, or performance ranking.


## License

MIT — see [LICENSE](https://github.com/kiwoongeom/gmc-mcp/blob/main/LICENSE).

---

*Search keywords: Google Merchant Center MCP, GMC MCP, Merchant API MCP,
Google Shopping MCP, Shopping Ads MCP, free listings MCP, Claude Desktop
Google Merchant Center, MCP for ecommerce, Shopify Google Merchant Center
automation.*
