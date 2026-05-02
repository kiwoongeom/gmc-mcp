"""Build the FastMCP server. Stays import-light so tests can patch pieces individually."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import tools
from ._logging import configure_default, get_logger
from .audit import AuditLog
from .auth import load_auth
from .client import MerchantClient
from .config import Config, load_config

logger = get_logger("server")


def build_server(config: Config | None = None, env_file: Path | None = None) -> FastMCP:
    """Construct a FastMCP instance with all gmc_* tools registered."""
    configure_default()
    if config is None:
        config = load_config(env_file=env_file)

    auth = load_auth(
        service_account_key=config.service_account_key,
        oauth_token=config.oauth_token,
    )
    audit = AuditLog(config.audit_log)
    client = MerchantClient(config, auth, audit)

    logger.info(
        "starting gmc-mcp account=%s subaccount=%s auth=%s dry_run=%s",
        config.account_id,
        config.subaccount_id or "-",
        auth.account_label,
        config.dry_run,
    )

    mcp = FastMCP("gmc-mcp")

    @mcp.tool()
    def gmc_describe_server() -> dict[str, Any]:
        """Show what this server is connected to and how it's configured."""
        return {
            "account_id": config.account_id,
            "subaccount_id": config.subaccount_id,
            "effective_account_id": config.effective_account_id,
            "auth": auth.account_label,
            "audit_log": str(config.audit_log),
            "dry_run": config.dry_run,
            "page_size": config.page_size,
            "timeout": config.timeout,
            "transport": config.transport,
        }

    @mcp.tool()
    def gmc_audit_lookup(audit_id: str) -> dict[str, Any]:
        """Look up an audit log entry by ID. Useful for diagnosing failed writes or rolling back."""
        entry = audit.find(audit_id)
        if not entry:
            return {"found": False, "audit_id": audit_id}
        return {"found": True, "entry": entry}

    @mcp.tool()
    def gmc_audit_tail(limit: int = 20) -> dict[str, Any]:
        """Show the most recent audit log entries."""
        if not config.audit_log.exists():
            return {"count": 0, "entries": []}
        with config.audit_log.open("r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        entries = [json.loads(line) for line in lines]
        return {"count": len(entries), "entries": entries}

    @mcp.tool()
    def gmc_set_dry_run(enabled: bool) -> dict[str, Any]:
        """Toggle dry-run mode for this session. When enabled, write operations
        are recorded to the audit log but NOT sent to Merchant API."""
        client.config.dry_run = enabled
        logger.info("dry_run=%s (set via tool)", enabled)
        return {"dry_run": enabled}

    tools.products.register(mcp, client)
    tools.inventory.register(mcp, client)
    tools.issues.register(mcp, client)
    tools.reports.register(mcp, client)
    tools.promotions.register(mcp, client)
    tools.accounts.register(mcp, client)
    tools.notifications.register(mcp, client)
    tools.feeds.register(mcp, client)
    tools.return_policies.register(mcp, client)
    tools.homepage.register(mcp, client)
    tools.account_config.register(mcp, client)
    tools.quotas.register(mcp, client)
    tools.reviews.register(mcp, client)
    tools.conversions.register(mcp, client)
    tools.omnichannel.register(mcp, client)
    tools.lfp.register(mcp, client)
    tools.mca.register(mcp, client)
    tools.bulk.register(mcp, client)
    tools.diagnostics.register(mcp, client)
    tools.regions.register(mcp, client)

    return mcp
