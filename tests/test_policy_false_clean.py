"""Regression checks for false clean scores, independent of rule implementation."""

import hashlib
import io
from pathlib import Path

import pytest

from gmc_mcp import policy


@pytest.mark.parametrize(
    "failure",
    [
        "soft404",
        "nested_soft404",
        "korean_soft404",
        "homepage_fallback",
        "homepage_whitespace",
        "http404",
        "http403",
        "challenge",
        "partial",
        "single_missing",
        "footer_only",
        "footer_form",
        "valid",
    ],
)
def test_nonexistent_policy_pages_do_not_pass(client, monkeypatch, failure):
    links = [
        ("contact", "Contact"),
        ("about", "About our company"),
        ("returns", "Returns"),
        ("shipping", "Shipping"),
        ("terms", "Terms"),
        ("privacy", "Privacy"),
    ]
    footer = (
        "Contact support@example.com. Newsletter: 30 days, refund options and free shipping costs."
    )
    home = (
        "<html><h1>A demonstration storefront</h1>"
        + "".join(f'<a href="/{path}">{label}</a>' for path, label in links)
        + "<footer>"
        + footer
        + "</footer></html>"
    )
    missing = (
        "<html><title>404 - Page not found</title><h1>Page not found</h1><footer>"
        + footer
        + "</footer></html>"
    )

    class Response:
        status = 200

        def __init__(self, html):
            self.read = io.BytesIO(html.encode()).read

        def getheader(self, name, default=""):
            return "text/html" if name == "Content-Type" else default

        def getheaders(self):
            return [("Content-Type", "text/html")]

    class Connection:
        def __init__(self, *args, **kwargs):
            self.path = "/"

        def request(self, method, path, **kwargs):
            self.path = path

        def getresponse(self):
            valid = "<html><h1>Store policy</h1><p>" + footer * 3 + "</p></html>"
            body = missing
            if failure == "nested_soft404":
                body = missing.replace(
                    "<h1>Page not found</h1>", "<h1><span>Page</span> not found</h1>"
                ).replace("404 - Page not found", "Store")
            elif failure == "korean_soft404":
                body = missing.replace("404 - Page not found", "안내").replace(
                    "Page not found", "페이지를 찾을 수 없습니다"
                )
            elif failure == "challenge":
                body = "<title>Just a moment</title>" + footer
            elif failure == "homepage_whitespace":
                body = home.replace(" ", "  ")
            elif failure == "homepage_fallback":
                body = home
            elif failure in {"footer_only", "footer_form"}:
                body = (
                    "<html><main><h1>Policy</h1></main><footer>"
                    + footer * 3
                    + ('<form><input name="newsletter"></form>' if failure == "footer_form" else "")
                    + "</footer></html>"
                )
            elif failure == "valid" or (failure == "single_missing" and self.path != "/privacy"):
                body = valid
            response = Response(home if self.path == "/" else body)
            if self.path != "/":
                if failure in {"http404", "http403"}:
                    response.status = int(failure[4:])
                elif failure == "partial":

                    def interrupted(*args):
                        raise policy.http.client.IncompleteRead(body.encode(), 100)

                    response.read = interrupted
            return response

        def close(self):
            pass

    monkeypatch.setattr(policy, "PinnedHTTPS", Connection)
    monkeypatch.setattr(client, "request", lambda *a, **k: {"accountIssues": []})
    report = policy.PolicyAuditor(client).run("https://example.com/")
    for page in report["pages"]:
        for hop in page["hops"]:
            raw = Path(hop["raw_download_path"]).read_bytes()
            assert len(raw) == hop["bytes"]
            assert hashlib.sha256(raw).hexdigest() == hop["sha256"]
    if failure == "valid":
        assert report["risk_score"] == 0
        assert report["assessment_status"] == "automated_checks_completed"
        return
    if failure in {"footer_only", "footer_form"}:
        assert report["risk_score"] == 70
        assert all(c["status"] == "fail" for c in report["checks"] if c["id"] != "homepage")
        return
    assert report["risk_score"] is None
    assert report["risk_level"] == "unassessed"
    assert report["assessment_status"] == "partial"
    if failure != "single_missing":
        assert not any(c["status"] == "pass" for c in report["checks"] if c["id"] != "homepage")
    auditor = policy.PolicyAuditor(client)
    assert auditor.plan(report["audit_id"])["steps"]
    assert auditor.appeal(report["audit_id"], "Review pending")["submitted"] is False
