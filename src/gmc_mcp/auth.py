"""Authentication providers for the Merchant API.

Two paths are supported:

* `ServiceAccountAuth` — best for first-party automation against your own
  Merchant Center account. Uses a JSON key file. No browser flow.
* `OAuthUserAuth` — best when the operator is acting on behalf of an end user.
  Reads / writes a refresh-token JSON file. Run a one-time CLI flow to obtain it
  via `python -m gmc_mcp.cli auth-init`.

Both classes expose the same `access_token()` method and `service_account_email`
or `account_label` property so the rest of the codebase doesn't care which is in use.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Protocol

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials

SCOPES = ["https://www.googleapis.com/auth/content"]


class Auth(Protocol):
    @property
    def account_label(self) -> str: ...

    def access_token(self) -> str: ...


class ServiceAccountAuth:
    """Thread-safe service-account credential holder with auto-refresh."""

    def __init__(self, key_path: Path):
        self._creds = service_account.Credentials.from_service_account_file(
            str(key_path), scopes=SCOPES
        )
        self._lock = threading.Lock()
        self._request = Request()

    @property
    def account_label(self) -> str:
        return f"service-account:{self._creds.service_account_email}"

    @property
    def service_account_email(self) -> str:
        return self._creds.service_account_email

    def access_token(self) -> str:
        with self._lock:
            if not self._creds.valid or self._is_about_to_expire():
                self._creds.refresh(self._request)
            return self._creds.token

    def _is_about_to_expire(self) -> bool:
        if self._creds.expiry is None:
            return False
        remaining = self._creds.expiry.timestamp() - time.time()
        return remaining < 60


class OAuthUserAuth:
    """User-level OAuth credentials persisted to a JSON file.

    The file is created/refreshed by `gmc_mcp.cli auth-init`, which runs the
    InstalledAppFlow against the OAuth client secrets you create in GCP.
    """

    def __init__(self, token_path: Path):
        self.token_path = token_path
        if not token_path.exists():
            raise RuntimeError(
                f"OAuth token file not found at {token_path}. "
                "Run `gmc-mcp auth-init` to obtain one."
            )
        data = json.loads(token_path.read_text(encoding="utf-8"))
        self._creds = UserCredentials.from_authorized_user_info(data, SCOPES)
        self._lock = threading.Lock()
        self._request = Request()

    @property
    def account_label(self) -> str:
        # UserCredentials don't expose email — use the file path as a stable label.
        return f"oauth-user:{self.token_path.name}"

    def access_token(self) -> str:
        with self._lock:
            if not self._creds.valid:
                self._creds.refresh(self._request)
                self._persist()
            return self._creds.token

    def _persist(self) -> None:
        self.token_path.write_text(self._creds.to_json(), encoding="utf-8")


def load_auth(
    *,
    service_account_key: Path | None,
    oauth_token: Path | None,
) -> Auth:
    """Pick the available auth method. Prefers service-account if both present."""
    if service_account_key and service_account_key.exists():
        return ServiceAccountAuth(service_account_key)
    if oauth_token and oauth_token.exists():
        return OAuthUserAuth(oauth_token)
    raise RuntimeError(
        "No credentials configured. Set GMC_SERVICE_ACCOUNT_KEY to a service "
        "account JSON, or GMC_OAUTH_TOKEN to a token JSON produced by "
        "`gmc-mcp auth-init`."
    )
