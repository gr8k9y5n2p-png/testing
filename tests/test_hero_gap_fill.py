"""Hero-package gap fill on the existing Aftertax book (not net-new families)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.categories import resolve_category
from app.models import AmountUnit, EstimateType, PublicationStage
from app.services.lookback import LOOKBACK_YEARS, lookback_digest_from_rows
from app.services.nav import fixture_quote, load_fixture_catalog, load_history_catalog
from app.sources.dws import DwsSource
from app.sources.fourth_tier import FirstEagleSource, GmoSource, JohnHancockSource
from app.sources.registry import list_sources


WAVE14_AF = ("AMCFX", "AMPCX", "FMACX", "RAFGX", "GFAFX", "AMBFX", "RGAFX")
YAHOO_NO_PRINT = (
    "AHSXZ",
    "BJK",
    "CA",
    "FMSJX",
    "FMSKX",
    "FMSMX",
    "FMSNX",
    "MDCDX",
    "NUESK",
    "PIUXC",
    "TMET",
    "UNWGX",
)


def test_wave14_american_funds_share_classes_have_weekly_nav() -> None:
    catalog = load_fixture_catalog()
    assert len(catalog) >= 9100
    for ticker in WAVE14_AF:
        quote = fixture_quote(ticker, catalog=catalog)
        assert quote is not None, f"{ticker} still missing weekly NAV"
        assert quote.nav_per_share > 0
        assert quote.nav_as_of is not None
    history = load_history_catalog()
    amcfx_days = [when for (ticker, when) in history if ticker == "AMCFX"]
    assert amcfx_days, "AMCFX must have NAV on a distribution day"


def test_yahoo_no_print_stays_null() -> None:
    catalog = load_fixture_catalog()
    for ticker in YAHOO_NO_PRINT:
        assert fixture_quote(ticker, catalog=catalog) is None


def test_listed_category_coverage_digest() -> None:
    from collections import Counter

    from app.services.nav import listed_ticker
    from app.sources.registry import list_sources

    seen: dict[str, tuple[str | None, str | None]] = {}
    for source in list_sources():
        if not source.implemented:
            continue
        try:
            result = source.fetch(mode="fixture")
        except Exception:
            continue
        for row in result.records:
            ticker = (row.ticker or "").strip().upper()
            if not ticker or listed_ticker(ticker, ticker) is None:
                continue
            seen.setdefault(ticker, (row.fund_name, row.fund_family))
    categorized = 0
    for ticker, (name, family) in seen.items():
        if resolve_category(
            ticker=ticker, fund_identifier=ticker, fund_name=name, fund_family=family
        ):
            categorized += 1
    listed = len(seen)
    # In-book hero gap-fill: high-confidence name rules only. Never invent.
    assert listed == 9765
    assert categorized >= 9400
    assert categorized / listed >= 0.964


def test_lifecycle_and_asia_ex_japan_stay_conservative() -> None:
    assert resolve_category(fund_name="Nuveen Lifecycle 2035 Fund") == "Target-Date 2035"
    assert resolve_category(fund_name="Nuveen Lifecycle Index 2010 Fund") == (
        "Target-Date 2000-2010"
    )
    assert resolve_category(fund_name="iShares MSCI All Country Asia ex Japan ETF") == (
        "Pacific/Asia ex-Japan Stk"
    )
    assert resolve_category(fund_name="Capital Group — KKR Core Plus+") is None
    assert resolve_category(fund_name="Harbor Growth Fund") is None


def test_official_5y_lookback_does_not_invent_missing_years() -> None:
    rows = []
    for year in LOOKBACK_YEARS:
        if year == 2022:
            continue
        rows.append(
            (
                "AMCFX",
                "AMCFX",
                "AMCAP Fund F-2 shares",
                None,
                date(year, 12, 15),
                PublicationStage.final.value,
                "per_share",
                Decimal("1.00"),
                None,
            )
        )
    digest = lookback_digest_from_rows(rows)
    assert digest.funds_with_5y == 0
    assert digest.funds_with_finals_by_year[2022] == 0
    assert digest.funds_with_finals_by_year[2021] == 1


def test_in_book_large_aum_filter_still_keeps_share_classes() -> None:
    from dataclasses import replace

    from app.sources.aum import filter_large_aum
    from app.sources.parser import NormalizedRecord

    hero = NormalizedRecord(
        fund_family="First Eagle",
        fund_name="First Eagle Global Fund Class A",
        ticker="SGENX",
        cusip=None,
        share_class="A",
        estimate_type=EstimateType.ordinary_income,
        amount=Decimal("2.883"),
        amount_min=None,
        amount_max=None,
        amount_unit=AmountUnit.per_share,
        record_date=None,
        ex_date=date(2025, 12, 4),
        payable_date=None,
        as_of=date(2025, 12, 5),
        publication_stage=PublicationStage.final,
        source_url="fixture://fei",
    )
    in_book = replace(hero, ticker="FEGRX", fund_name="First Eagle Global Fund Class R6")
    unknown = replace(hero, ticker="ZZTINY", fund_name="Tiny")
    kept = filter_large_aum([hero, in_book, unknown], {"FEGRX"})
    assert [row.ticker for row in kept] == ["SGENX", "FEGRX"]


def test_published_oi_estimates_stay_and_date_only_stays_empty() -> None:
    first_eagle = FirstEagleSource().fetch(mode="fixture").records
    sgenx = next(
        row
        for row in first_eagle
        if row.ticker == "SGENX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.publication_stage == PublicationStage.preliminary_estimate
    )
    assert sgenx.amount_min == Decimal("2.80")
    assert sgenx.amount_max == Decimal("2.85")

    gmo = GmoSource().fetch(mode="fixture").records
    gqetx = [
        row
        for row in gmo
        if row.ticker == "GQETX" and row.publication_stage == PublicationStage.preliminary_estimate
    ]
    assert gqetx, "GMO July 2026 manager-published estimates must stay ingested"
    assert all(row.amount is not None or row.amount_min is not None for row in gqetx)

    john_hancock = JohnHancockSource().fetch(mode="fixture").records
    jemqx = next(
        row
        for row in john_hancock
        if row.ticker == "JEMQX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.publication_stage == PublicationStage.preliminary_estimate
    )
    assert jemqx.amount_min == Decimal("0.08")

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


def test_fixture_book_lookback_stays_official_only() -> None:
    rows = []
    for source in list_sources():
        if not source.implemented:
            continue
        try:
            result = source.fetch(mode="fixture")
        except Exception:
            continue
        for row in result.records:
            rows.append(
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
            )
    digest = lookback_digest_from_rows(rows)
    # Official paid/final only. Missing years stay unmatched — never invent $0.
    # 3,258 after #164 Parallel D. Parallel E leftover Nuveen fills raise the pin +3 MF.
    # Parallel C leftover: Northern Trust 2022 ICI CG-dash equity (NMIEX +1 MF).
    # Parallel H leftover: Janus Henderson quarterly / midyear ICI +33 MF.
    # Parallel F leftover: T. Rowe TBLYX 2021+2022 YE PDF (+1 MF 5y).
    # Parallel G leftover: BIRAX + MDLOX (+2 MF) and IBHF + NZAC (+2 ETF).
    # Parallel K leftover: Allspring leftover December income +31 MF 5y.
    # Parallel I leftover: Artisan leftover ICI + Calamos Class A paid/product
    # pages raise the pin +20 MF (Victory 2022 RS is year-depth).
    # Parallel J leftover: AllianceBernstein Class A product-page paid YE +15 MF.
    # Parallel O leftover: VanEck tax-guide + later 2025 paid PDF +3 ETF 5y
    # (EINC / LFEQ / RAAX).
    # Parallel M leftover: GuideStone Investor product-page paid history +17 MF.
    # Parallel N leftover: Federated Hermes Final Capital Gains API leftover
    # paid YE +44 MF. SEI 2025 final is year-depth only.
    # Impax / Pax hero-package gap fill: official 2021–2025 paid book for
    # the 22 in-book tickered shells plus the four already-healthy identities
    # unlocks +18 MF 5y (PAXLX / PXLIX / PGINX + 15 leftover shells).
    # Parallel L leftover: BNY Mellon leftover paid YE +10 MF / +9 ETF and
    # Royce RDVIX November 2025 +1 MF.
    # Parallel P leftover: Wasatch official product-page paid YE +2 MF
    # (WHOSX / WMCVX). Gabelli leftover 2025 is year-depth only.
    # Parallel S leftover: Davis / PRIMECAP / Ariel / Baird / Hotchkis & Wiley /
    # Champlain leftover paid YE +12 MF.
    assert digest.funds_with_5y == 3482
    assert digest.book_funds >= 7200
