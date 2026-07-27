from __future__ import annotations

import random
import time
from collections.abc import Iterator
from typing import Any

import httpx

from ._logging import get_logger
from .audit import AuditLog
from .auth import Auth
from .config import Config

BASE_URL = "https://merchantapi.googleapis.com"
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 5

logger = get_logger("client")


class MerchantAPIError(Exception):
    def __init__(self, status: int, body: Any, message: str = ""):
        self.status = status
        self.body = body
        super().__init__(message or f"Merchant API error {status}: {body}")


class MerchantClient:
    """Thin HTTP wrapper over Merchant API v1beta. Handles auth, retries, paging, audit."""

    def __init__(self, config: Config, auth: Auth, audit: AuditLog):
        self.config = config
        self.auth = auth
        self.audit = audit
        self._http = httpx.Client(
            timeout=config.timeout,
            headers={"User-Agent": "gmc-mcp/0.1.0"},
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> MerchantClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def account_path(self, account_id: str | None = None) -> str:
        return f"accounts/{account_id or self.config.effective_account_id}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        op: str | None = None,
        before: Any | None = None,
    ) -> Any:
        """Perform a single Merchant API request. Returns parsed JSON or {} for 204."""
        url = f"{BASE_URL}/{path.lstrip('/')}"
        # ':search' endpoints (reports:search) are read-only queries that use
        # POST as their transport. They must bypass the dry-run interception,
        # otherwise every reports-based tool silently returns 0 results under
        # dry-run — e.g. gmc_list_disapproved_products reporting a clean feed
        # while hundreds of products are actually disapproved.
        is_write = (
            method.upper() in WRITE_METHODS
            and not path.rstrip("/").endswith(":search")
        )

        if is_write and self.config.dry_run:
            audit_id = self.audit.record(
                op=op or f"{method} {path}",
                resource=path,
                method=method,
                url=url,
                request_body=json_body,
                dry_run=True,
                before=before,
            )
            logger.info("dry-run %s %s (audit=%s)", method, path, audit_id)
            return {
                "_dry_run": True,
                "method": method,
                "url": url,
                "body": json_body,
                "audit_id": audit_id,
            }

        last_exc: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                resp = self._http.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    headers={"Authorization": f"Bearer {self.auth.access_token()}"},
                )
            except httpx.RequestError as e:
                last_exc = e
                logger.warning(
                    "transport error attempt=%d %s %s: %s",
                    attempt + 1,
                    method,
                    path,
                    e,
                )
                self._sleep_backoff(attempt)
                continue

            if resp.status_code in RETRYABLE_STATUSES and attempt < MAX_ATTEMPTS - 1:
                logger.warning(
                    "retryable status=%d attempt=%d %s %s",
                    resp.status_code,
                    attempt + 1,
                    method,
                    path,
                )
                self._sleep_backoff(attempt, resp)
                continue

            payload: Any = {} if resp.status_code == 204 else self._safe_json(resp)

            if not (200 <= resp.status_code < 300):
                if is_write:
                    self.audit.record(
                        op=op or f"{method} {path}",
                        resource=path,
                        method=method,
                        url=url,
                        request_body=json_body,
                        response_status=resp.status_code,
                        response_body=payload,
                        before=before,
                        error=f"HTTP {resp.status_code}",
                    )
                logger.error("api error %d %s %s: %s", resp.status_code, method, path, payload)
                raise MerchantAPIError(resp.status_code, payload)

            if is_write:
                audit_id = self.audit.record(
                    op=op or f"{method} {path}",
                    resource=path,
                    method=method,
                    url=url,
                    request_body=json_body,
                    response_status=resp.status_code,
                    response_body=payload,
                    before=before,
                )
                logger.info(
                    "write %s %s -> %d (audit=%s)",
                    method,
                    path,
                    resp.status_code,
                    audit_id,
                )
            else:
                logger.debug("read  %s %s -> %d", method, path, resp.status_code)
            return payload

        raise MerchantAPIError(0, str(last_exc) if last_exc else "exhausted retries")

    def paginate(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        items_key: str,
        max_pages: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        params = dict(params or {})
        params.setdefault("pageSize", self.config.page_size)
        page_count = 0
        while True:
            payload = self.request(method, path, params=params)
            for item in payload.get(items_key, []) or []:
                yield item
            page_count += 1
            token = payload.get("nextPageToken")
            if not token:
                return
            if max_pages is not None and page_count >= max_pages:
                return
            params["pageToken"] = token

    @staticmethod
    def _safe_json(resp: httpx.Response) -> Any:
        try:
            return resp.json()
        except ValueError:
            return {"_raw": resp.text}

    @staticmethod
    def _sleep_backoff(attempt: int, resp: httpx.Response | None = None) -> None:
        retry_after = 0.0
        if resp is not None and "Retry-After" in resp.headers:
            try:
                retry_after = float(resp.headers["Retry-After"])
            except ValueError:
                retry_after = 0.0
        base = max(retry_after, min(2**attempt, 30))
        time.sleep(base + random.uniform(0, 0.5))
