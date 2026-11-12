"""Evidence-based storefront checks. Scores are heuristics, never Google verdicts."""

from __future__ import annotations

import hashlib
import http.client
import ipaddress
import json
import re
import socket
import sqlite3
import ssl
import time
import traceback
import uuid
from contextlib import contextmanager
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit, urlunsplit

from .client import MerchantClient

POLICY_SOURCE = "https://support.google.com/merchants/answer/6150127"
RULE_SOURCE = "https://support.google.com/merchants/answer/6150244"
WEEK = 7 * 24 * 3600
RULES_VERSION = "1.2"
LIMIT = 2 * 1024 * 1024
CATEGORIES = {
    "contact": r"contact|support|customer.service|문의|고객센터|연락",
    "identity": r"about|our.story|company|소개|회사",
    "returns": r"return|refund|반품|환불",
    "shipping": r"shipping|delivery|배송",
    "terms": r"terms|conditions|이용약관",
    "privacy": r"privacy|개인정보",
}
FIXES = {
    "homepage": "Ensure the storefront loads publicly over HTTPS without a login or bot challenge.",
    "contact": "Publish a working contact email, telephone number or contact form; verify it manually.",
    "identity": "Publish the business identity and About information; match it to Merchant Center.",
    "returns": "Publish return conditions, the return window and refund processing terms, or a clear no-return policy where lawful.",
    "shipping": "Publish delivery timeframes and shipping charges, including any restrictions.",
    "terms": "Make the store terms accessible from the storefront navigation or footer.",
    "privacy": "Make the privacy policy accessible from the storefront navigation or footer.",
}
WEIGHTS = {
    "homepage": 30,
    "contact": 20,
    "identity": 10,
    "returns": 20,
    "shipping": 10,
    "terms": 5,
    "privacy": 5,
}


def normalize_url(value: str) -> str:
    parsed = urlsplit(value if "://" in value else "https://" + value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
    ):
        raise ValueError("Use a public HTTPS storefront URL without credentials or custom ports")
    host = parsed.hostname.encode("idna").decode("ascii").lower()
    return urlunsplit(("https", f"[{host}]" if ":" in host else host, parsed.path or "/", "", ""))


class Page(HTMLParser):
    def __init__(self, html: str):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.content_parts: list[str] = []
        self.content_links: list[tuple[str, str]] = []
        self.content_stack: list[tuple[str, bool]] = []
        self.current_is_content = False
        self.has_content_form = False
        self.hidden = 0
        self.current: tuple[str, list[str]] | None = None
        self.has_form = False
        self.heading_parts: list[str] = []
        self.heading_depth = 0
        self.feed(html)
        self.text = " ".join(self.parts)
        self.content_text = " ".join(self.content_parts)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        excluded = (
            bool(self.content_stack and self.content_stack[-1][1])
            or tag in {"head", "header", "footer", "nav", "aside"}
            or values.get("role") in {"banner", "contentinfo", "navigation", "complementary"}
            or "hidden" in values
            or values.get("aria-hidden") == "true"
        )
        if tag not in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }:
            self.content_stack.append((tag, excluded))
        if tag in {"title", "h1"}:
            self.heading_depth += 1
        if tag in {"script", "style", "noscript"}:
            self.hidden += 1
        if tag == "form":
            self.has_form = True
            if not excluded and not self.hidden:
                self.has_content_form = True
        if tag == "a" and values.get("href"):
            self.current = (str(values["href"]), [])
            self.current_is_content = not excluded

    def handle_data(self, data: str) -> None:
        if not self.hidden and data.strip():
            if self.heading_depth:
                self.heading_parts.append(data.strip())
            self.parts.append(data.strip())
            if not self.content_stack or not self.content_stack[-1][1]:
                self.content_parts.append(data.strip())
            if self.current:
                self.current[1].append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag in {"title", "h1"}:
            self.heading_depth = max(0, self.heading_depth - 1)
        if tag in {"script", "style", "noscript"}:
            self.hidden = max(0, self.hidden - 1)
        if tag == "a" and self.current:
            self.links.append((self.current[0], " ".join(self.current[1])))
            if self.current_is_content:
                self.content_links.append(self.links[-1])
            self.current = None
        for index in range(len(self.content_stack) - 1, -1, -1):
            if self.content_stack[index][0] == tag:
                del self.content_stack[index:]
                break


def public_addresses(host: str) -> list[str]:
    addresses = list(
        dict.fromkeys(
            str(row[4][0]) for row in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        )
    )
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError("Private, loopback, link-local and reserved destinations are blocked")
    return addresses


class PinnedHTTPS(http.client.HTTPSConnection):
    """Connect to the validated IP while keeping TLS hostname verification/SNI."""

    def connect(self) -> None:
        address = public_addresses(self.host)[0]
        stream = socket.create_connection((address, 443), timeout=self.timeout)
        try:
            self.sock = ssl.create_default_context().wrap_socket(stream, server_hostname=self.host)
        except BaseException:
            stream.close()
            raise


def fetch_page(url: str, raw_dir: Path, origin: str) -> dict[str, Any]:
    """Bounded public GETs; retain every downloaded byte, including error pages."""
    hops: list[dict[str, Any]] = []
    for _ in range(5):
        try:
            url = normalize_url(url)
            host = urlsplit(url).hostname or ""
            if host.removeprefix("www.") != origin.removeprefix("www."):
                raise ValueError("Off-site redirects are not followed")
        except ValueError:
            path = raw_dir / f"{uuid.uuid4().hex}.error.txt"
            path.write_text(traceback.format_exc(), encoding="utf-8")
            return {
                "url": url,
                "usable": False,
                "html": "",
                "hops": hops,
                "raw_error_path": str(path),
            }
        connection = PinnedHTTPS(host, timeout=4)
        try:
            connection.request(
                "GET",
                urlsplit(url).path or "/",
                headers={"User-Agent": "gmc-mcp-policy-audit/1.0", "Accept": "text/html"},
            )
            response = connection.getresponse()
            path = raw_dir / f"{uuid.uuid4().hex}.download"
            record: dict[str, Any] = {
                "url": url,
                "status": response.status,
                "headers": response.getheaders(),
                "raw_download_path": str(path),
                "bytes": 0,
                "sha256": hashlib.sha256(b"").hexdigest(),
                "download_complete": False,
            }
            hops.append(record)
            digest = hashlib.sha256()
            remaining = LIMIT + 1
            broken = False
            with path.open("wb") as stream:
                while remaining:
                    try:
                        chunk = getattr(response, "read1", response.read)(min(65536, remaining))
                    except http.client.IncompleteRead as exc:
                        chunk = exc.partial
                        broken = True
                    if chunk:
                        stream.write(chunk)
                        digest.update(chunk)
                        remaining -= len(chunk)
                        record["bytes"] += len(chunk)
                        record["sha256"] = digest.hexdigest()
                    if not chunk or broken:
                        break
            complete = remaining > 0 and not broken
            record["download_complete"] = complete
            data = path.read_bytes() if complete else b""
            if response.status in {301, 302, 303, 307, 308}:
                target = response.getheader("Location")
                if not target:
                    break
                url = urljoin(url, target)
                continue
            content_type = response.getheader("Content-Type", "")
            html = data.decode("utf-8", errors="replace")
            blocked = bool(
                re.search(
                    r"<title[^>]*>\s*(client challenge|just a moment|access denied)", html, re.I
                )
            )
            soft404 = bool(
                re.search(
                    r"\b404\b|\bnot\s+found\b|페이지를?\s*찾을\s*수\s*없|존재하지\s*않",
                    " ".join(Page(html).heading_parts),
                    re.I,
                )
            )
            usable = (
                response.status == 200
                and complete
                and "html" in content_type
                and not blocked
                and not soft404
            )
            reason = (
                "incomplete_download"
                if not complete
                else "http_error"
                if response.status != 200
                else "non_html"
                if "html" not in content_type
                else "blocked"
                if blocked
                else "soft_404"
                if soft404
                else None
            )
            return {
                "url": url,
                "usable": usable,
                "html": html if usable else "",
                "hops": hops,
                "unusable_reason": reason,
            }
        except Exception:
            path = raw_dir / f"{uuid.uuid4().hex}.error.txt"
            path.write_text(traceback.format_exc(), encoding="utf-8")
            return {
                "url": url,
                "usable": False,
                "html": "",
                "hops": hops,
                "raw_error_path": str(path),
            }
        finally:
            connection.close()
    return {
        "url": url,
        "usable": False,
        "html": "",
        "hops": hops,
        "error": "Redirect chain did not reach a usable page",
    }


class PolicyAuditor:
    def __init__(self, client: MerchantClient, fetcher=fetch_page):
        self.client = client
        self.root = client.config.audit_log.parent / "policy" / client.config.effective_account_id
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = self.root / "policy.sqlite3"
        self.fetcher = fetcher
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS audits(id TEXT PRIMARY KEY, created REAL, url TEXT, body TEXT);
                CREATE TABLE IF NOT EXISTS monitors(url TEXT PRIMARY KEY, enabled INTEGER, next_due REAL,
                    lease_until REAL DEFAULT 0, last_audit TEXT, last_error TEXT, last_alert TEXT);
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.db, timeout=20)
        try:
            with db:
                yield db
        finally:
            db.close()

    def get(self, audit_id: str) -> dict[str, Any]:
        with self.connection() as db:
            row = db.execute("SELECT body FROM audits WHERE id=?", (audit_id,)).fetchone()
        if not row:
            raise ValueError("Audit ID not found for this Merchant Center account")
        audit = json.loads(row[0])
        if audit.get("rules_version") != RULES_VERSION:
            # Preserve the stored evidence; never present a superseded score as current.
            audit["previous_rules_assessment"] = {
                key: audit.get(key)
                for key in ("risk_score", "risk_level", "assessment_status", "coverage", "checks")
            }
            audit.update(
                risk_score=None,
                risk_level="unassessed",
                assessment_status="partial",
                coverage=0.0,
                requires_reaudit=True,
                checks=[
                    {
                        **check,
                        "status": "unknown",
                        "evidence": "Stored audit uses superseded rules; run a new audit before relying on this check",
                    }
                    for check in audit["checks"]
                ],
            )
        return audit

    def list_audits(self, limit: int = 20) -> dict[str, Any]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT id,created,url FROM audits ORDER BY created DESC LIMIT ?",
                (max(1, min(limit, 100)),),
            ).fetchall()
        return {
            "audits": [{"audit_id": r[0], "created_utc_epoch": r[1], "url": r[2]} for r in rows]
        }

    def run(self, url: str, max_pages: int = 8, include_account: bool = True) -> dict[str, Any]:
        url = normalize_url(url)
        if not 1 <= max_pages <= 8:
            raise ValueError("max_pages must be between 1 and 8")
        audit_id = uuid.uuid4().hex
        raw = self.root / audit_id
        raw.mkdir()
        checks = []
        pages = []
        fetched: dict[str, dict] = {}
        deadline = time.monotonic() + 24

        def fetch(target: str) -> dict:
            if target not in fetched and len(fetched) < max_pages and time.monotonic() < deadline:
                fetched[target] = self.fetcher(target, raw, urlsplit(url).hostname or "")
                pages.append({k: v for k, v in fetched[target].items() if k != "html"})
            return fetched.get(target, {"usable": False, "html": "", "url": target})

        home = fetch(url)
        parsed = Page(home["html"])
        home_ok = home["usable"] and len(parsed.text) >= 40
        checks.append(
            self.check(
                "homepage",
                "pass" if home_ok else "unknown",
                url,
                "Public HTML retrieved"
                if home_ok
                else "Unavailable, blocked, non-HTML or incomplete response",
            )
        )
        for name, pattern in CATEGORIES.items():
            candidate = None
            for href, label in parsed.links:
                if re.search(pattern, href + " " + label, re.I):
                    try:
                        target = normalize_url(urljoin(home["url"], href))
                    except ValueError:
                        continue
                    if urlsplit(target).hostname == urlsplit(home["url"]).hostname:
                        candidate = target
                        break
            page = fetch(candidate) if candidate else home
            document = Page(page["html"])
            # Shared navigation/footer text is not independent policy evidence.
            text = document.content_text if candidate else document.text
            duplicates_home = bool(
                candidate
                and (
                    page["url"] == home["url"]
                    or " ".join(document.text.split()) == " ".join(parsed.text.split())
                )
            )
            if not home_ok or not page["usable"] or duplicates_home:
                status, evidence = (
                    "unknown",
                    "Page could not be assessed: "
                    + str(page.get("unusable_reason") or "unavailable"),
                )
                if duplicates_home:
                    evidence = "Policy URL returned the same content as the homepage; policy content was not independently observed"
            elif name == "contact":
                match = re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}|\+?\d[\d ()-]{7,}\d", text, re.I)
                links = document.content_links if candidate else document.links
                mail_link = any(h.startswith(("mailto:", "tel:")) for h, _ in links)
                observed = bool(match or mail_link or (candidate and document.has_content_form))
                status = "pass" if observed else "fail"
                evidence = (
                    "Contact method observed; validity requires manual verification"
                    if observed
                    else "No contact method observed in sampled public pages"
                )
            else:
                observed = candidate is not None and len(text) >= 80
                status = "pass" if observed else "fail"
                evidence = (
                    "Linked substantive page observed; content/legal adequacy requires review"
                    if observed
                    else "Substantive linked page not observed within this bounded audit"
                )
                if observed and name in {"returns", "shipping"}:
                    time_terms = bool(
                        re.search(
                            r"\d+\s*(?:business\s*)?(?:days?|weeks?|일|주)|no returns|non.returnable|반품 불가",
                            text,
                            re.I,
                        )
                    )
                    detail = (
                        bool(re.search(r"refund|환불", text, re.I))
                        if name == "returns"
                        else bool(re.search(r"cost|charge|free|fee|배송비|무료", text, re.I))
                    )
                    status = "pass" if time_terms and detail else "fail"
                    evidence = (
                        "Timeframe and refund/shipping-cost wording observed"
                        if status == "pass"
                        else "Verify timeframe and refund/shipping-cost wording; automatic text check did not find both"
                    )
            checks.append(self.check(name, status, page["url"], evidence))
        account = {"status": "not_requested"}
        if include_account:
            try:
                payload = self.client.request(
                    "GET",
                    f"accounts/v1/{self.client.account_path()}/issues",
                    params={"languageCode": "en"},
                )
                path = raw / "account-issues.json"
                path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                account = {
                    "status": "checked",
                    "issues": payload.get("accountIssues", []),
                    "raw_response_path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            except Exception:
                path = raw / "account-error.txt"
                path.write_text(traceback.format_exc(), encoding="utf-8")
                account = {"status": "unknown", "raw_error_path": str(path)}
        coverage = sum(c["status"] != "unknown" for c in checks) / len(checks)
        score = (
            sum(c["weight"] for c in checks if c["status"] == "fail")
            if home_ok and coverage == 1
            else None
        )
        result = {
            "audit_id": audit_id,
            "url": url,
            "created_utc_epoch": time.time(),
            "rules_version": RULES_VERSION,
            "risk_score": score,
            "risk_scope": "Sampled storefront text only; Google-reported account issues are shown independently",
            "assessment_status": "partial"
            if score is None or coverage < 1 or (include_account and account["status"] != "checked")
            else "automated_checks_completed",
            "risk_level": "unassessed"
            if score is None
            else "high"
            if score >= 40
            else "medium"
            if score >= 15
            else "low",
            "score_meaning": "Heuristic observed-risk score, 0=lowest observed risk, 100=highest. Not a Google score or approval guarantee.",
            "coverage": round(coverage, 3),
            "checks": checks,
            "account": account,
            "pages": pages,
            "manual_review_required": [
                "Checkout/payment flow",
                "Product claims and price/feed consistency",
                "Business identity verification",
                "Full Google policy compliance",
            ],
            "policy_sources": [POLICY_SOURCE, RULE_SOURCE],
        }
        with self.connection() as db:
            db.execute(
                "INSERT INTO audits VALUES(?,?,?,?)",
                (audit_id, result["created_utc_epoch"], url, json.dumps(result)),
            )
        return result

    @staticmethod
    def check(name: str, status: str, url: str, evidence: str) -> dict:
        return {
            "id": name,
            "status": status,
            "weight": WEIGHTS[name],
            "url": url,
            "evidence": evidence,
            "recommendation": FIXES[name],
            "source": RULE_SOURCE,
        }

    def plan(self, audit_id: str) -> dict:
        audit = self.get(audit_id)
        items = sorted(
            (c for c in audit["checks"] if c["status"] != "pass"),
            key=lambda c: c["weight"],
            reverse=True,
        )
        return {
            "audit_id": audit_id,
            "steps": [
                {
                    **c,
                    "priority": index + 1,
                    "verification": "Correct or verify this item, then run a new audit; do not treat a plan as a completed fix",
                }
                for index, c in enumerate(items)
            ],
            "account_issues": audit["account"].get("issues", []),
            "manual_review_required": audit["manual_review_required"],
        }

    def appeal(self, audit_id: str, merchant_statement: str = "") -> dict:
        audit = self.get(audit_id)
        plan = self.plan(audit_id)
        draft = (
            f"Subject: Request for Merchant Center policy review — {audit['url']}\n\n"
            f"Please review the Merchant Center account associated with {audit['url']}.\n"
            f"We performed a limited storefront audit (reference {audit_id}).\n\n"
            "Items still requiring verification or remediation:\n"
            + "\n".join(f"- {c['id']}: {c['recommendation']}" for c in plan["steps"])
            + "\n\nMerchant-provided statement (not independently verified):\n"
            + (
                merchant_statement
                or "[Add factual changes, dates and supporting evidence before submission.]"
            )
            + "\n\nGoogle-reported account issues (as retrieved; not proof they are resolved):\n"
            + json.dumps(
                {
                    "status": audit["account"]["status"],
                    "issues": audit["account"].get("issues", []),
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n\n[Add the exact Google issue, account ID and relevant supporting evidence. "
            "Complete identity, checkout and product-policy checks before submitting through Merchant Center.]"
        )
        path = self.root / audit_id / "appeal-draft.txt"
        path.write_text(draft, encoding="utf-8")
        return {
            "audit_id": audit_id,
            "draft": draft,
            "raw_draft_path": str(path),
            "status": "draft_requires_merchant_review",
            "submitted": False,
            "unresolved_checks": len(plan["steps"]),
            "approval_guaranteed": False,
        }

    def set_monitor(self, url: str, enabled: bool = True) -> dict:
        url = normalize_url(url)
        # Validate immediately; the pinned fetcher validates DNS again when executing.
        if enabled:
            public_addresses(urlsplit(url).hostname or "")
        with self.connection() as db:
            db.execute(
                "INSERT INTO monitors(url,enabled,next_due) VALUES(?,?,?) "
                "ON CONFLICT(url) DO UPDATE SET enabled=excluded.enabled",
                (url, int(enabled), time.time()),
            )
        return {
            "url": url,
            "enabled": enabled,
            "interval_days": 7,
            "worker_required": "Schedule gmc-mcp --env <file> policy-monitor-run hourly using your OS scheduler",
        }

    def monitoring(self) -> dict:
        with self.connection() as db:
            db.row_factory = sqlite3.Row
            rows = [dict(r) for r in db.execute("SELECT * FROM monitors")]
        for r in rows:
            if r["last_alert"]:
                r["last_alert"] = json.loads(r["last_alert"])
        return {
            "monitors": rows,
            "interval_days": 7,
            "delivery": "Persisted local alerts; inspect this tool or worker JSON. No emails or external notifications are sent.",
        }

    def run_due(self) -> dict:
        now = time.time()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            rows = db.execute(
                "SELECT url,last_audit FROM monitors WHERE enabled=1 AND next_due<=? AND lease_until<=?",
                (now, now),
            ).fetchall()
        results = []
        for url, previous in rows:
            with self.connection() as db:
                db.execute("BEGIN IMMEDIATE")
                claimed = db.execute(
                    "UPDATE monitors SET lease_until=? WHERE url=? AND enabled=1 AND next_due<=? AND lease_until<=?",
                    (time.time() + 1200, url, time.time(), time.time()),
                ).rowcount
            if not claimed:
                continue
            try:
                result = self.run(url)
                old = self.get(previous) if previous else None
                alert = {
                    "audit_id": result["audit_id"],
                    "risk_score": result["risk_score"],
                    "previous_risk_score": old["risk_score"] if old else None,
                    "changed": old is None
                    or old["risk_score"] != result["risk_score"]
                    or old["checks"] != result["checks"]
                    or old["account"].get("issues") != result["account"].get("issues"),
                    "account_status": result["account"]["status"],
                    "incomplete": result["assessment_status"] != "automated_checks_completed",
                }
                with self.connection() as db:
                    db.execute(
                        "UPDATE monitors SET next_due=?,lease_until=0,last_audit=?,last_error=NULL,last_alert=? WHERE url=?",
                        (time.time() + WEEK, result["audit_id"], json.dumps(alert), url),
                    )
                results.append({"url": url, "status": "completed", **alert})
            except Exception:
                path = self.root / f"monitor-error-{uuid.uuid4().hex}.txt"
                path.write_text(traceback.format_exc(), encoding="utf-8")
                with self.connection() as db:
                    db.execute(
                        "UPDATE monitors SET next_due=?,lease_until=0,last_error=? WHERE url=?",
                        (time.time() + 3600, str(path), url),
                    )
                results.append({"url": url, "status": "failed", "raw_error_path": str(path)})
        return {"runs": results}
