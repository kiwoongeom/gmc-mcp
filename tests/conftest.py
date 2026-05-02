"""Shared fixtures for the test suite.

All tests run fully offline. We never hit the real Merchant API or read a real
service-account key.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from gmc_mcp.audit import AuditLog
from gmc_mcp.client import MerchantClient
from gmc_mcp.config import Config


class FakeAuth:
    """Stand-in for ServiceAccountAuth / OAuthUserAuth in tests."""

    account_label = "fake:test"

    def access_token(self) -> str:
        return "fake-token"


@pytest.fixture
def tmp_audit_log(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


@pytest.fixture
def config(tmp_audit_log: Path) -> Config:
    return Config(
        account_id="1234567890",
        service_account_key=None,
        oauth_token=None,
        subaccount_id=None,
        audit_log=tmp_audit_log,
        page_size=10,
        timeout=5.0,
        dry_run=False,
    )


@pytest.fixture
def audit(tmp_audit_log: Path) -> AuditLog:
    return AuditLog(tmp_audit_log)


@pytest.fixture
def client(config: Config, audit: AuditLog) -> MerchantClient:
    c = MerchantClient(config, FakeAuth(), audit)
    yield c
    c.close()


@pytest.fixture
def captured_calls() -> list[dict[str, Any]]:
    """Mutable list test code can append to from inside respx side-effects."""
    return []
