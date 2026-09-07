from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "american_funds" in body["registered_families"]


def test_ingest_validation_error(client: TestClient) -> None:
    response = client.post("/ingest/distributions", json={"records": [{"fund_family": "X"}]})
    assert response.status_code == 422
    assert response.json()["detail"] == "Validation failed"
    assert "errors" in response.json()


def test_fetch_unknown_family(client: TestClient) -> None:
    response = client.post("/ingest/fetch", json={"fund_family": "not-a-family", "mode": "fixture"})
    assert response.status_code == 404


def test_fetch_vanguard_fixture(client: TestClient) -> None:
    response = client.post("/ingest/fetch", json={"fund_family": "vanguard", "mode": "fixture"})
    assert response.status_code == 200, response.text
    assert response.json()["created"] > 0
    found = client.get("/distributions", params={"ticker": "VBIAX"})
    assert found.json()["total"] >= 1


def test_fixture_fetch_and_search_filters(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text
    body = fetched.json()
    assert body["created"] > 0
    assert body["updated"] == 0

    rerun = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert rerun.status_code == 200
    assert rerun.json()["created"] == 0
    assert rerun.json()["updated"] == body["created"]

    search = client.get("/distributions", params={"q": "AMCAP", "estimate_type": "long_term_capital_gains"})
    assert search.status_code == 200
    payload = search.json()
    assert payload["total"] >= 1
    names = {item["fund_name"] for item in payload["items"]}
    assert "AMCAP Fund" in names
    assert all(item["raw_payload"] is None for item in payload["items"])

    ticker = client.get("/distributions", params={"ticker": "CGHM"})
    assert ticker.json()["total"] >= 1
    assert all(item["ticker"] == "CGHM" for item in ticker.json()["items"])

    dates = client.get(
        "/distributions",
        params={"ex_date_from": "2026-06-01", "ex_date_to": "2026-06-30", "estimate_type": "long_term_capital_gains"},
    )
    assert dates.json()["total"] >= 1
    assert all(item["ex_date"].startswith("2026-06") for item in dates.json()["items"])

    pct = client.get("/distributions", params={"estimate_type": "total_capital_gains"})
    assert pct.json()["total"] >= 1
    assert any(item["amount_unit"] == "percent_of_nav" for item in pct.json()["items"])

    page1 = client.get("/distributions", params={"page": 1, "page_size": 5})
    page2 = client.get("/distributions", params={"page": 2, "page_size": 5})
    assert page1.json()["page_size"] == 5
    assert page1.json()["total"] == page2.json()["total"]
    assert page1.json()["items"][0]["id"] != page2.json()["items"][0]["id"]

    detail_id = page1.json()["items"][0]["id"]
    detail = client.get(f"/distributions/{detail_id}")
    assert detail.status_code == 200
    assert detail.json()["raw_payload"] is not None

    missing = client.get("/distributions/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404

    families = client.get("/fund-families")
    assert families.status_code == 200
    slugs = {row["slug"]: row for row in families.json()}
    assert slugs["american_funds"]["implemented"] is True
    assert slugs["american_funds"]["coverage_tier"] == "implemented"
    assert slugs["american_funds"]["aum_rank"] == 7
    assert slugs["american_funds"]["last_ingest_status"] == "success"
    assert slugs["vanguard"]["implemented"] is True
    assert slugs["vanguard"]["aum_rank"] == 2
    assert slugs["blackrock"]["aum_rank"] == 1
    assert len(slugs) == 10


def test_manual_ingest_partner_feed(client: TestClient) -> None:
    response = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "Vanguard",
                    "fund_name": "Vanguard 500 Index Fund",
                    "ticker": "VFIAX",
                    "share_class": "Admiral",
                    "estimate_type": "total_capital_gains",
                    "amount_min": "1.2",
                    "amount_max": "1.8",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2025-11-15",
                    "ex_date": "2025-12-17",
                    "source_url": "https://example.invalid/partner",
                }
            ]
        },
    )
    assert response.status_code == 200
    assert response.json()["created"] == 1
    found = client.get("/distributions", params={"ticker": "VFIAX"})
    item = found.json()["items"][0]
    assert item["amount_unit"] == "percent_of_nav"
    assert Decimal(item["amount"]) == Decimal("1.5")
