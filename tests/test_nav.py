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
    load_history_catalog,
    lookup_nav_on_day,
    parse_yahoo_chart,
    parse_yahoo_daily_points,
    refresh_navs,
    unique_fund_nav_coverage,
    upsert_nav,
    upsert_nav_history,
    uses_distribution_day_nav,
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
    for ticker in ("ABALX", "VFIAX", "SPY", "DBEF"):
        quote = fixture_quote(ticker)
        assert quote is not None, ticker
        assert quote.nav_per_share > 0
        assert quote.nav_as_of is not None
        assert quote.source in {SOURCE_FIXTURE, "fixture_fallback"}
    assert fixture_quote("NOTAREALTICKER") is None


def test_history_catalog_has_sample_distribution_days() -> None:
    catalog = load_history_catalog()
    for ticker, when in (
        ("ABALX", date(2025, 12, 15)),
        ("VFIAX", date(2025, 12, 23)),
        ("SPY", date(2025, 12, 19)),
        ("DBEF", date(2025, 12, 19)),
    ):
        quote = catalog.get((ticker, when))
        assert quote is not None, (ticker, when)
        assert quote.nav_per_share > 0
        assert quote.source == SOURCE_FIXTURE


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
    for ticker in ("ABALX", "VFIAX", "SPY", "DBEF"):
        expected = fixture_quote(ticker)
        assert expected is not None
        assert summary.sample[ticker]["nav_per_share"] == str(expected.nav_per_share)
        assert summary.sample[ticker]["nav_as_of"] == expected.nav_as_of.isoformat()
    assert summary.unknown >= 1

    after = unique_fund_nav_coverage(session)
    assert after["with_nav"] >= 4
    assert after["coverage_pct"] > before["coverage_pct"]

    for ticker in ("ABALX", "VFIAX", "SPY", "DBEF"):
        expected = fixture_quote(ticker)
        assert expected is not None
        body = client.get("/funds", params={"q": ticker}).json()["items"][0]
        assert Decimal(body["nav_per_share"]) == expected.nav_per_share
        assert body["nav_as_of"] == expected.nav_as_of.isoformat()
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


def test_historical_percent_of_nav_uses_distribution_day_not_today(
    client: TestClient, session
) -> None:
    ingested = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "Vanguard",
                    "fund_name": "Vanguard 500 Index Fund",
                    "ticker": "VFIAX",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "2.00",
                    "amount_unit": "per_share",
                    "as_of": "2025-12-24",
                    "ex_date": "2025-12-23",
                    "payable_date": "2025-12-24",
                    "publication_stage": "paid",
                }
            ]
        },
    )
    assert ingested.status_code == 200
    upsert_nav(
        session,
        NavQuote(
            ticker="VFIAX",
            nav_per_share=Decimal("100"),
            nav_as_of=date(2026, 9, 8),
            source=SOURCE_YAHOO,
            source_url="https://example.invalid/latest",
            fund_identifier="VFIAX",
        ),
    )
    upsert_nav_history(
        session,
        NavQuote(
            ticker="VFIAX",
            nav_per_share=Decimal("50"),
            nav_as_of=date(2025, 12, 23),
            source=SOURCE_YAHOO,
            source_url="https://example.invalid/ex-day",
        ),
    )
    session.commit()

    listed = client.get("/distributions", params={"ticker": "VFIAX"}).json()["items"][0]
    assert Decimal(listed["nav_on_distribution_day"]) == Decimal("50")
    assert listed["nav_on_distribution_day_as_of"] == "2025-12-23"
    assert listed["nav_on_distribution_day_source"] == SOURCE_YAHOO
    by_id = client.get(f"/distributions/{listed['id']}").json()
    assert Decimal(by_id["nav_on_distribution_day"]) == Decimal("50")

    body = client.post(
        "/illustrate",
        json={"holding_dollars": 1000, "selectors": {"ticker": "VFIAX"}},
    ).json()
    # Live Dist $ still uses latest weekly NAV: $2 × ($1000 / $100) = $20
    assert Decimal(body["nav_per_share"]) == Decimal("100")
    assert Decimal(body["components"][0]["distribution_dollars"]) == Decimal("20.00")
    # Historical % of NAV uses NAV on ex_date, not today: $2 ÷ $50 = 4%
    assert Decimal(body["components"][0]["nav_on_distribution_day"]) == Decimal("50")
    assert Decimal(body["components"][0]["percent_of_nav"]) == Decimal("4.000000")
    assert body["components"][0]["percent_of_nav"] != "2.000000"


def test_historical_percent_stays_null_without_distribution_day_nav(
    client: TestClient, session
) -> None:
    ingested = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "Example",
                    "fund_name": "No History NAV Fund",
                    "ticker": "NAVUKN",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "2.00",
                    "amount_unit": "per_share",
                    "as_of": "2025-12-24",
                    "ex_date": "2025-12-23",
                    "publication_stage": "paid",
                }
            ]
        },
    )
    assert ingested.status_code == 200
    upsert_nav(
        session,
        NavQuote(
            ticker="NAVUKN",
            nav_per_share=Decimal("100"),
            nav_as_of=date(2026, 9, 8),
            source=SOURCE_YAHOO,
            source_url="https://example.invalid/latest",
        ),
    )
    session.commit()

    listed = client.get("/distributions", params={"ticker": "NAVUKN"}).json()["items"][0]
    assert listed["nav_on_distribution_day"] is None
    assert listed["nav_on_distribution_day_as_of"] is None

    body = client.post(
        "/illustrate",
        json={"holding_dollars": 1000, "selectors": {"ticker": "NAVUKN"}},
    ).json()
    assert Decimal(body["nav_per_share"]) == Decimal("100")
    assert Decimal(body["components"][0]["distribution_dollars"]) == Decimal("20.00")
    assert body["components"][0]["percent_of_nav"] is None
    assert body["components"][0]["nav_on_distribution_day"] is None


def test_weekend_ex_uses_prior_close_within_lookback(client: TestClient, session) -> None:
    ingested = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "State Street",
                    "fund_name": "SPDR S&P 500 ETF Trust",
                    "ticker": "SPY",
                    "estimate_type": "ordinary_income",
                    "amount": "1.00",
                    "amount_unit": "per_share",
                    "as_of": "2025-12-22",
                    "ex_date": "2025-12-21",
                    "publication_stage": "paid",
                }
            ]
        },
    )
    assert ingested.status_code == 200
    # 2025-12-21 was a Sunday. Friday 2025-12-19 is within 7 days.
    upsert_nav_history(
        session,
        NavQuote(
            ticker="SPY",
            nav_per_share=Decimal("580"),
            nav_as_of=date(2025, 12, 19),
            source=SOURCE_YAHOO,
            source_url="https://example.invalid/friday",
        ),
    )
    session.commit()
    listed = client.get("/distributions", params={"ticker": "SPY"}).json()["items"][0]
    assert Decimal(listed["nav_on_distribution_day"]) == Decimal("580")
    assert listed["nav_on_distribution_day_as_of"] == "2025-12-19"


def test_uses_distribution_day_nav_rules() -> None:
    class Row:
        def __init__(self, ex=None, payable=None, stage=None):
            self.ex_date = ex
            self.payable_date = payable
            self.publication_stage = stage

    today = date(2026, 9, 9)
    assert uses_distribution_day_nav(Row(ex=date(2025, 12, 23)), today=today) is True
    assert uses_distribution_day_nav(Row(payable=date(2025, 12, 24)), today=today) is True
    assert uses_distribution_day_nav(Row(stage="paid"), today=today) is True
    assert uses_distribution_day_nav(Row(ex=date(2026, 12, 15), stage="preliminary_estimate"), today=today) is False
    assert uses_distribution_day_nav(Row(stage="preliminary_estimate"), today=today) is False


def test_later_close_is_never_used_for_distribution_day(session) -> None:
    upsert_nav_history(
        session,
        NavQuote(
            ticker="ABALX",
            nav_per_share=Decimal("99"),
            nav_as_of=date(2025, 12, 24),
            source=SOURCE_YAHOO,
            source_url="https://example.invalid/after",
        ),
    )
    session.flush()
    assert lookup_nav_on_day(session, "ABALX", date(2025, 12, 23), catalog={}) is None


def test_print_older_than_lookback_stays_null(session) -> None:
    upsert_nav_history(
        session,
        NavQuote(
            ticker="ABALX",
            nav_per_share=Decimal("38"),
            nav_as_of=date(2025, 12, 10),
            source=SOURCE_YAHOO,
            source_url="https://example.invalid/old",
        ),
    )
    session.flush()
    # 2025-12-23 minus 2025-12-10 = 13 days > 7
    assert lookup_nav_on_day(session, "ABALX", date(2025, 12, 23), catalog={}) is None


def test_payable_date_used_when_ex_date_missing(client: TestClient, session) -> None:
    ingested = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "American Funds",
                    "fund_name": "American Balanced Fund",
                    "ticker": "ABALX",
                    "estimate_type": "ordinary_income",
                    "amount": "0.50",
                    "amount_unit": "per_share",
                    "as_of": "2025-12-24",
                    "payable_date": "2025-12-22",
                    "publication_stage": "paid",
                }
            ]
        },
    )
    assert ingested.status_code == 200
    upsert_nav_history(
        session,
        NavQuote(
            ticker="ABALX",
            nav_per_share=Decimal("36.25"),
            nav_as_of=date(2025, 12, 22),
            source=SOURCE_YAHOO,
            source_url="https://example.invalid/payable",
        ),
    )
    session.commit()
    listed = client.get("/distributions", params={"ticker": "ABALX"}).json()["items"][0]
    assert listed["ex_date"] is None
    assert listed["payable_date"] == "2025-12-22"
    assert Decimal(listed["nav_on_distribution_day"]) == Decimal("36.25")


def test_parse_yahoo_daily_points_skips_null_closes() -> None:
    points = parse_yahoo_daily_points(
        {
            "chart": {
                "result": [
                    {
                        "timestamp": [1766448000, 1766534400],
                        "indicators": {"quote": [{"close": [None, 50.5]}]},
                    }
                ]
            }
        },
        "VFIAX",
        "https://example.invalid/history",
    )
    assert len(points) == 1
    assert points[0].nav_per_share == Decimal("50.500000")
    assert points[0].source == SOURCE_YAHOO


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
