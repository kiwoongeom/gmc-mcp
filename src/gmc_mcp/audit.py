from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any


class AuditLog:
    """Append-only JSONL log of every write operation. Used for debugging and rollback."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.Lock()

    def record(
        self,
        *,
        op: str,
        resource: str,
        method: str,
        url: str,
        request_body: Any | None = None,
        response_status: int | None = None,
        response_body: Any | None = None,
        before: Any | None = None,
        dry_run: bool = False,
        error: str | None = None,
    ) -> str:
        audit_id = uuid.uuid4().hex
        entry = {
            "audit_id": audit_id,
            "ts": time.time(),
            "op": op,
            "resource": resource,
            "method": method,
            "url": url,
            "request_body": request_body,
            "response_status": response_status,
            "response_body": response_body,
            "before": before,
            "dry_run": dry_run,
            "error": error,
        }
        line = json.dumps(entry, ensure_ascii=False, default=str)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        return audit_id

    def find(self, audit_id: str) -> dict[str, Any] | None:
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                if entry.get("audit_id") == audit_id:
                    return entry
        return None
