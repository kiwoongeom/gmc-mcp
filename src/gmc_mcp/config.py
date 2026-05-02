from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_AUDIT_LOG_NAME = "audit.jsonl"


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Config:
    account_id: str
    service_account_key: Path | None
    oauth_token: Path | None
    subaccount_id: str | None
    audit_log: Path
    page_size: int
    timeout: float
    dry_run: bool
    log_level: str = "INFO"
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    extras: dict[str, str] = field(default_factory=dict)

    @property
    def effective_account_id(self) -> str:
        return self.subaccount_id or self.account_id


def _path_or_none(raw: str | None) -> Path | None:
    if not raw or not raw.strip():
        return None
    return Path(raw).expanduser().resolve()


def load_config(env_file: Path | None = None) -> Config:
    """Read configuration from environment (and optional .env file).

    Raises RuntimeError with actionable messages on misconfiguration."""
    if env_file is not None:
        load_dotenv(dotenv_path=env_file, override=False)
    else:
        load_dotenv(override=False)

    account_id = os.environ.get("GMC_ACCOUNT_ID", "").strip()
    if not account_id:
        raise RuntimeError(
            "GMC_ACCOUNT_ID is not set.\n"
            "  - Find your 10-digit Merchant Center ID in the top-right of "
            "https://merchants.google.com\n"
            "  - Add it to .env: GMC_ACCOUNT_ID=1234567890"
        )
    if not account_id.isdigit():
        raise RuntimeError(
            f"GMC_ACCOUNT_ID must be numeric, got '{account_id}'."
        )

    sa_key = _path_or_none(os.environ.get("GMC_SERVICE_ACCOUNT_KEY"))
    oauth_token = _path_or_none(os.environ.get("GMC_OAUTH_TOKEN"))
    if sa_key is None and oauth_token is None:
        raise RuntimeError(
            "No credentials configured. Set ONE of:\n"
            "  - GMC_SERVICE_ACCOUNT_KEY: path to a service-account JSON key\n"
            "  - GMC_OAUTH_TOKEN: path to an OAuth token file (run "
            "`gmc-mcp auth-init` to create one)"
        )
    if sa_key is not None and not sa_key.exists():
        raise RuntimeError(f"GMC_SERVICE_ACCOUNT_KEY points to a missing file: {sa_key}")
    if oauth_token is not None and not oauth_token.exists() and sa_key is None:
        raise RuntimeError(
            f"GMC_OAUTH_TOKEN points to a missing file: {oauth_token}\n"
            "Run `gmc-mcp auth-init` to obtain a token."
        )

    subaccount = os.environ.get("GMC_SUBACCOUNT_ID", "").strip() or None
    if subaccount and not subaccount.isdigit():
        raise RuntimeError(f"GMC_SUBACCOUNT_ID must be numeric, got '{subaccount}'.")

    default_audit = (
        Path(__file__).resolve().parent.parent.parent / "logs" / DEFAULT_AUDIT_LOG_NAME
    )
    audit_path = (
        _path_or_none(os.environ.get("GMC_AUDIT_LOG")) or default_audit
    )
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    transport = os.environ.get("GMC_TRANSPORT", "stdio").strip().lower()
    if transport not in {"stdio", "sse"}:
        raise RuntimeError(
            f"GMC_TRANSPORT must be 'stdio' or 'sse', got '{transport}'."
        )

    try:
        page_size = int(os.environ.get("GMC_PAGE_SIZE", "100"))
    except ValueError as e:
        raise RuntimeError("GMC_PAGE_SIZE must be an integer") from e
    try:
        timeout = float(os.environ.get("GMC_TIMEOUT", "30"))
    except ValueError as e:
        raise RuntimeError("GMC_TIMEOUT must be a number") from e
    try:
        port = int(os.environ.get("GMC_PORT", "8000"))
    except ValueError as e:
        raise RuntimeError("GMC_PORT must be an integer") from e

    return Config(
        account_id=account_id,
        service_account_key=sa_key,
        oauth_token=oauth_token,
        subaccount_id=subaccount,
        audit_log=audit_path,
        page_size=page_size,
        timeout=timeout,
        dry_run=_truthy(os.environ.get("GMC_DRY_RUN")),
        log_level=os.environ.get("GMC_LOG_LEVEL", "INFO").upper(),
        transport=transport,
        host=os.environ.get("GMC_HOST", "127.0.0.1"),
        port=port,
    )
