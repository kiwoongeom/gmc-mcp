"""Regressions for routes rejected by the real Merchant API."""

from types import SimpleNamespace

import pytest

from gmc_mcp.client import MerchantAPIError
from gmc_mcp.tools import (
    account_config,
    accounts,
    diagnostics,
    mca,
    products,
    reports,
    return_policies,
    reviews,
)


@pytest.fixture
def registered():
    functions = {}
    calls = []

    def request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return {"name": "test"}

    def paginate(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return iter([])

    client = SimpleNamespace(
        account_path=lambda: "accounts/123",
        request=request,
        paginate=paginate,
        config=SimpleNamespace(dry_run=True),
    )
    mcp = SimpleNamespace(tool=lambda: lambda f: functions.setdefault(f.__name__, f))
    for module in (account_config, accounts, mca, reviews, return_policies, products, reports):
        module.register(mcp, client)
    return functions, calls


@pytest.mark.parametrize(
    "tool,path",
    [
        ("gmc_list_relationships", "accounts/v1/accounts/123/relationships"),
        ("gmc_list_merchant_reviews", "reviews/v1alpha/accounts/123/merchantReviews"),
        ("gmc_list_product_reviews", "reviews/v1/accounts/123/productReviews"),
        ("gmc_get_latest_tos", "accounts/v1/termsOfService:retrieveLatest"),
    ],
)
def test_correct_live_routes(registered, tool, path):
    functions, calls = registered
    functions[tool]()
    assert calls[-1][0:2] == ("GET", path)


def test_tos_state_is_retrieval_not_nonexistent_list(registered):
    functions, calls = registered
    assert functions["gmc_list_tos_agreement_states"]() == {
        "count": 1,
        "states": [{"name": "test"}],
    }
    assert calls[-1][1].endswith("/termsOfServiceAgreementStates:retrieveForApplication")


def test_tos_accept_uses_account_and_region(registered):
    functions, calls = registered
    functions["gmc_accept_tos"]("termsOfService/123", region_code="KR")
    assert calls[-1] == (
        "POST",
        "accounts/v1/termsOfService/123:accept",
        {
            "params": {"account": "accounts/123", "regionCode": "KR"},
            "op": "accept_tos",
        },
    )
    with pytest.raises(ValueError):
        functions["gmc_accept_tos"]("termsOfService/123", agreement_state="invalid")


@pytest.mark.parametrize("kind,version", [("merchant", "v1alpha"), ("product", "v1")])
def test_review_insert_requires_custom_method_suffix(registered, kind, version):
    functions, calls = registered
    functions[f"gmc_insert_{kind}_review"]({"reviewId": "test"}, "accounts/123/dataSources/1")
    assert calls[-1][0:2] == ("POST", f"reviews/{version}/accounts/123/{kind}Reviews:insert")


def test_tax_is_explicitly_unsupported_without_network(registered):
    functions, calls = registered
    with pytest.raises(NotImplementedError, match="UNSUPPORTED_FEATURE"):
        functions["gmc_get_account_tax"]()
    with pytest.raises(NotImplementedError, match="UNSUPPORTED_FEATURE"):
        functions["gmc_update_account_tax"]([])
    assert calls == []


def test_google_preconditions_are_not_hidden_as_success():
    body = {
        "error": {
            "details": [
                {
                    "metadata": {
                        "REASON": "PERMISSION_DENIED_NOT_ALLOWLISTED_TO_USE_PROMOTION_PROGRAM"
                    }
                }
            ]
        }
    }
    error = MerchantAPIError(403, body)
    assert error.status == 403 and error.body == body
    assert "Enable the Promotions program" in str(error)


def test_program_state_uses_program_resource_and_review_submission_is_unsupported(registered):
    functions, calls = registered
    functions["gmc_get_program_review"]("shopping-ads")
    assert calls[-1][1] == "accounts/v1/accounts/123/programs/shopping-ads"
    with pytest.raises(NotImplementedError, match="UNSUPPORTED_FEATURE"):
        functions["gmc_request_program_review"]("shopping-ads")


def test_return_policy_patch_is_not_invented(registered):
    functions, calls = registered
    with pytest.raises(NotImplementedError, match="UNSUPPORTED_FEATURE"):
        functions["gmc_update_return_policy"]("123", {})
    assert calls == []


def test_aggregation_proposes_real_account_service(registered):
    functions, calls = registered
    functions["gmc_create_aggregation"]("accounts/456")
    assert calls[-1][1] == "accounts/v1/accounts/123/services:propose"
    assert calls[-1][2]["json_body"] == {
        "provider": "providers/456",
        "accountService": {"accountAggregation": {}},
    }
    functions["gmc_propose_account_service"]("providers/456", "ACCOUNT_MANAGEMENT")
    assert calls[-1][2]["json_body"]["accountService"] == {"accountManagement": {}}


def test_filtered_bulk_delete_never_ignores_filter(registered):
    functions, calls = registered
    with pytest.raises(ValueError, match="no products were deleted"):
        functions["gmc_bulk_delete_products"](confirm="DELETE", filter_status="DISAPPROVED")
    assert calls == []


def test_aggregation_removal_rejects_only_aggregation_services():
    functions = {}
    calls = []
    services = [
        {"name": "accounts/123/services/1", "accountAggregation": {}},
        {"name": "accounts/123/services/2", "accountManagement": {}},
    ]
    client = SimpleNamespace(
        account_path=lambda: "accounts/123",
        config=SimpleNamespace(dry_run=True),
        paginate=lambda *a, **k: iter(services),
        request=lambda *a, **k: calls.append((a, k)),
    )
    mca.register(
        SimpleNamespace(tool=lambda: lambda f: functions.setdefault(f.__name__, f)), client
    )
    result = functions["gmc_delete_aggregation"]()
    assert result["status"] == "dry_run"
    assert len(calls) == 1
    assert calls[0][0] == ("POST", "accounts/v1/accounts/123/services/1:reject")


@pytest.mark.parametrize(
    "name,args,required",
    [
        (
            "gmc_product_performance",
            {"start_date": "2026-11-01", "end_date": "2026-11-10"},
            ["click_through_rate", "conversion_value"],
        ),
        ("gmc_zero_click_products", {}, ["click_through_rate", "date BETWEEN"]),
        ("gmc_price_competitiveness", {}, ["SELECT id, report_country_code"]),
        (
            "gmc_best_sellers",
            {},
            ["report_category_id", "report_granularity = 'WEEKLY'", "report_date"],
        ),
        ("gmc_price_insights", {}, ["SELECT id,"]),
        (
            "gmc_competitive_visibility_top_merchants",
            {"report_category_id": 166},
            ["traffic_source", "report_category_id = 166", "date BETWEEN"],
        ),
    ],
)
def test_reports_include_real_required_fields_and_filters(registered, name, args, required):
    functions, calls = registered
    functions[name](**args)
    query = calls[-1][2]["json_body"]["query"]
    assert all(part in query for part in required)
    assert "conversion_value_micros" not in query


def test_missing_audit_file_is_not_a_crash(tmp_path):
    from gmc_mcp.audit import AuditLog

    assert AuditLog(tmp_path / "missing.jsonl").find("absent") is None


def test_export_preserves_other_resources_and_full_error(client, monkeypatch, tmp_path):
    import hashlib
    from pathlib import Path

    functions = {}
    mcp = SimpleNamespace(tool=lambda: lambda f: functions.setdefault(f.__name__, f))

    def request(method, path, **kwargs):
        if "/promotions" in path:
            raise MerchantAPIError(403, {"error": {"message": "Not enabled"}})
        if "/products" in path:
            return {"products": [{"name": "one"}, {"name": "two"}]}
        return {}

    monkeypatch.setattr(client, "request", request)
    diagnostics.register(mcp, client)
    result = functions["gmc_export_all"](str(tmp_path / "export"), max_per_resource=1)
    assert result["status"] == "partial"
    assert result["resources"]["products"]["count"] == 1
    error = result["resources"]["promotions"]
    raw = Path(error["raw_error_path"]).read_bytes()
    assert b"Not enabled" in raw
    assert hashlib.sha256(raw).hexdigest() == error["sha256"]


def test_rollback_refuses_unapplied_dry_run(client):
    from gmc_mcp.audit import AuditLog

    functions = {}
    mcp = SimpleNamespace(tool=lambda: lambda f: functions.setdefault(f.__name__, f))
    diagnostics.register(mcp, client)
    aid = AuditLog(client.config.audit_log).record(
        op="update_business_info",
        resource="test",
        method="PATCH",
        url="test",
        before={"name": "before"},
        dry_run=True,
    )
    assert "changed no remote data" in functions["gmc_rollback"](aid, confirm="ROLLBACK")["error"]
