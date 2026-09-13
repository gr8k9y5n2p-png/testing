"""Impax / Pax hero-package gap fill for 22 in-book tickered shells."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.categories import resolve_category
from app.models import EstimateType, PublicationStage
from app.services.lookback import lookback_digest_from_rows
from app.services.nav import fixture_quote, load_fixture_catalog, load_history_catalog
from app.sources.impax import (
    IMPAX_IN_BOOK_TICKERS,
    ImpaxSource,
    is_impax_junk_identity,
    sanitize_impax_records,
)
from app.sources.parser import parse_distribution_html

SHELLS = (
    "BLDX",
    "IGSIX",
    "IGSLX",
    "PAXBX",
    "PAXDX",
    "PAXGX",
    "PAXIX",
    "PAXWX",
    "PGRNX",
    "PWGIX",
    "PXBIX",
    "PXDIX",
    "PXEAX",
    "PXGAX",
    "PXGOX",
    "PXINX",
    "PXNIX",
    "PXSAX",
    "PXSIX",
    "PXWEX",
    "PXWGX",
    "PXWIX",
)
HEALTHY = ("PAXLX", "PXLIX", "PXSCX", "PGINX")
YAHOO_NO_PRINT = ("IGSIX", "IGSLX")
FIVE_YEAR = {
    "PAXDX",
    "PAXGX",
    "PAXIX",
    "PAXLX",
    "PAXWX",
    "PGINX",
    "PGRNX",
    "PWGIX",
    "PXDIX",
    "PXEAX",
    "PXGAX",
    "PXGOX",
    "PXINX",
    "PXLIX",
    "PXNIX",
    "PXWEX",
    "PXWGX",
    "PXWIX",
}


def test_impax_in_book_allowlist_is_exactly_healthy_plus_22_shells() -> None:
    assert IMPAX_IN_BOOK_TICKERS == frozenset(SHELLS + HEALTHY)
    assert "PAXHX" not in IMPAX_IN_BOOK_TICKERS
    assert "PXHIX" not in IMPAX_IN_BOOK_TICKERS
    assert "PXHAX" not in IMPAX_IN_BOOK_TICKERS


def test_impax_junk_gate_drops_numeric_cusip_and_ira_slugs() -> None:
    assert is_impax_junk_identity("3040", "Some Fund")
    assert is_impax_junk_identity("704223106", "Impax Sustainable Allocation Fund - Investor Class")
    assert is_impax_junk_identity("70422T208", "Impax Ellevate")
    assert is_impax_junk_identity(None, "2026 IRA Contribution Limit")
    assert is_impax_junk_identity(None, "ira-contribution-limit")
    assert not is_impax_junk_identity("PAXLX", "Impax Large Cap Fund - Investor Class")

    junk_html = """
    <html><head><title>Impax distributions</title></head><body>
    <table>
      <tr><th>Fund Name</th><th>Ticker</th><th>Ordinary Income</th></tr>
      <tr><td>Impax Sustainable Allocation Fund - Investor Class</td><td>704223106</td><td>0.532242</td></tr>
      <tr><td>Some Fund</td><td>3040</td><td>1.00</td></tr>
      <tr><td>2026 IRA Contribution Limit</td><td></td><td>7000</td></tr>
      <tr><td>Impax High Yield Bond Fund - Investor Class</td><td>PAXHX</td><td>0.01</td></tr>
      <tr><td>Impax Large Cap Fund - Investor Class</td><td>PAXLX</td><td>0.045694</td></tr>
    </table>
    </body></html>
    """
    raw = parse_distribution_html(
        junk_html,
        source_url="https://impaxam.com/customer-service/distributions/",
        fund_family="Impax / Pax",
    )
    cleaned = sanitize_impax_records(raw)
    tickers = {row.ticker for row in cleaned}
    assert tickers == {"PAXWX", "PAXLX"}
    recovered = next(row for row in cleaned if row.ticker == "PAXWX")
    assert recovered.amount == Decimal("0.532242")
    assert recovered.cusip == "704223106"


def test_impax_official_heroes_and_walls() -> None:
    records = ImpaxSource().fetch(mode="fixture").records
    tickers = {row.ticker for row in records if row.ticker}
    assert tickers == IMPAX_IN_BOOK_TICKERS
    assert "PAXHX" not in tickers
    assert "704223106" not in tickers

    paxlx_2025 = next(
        row
        for row in records
        if row.ticker == "PAXLX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date == date(2025, 12, 22)
        and row.publication_stage == PublicationStage.final
    )
    assert paxlx_2025.amount == Decimal("3.19835")

    paxgx_2025 = next(
        row
        for row in records
        if row.ticker == "PAXGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date == date(2025, 12, 22)
    )
    assert paxgx_2025.amount == Decimal("1.11926")

    paxwx_2025 = next(
        row
        for row in records
        if row.ticker == "PAXWX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and (row.ex_date == date(2025, 12, 22) or row.as_of == date(2025, 12, 23))
        and row.amount is not None
    )
    assert paxwx_2025.amount == Decimal("1.59892")

    bldx = next(row for row in records if row.ticker == "BLDX")
    assert bldx.amount == Decimal("0.253933")
    assert bldx.ex_date == date(2026, 6, 22)
    assert bldx.payable_date == date(2026, 6, 24)
    assert bldx.publication_stage == PublicationStage.final

    igsix_2025 = next(
        row
        for row in records
        if row.ticker == "IGSIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date == date(2025, 12, 22)
    )
    assert igsix_2025.amount == Decimal("0.010132")

    paxbx_2021 = next(
        row
        for row in records
        if row.ticker == "PAXBX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
    )
    assert paxbx_2021.amount == Decimal("0.01688")

    rows = [
        (
            row.ticker,
            row.ticker,
            row.fund_name,
            row.as_of,
            row.ex_date,
            getattr(row.publication_stage, "value", row.publication_stage),
            getattr(row.amount_unit, "value", row.amount_unit),
            row.amount,
            row.payable_date,
        )
        for row in records
    ]
    digest = lookback_digest_from_rows(rows)
    assert digest.funds_with_5y == 18
    assert digest.funds_with_5y_mf == 18
    assert digest.funds_with_5y_etf == 0

    years: dict[str, set[int]] = {}
    for row in records:
        stamp = row.ex_date or row.payable_date or row.as_of
        stage = getattr(row.publication_stage, "value", row.publication_stage)
        if (
            stamp
            and stamp.year in {2021, 2022, 2023, 2024, 2025}
            and row.amount is not None
            and stage in {PublicationStage.final.value, PublicationStage.paid.value}
        ):
            years.setdefault(row.ticker or "", set()).add(stamp.year)
    assert {ticker for ticker, ys in years.items() if ys >= {2021, 2022, 2023, 2024, 2025}} == FIVE_YEAR
    assert years["IGSIX"] == {2024, 2025}
    assert years["IGSLX"] == {2024, 2025}
    assert years["PAXBX"] == {2021}
    assert years["PXBIX"] == {2021}
    assert years["PXSCX"] == {2021, 2022, 2024, 2025}
    assert years["PXSIX"] == {2021, 2022, 2024, 2025}
    assert years["PXSAX"] == {2021, 2022, 2024, 2025}
    assert "BLDX" not in years or years.get("BLDX") == set()


def test_impax_weekly_nav_and_categories() -> None:
    catalog = load_fixture_catalog()
    history = load_history_catalog()
    for ticker in SHELLS:
        if ticker in YAHOO_NO_PRINT:
            assert fixture_quote(ticker, catalog=catalog) is None
            continue
        quote = fixture_quote(ticker, catalog=catalog)
        assert quote is not None, f"{ticker} still missing weekly NAV"
        assert quote.nav_per_share > 0
        assert quote.nav_as_of is not None
    assert fixture_quote("IGSIX", catalog=catalog) is None
    assert fixture_quote("IGSLX", catalog=catalog) is None

    paxgx_days = [when for (ticker, when) in history if ticker == "PAXGX"]
    assert date(2025, 12, 22) in paxgx_days
    bldx_days = [when for (ticker, when) in history if ticker == "BLDX"]
    assert date(2026, 6, 22) in bldx_days

    assert resolve_category(ticker="PAXGX") == "World Large-Stock Growth"
    assert resolve_category(ticker="PAXWX") == "Moderate Allocation"
    assert resolve_category(ticker="PXINX") == "Foreign Large Blend"
    assert resolve_category(ticker="PGRNX") == "Infrastructure"
    assert resolve_category(ticker="PAXBX") == "Intermediate Core Bond"
    assert resolve_category(ticker="PXWEX") == "World Large-Stock Blend"
    assert resolve_category(ticker="PXWGX") == "Large Blend"
    assert resolve_category(ticker="IGSIX") == "World Large-Stock Growth"
    assert resolve_category(ticker="BLDX") == "Infrastructure"
    assert resolve_category(ticker="PXSAX") == "Small Blend"


def test_impax_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "impax", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("PAXDX", "PAXGX", "PAXWX", "BLDX", "IGSIX", "PAXBX", "PXSCX", "PAXLX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"
        item = next(row for row in body["items"] if row["ticker"] == ticker)
        assert item["latest_as_of"] is not None

    paxgx = client.get(
        "/distributions",
        params={"ticker": "PAXGX", "publication_stage": "final", "page_size": 200},
    ).json()
    amounts = {
        (row["estimate_type"], row.get("ex_date") or row.get("as_of")): Decimal(row["amount"])
        for row in paxgx["items"]
        if row.get("amount") is not None
    }
    assert amounts[("long_term_capital_gains", "2025-12-22")] == Decimal("1.11926")
