from __future__ import annotations

import asyncio
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from gmc_mcp import server
from gmc_mcp.public_tools import VERIFIED_TOOLS


def test_default_surface_and_removed_calls(config, client, monkeypatch):
    monkeypatch.setattr(server, "load_auth", lambda **kw: SimpleNamespace(account_label="test"))
    monkeypatch.setattr(server, "MerchantClient", lambda *a, **kw: client)
    removed = []
    original_remove = server.FastMCP.remove_tool

    def remove(mcp, name):
        removed.append(name)
        original_remove(mcp, name)

    monkeypatch.setattr(server.FastMCP, "remove_tool", remove)
    mcp = server.build_server(config)

    def unexpected_request(*args, **kwargs):
        pytest.fail("An excluded tool must never reach Merchant API")

    monkeypatch.setattr(client, "request", unexpected_request)

    async def check():
        assert {tool.name for tool in await mcp.list_tools()} == VERIFIED_TOOLS
        assert removed
        for name in removed:
            with pytest.raises(ToolError, match="Unknown tool"):
                await mcp.call_tool(name, {})

    asyncio.run(check())
    assert {
        "gmc_product_performance",
        "gmc_list_regions",
        "gmc_list_local_inventories",
    } <= VERIFIED_TOOLS
    assert {
        "gmc_update_product",
        "gmc_rollback",
        "gmc_get_account_tax",
        "gmc_list_product_reviews",
        "gmc_list_omnichannel_settings",
        "gmc_lfp_list_stores",
    } <= set(removed)


def test_readme_default_table_matches_runtime():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    table = readme.split("## Default tools\n", 1)[1].split("## Quick start", 1)[0]
    assert set(re.findall(r"`(gmc_\w+)`", table)) == VERIFIED_TOOLS
