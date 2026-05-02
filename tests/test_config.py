from __future__ import annotations

from pathlib import Path

import pytest

from gmc_mcp.config import load_config


@pytest.fixture
def empty_env(tmp_path: Path) -> Path:
    """Pointer to a non-existent .env so load_dotenv finds nothing.

    Without this, tests pick up the developer's real .env from the project root
    and monkeypatched env vars don't take effect."""
    return tmp_path / "nonexistent.env"


def _setup_env(monkeypatch: pytest.MonkeyPatch, sa_key: Path, **overrides: str) -> None:
    monkeypatch.setenv("GMC_ACCOUNT_ID", "1234567890")
    monkeypatch.setenv("GMC_SERVICE_ACCOUNT_KEY", str(sa_key))
    monkeypatch.delenv("GMC_OAUTH_TOKEN", raising=False)
    monkeypatch.delenv("GMC_SUBACCOUNT_ID", raising=False)
    monkeypatch.delenv("GMC_TRANSPORT", raising=False)
    monkeypatch.delenv("GMC_DRY_RUN", raising=False)
    for k, v in overrides.items():
        monkeypatch.setenv(k, v)


def test_load_config_minimal(
    tmp_path: Path, empty_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sa = tmp_path / "sa.json"
    sa.write_text("{}")
    _setup_env(monkeypatch, sa)

    cfg = load_config(env_file=empty_env)
    assert cfg.account_id == "1234567890"
    assert cfg.service_account_key == sa.resolve()
    assert cfg.oauth_token is None
    assert cfg.dry_run is False
    assert cfg.transport == "stdio"
    assert cfg.effective_account_id == "1234567890"


def test_subaccount_overrides_account(
    tmp_path: Path, empty_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sa = tmp_path / "sa.json"
    sa.write_text("{}")
    _setup_env(monkeypatch, sa, GMC_SUBACCOUNT_ID="999")
    cfg = load_config(env_file=empty_env)
    assert cfg.effective_account_id == "999"


def test_missing_account_raises(empty_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GMC_ACCOUNT_ID", raising=False)
    monkeypatch.delenv("GMC_SERVICE_ACCOUNT_KEY", raising=False)
    monkeypatch.delenv("GMC_OAUTH_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="GMC_ACCOUNT_ID"):
        load_config(env_file=empty_env)


def test_non_numeric_account_raises(
    tmp_path: Path, empty_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sa = tmp_path / "sa.json"
    sa.write_text("{}")
    monkeypatch.setenv("GMC_ACCOUNT_ID", "abc")
    monkeypatch.setenv("GMC_SERVICE_ACCOUNT_KEY", str(sa))
    monkeypatch.delenv("GMC_OAUTH_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="numeric"):
        load_config(env_file=empty_env)


def test_no_credentials_raises(
    empty_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GMC_ACCOUNT_ID", "1234567890")
    monkeypatch.delenv("GMC_SERVICE_ACCOUNT_KEY", raising=False)
    monkeypatch.delenv("GMC_OAUTH_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="No credentials"):
        load_config(env_file=empty_env)


def test_invalid_transport(
    tmp_path: Path, empty_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sa = tmp_path / "sa.json"
    sa.write_text("{}")
    _setup_env(monkeypatch, sa, GMC_TRANSPORT="websocket")
    with pytest.raises(RuntimeError, match="GMC_TRANSPORT"):
        load_config(env_file=empty_env)


def test_truthy_dry_run(
    tmp_path: Path, empty_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sa = tmp_path / "sa.json"
    sa.write_text("{}")
    for value in ("true", "TRUE", "1", "yes", "on"):
        _setup_env(monkeypatch, sa, GMC_DRY_RUN=value)
        assert load_config(env_file=empty_env).dry_run is True
    for value in ("false", "0", "no", ""):
        _setup_env(monkeypatch, sa, GMC_DRY_RUN=value)
        assert load_config(env_file=empty_env).dry_run is False
