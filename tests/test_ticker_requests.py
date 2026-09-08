from __future__ import annotations

from fastapi.testclient import TestClient


def test_submit_ticker_already_covered_after_fetch(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "first_eagle", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text

    created = client.post(
        "/requests/tickers",
        json={"ticker": "sgenx", "source": "website_ui"},
    )
    assert created.status_code == 202, created.text
    body = created.json()
    assert body["ticker"] == "SGENX"
    assert body["status"] == "already_covered"
    assert body["adapter_slug"] == "first_eagle"
    assert "already" in (body["detail"] or "").lower()


def test_submit_ticker_matched_family_and_pickup(client: TestClient) -> None:
    created = client.post(
        "/requests/tickers",
        json={"ticker": "GDX", "fund_family": "VanEck", "source": "website_ui"},
    )
    assert created.status_code == 202, created.text
    body = created.json()
    assert body["status"] == "matched"
    assert body["adapter_slug"] == "vaneck"

    listed = client.get("/requests/tickers", params={"status": "matched"})
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
    assert any(item["ticker"] == "GDX" for item in listed.json()["items"])

    pickup = client.post("/ingest/ticker-requests", params={"mode": "fixture"})
    assert pickup.status_code == 200, pickup.text
    assert pickup.json()["processed"] >= 1
    covered = next(item for item in pickup.json()["items"] if item["ticker"] == "GDX")
    assert covered["status"] == "already_covered"

    found = client.get("/distributions", params={"ticker": "GDX", "page_size": 10})
    assert found.status_code == 200
    assert found.json()["total"] >= 1


def test_submit_unknown_ticker_stays_search_issuer(client: TestClient) -> None:
    created = client.post("/requests/tickers", json={"ticker": "ZZQRX"})
    assert created.status_code == 202
    body = created.json()
    assert body["status"] == "search_issuer"
    assert body["adapter_slug"] is None
    assert "do not invent" in (body["detail"] or "").lower()

    pickup = client.post("/ingest/ticker-requests", params={"mode": "fixture"})
    assert pickup.status_code == 200
    leftover = next(item for item in pickup.json()["items"] if item["ticker"] == "ZZQRX")
    assert leftover["status"] == "search_issuer"


def test_website_submit_ticker_contract(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "first_eagle", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text

    covered = client.post("/request/ticker", json={"ticker": "sgenx", "source": "website_ui"})
    assert covered.status_code == 200, covered.text
    assert set(covered.json()) == {"id", "ticker", "status", "message"}
    assert covered.json()["status"] == "already_covered"
    assert covered.json()["ticker"] == "SGENX"
    assert covered.json()["message"]

    queued = client.post(
        "/request/ticker",
        json={"ticker": "ZZQRX", "note": "advisor requested", "source": "website_ui"},
    )
    assert queued.status_code == 201, queued.text
    assert set(queued.json()) == {"id", "ticker", "status", "message"}
    assert queued.json()["status"] == "queued"
    assert queued.json()["ticker"] == "ZZQRX"
    assert "do not invent" in (queued.json()["message"] or "").lower()

    listed = client.get("/request/ticker", params={"status": "queued"})
    assert listed.status_code == 200
    assert any(item["ticker"] == "ZZQRX" for item in listed.json()["items"])
    queued_item = next(item for item in listed.json()["items"] if item["ticker"] == "ZZQRX")
    assert set(queued_item) == {"id", "ticker", "status", "message"}

    invalid = client.post("/request/ticker", json={"ticker": "!!!"})
    assert invalid.status_code == 422


def test_website_queued_first_trust_ticker_picks_up_september_book(client: TestClient) -> None:
    queued = client.post(
        "/request/ticker",
        json={"ticker": "FVD", "note": "advisor requested First Trust dividend ETF"},
    )
    assert queued.status_code == 201, queued.text
    assert queued.json()["status"] == "queued"

    pickup = client.post("/ingest/ticker-requests", params={"mode": "fixture"})
    assert pickup.status_code == 200, pickup.text
    covered = next(item for item in pickup.json()["items"] if item["ticker"] == "FVD")
    assert covered["status"] == "already_covered"
    assert covered["adapter_slug"] == "first_trust"

    found = client.get("/distributions", params={"ticker": "FVD", "page_size": 10})
    assert found.status_code == 200
    assert found.json()["total"] >= 1


def test_website_queued_dws_ticker_picks_up_ici_book(client: TestClient) -> None:
    queued = client.post(
        "/request/ticker",
        json={"ticker": "DBEF", "note": "advisor requested Xtrackers EAFE hedged ETF"},
    )
    assert queued.status_code == 201, queued.text
    assert queued.json()["status"] == "queued"

    pickup = client.post("/ingest/ticker-requests", params={"mode": "fixture"})
    assert pickup.status_code == 200, pickup.text
    covered = next(item for item in pickup.json()["items"] if item["ticker"] == "DBEF")
    assert covered["status"] == "already_covered"
    assert covered["adapter_slug"] == "dws"

    found = client.get("/distributions", params={"ticker": "DBEF", "page_size": 10})
    assert found.status_code == 200
    assert found.json()["total"] >= 1


def test_submit_amundi_ticker_is_matched_and_covered(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "amundi", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text

    created = client.post(
        "/requests/tickers",
        json={"ticker": "PIODX", "fund_family": "pioneer"},
    )
    assert created.status_code == 202
    body = created.json()
    assert body["status"] == "already_covered"
    assert body["adapter_slug"] == "amundi"
