from __future__ import annotations

from app.crud import resolve_page_from_limit_offset
from fastapi.testclient import TestClient


def _record(
    *,
    fund_family: str,
    fund_name: str,
    ticker: str | None,
    estimate_type: str,
    amount: str,
    as_of: str,
    publication_stage: str | None = None,
) -> dict:
    payload = {
        "fund_family": fund_family,
        "fund_name": fund_name,
        "ticker": ticker,
        "estimate_type": estimate_type,
        "amount": amount,
        "amount_unit": "per_share",
        "as_of": as_of,
    }
    if publication_stage:
        payload["publication_stage"] = publication_stage
    return payload


def _seed_unique_funds(client: TestClient) -> None:
    """Three unique funds, two distribution rows each. Never invents extra names."""
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
                    as_of="2025-11-15",
                    publication_stage="preliminary_estimate",
                ),
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard 500 Index Fund",
                    ticker="VFIAX",
                    estimate_type="short_term_capital_gains",
                    amount="0.20",
                    as_of="2025-12-01",
                    publication_stage="updated_estimate",
                ),
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard Balanced Index Fund",
                    ticker="VBIAX",
                    estimate_type="long_term_capital_gains",
                    amount="0.50",
                    as_of="2025-11-15",
                    publication_stage="preliminary_estimate",
                ),
                _record(
                    fund_family="Vanguard",
                    fund_name="Vanguard Balanced Index Fund",
                    ticker="VBIAX",
                    estimate_type="ordinary_income",
                    amount="0.10",
                    as_of="2024-12-17",
                    publication_stage="paid",
                ),
                _record(
                    fund_family="Dodge & Cox",
                    fund_name="Dodge & Cox Income Fund",
                    ticker="DODIX",
                    estimate_type="ordinary_income",
                    amount="0.13",
                    as_of="2025-12-15",
                    publication_stage="paid",
                ),
                _record(
                    fund_family="Dodge & Cox",
                    fund_name="Dodge & Cox Income Fund",
                    ticker="DODIX",
                    estimate_type="ordinary_income",
                    amount="0.12",
                    as_of="2024-12-16",
                    publication_stage="paid",
                ),
            ]
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["created"] == 6


def test_resolve_page_from_limit_offset() -> None:
    assert resolve_page_from_limit_offset(page=1, page_size=50, limit=None, offset=None) == (1, 50)
    assert resolve_page_from_limit_offset(page=3, page_size=10, limit=None, offset=None) == (3, 10)
    assert resolve_page_from_limit_offset(page=1, page_size=50, limit=25, offset=None) == (1, 25)
    assert resolve_page_from_limit_offset(page=1, page_size=50, limit=50, offset=0) == (1, 50)
    assert resolve_page_from_limit_offset(page=1, page_size=50, limit=50, offset=50) == (2, 50)
    assert resolve_page_from_limit_offset(page=1, page_size=50, limit=50, offset=100) == (3, 50)
    assert resolve_page_from_limit_offset(page=9, page_size=10, limit=10, offset=20) == (3, 10)
    assert resolve_page_from_limit_offset(page=1, page_size=50, limit=None, offset=50) == (2, 50)
    assert resolve_page_from_limit_offset(page=1, page_size=50, limit=200, offset=0) == (1, 200)
    assert resolve_page_from_limit_offset(page=1, page_size=500, limit=None, offset=None) == (1, 200)


def test_funds_empty_store(client: TestClient) -> None:
    response = client.get("/funds")
    assert response.status_code == 200
    body = response.json()
    assert body == {"items": [], "limit": 50, "offset": 0, "total": 0}


def test_funds_unique_total_and_pagination_math(client: TestClient) -> None:
    _seed_unique_funds(client)

    rows = client.get("/distributions", params={"page_size": 50})
    assert rows.json()["total"] == 6

    defaulted = client.get("/funds")
    assert defaulted.status_code == 200
    body = defaulted.json()
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["total"] == 3
    assert len(body["items"]) == 3

    identifiers = [item["fund_identifier"] for item in body["items"]]
    assert len(identifiers) == len(set(identifiers))
    assert set(identifiers) == {"VFIAX", "VBIAX", "DODIX"}
    assert identifiers == ["DODIX", "VFIAX", "VBIAX"]

    by_id = {item["fund_identifier"]: item for item in body["items"]}
    assert by_id["VFIAX"]["ticker"] == "VFIAX"
    assert by_id["VFIAX"]["fund_name"] == "Vanguard 500 Index Fund"
    assert by_id["VFIAX"]["fund_family"] == "Vanguard"
    assert by_id["VFIAX"]["latest_as_of"] == "2025-12-01"
    assert by_id["VFIAX"]["has_estimate"] is True
    assert by_id["DODIX"]["latest_as_of"] == "2025-12-15"
    assert by_id["DODIX"]["has_estimate"] is False

    page1 = client.get("/funds", params={"limit": 2, "offset": 0})
    page2 = client.get("/funds", params={"limit": 2, "offset": 2})
    assert page1.json()["total"] == page2.json()["total"] == 3
    assert page1.json()["limit"] == 2
    assert page1.json()["offset"] == 0
    assert page2.json()["limit"] == 2
    assert page2.json()["offset"] == 2
    assert len(page1.json()["items"]) == 2
    assert len(page2.json()["items"]) == 1

    page1_ids = [item["fund_identifier"] for item in page1.json()["items"]]
    page2_ids = [item["fund_identifier"] for item in page2.json()["items"]]
    assert not set(page1_ids) & set(page2_ids)
    assert set(page1_ids + page2_ids) == {"VFIAX", "VBIAX", "DODIX"}

    past_end = client.get("/funds", params={"limit": 50, "offset": 3})
    assert past_end.json()["total"] == 3
    assert past_end.json()["items"] == []


def test_funds_q_and_family_filters(client: TestClient) -> None:
    _seed_unique_funds(client)

    search = client.get("/funds", params={"q": "Balanced"})
    assert search.json()["total"] == 1
    assert search.json()["items"][0]["ticker"] == "VBIAX"

    ticker = client.get("/funds", params={"q": "DODIX"})
    assert ticker.json()["total"] == 1
    assert ticker.json()["items"][0]["fund_identifier"] == "DODIX"

    family = client.get("/funds", params={"fund_family": "Dodge"})
    assert family.json()["total"] == 1
    assert family.json()["items"][0]["fund_family"] == "Dodge & Cox"

    missing = client.get("/funds", params={"q": "ZZNOTAREALFUND"})
    assert missing.json()["total"] == 0
    assert missing.json()["items"] == []


def test_funds_limit_bounds(client: TestClient) -> None:
    too_big = client.get("/funds", params={"limit": 201})
    assert too_big.status_code == 422
    too_small = client.get("/funds", params={"limit": 0})
    assert too_small.status_code == 422
    negative_offset = client.get("/funds", params={"offset": -1})
    assert negative_offset.status_code == 422


def test_funds_from_fixture_are_stored_only(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text

    funds = client.get("/funds", params={"limit": 200, "q": "AMCAP"})
    assert funds.status_code == 200
    body = funds.json()
    assert body["total"] >= 1
    assert all(item["fund_identifier"] == "amcap-fund" for item in body["items"])
    assert all(item["ticker"] == "AMCPX" for item in body["items"])
    assert all(item["fund_name"] == "AMCAP Fund" for item in body["items"])

    rows = client.get("/distributions", params={"q": "AMCAP", "page_size": 50})
    assert rows.json()["total"] >= body["total"]
    assert rows.json()["total"] > body["total"]


def test_distributions_limit_offset_aliases(client: TestClient) -> None:
    _seed_unique_funds(client)

    by_page = client.get("/distributions", params={"page": 2, "page_size": 2})
    by_alias = client.get("/distributions", params={"limit": 2, "offset": 2})
    assert by_page.status_code == 200
    assert by_alias.status_code == 200
    assert by_page.json()["page"] == 2
    assert by_page.json()["page_size"] == 2
    assert by_alias.json()["page"] == 2
    assert by_alias.json()["page_size"] == 2
    assert by_page.json()["total"] == by_alias.json()["total"] == 6
    assert [item["id"] for item in by_page.json()["items"]] == [
        item["id"] for item in by_alias.json()["items"]
    ]

    first = client.get("/distributions", params={"limit": 2, "offset": 0})
    assert first.json()["page"] == 1
    assert first.json()["page_size"] == 2
    assert [item["id"] for item in first.json()["items"]] != [
        item["id"] for item in by_alias.json()["items"]
    ]
