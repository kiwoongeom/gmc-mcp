# Changelog — Google Merchant Center MCP (`gmc-mcp`)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `tools/regions.py`: regions CRUD (list / get / create / update / delete) —
  required to set up regional inventory targeting.
- `tools/accounts.py`: `gmc_update_business_info` (PATCH businessInfo —
  address, phone, customer service, KR business registration number).
- `tools/accounts.py`: `gmc_request_program_review` and `gmc_get_program_review`
  for re-requesting Shopping Ads / Free Listings approval after fixing issues.

## [0.2.0] - 2026-05-01

### Added — full Merchant API v1 surface
- `tools/return_policies.py`: list / get / create / update / delete `onlineReturnPolicies` (Google now requires a return policy in US/EU).
- `tools/homepage.py`: get / update / `claim` / `unclaim` the registered homepage.
- `tools/account_config.py`: business identity, checkout settings (per program),
  automatic improvements, autofeed settings, account tax, email preferences,
  Terms of Service (latest / agreement states / accept).
- `tools/quotas.py`: list per-method quota usage and limits.
- `tools/reviews.py`: merchant + product reviews CRUD.
- `tools/conversions.py`: conversion sources CRUD + undelete.
- `tools/omnichannel.py`: omnichannel settings, GBP account linkage,
  `requestInventoryVerification`.
- `tools/lfp.py`: full Local Feed Partnership API
  (lfpStores / lfpInventories / lfpSales / lfpMerchantStates).
- `tools/mca.py`: relationships, account aggregation, account services delegation
  (propose / approve / reject).
- `tools/bulk.py`: `gmc_bulk_update_regional_prices`,
  `gmc_bulk_set_availability` — both gated by `confirm='APPLY'`.
- `tools/diagnostics.py`: `gmc_health_check`, `gmc_rollback(audit_id)`,
  `gmc_export_all(output_dir)`, `gmc_diff_with_shopify(shopify_csv)`.
- `tools/products.py`: `gmc_bulk_delete_products` with `confirm='DELETE'` gate
  and automatic `dataSource` extraction (works on orphan products).
- `tools/reports.py`: 6 new canned queries — revenue by brand, category
  performance, competitive visibility, price insights, demoted products.
- CLI: `gmc-mcp webhook` — tiny HTTP receiver that decodes Pub/Sub push
  notifications from `gmc_subscribe`. Logs to JSONL with `--out`.

### Fixed
- `gmc_summarize_product_issues` now reads the v1 `itemIssues` schema
  (`type.code`, `type.canonicalAttribute`, `severity.aggregatedSeverity`,
  `resolution`) instead of the v1beta flat shape.
- `gmc_list_disapproved_products` now includes the required `id` field in the
  Reports SELECT (v1 requirement).
- `gmc_update_regional_inventory` / `gmc_update_local_inventory` build the
  `regionalInventoryAttributes` / `localInventoryAttributes` envelope required
  by v1 (v1beta flat fields are no longer accepted).

## [0.1.0] - 2026-04-30

### Added
- Initial release. Targets **Merchant API v1** (v1beta was shut down 2026-02-28).
- `gmc-mcp register-gcp` CLI: one-time link of GCP project to Merchant Center,
  required before any v1 call works.
- 42 MCP tools across 8 modules covering products, inventory, issues, reports,
  promotions, accounts, notifications, and data sources (feeds).
- Service-account authentication with auto-refresh.
- OAuth 2.0 user-credential authentication as an alternative.
- Append-only audit log for every write operation, with `gmc_audit_lookup`
  and `gmc_audit_tail` for inspection.
- Dry-run mode (`GMC_DRY_RUN=true` or `gmc_set_dry_run`) for safe testing.
- Both stdio and HTTP/SSE transports.
- CLI entrypoint `gmc-mcp` with `--transport`, `--host`, `--port`, `--env`.
- Reports API helpers: raw SQL queries, top performers, price competitiveness,
  best sellers, zero-click outliers.
- Issue summarization that aggregates problem codes across all products.
