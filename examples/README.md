# Examples

Stand-alone scripts that use `gmc_mcp` directly (without going through Claude /
MCP). Useful for cron jobs, ad-hoc audits, or as a sanity check that your
credentials work.

| Script | Purpose |
|---|---|
| `quickstart.py` | Connect, fetch account info, list 5 products. |
| `audit_disapproved.py` | Save a CSV of every disapproved product with issue codes. |
| `bulk_price_update.py` | Apply a price-bump to a list of SKUs (with --dry-run). |
| `claude_desktop_config_snippet.json` | Drop-in MCP entry for Claude Desktop / Code. |

Run any script after creating `.env`:

```bash
python examples/quickstart.py
```
