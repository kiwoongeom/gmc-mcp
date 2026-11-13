<!-- mcp-name: io.github.kiwoongeom/gmc-mcp -->

# Google Merchant Center MCP (GMC MCP)

**Understand your catalog. Diagnose product issues. Turn policy findings into an action plan.**

Google Merchant Center MCP (GMC MCP) brings Merchant Center data and storefront policy workflows into your MCP client. Read products, investigate disapprovals, query Shopping reports, and prepare evidence-backed fixes and appeal drafts using your own Google credentials.

Built on Merchant API v1, with 60 focused tools in an MIT-licensed Python package.

> **0.3.2:** a focused 60-tool configuration for catalog insights, Merchant Center queries and storefront policy workflows.

## What you can do

| Workflow | How it helps |
|---|---|
| Catalog and issue diagnosis | Inspect product details and status, find disapproved products, and summarize product and account issues. |
| Shopping insights | Query performance, pricing, category, competitive visibility and best-seller reports to inform catalog decisions. |
| Merchant configuration | Read shipping, returns, data sources, programs, users, quotas and other account settings in one place. |
| Inventory and account connections | Inspect local/regional inventory, regions, conversion sources, account relationships and linked Business Profile listings. |
| Promotions and checkout | List promotions, inspect checkout settings, and create checkout settings for eligible accounts. |
| Storefront policy audit | Review public contact and policy pages, retain downloaded evidence, and identify failed or unknown checks. |
| Fix plans and appeal drafts | Prioritize findings and create a draft for merchant review before any submission. |
| Scheduled policy reviews | Save weekly schedules, run due audits, compare findings, and read local alerts. Unattended execution requires an OS worker. |

## Why use GMC MCP?

- **One interface for daily investigation.** Bring catalog, account settings, reports and policy findings into the same assistant workflow.
- **Evidence you can inspect.** Saved policy reports reference downloaded content, byte counts and hashes so findings can be traced to their source.
- **Actionable policy findings.** Move from failed or unknown checks to prioritized fixes and a reviewable appeal draft.
- **Your credentials and local records.** Run the Python server with your Google account access; keep audit history and policy state on your host. API requests go directly to Google.
- **A focused default tool set.** The exposed tools cover confirmed query behavior and executed policy workflows, with clear boundaries for writes and Google approvals.

## Example requests

- "Show my disapproved products and group them by issue."
- "Summarize my shipping settings, return policy and data sources."
- "Query product performance for the last 30 days."
- "Audit my storefront policies and prioritize failed or unknown checks."
- "Prepare an appeal draft using the saved findings."
- "Save a weekly policy review schedule and show changes from the previous audit."

## Default tools

The server exposes the following 60 tools. The table lists capabilities; it does not imply that every account has data or permission for every query.

<details>
<summary>View tools by workflow</summary>

| Workflow | Tools |
|---|---|
| Products | `gmc_get_product`, `gmc_list_disapproved_products`, `gmc_list_products` |
| Product and account issues | `gmc_get_product_status`, `gmc_list_account_issues`, `gmc_summarize_product_issues` |
| Shopping reports | `gmc_best_sellers`, `gmc_category_performance`, `gmc_competitive_visibility_top_merchants`, `gmc_demoted_products`, `gmc_price_competitiveness`, `gmc_price_insights`, `gmc_product_performance`, `gmc_query_report`, `gmc_revenue_by_brand`, `gmc_zero_click_products` |
| Account, shipping and programs | `gmc_get_account`, `gmc_get_business_info`, `gmc_get_program_review`, `gmc_get_shipping_settings`, `gmc_list_programs`, `gmc_list_users` |
| Configuration, checkout and terms | `gmc_create_checkout_settings`, `gmc_get_autofeed_settings`, `gmc_get_automatic_improvements`, `gmc_get_business_identity`, `gmc_get_checkout_settings`, `gmc_get_email_preferences`, `gmc_get_latest_tos`, `gmc_list_tos_agreement_states` |
| Data sources | `gmc_get_datasource`, `gmc_list_datasources` |
| Return policies | `gmc_get_return_policy`, `gmc_list_return_policies` |
| Conversion sources | `gmc_get_conversion_source`, `gmc_list_conversion_sources` |
| Account relationships and services | `gmc_get_relationship`, `gmc_list_account_services`, `gmc_list_relationships` |
| Inventory reads | `gmc_list_local_inventories`, `gmc_list_regional_inventories` |
| Homepage | `gmc_get_homepage` |
| Promotion listings | `gmc_list_promotions` |
| Quotas | `gmc_list_quotas` |
| Region listings | `gmc_list_regions` |
| Notification subscription listings | `gmc_list_subscriptions` |
| Linked Business Profile listings | `gmc_list_gbp_accounts` |
| Policy audits and monitoring | `gmc_generate_policy_appeal`, `gmc_get_policy_audit`, `gmc_get_policy_fix_plan`, `gmc_get_policy_monitoring`, `gmc_list_policy_audits`, `gmc_run_policy_audit`, `gmc_run_policy_monitors`, `gmc_set_policy_monitoring` |
| Server configuration, audit history and session control | `gmc_audit_lookup`, `gmc_audit_tail`, `gmc_describe_server`, `gmc_set_dry_run` |
| Endpoint diagnostics | `gmc_health_check` |

</details>

## Install

```bash
pip install --upgrade gmc-mcp
```

Requires Python 3.10 or newer and access to a Google Merchant Center account.

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

## Policy audit and monitoring

The auditor reads public HTTPS pages and linked contact, business, return/refund, shipping, terms and privacy content. It can also retrieve Merchant Center account issues. Each run saves a report and evidence for later inspection, fix planning and appeal drafting.

The risk score is a **heuristic assessment of observed storefront content**, not a Google score or approval guarantee. Unknown or missing evidence is kept distinct from a passed check; insufficient coverage produces an unassessed score. Official account issues remain separate from the storefront score.

An audit defaults to a maximum of eight pages within a 24-second collection window. URLs skipped by these limits appear in `skipped_pages` with `requested: false` and `page_limit_reached` or `audit_deadline_reached`. Fix plans and appeal drafts call for collection or manual inspection rather than claiming these policies are missing. Incomplete assessment does not receive a clean score.

For weekly reviews, save a schedule with `gmc_set_policy_monitoring`. An OS scheduler or service must invoke the worker; saving a schedule alone does not start unattended monitoring:

```bash
gmc-mcp --env /absolute/path/to/.env policy-monitor-run
```

The worker runs audits that are due and records local alerts. Appeal generation saves a draft for review. External notification delivery and automatic appeal submission are not included.

## Supported scope and validation

The default list is based on previously recorded Merchant API responses and executed local workflows. Successful empty lists and reports count as accepted queries; they do not establish populated-output behavior. API errors remain errors. Report data and program access depend on the merchant account.

Checkout settings creation and retrieval were accepted by Google. The observed status was `ENROLLED / IN_REVIEW`; this is not approval or confirmation that checkout links are showing on Google. Previously submitted product links were observed in processed product responses; persistence after later Shopify syncs remains unconfirmed.

Policy audit, saved reports, fix plans, appeal drafts, schedule storage and due-run execution were exercised. Seven-day unattended operation was not established. The auditor does not verify identity documents, complete checkout purchases, or certify compliance with every Google policy.

Product/catalog writes, bulk updates, deletion and rollback are outside this default tool set. Review APIs, omnichannel setup, LFP operations and unsupported compatibility placeholders are also excluded. Reading linked Business Profiles does not enable omnichannel setup. Program review lookup reports eligibility and unmet requirements; it does not submit a manual review.

Release 0.3.2 uses one integrated release candidate. Release notes distinguish offline regression checks, live read/policy flows and preview-only checkout creation. Google approval, arbitrary merchant compatibility and seven-day unattended operation are not guaranteed.

## Development

```bash
pytest
ruff check src tests
mypy src/gmc_mcp
```

## License

MIT. See [LICENSE](LICENSE).
