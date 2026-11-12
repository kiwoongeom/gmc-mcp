from __future__ import annotations

import hashlib
import io
from pathlib import Path
from types import SimpleNamespace

import pytest

from gmc_mcp import policy
from gmc_mcp.client import MerchantClient
from gmc_mcp.policy import (
    Page,
    PinnedHTTPS,
    PolicyAuditor,
    fetch_page,
    normalize_url,
    public_addresses,
)


@pytest.fixture
def auditor(client: MerchantClient, monkeypatch: pytest.MonkeyPatch) -> PolicyAuditor:
    monkeypatch.setattr(client, "request", lambda *a, **k: {"accountIssues": []})
    monkeypatch.setattr(policy, "public_addresses", lambda host: ["93.184.216.34"])

    def fetch(url, raw, origin):
        if url.endswith("/"):
            html = "<html><h1>A real demonstration shop with public policies</h1>"
            html += "".join(
                f'<a href="/{name}">{"About our company" if name == "identity" else name}</a>'
                for name in policy.CATEGORIES
            )
            html += "</html>"
        else:
            html = (
                "<p>Our company provides customer support at support@example.com. "
                "Returns accepted within 30 days. Refund processing takes 7 days. "
                "Shipping costs are free and delivery takes 5 business days. "
                "These policies apply to our products and customers.</p>"
            )
        path = raw / (hashlib.sha256(url.encode()).hexdigest() + ".download")
        path.write_bytes(html.encode())
        return {
            "url": url,
            "usable": True,
            "html": html,
            "hops": [
                {
                    "raw_download_path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "bytes": path.stat().st_size,
                    "download_complete": True,
                }
            ],
        }

    return PolicyAuditor(client, fetch)


def test_audit_roundtrip_and_raw_evidence(auditor: PolicyAuditor) -> None:
    result = auditor.run("https://example.com/")
    assert result["risk_score"] == 0
    assert result["coverage"] == 1
    assert auditor.get(result["audit_id"]) == result
    assert auditor.list_audits()["audits"][0]["audit_id"] == result["audit_id"]
    assert len(result["pages"]) == 7
    for page in result["pages"]:
        evidence = page["hops"][0]
        data = Path(evidence["raw_download_path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == evidence["sha256"]
    assert Path(result["account"]["raw_response_path"]).is_file()


@pytest.mark.parametrize("old_rules", ["1.0", "1.1", None])
def test_old_saved_scores_require_reaudit_without_erasing_evidence(auditor, old_rules):
    import json

    old = auditor.run("https://example.com/")
    old["rules_version"] = old_rules
    stored = json.dumps(old)
    with auditor.connection() as db:
        db.execute("UPDATE audits SET body=? WHERE id=?", (stored, old["audit_id"]))
    result = auditor.get(old["audit_id"])
    assert result["risk_score"] is None
    assert result["risk_level"] == "unassessed"
    assert result["requires_reaudit"] is True
    assert result["previous_rules_assessment"]["risk_score"] == 0
    assert len(auditor.plan(old["audit_id"])["steps"]) == 7
    assert auditor.appeal(old["audit_id"])["unresolved_checks"] == 7
    with auditor.connection() as db:
        assert (
            db.execute("SELECT body FROM audits WHERE id=?", (old["audit_id"],)).fetchone()[0]
            == stored
        )


def test_missing_policy_plan_and_honest_appeal(auditor: PolicyAuditor) -> None:
    original = auditor.fetcher

    def missing(url, raw, origin):
        page = original(url, raw, origin)
        page["html"] = "<p>A public shop homepage without linked policies or contact methods.</p>"
        return page

    auditor.fetcher = missing
    report = auditor.run("https://example.com/")
    assert report["risk_score"] == 70
    assert report["risk_level"] == "high"
    plan = auditor.plan(report["audit_id"])
    assert plan["steps"][0]["weight"] == 20
    appeal = auditor.appeal(report["audit_id"], "We are reviewing the return policy.")
    assert appeal["submitted"] is False
    assert appeal["unresolved_checks"] == 6
    assert "not independently verified" in appeal["draft"]
    assert "Items still requiring verification" in appeal["draft"]
    assert Path(appeal["raw_draft_path"]).read_text(encoding="utf-8") == appeal["draft"]


def test_blocked_site_never_gets_clean_score(auditor: PolicyAuditor) -> None:
    auditor.fetcher = lambda url, raw, origin: {"url": url, "usable": False, "html": "", "hops": []}
    report = auditor.run("https://example.com/")
    assert report["risk_score"] is None
    assert report["risk_level"] == "unassessed"
    assert all(c["status"] == "unknown" for c in report["checks"])


def test_fetch_budget_reports_incomplete_coverage(auditor: PolicyAuditor) -> None:
    report = auditor.run("https://example.com/", max_pages=1)
    assert len(report["pages"]) == 1
    assert report["risk_score"] is None
    with pytest.raises(ValueError):
        auditor.run("https://example.com/", max_pages=9)


def test_partial_coverage_cannot_receive_zero_score(
    auditor: PolicyAuditor,
) -> None:
    report = auditor.run("https://example.com/", max_pages=5)
    assert report["risk_score"] is None
    assert report["coverage"] < 1
    assert report["assessment_status"] == "partial"


@pytest.mark.parametrize(
    "url", ["http://example.com", "https://user:secret@example.com", "https://example.com:8443"]
)
def test_bad_urls_rejected(url: str) -> None:
    with pytest.raises(ValueError):
        normalize_url(url)


def test_dns_all_addresses_must_be_public(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        policy.socket,
        "getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443)), (2, 1, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(ValueError, match="blocked"):
        public_addresses("example.com")


def test_connections_pin_ip_and_keep_certificate_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    stream = SimpleNamespace(close=lambda: None)
    monkeypatch.setattr(policy, "public_addresses", lambda host: ["93.184.216.34"])
    monkeypatch.setattr(
        policy.socket, "create_connection", lambda addr, **kw: calls.append(addr) or stream
    )
    monkeypatch.setattr(
        policy.ssl,
        "create_default_context",
        lambda: SimpleNamespace(
            wrap_socket=lambda sock, **kw: calls.append(kw["server_hostname"]) or stream
        ),
    )
    connection = PinnedHTTPS("example.com", timeout=1)
    connection.connect()
    assert calls == [("93.184.216.34", 443), "example.com"]


@pytest.mark.parametrize("oversized,status", [(False, 500), (True, 200)])
def test_raw_download_not_truncated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, oversized: bool, status: int
) -> None:
    data = b"x" * (policy.LIMIT + 1) if oversized else b"<html>full server error\xff</html>"
    response = SimpleNamespace(
        status=status,
        read=io.BytesIO(data).read,
        getheader=lambda name, default="": "text/html" if name == "Content-Type" else default,
        getheaders=lambda: [("Content-Type", "text/html")],
    )
    monkeypatch.setattr(
        policy,
        "PinnedHTTPS",
        lambda *a, **k: SimpleNamespace(
            request=lambda *a, **k: None, getresponse=lambda: response, close=lambda: None
        ),
    )
    result = fetch_page("https://example.com/", tmp_path, "example.com")
    assert not result["usable"]
    assert Path(result["hops"][0]["raw_download_path"]).read_bytes() == data
    assert result["hops"][0]["download_complete"] is not oversized


def test_offsite_redirect_is_blocked_with_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    response = SimpleNamespace(
        status=302,
        read=io.BytesIO(b"redirect").read,
        getheader=lambda name, default="": "https://127.0.0.1/" if name == "Location" else default,
        getheaders=lambda: [("Location", "https://127.0.0.1/")],
    )
    monkeypatch.setattr(
        policy,
        "PinnedHTTPS",
        lambda *a, **k: SimpleNamespace(
            request=lambda *a, **k: None, getresponse=lambda: response, close=lambda: None
        ),
    )
    result = fetch_page("https://example.com/", tmp_path, "example.com")
    assert not result["usable"]
    assert Path(result["hops"][0]["raw_download_path"]).read_bytes() == b"redirect"
    assert Path(result["raw_error_path"]).is_file()


def test_weekly_persistence_disable_and_no_duplicate_run(
    auditor: PolicyAuditor, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = [100000.0]
    monkeypatch.setattr(policy.time, "time", lambda: clock[0])
    auditor.set_monitor("https://example.com/")
    first = auditor.run_due()["runs"]
    assert len(first) == 1 and first[0]["changed"]
    assert auditor.run_due()["runs"] == []
    restarted = PolicyAuditor(auditor.client, auditor.fetcher)
    assert restarted.monitoring()["monitors"][0]["last_audit"] == first[0]["audit_id"]
    clock[0] += policy.WEEK + 1
    second = restarted.run_due()["runs"]
    assert len(second) == 1 and not second[0]["changed"]
    restarted.set_monitor("https://example.com/", enabled=False)
    clock[0] += policy.WEEK + 1
    assert restarted.run_due()["runs"] == []


def test_monitor_account_changes_and_failure_retry(
    auditor: PolicyAuditor, monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = [100000.0]
    monkeypatch.setattr(policy.time, "time", lambda: clock[0])
    auditor.set_monitor("https://example.com/")
    auditor.run_due()
    clock[0] += policy.WEEK + 1
    monkeypatch.setattr(
        auditor.client, "request", lambda *a, **k: {"accountIssues": [{"title": "New issue"}]}
    )
    assert auditor.run_due()["runs"][0]["changed"]
    clock[0] += policy.WEEK + 1
    monkeypatch.setattr(
        auditor, "run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("worker failure"))
    )
    failure = auditor.run_due()["runs"][0]
    assert failure["status"] == "failed"
    assert "worker failure" in Path(failure["raw_error_path"]).read_text(encoding="utf-8")
    assert auditor.run_due()["runs"] == []


def test_scripts_do_not_supply_policy_evidence() -> None:
    page = Page("<script>contact support@example.com</script><p>Real content</p>")
    assert "support@example.com" not in page.text


def test_partial_transfer_retains_every_received_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_read(n):
        raise policy.http.client.IncompleteRead(b"partial-response", 999)

    response = SimpleNamespace(
        status=200,
        read=broken_read,
        getheader=lambda name, default="": "text/html" if name == "Content-Type" else default,
        getheaders=lambda: [("Content-Type", "text/html")],
    )
    monkeypatch.setattr(
        policy,
        "PinnedHTTPS",
        lambda *a, **k: SimpleNamespace(
            request=lambda *a, **k: None, getresponse=lambda: response, close=lambda: None
        ),
    )
    result = fetch_page("https://example.com/", tmp_path, "example.com")
    assert not result["usable"]
    hop = result["hops"][0]
    assert not hop["download_complete"]
    assert Path(hop["raw_download_path"]).read_bytes() == b"partial-response"
    assert hop["sha256"] == hashlib.sha256(b"partial-response").hexdigest()


def test_other_worker_lease_prevents_duplicate_audit(auditor: PolicyAuditor) -> None:
    auditor.set_monitor("https://example.com/")
    with auditor.connection() as db:
        db.execute("UPDATE monitors SET lease_until=?", (policy.time.time() + 100,))
    assert auditor.run_due()["runs"] == []


def test_active_run_is_not_reentered_by_other_worker(
    auditor: PolicyAuditor, monkeypatch: pytest.MonkeyPatch
) -> None:
    auditor.set_monitor("https://example.com/")
    other = PolicyAuditor(auditor.client, auditor.fetcher)
    original = auditor.run

    def interleaved(url):
        assert other.run_due()["runs"] == []
        return original(url)

    monkeypatch.setattr(auditor, "run", interleaved)
    assert len(auditor.run_due()["runs"]) == 1


def test_verified_default_tools(config, client, monkeypatch: pytest.MonkeyPatch) -> None:
    from gmc_mcp import server

    monkeypatch.setattr(server, "load_auth", lambda **kw: SimpleNamespace(account_label="test"))
    monkeypatch.setattr(server, "MerchantClient", lambda *a, **kw: client)
    mcp = server.build_server(config)
    tools = mcp._tool_manager._tools
    from gmc_mcp.public_tools import VERIFIED_TOOLS

    assert set(tools) == VERIFIED_TOOLS
    assert all(
        t in tools
        for t in [
            "gmc_list_products",
            "gmc_query_report",
            "gmc_get_checkout_settings",
            "gmc_generate_policy_appeal",
            "gmc_run_policy_monitors",
        ]
    )
