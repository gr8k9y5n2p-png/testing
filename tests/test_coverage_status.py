"""In-book coverage_status vs ticker-miss not_in_universe. Never invents estimates."""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.crud import coverage_status_for_in_book_fund
from fastapi.testclient import TestClient

# Official Fidelity estimate DPL window for FBGRX (ex 2026-09-11 / pay 2026-09-14).
_FBGRX_ESTIMATE_EX = date(2026, 9, 11)


def test_in_book_coverage_status_helper() -> None:
    assert coverage_status_for_in_book_fund(has_estimate=False) == "awaiting_estimate"
    assert coverage_status_for_in_book_fund(has_estimate=True) == "estimate_announced"


def test_agthx_awaiting_estimate_after_american_funds_fixture(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text

    listed = client.get("/funds", params={"q": "AGTHX"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    item = listed.json()["items"][0]
    assert item["ticker"] == "AGTHX"
    assert item["has_estimate"] is False
    assert item["coverage_status"] == "awaiting_estimate"

    lookup = client.get("/funds/lookup", params={"ticker": "agthx"})
    assert lookup.status_code == 200
    assert lookup.json()["ticker"] == "AGTHX"
    assert lookup.json()["coverage_status"] == "awaiting_estimate"
    assert lookup.json()["has_estimate"] is False


def test_fbgrx_estimate_announced_after_fidelity_fixture(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "fidelity", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text

    listed = client.get("/funds", params={"q": "FBGRX"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    item = listed.json()["items"][0]
    assert item["ticker"] == "FBGRX"
    live = datetime.now(timezone.utc).date() < _FBGRX_ESTIMATE_EX
    assert item["has_estimate"] is live
    assert item["coverage_status"] == (
        "estimate_announced" if live else "awaiting_estimate"
    )

    lookup = client.get("/funds/lookup", params={"ticker": "FBGRX"})
    assert lookup.status_code == 200
    assert lookup.json()["ticker"] == "FBGRX"
    assert lookup.json()["has_estimate"] is live
    assert lookup.json()["coverage_status"] == (
        "estimate_announced" if live else "awaiting_estimate"
    )


def test_zzzzz_not_in_universe_and_add_to_universe_intake(client: TestClient) -> None:
    listed = client.get("/funds", params={"q": "ZZZZZ"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 0
    assert listed.json()["items"] == []
    assert "coverage_status" not in listed.json()

    miss = client.get("/funds/lookup", params={"ticker": "zzzzz"})
    assert miss.status_code == 404
    body = miss.json()
    assert body["coverage_status"] == "not_in_universe"
    assert body["ticker"] == "ZZZZZ"
    assert body["add_to_universe"] == "POST /request/ticker"
    assert "awaiting" not in (body.get("message") or "").lower()
    assert "add to universe" in (body.get("message") or "").lower()

    queued = client.post(
        "/request/ticker",
        json={"ticker": "ZZZZZ", "note": "Add to universe", "source": "website_ui"},
    )
    assert queued.status_code == 201, queued.text
    assert queued.json()["ticker"] == "ZZZZZ"
    assert queued.json()["status"] == "queued"
    assert "do not invent" in (queued.json()["message"] or "").lower()
