"""Overnight gap fill: NAV + hist years + official income/CG on the existing book."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.categories import resolve_category
from app.models import AmountUnit, EstimateType, PublicationStage
from app.services.lookback import LOOKBACK_YEARS, lookback_digest_from_rows
from app.services.nav import fixture_quote
from app.sources.dws import DwsSource
from app.sources.fourth_tier import FirstEagleSource, JohnHancockSource

MEGA_MISSING_NAV = (
    "QQQ",
    "IVV",
    "IWM",
    "EFA",
    "JEPI",
    "JEPQ",
    "SCHD",
    "ARKK",
    "VNQ",
    "VGT",
)
WAVE13 = ("MGTIX", "MFEIX", "TCAF", "THEQ")
WAVE14_AF = ("AMCFX", "AMPCX", "FMACX", "RAFGX", "GFAFX", "AMBFX", "RGAFX")


def test_existing_book_tickers_have_fixture_nav() -> None:
    for ticker in MEGA_MISSING_NAV + WAVE13 + WAVE14_AF:
        quote = fixture_quote(ticker)
        assert quote is not None, f"{ticker} still missing weekly NAV fixture"
        assert quote.nav_per_share > 0
        assert quote.nav_as_of is not None


def test_lookback_uses_ex_date_not_page_as_of() -> None:
    """Multi-year tables that stamp one page as_of still count official prior years."""
    rows = []
    for year in LOOKBACK_YEARS:
        rows.append(
            (
                "SCHD",
                "SCHD",
                "Schwab U.S. Dividend Equity ETF",
                date(2025, 12, 31),
                date(year, 12, 10),
                PublicationStage.final.value,
                AmountUnit.per_share.value,
                Decimal("0.20"),
                date(year, 12, 15),
            )
        )
    digest = lookback_digest_from_rows(rows)
    assert digest.funds_with_5y == 1
    assert digest.funds_with_finals_by_year == {year: 1 for year in LOOKBACK_YEARS}
    assert "ex_date" in " ".join(digest.notes)


def test_schwab_etf_official_years_are_searchable(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "schwab", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text
    body = client.get("/distributions", params={"ticker": "SCHD", "page_size": 50}).json()
    years = {
        (row.get("ex_date") or "")[:4]
        for row in body["items"]
        if row.get("ticker") == "SCHD" and row.get("amount_unit") == "per_share"
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= years
    lookback = client.get("/coverage").json()["lookback_5y"]
    assert lookback["funds_with_finals_by_year"]["2021"] >= 1
    assert lookback["funds_with_5y_etf"] >= 1


def test_country_etf_name_rules_are_conservative() -> None:
    assert resolve_category(fund_name="iShares MSCI Chile ETF") == "Miscellaneous Region"
    assert resolve_category(fund_name="iShares MSCI Denmark ETF") == "Miscellaneous Region"
    assert resolve_category(fund_name="iShares MSCI Israel ETF") == "Miscellaneous Region"
    assert resolve_category(fund_name="iShares GSCI Commodity Dynamic Roll Strategy ETF") == (
        "Commodities Broad Basket"
    )
    # Do not invent a country from a developed-markets sleeve.
    assert resolve_category(fund_name="iShares MSCI EAFE ETF") == "Foreign Large Blend"
    assert resolve_category(fund_name="iShares MSCI All Country Asia ex Japan ETF") == (
        "Pacific/Asia ex-Japan Stk"
    )
    # "Asia ex Japan" must never collapse to Japan Stock.
    assert resolve_category(fund_name="iShares MSCI Asia ex-Japan ETF") == "Pacific/Asia ex-Japan Stk"
    assert resolve_category(fund_name="Nuveen Lifecycle 2050 Fund") == "Target-Date 2050"
    assert resolve_category(fund_name="Harbor Growth Fund") is None


def test_in_book_paid_income_is_kept_for_existing_share_classes() -> None:
    """Official 2025 paid income/CG for in-universe First Eagle classes (not only heroes)."""
    records = FirstEagleSource().fetch(mode="fixture").records
    fegrx_oi = next(
        row
        for row in records
        if row.ticker == "FEGRX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.publication_stage == PublicationStage.final
        and row.as_of and row.as_of.year == 2025
    )
    assert fegrx_oi.amount == Decimal("3.129")
    fesgx_lt = next(
        row
        for row in records
        if row.ticker == "FESGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.publication_stage == PublicationStage.final
        and row.as_of and row.as_of.year == 2025
    )
    assert fesgx_lt.amount == Decimal("4.654")


def test_upcoming_dividend_estimates_are_ingested_when_published() -> None:
    """Manager-published ordinary-income estimates stay on the book; never invent."""
    first_eagle = FirstEagleSource().fetch(mode="fixture").records
    sgenx_oi = next(
        row
        for row in first_eagle
        if row.ticker == "SGENX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.publication_stage == PublicationStage.preliminary_estimate
    )
    assert sgenx_oi.amount_min == Decimal("2.80")
    assert sgenx_oi.amount_max == Decimal("2.85")

    john_hancock = JohnHancockSource().fetch(mode="fixture").records
    jemqx = next(
        row
        for row in john_hancock
        if row.ticker == "JEMQX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.publication_stage == PublicationStage.preliminary_estimate
    )
    assert jemqx.amount_min == Decimal("0.08")
    assert jemqx.amount_max == Decimal("0.18")

    dws = DwsSource().fetch(mode="fixture").records
    invented_2026 = [
        row
        for row in dws
        if row.estimate_type == EstimateType.ordinary_income
        and (
            (row.as_of and row.as_of.year == 2026)
            or (row.ex_date and row.ex_date.year == 2026)
        )
    ]
    assert invented_2026 == []
