from __future__ import annotations

import json
from pathlib import Path

from gmc_mcp.audit import AuditLog


def test_record_and_find(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "a.jsonl")
    aid = log.record(
        op="insert_product",
        resource="products/v1/accounts/123/productInputs:insert",
        method="POST",
        url="https://merchantapi.googleapis.com/products/v1/accounts/123/productInputs:insert",
        request_body={"offerId": "SKU1"},
        response_status=200,
        response_body={"name": "products/.../SKU1"},
    )
    entry = log.find(aid)
    assert entry is not None
    assert entry["op"] == "insert_product"
    assert entry["request_body"] == {"offerId": "SKU1"}
    assert entry["response_status"] == 200


def test_find_missing(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "a.jsonl")
    log.record(op="x", resource="r", method="POST", url="u")
    assert log.find("nonexistent") is None


def test_appends_per_record(tmp_path: Path) -> None:
    path = tmp_path / "a.jsonl"
    log = AuditLog(path)
    for i in range(3):
        log.record(op=f"op{i}", resource="r", method="POST", url="u")
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3
    parsed = [json.loads(line) for line in lines]
    assert [e["op"] for e in parsed] == ["op0", "op1", "op2"]


def test_dry_run_flag_persisted(tmp_path: Path) -> None:
    log = AuditLog(tmp_path / "a.jsonl")
    aid = log.record(op="x", resource="r", method="POST", url="u", dry_run=True)
    assert log.find(aid)["dry_run"] is True
