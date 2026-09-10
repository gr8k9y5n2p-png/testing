"""GET /distributions?category= — server-side Paid History filter.

Reuses the same Morningstar-style vocabulary as GET /funds and
GET /funds/categories. Never invents funds, categories, or amounts.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.crud import (
    _FUND_SEARCH_COLUMNS,
    _filter_stmt,
    fund_identifiers_matching_category,
    search_distributions,
)


def _record(
    *,
    fund_family: str,
    fund_name: str,
    ticker: str,
    estimate_type: str,
    amount: str,
    as_of: str,
    publication_stage: str,
    ex_date: str | None = None,
) -> dict:
    payload = {
        "fund_family": fund_family,
        "fund_name": fund_name,
        "ticker": ticker,
        "estimate_type": estimate_type,
        "amount": amount,
        "amount_unit": "per_share",
        "as_of": as_of,
        "publication_stage": publication_stage,
    }
    if ex_date:
        payload["ex_date"] = ex_date
    return payload


def _seed_paid_history_categories(client: TestClient) -> None:
    """Stored flagship rows only. Amounts are test fixtures, not invented live data."""
    response = client.post(
        "/ingest/distributions",
        json={
            "records": [
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard 500 Index Fund",
                    ticker="VFIAX",
                    estimate_type="long_term_capital_gains",
                    amount="1.10",
                    as_of="2025-12-16",
                    publication_stage="final",
                    ex_date="2025-12-16",
                ),
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard 500 Index Fund",
                    ticker="VFIAX",
                    estimate_type="short_term_capital_gains",
                    amount="0.20",
                    as_of="2025-12-16",
                    publication_stage="final",
                    ex_date="2025-12-16",
                ),
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard 500 Index Fund",
                    ticker="VFIAX",
                    estimate_type="long_term_capital_gains",
                    amount="0.90",
                    as_of="2024-12-17",
                    publication_stage="final",
                    ex_date="2024-12-17",
                ),
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard Balanced Index Fund",
                    ticker="VBIAX",
                    estimate_type="ordinary_income",
                    amount="0.10",
                    as_of="2025-12-17",
                    publication_stage="final",
                    ex_date="2025-12-17",
                ),
                _record(
                    fund_family="Dodge & Cox",
                    fund_name="Dodge & Cox Income Fund",
                    ticker="DODIX",
                    estimate_type="ordinary_income",
                    amount="0.13",
                    as_of="2025-12-15",
                    publication_stage="final",
                    ex_date="2025-12-15",
                ),
                _record(
                    fund_family="American Funds",
                    fund_name="AMCAP Fund",
                    ticker="AMCPX",
                    estimate_type="long_term_capital_gains",
                    amount="2.15",
                    as_of="2025-12-12",
                    publication_stage="final",
                    ex_date="2025-12-12",
                ),
            ]
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["created"] == 6


def test_distributions_category_alone(client: TestClient) -> None:
    _seed_paid_history_categories(client)

    unfiltered = client.get("/distributions", params={"page_size": 50})
    assert unfiltered.status_code == 200
    assert unfiltered.json()["total"] == 6

    blend = client.get("/distributions", params={"category": "Large Blend", "page_size": 50})
    assert blend.status_code == 200
    body = blend.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
    assert {item["ticker"] for item in body["items"]} == {"VFIAX"}
    assert all(item["category"] == "Large Blend" for item in body["items"])
    assert all(item["raw_payload"] is None for item in body["items"])

    page1 = client.get("/distributions", params={"category": "Large Blend", "page": 1, "page_size": 2})
    page2 = client.get("/distributions", params={"category": "Large Blend", "page": 2, "page_size": 2})
    assert page1.json()["total"] == page2.json()["total"] == 3
    assert len(page1.json()["items"]) == 2
    assert len(page2.json()["items"]) == 1
    assert page1.json()["items"][0]["id"] != page2.json()["items"][0]["id"]


def test_distributions_category_plus_year_window(client: TestClient) -> None:
    _seed_paid_history_categories(client)

    year = client.get(
        "/distributions",
        params={
            "publication_stage": "final",
            "ex_date_from": "2025-01-01",
            "ex_date_to": "2025-12-31",
            "category": "Large Blend",
            "limit": 50,
        },
    )
    assert year.status_code == 200
    body = year.json()
    assert body["total"] == 2
    assert body["page_size"] == 50
    assert {item["ticker"] for item in body["items"]} == {"VFIAX"}
    assert all(item["category"] == "Large Blend" for item in body["items"])
    assert all(item["ex_date"].startswith("2025-") for item in body["items"])
    assert all(item["publication_stage"] == "final" for item in body["items"])

    prior = client.get(
        "/distributions",
        params={
            "category": "Large Blend",
            "ex_date_from": "2024-01-01",
            "ex_date_to": "2024-12-31",
        },
    )
    assert prior.json()["total"] == 1
    assert prior.json()["items"][0]["ex_date"] == "2024-12-17"


def test_distributions_category_plus_fund_family(client: TestClient) -> None:
    _seed_paid_history_categories(client)

    vanguard = client.get(
        "/distributions",
        params={"category": "Large Blend", "fund_family": "Vanguard", "page_size": 50},
    )
    assert vanguard.status_code == 200
    assert vanguard.json()["total"] == 3
    assert all(item["fund_family"] == "Vanguard" for item in vanguard.json()["items"])
    assert all(item["category"] == "Large Blend" for item in vanguard.json()["items"])

    dodge = client.get(
        "/distributions",
        params={"category": "Large Blend", "fund_family": "Dodge"},
    )
    assert dodge.status_code == 200
    assert dodge.json()["total"] == 0
    assert dodge.json()["items"] == []

    bond = client.get(
        "/distributions",
        params={"category": "Intermediate Core Bond", "fund_family": "Dodge"},
    )
    assert bond.json()["total"] == 1
    assert bond.json()["items"][0]["ticker"] == "DODIX"


def test_distributions_unknown_category_empty_total(client: TestClient) -> None:
    _seed_paid_history_categories(client)

    empty = client.get("/distributions", params={"category": "Not A Real Category"})
    assert empty.status_code == 200
    assert empty.json()["total"] == 0
    assert empty.json()["items"] == []

    alias = client.get("/distributions", params={"category": "large-blend", "page_size": 50})
    assert alias.json()["total"] == 3
    assert all(item["category"] == "Large Blend" for item in alias.json()["items"])


def test_distributions_category_in_openapi(client: TestClient) -> None:
    spec = client.get("/openapi.json").json()
    params = spec["paths"]["/distributions"]["get"]["parameters"]
    by_name = {item["name"]: item for item in params}
    assert "category" in by_name
    description = by_name["category"]["description"]
    assert "Large Blend" in description
    assert "/funds" in description


def test_distributions_category_uses_identity_not_raw_payload(session) -> None:
    """Category resolve + row filter stay on identity / fund_identifier indexes."""
    identity_stmt = _filter_stmt(columns=_FUND_SEARCH_COLUMNS)
    compiled = identity_stmt.compile(compile_kwargs={"literal_binds": True})
    sql = str(compiled).lower()
    assert "raw_payload" not in sql

    assert fund_identifiers_matching_category(session, category="Not A Real Category") == []
    rows, total = search_distributions(session, category="Not A Real Category")
    assert rows == []
    assert total == 0

    idents = ["VFIAX"]
    filtered = _filter_stmt(fund_identifiers=idents)
    compiled_filter = filtered.compile(compile_kwargs={"literal_binds": True})
    plan = session.execute(text(f"EXPLAIN QUERY PLAN {compiled_filter}")).all()
    blob = " ".join(str(part).lower() for row in plan for part in row)
    assert "index" in blob
    assert "ix_dist_fund_identifier" in blob or "ix_dist_fund_search" in blob
