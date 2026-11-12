"""Prevent provider/target confusion and invalid Google request field names."""

from types import SimpleNamespace

import pytest

from gmc_mcp.tools import lfp, omnichannel


def tools_for(module, client):
    functions = {}
    module.register(
        SimpleNamespace(tool=lambda: lambda f: functions.setdefault(f.__name__, f)), client
    )
    return functions


def test_lfp_parent_is_provider_even_when_subaccount_is_configured(client, monkeypatch):
    client.config.subaccount_id = "999"
    calls = []
    monkeypatch.setattr(client, "request", lambda *a, **k: calls.append((a, k)) or {})
    functions = tools_for(lfp, client)
    functions["gmc_lfp_get_merchant_state"]("999")
    assert calls[-1][0] == ("GET", "lfp/v1/accounts/1234567890/lfpMerchantStates/999")


def test_lfp_store_get_and_delete_use_composite_target_id(client, monkeypatch):
    client.config.subaccount_id = "999"
    calls = []
    monkeypatch.setattr(client, "request", lambda *a, **k: calls.append((a, k)) or {})
    functions = tools_for(lfp, client)
    functions["gmc_lfp_get_store"]("store-1", target_account="999")
    assert calls[-1][0][1] == "lfp/v1/accounts/1234567890/lfpStores/999~store-1"
    functions["gmc_lfp_delete_store"]("999~store-1")
    assert calls[-1][0] == ("DELETE", "lfp/v1/accounts/1234567890/lfpStores/999~store-1")


def test_lfp_bare_store_id_requires_target_before_any_request(client, monkeypatch):
    calls = []
    monkeypatch.setattr(client, "request", lambda *a, **k: calls.append((a, k)))
    functions = tools_for(lfp, client)
    for name in ("gmc_lfp_get_store", "gmc_lfp_delete_store"):
        with pytest.raises(ValueError, match="target_merchant_id"):
            functions[name]("store-1")
    assert calls == []


def test_gbp_link_body_matches_discovery_schema(client, monkeypatch):
    calls = []
    monkeypatch.setattr(client, "request", lambda *a, **k: calls.append((a, k)) or {})
    functions = tools_for(omnichannel, client)
    functions["gmc_link_gbp_account"]("owner@example.com")
    assert calls[-1][1]["json_body"] == {"gbpEmail": "owner@example.com"}
