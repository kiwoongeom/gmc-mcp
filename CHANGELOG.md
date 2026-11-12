# Changelog — Google Merchant Center MCP (`gmc-mcp`)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-11-12

### Focused default tools
- Expose 60 tools backed by existing successful API/local execution records, including successful empty queries. Remove 74 unverified, account-blocked or unsupported operations from the public MCP surface while preserving internal source modules.
- Lead README and package descriptions with supported workflows and benefits. Keep checkout review, heuristic policy scoring and monitoring limits explicit.
- Reuse existing execution evidence. No new test suite or runtime checks were run for this release.

### Corrected capability claims and API requests
- Preserve dry-run responses in delete/remove tools and distinguish bulk preview
  counts from actual applied/deleted counts. A preview is not a completed write.
- Policy rules 1.2: separate shared/hidden page content from policy evidence so
  an empty page with a newsletter footer cannot receive a clean score. Older
  stored scores require re-auditing without erasing their original evidence.
- Four compatibility placeholders are not supported operations: account tax
  read/update, program manual-review submission, and online return policy update.
  Earlier feature-list claims for these operations were incorrect. They now
  report `UNSUPPORTED_FEATURE` internally and are not registered as public tools.
- Registration counts are not working-feature counts. Actual Google access,
  resource configuration, local execution and dry-run validation are distinct.
- Correct policy false-clean scoring, API routes and report queries; preserve
  partial export results and refuse ignored bulk-delete filters/dry-run rollback.
- Correct LFP provider/subaccount routing and composite target/store IDs; fix the
  Business Profile link request to use `gbpEmail`. These writes have only been
  exercised as local dry-runs, not accepted changes on Google.

## [0.3.0] - 2026-11-12

### Added
- Eight account-isolated policy tools: bounded public HTTPS storefront audits,
  persisted evidence, heuristic risk scores, prioritized fix plans, review-required
  appeal drafts, and persistent weekly monitoring with local alerts.
- `policy-monitor-run` CLI for an OS scheduler: due-job leases, seven-day cadence,
  retryable failures, score/account-issue change tracking and raw error retention.
- DNS/IP validation, IP-pinned TLS connections, redirect restrictions, explicit
  incomplete coverage and full downloaded-byte evidence paths and hashes.

### Compatibility
- Historical 0.3.0 registered 134 tools. Version 0.3.1 replaces this public surface with 60 selected tools.
- Keep the 12 OS/Python CI combinations and select the supported macOS Intel
  runner explicitly after arm64 runner allocation left release checks queued.
- No external LLM dependency, automatic Merchant API writes, appeal submission,
  official Google risk score or guarantee of policy compliance.

## [0.2.7] - 2026-11-11

### Documentation
- Lead the GitHub and PyPI introduction with product workflows, inventory,
  feed diagnostics, reports, authentication, dry-run, auditing and supported rollback.
- State the verified startup, tool registration, regression-test and live-read
  coverage explicitly, without claiming every tool has been live-tested.
- Keep Google Merchant Center MCP and GMC MCP search keywords and move the
  unchanged, scoped earliest-identified-release finding to a historical section.
- Refresh package and registry descriptions. Runtime behavior and the 0.2.6
  compatibility and Reports fixes are unchanged.

## [0.2.6] - 2026-11-05

### Fixed
- Allow read-only Reports API POST queries through dry-run mode. Report tools
  return actual rows and propagate API errors instead of silently returning zero
  results (#1, #2). Other POST actions and all PUT/PATCH/DELETE requests remain
  intercepted and audited in dry-run mode.
- Bound the MCP SDK dependency to `mcp>=1.2.0,<2`, matching the FastMCP v1 API
  used by this server and preventing startup failures with MCP 2.x (#4).
- Use the package version in the Merchant API User-Agent header.
- Fix missing CLI type imports and clean up existing lint/format violations so
  the release passes the repository's CI checks.

### Tests
- Cover report pagination and HTTP 400/403/503 errors under dry-run, plus
  continued write interception and auditing.

## [0.2.5] - 2026-05-02

### Changed — positioning corrected (second time)
After publication, discovered another prior-art self-hosted GMC MCP server:
[`archpeng/GMC-mcp-server`](https://github.com/archpeng/GMC-mcp-server),
created 2026-02-23 (10 weeks before this package). My original "first
open-source self-hosted" claim was inaccurate.

The correct, verifiable framing:
- Both `archpeng/GMC-mcp-server` and this package are self-hosted Python.
- `archpeng/GMC-mcp-server` is on **Content API v2.1** (deprecated, Google
  retires August 2026), **no LICENSE file** (default copyright = not OSS),
  **not on PyPI**, 34 tools, last updated 2026-02-24.
- `gmc-mcp` is on **Merchant API v1** (current/future-proof), **MIT-licensed**,
  **on PyPI** (`pip install gmc-mcp`), 126 tools, audit log + rollback +
  dry-run + CI to PyPI/Registry.

README, pyproject description, and server.json description rewritten to
remove the "first" overclaim and present a comparison table instead.

## [0.2.4] - 2026-05-02

### Fixed
- Removed `runtimeArguments` from `server.json` (was triggering MCP Registry
  semantic validation on the `default` field). The CLI invokes the `run`
  subcommand automatically when called with no arguments, so the runtime
  argument was redundant anyway.

## [0.2.3] - 2026-05-02

### Fixed
- `server.json` description shortened to ≤100 characters to satisfy the
  MCP Registry validation rule. v0.2.2 publish to the registry failed on
  this constraint; v0.2.3 retries with a compliant description.

## [0.2.2] - 2026-05-02

### Added
- Published to the official **MCP Registry** at
  [registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io)
  under the namespace `io.github.kiwoongeom/gmc-mcp`. Discoverable from Claude
  Desktop's MCP Registry browser and any other MCP-Registry-aware client.
- New file `server.json` — MCP Registry manifest with package + transport +
  environment-variable schema.
- New CI workflow `.github/workflows/publish-mcp-registry.yml` — auto-publishes
  to the MCP Registry on every `v*` tag push, using GitHub OIDC (no tokens).
- README now contains a `mcp-name:` HTML comment as required for PyPI-package
  ownership verification by the MCP Registry.

## [0.2.1] - 2026-05-02

### Changed
- README, CHANGELOG, and PyPI description updated for accurate positioning:
  this is the first **free, open-source, self-hosted** MCP server for Google
  Merchant Center. All known prior alternatives (Adzviser, Catchr, Windsor.ai,
  Pipedream) are paid hosted SaaS; Google's MAPI Docs MCP is documentation-
  lookup only. Differentiators of this package:
  1. Free (MIT) vs paid SaaS
  2. Open source — auditable, forkable
  3. Self-hosted — credentials never leave your machine
  4. `pip install`-able (no third-party signup)
  5. 126 tools mapping the full Merchant API v1 surface

### Added (carried over from unreleased)
- `tools/regions.py`: regions CRUD (list / get / create / update / delete) —
  required to set up regional inventory targeting.
- `tools/accounts.py`: `gmc_update_business_info` (PATCH businessInfo —
  address, phone, customer service, KR business registration number).
- `tools/accounts.py`: registered program-review tool names. Correction: v1 has
  no manual-review submission method; `gmc_request_program_review` is unsupported.
  `gmc_get_program_review` reads program eligibility, not a manual-review status.

## [0.2.0] - 2026-05-01

### Positioning
- **First open-source, self-hosted MCP server for Google Merchant Center.**
- Existing alternatives at the time of release (Adzviser, Catchr, Windsor.ai,
  Pipedream, Google's MAPI Docs MCP) are all commercial hosted SaaS or
  documentation-lookup helpers. This is the first one you can `pip install`,
  audit the source of, and run with your credentials staying local.

### Added — initial API coverage (corrected capability notes)
- `tools/return_policies.py`: list / get / create / delete `onlineReturnPolicies`.
  The originally advertised update operation is not provided by Merchant API.
- `tools/homepage.py`: get / update / `claim` / `unclaim` the registered homepage.
- `tools/account_config.py`: business identity, checkout settings (per program),
  automatic improvements, autofeed settings, email preferences,
  Terms of Service (latest / agreement states / accept).
  Originally advertised account tax read/update operations are unsupported.
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
