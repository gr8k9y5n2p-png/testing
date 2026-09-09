from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.services.nav import (
    SOURCE_FIXTURE,
    SOURCE_YAHOO,
    NavQuote,
    fixture_quote,
    listed_ticker,
    parse_yahoo_chart,
    refresh_navs,
    unique_fund_nav_coverage,
    upsert_nav,
)


def _per_share_record(ticker: str, fund_name: str, fund_family: str = "Vanguard") -> dict:
    return {
        "fund_family": fund_family,
        "fund_name": fund_name,
        "ticker": ticker,
        "estimate_type": "long_term_capital_gains",
        "amount": "2.00",
        "amount_unit": "per_share",
        "as_of": "2025-12-15",
        "publication_stage": "preliminary_estimate",
    }


def test_listed_ticker_skips_synthetic_and_name_slugs() -> None:
    assert listed_ticker("ABALX", "american-balanced-fund") == "ABALX"
    assert listed_ticker(None, "american-balanced-fund") == "ABALX"
    assert listed_ticker(None, "VFIAX") == "VFIAX"
    assert listed_ticker("ZZCAT", "zzcat") is None
    assert listed_ticker(None, "strategic-opportunities-fund") is None


def test_fixture_quote_sample_tickers() -> None:
    abalx = fixture_quote("ABALX")
    vfiax = fixture_quote("VFIAX")
    spy = fixture_quote("SPY")
    dbef = fixture_quote("DBEF")
    assert abalx is not None and abalx.nav_per_share == Decimal("40.930000")
    assert abalx.nav_as_of == date(2026, 9, 1)
    assert vfiax is not None and vfiax.nav_per_share == Decimal("713.559998")
    assert spy is not None and spy.nav_per_share == Decimal("770.190002")
    assert dbef is not None and dbef.nav_per_share == Decimal("55.480000")
    assert fixture_quote("NOTAREALTICKER") is None


def test_parse_yahoo_chart_uses_regular_close_not_adjclose() -> None:
    payload = {
        "chart": {
            "result": [
                {
                    "meta": {"symbol": "ABALX", "regularMarketPrice": 41.5},
                    "timestamp": [1756684800, 1756771200],
                    "indicators": {
                        "quote": [{"close": [40.1, 40.93]}],
                        "adjclose": [{"adjclose": [10.0, 10.1]}],
                    },
                }
            ]
        }
    }
    quote = parse_yahoo_chart(
        payload,
        "ABALX",
        "https://query1.finance.yahoo.com/v8/finance/chart/ABALX?interval=1d&range=10d",
    )
    assert quote is not None
    assert quote.nav_per_share == Decimal("40.930000")
    assert quote.source == SOURCE_YAHOO
    assert quote.nav_as_of == date(2025, 9, 2) or quote.nav_as_of >= date(2025, 1, 1)


def test_funds_nav_null_until_ingested(client: TestClient) -> None:
    seeded = client.post(
        "/ingest/distributions",
        json={"records": [_per_share_record("NONEV", "No NAV Fund", "Example")]},
    )
    assert seeded.status_code == 200
    funds = client.get("/funds", params={"q": "NONEV"})
    assert funds.status_code == 200
    item = funds.json()["items"][0]
    assert item["ticker"] == "NONEV"
    assert item["nav_per_share"] is None
    assert item["nav_as_of"] is None
    assert item["nav_source"] is None


def test_weekly_nav_fixture_and_funds_fields(client: TestClient, session) -> None:
    ingested = client.post(
        "/ingest/distributions",
        json={
            "records": [
                _per_share_record("VFIAX", "Vanguard 500 Index Fund"),
                _per_share_record("ABALX", "American Balanced Fund", "American Funds"),
                _per_share_record("SPY", "SPDR S&P 500 ETF Trust", "State Street"),
                _per_share_record("DBEF", "Xtrackers MSCI EAFE Hedged Equity ETF", "DWS"),
                _per_share_record("NONEV", "No NAV Fund", "Example"),
            ]
        },
    )
    assert ingested.status_code == 200

    before = unique_fund_nav_coverage(session)
    assert before["with_nav"] == 0
    assert before["coverage_pct"] == 0.0

    summary = refresh_navs(session, mode="fixture")
    session.commit()
    assert summary.created >= 4
    assert summary.sample["ABALX"]["nav_per_share"] == "40.930000"
    assert summary.sample["VFIAX"]["nav_per_share"] == "713.559998"
    assert summary.sample["SPY"]["nav_per_share"] == "770.190002"
    assert summary.sample["DBEF"]["nav_per_share"] == "55.480000"
    assert summary.unknown >= 1

    after = unique_fund_nav_coverage(session)
    assert after["with_nav"] >= 4
    assert after["coverage_pct"] > before["coverage_pct"]

    for ticker, expected in {
        "ABALX": "40.930000",
        "VFIAX": "713.559998",
        "SPY": "770.190002",
        "DBEF": "55.480000",
    }.items():
        body = client.get("/funds", params={"q": ticker}).json()["items"][0]
        assert Decimal(body["nav_per_share"]) == Decimal(expected)
        assert body["nav_as_of"] is not None
        assert body["nav_source"] == SOURCE_FIXTURE

    missing = client.get("/funds", params={"q": "NONEV"}).json()["items"][0]
    assert missing["nav_per_share"] is None
    assert missing["nav_source"] is None


def test_illustrate_uses_stored_weekly_nav(client: TestClient, session) -> None:
    ingested = client.post(
        "/ingest/distributions",
        json={"records": [_per_share_record("VFIAX", "Vanguard 500 Index Fund")]},
    )
    assert ingested.status_code == 200
    upsert_nav(
        session,
        NavQuote(
            ticker="VFIAX",
            nav_per_share=Decimal("50"),
            nav_as_of=date(2026, 9, 8),
            source=SOURCE_YAHOO,
            source_url="https://query1.finance.yahoo.com/v8/finance/chart/VFIAX?interval=1d&range=10d",
            fund_identifier="VFIAX",
        ),
    )
    session.commit()

    missing = client.post(
        "/illustrate",
        json={
            "holding_dollars": 1000,
            "selectors": {"ticker": "VFIAX"},
        },
    )
    assert missing.status_code == 200, missing.text
    body = missing.json()
    # Dist $ = $2 / share × ($1000 / $50 NAV) = $40
    assert Decimal(body["nav_per_share"]) == Decimal("50")
    assert Decimal(body["shares"]) == Decimal("20.00")
    assert Decimal(body["components"][0]["distribution_dollars"]) == Decimal("40.00")
    # % of NAV = $2 ÷ $50 = 4%
    assert Decimal(body["components"][0]["percent_of_nav"]) == Decimal("4.000000")
    assert any("stored weekly NAV" in note for note in body["notes"])

    override = client.post(
        "/illustrate",
        json={
            "holding_dollars": 1000,
            "selectors": {"ticker": "VFIAX"},
            "nav_per_share": "100",
        },
    )
    assert override.status_code == 200
    assert Decimal(override.json()["nav_per_share"]) == Decimal("100")
    assert Decimal(override.json()["components"][0]["distribution_dollars"]) == Decimal("20.00")
    assert Decimal(override.json()["components"][0]["percent_of_nav"]) == Decimal("2.000000")


def test_cli_refresh_nav_fixture(engine, capsys) -> None:
    from app.cli import main

    code = main(["refresh", "--mode", "fixture", "--family", "vanguard"])
    assert code == 0
    nav_code = main(["refresh-nav", "--mode", "fixture", "--ticker", "VFIAX"])
    assert nav_code == 0
    out = capsys.readouterr().out
    assert "Weekly NAV refresh" in out
    assert "VFIAX" in out


def test_older_nav_does_not_overwrite_newer(session) -> None:
    first = upsert_nav(
        session,
        NavQuote(
            ticker="SPY",
            nav_per_share=Decimal("770.19"),
            nav_as_of=date(2026, 9, 8),
            source=SOURCE_YAHOO,
            source_url="https://example.invalid/spy",
        ),
    )
    second = upsert_nav(
        session,
        NavQuote(
            ticker="SPY",
            nav_per_share=Decimal("1.00"),
            nav_as_of=date(2026, 1, 2),
            source=SOURCE_FIXTURE,
            source_url="https://example.invalid/old",
        ),
    )
    session.flush()
    assert first == "created"
    assert second == "unchanged"
    from app.services.nav import get_nav

    row = get_nav(session, "SPY")
    assert row is not None
    assert row.nav_per_share == Decimal("770.190000")
    assert row.nav_as_of == date(2026, 9, 8)
    assert row.source == SOURCE_YAHOO
