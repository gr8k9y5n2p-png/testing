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
    # Parallel Q leftover: GMO US Trust Class III + Voya VYCAX +4 MF.
    # Parallel R leftover: Diamond Hill Investor paid HTML +7 MF and
    # Bridgeway leftover paid +4 MF. AQR is year-depth only (3y).
    # Jensen 2021–2023 and TCW 2021–2024 stay unmatched.
    # Parallel V leftover: Heartland +6 MF, FMI +2 MF, Brandes Class I +5 MF.
    # Baillie 2025 Final is year-depth only. GQG leftovers stay estimate-only.
    # Parallel W leftover: Manning & Napier December paid YE +27 MF and
    # Westwood Institutional paid history +3 MF. Year-depth / walls unchanged
    # for Lazard / Homestead / Madison / BP / LSV leftover years.
    # Parallel T leftover: Marsico Investor leftover paid YE +5 MF.
    # Harding leftover 2021/2022 PDFs are year-depth. Alger / Driehaus walls.
    # All-events leftover (non-MFS, rebased onto #186+#181 tip): official
    # midyear / quarterly typed rows for American Funds, Vanguard, T. Rowe,
    # and iShares. MFS #186 mid-year fills stay. +1 MF 5y from a published
    # midyear fill on the Parallel T tip (3545).
    # Parallel U leftover: Tweedy + Osterweis + Longleaf leftover paid YE
    # +10 MF 5y. Buffalo 2024–2025 and Third Avenue 2022–2024 are year-depth.
    # Parallel AA leftover: Vanguard leftover ICI bond / tax-exempt / MM
    # years +14 (12 MF / 2 ETF). Schwab / SSGA / DFA / Nuveen stay walls.
    # Parallel AB leftover: Oakmark 2024 + Janus Daily leftover ICI +62 MF.
    # Parallel Y leftover: BlackRock Investor A leftover paid years +16 MF.
    # Parallel AC leftover: Principal leftover YEAR finals +12 MF (PFIJX /
    # GEM 2024; Real Estate 2025). AF / JH / Nationwide / Thrivent leftover
    # years stay walls. #188 midyear all-events not redone.
    # WAVE X leftover: Fidelity FTRIX + ACI Investor + JPM Trust II Class A +
    # GS Insights leftover N-CSR / DPL2 paid fills. Honest pin remasured
    # after rebase onto #192 tip: 3693 → 3721 (+28 MF).
    # WAVE AF leftover: Harbor Institutional product-page paid history +8 MF.
    # Honest pin = tip 3721 + AF +8.
    # WAVE AD leftover: Macquarie / Delaware Class A N-CSR 2021 +7 MF and
    # Eaton Vance EOI N-CSR +1 ETF. Honest pin remasured after rebase
    # onto #201 tip: 3729 → 3737.
    # WAVE AE leftover: Invesco ETF Tax Center ICI leftover December YE
    # +5 ETF (PIN / PSCI / IDMO / IVRA / PBP). Honest pin = tip 3737 + 5 → 3742.
    # WAVE AG leftover: Victory RS FYE Dec 31 2021 N-CSR unlocks +16 MF.
    # Honest pin remasured after rebase onto #203 tip ba30980: 3742 → 3758
    # (+16 MF; no overlap with AF/AD/AE).
    # WAVE AH leftover: BNY leftover Class A / Investor product-page paid YE
    # +4 MF (DMCVX / MIBLX / MIMSX / MISCX). Honest pin remasured after
    # rebase onto #204 tip 5b1ffa45: 3758 → 3762 (+4 MF).
    # WAVE AJ leftover: Value Line + Permanent Portfolio + Kopernik +
    # Tocqueville leftover paid YE +18 MF. Honest pin remasured after
    # rebase onto #205 tip f6bb49ef: 3762 → 3780 (+18 MF).
    # WAVE AI leftover: Gabelli Class AAA FYE Dec 31 N-CSR +3 MF
    # (GABAX / GABBX / GICPX). Honest pin remasured after additive rebase
    # onto #207 tip 70b8d77a: 3780 → 3783 (+3 MF; no overlap with AF/AD/AE/AG/AH/AJ).
    # WAVE AK leftover: American Century Mutual Funds, Inc. leftover sibling
    # N-CSR +31 MF. Honest pin remasured after additive rebase onto #206 tip
    # 56c52345: 3783 → 3814 (+31 MF; ETF 5y unchanged at 758).
    # WAVE AL leftover: T. Rowe leftover Advisor / R / Institutional 2024
    # N-CSR +36 MF. Honest pin remasured after additive rebase onto #208 tip
    # e8887ce9: 3814 → 3850 (+36 MF; ETF 5y unchanged at 758).
    # WAVE AM leftover: Columbia official all-class $0 leftover years +
    # Real Estate Equity leftover 2021 N-CSR +12 MF. Honest pin remasured
    # after additive rebase onto #209 tip e5cbe71d: 3850 → 3862 (+12 MF;
    # ETF 5y unchanged at 758).
    # WAVE AN leftover: Hartford leftover I/C/F/R/Y + IHOAX Oct 31 N-CSR
    # + Artisan Mid/Small/Focus/Discovery 2023 N-CSR +136 MF. Honest pin
    # remasured on #210 tip 51e2b28b: 3862 → 3998 (+136 MF; ETF 5y
    # unchanged at 758).
    # WAVE AO leftover: Fidelity Advisor leftover Class I December 2021
    # N-CSR pay tables +9 MF. Honest pin remasured on WAVE AN tip
    # 9fb7db5: 3998 → 4007 (+9 MF; ETF 5y unchanged at 758).
    # WAVE AP leftover: Vanguard leftover 4y bond / GNMA / tax-exempt
    # December ICI monthly income +21 MF. Honest pin remasured on WAVE AO
    # tip 058c4ca: 4007 → 4028 (+21 MF; ETF 5y unchanged at 758).
    # WAVE AR leftover: Homestead leftover no-load FYE Dec 31 N-CSR
    # Financial Highlights +5 MF. Honest pin remasured on WAVE AP tip
    # c8dee49: 4028 → 4033 (+5 MF; ETF 5y unchanged at 758).
    # WAVE AS leftover: Virtus Asset Trust leftover FYE Dec 31 N-CSR
    # Financial Highlights +37 MF. Honest pin remasured on WAVE AR tip
    # e82c647: 4033 → 4070 (+37 MF; ETF 5y unchanged at 758).
    # WAVE AQ leftover: Victory leftover I/II Sycamore / Diversified Oct 31
    # 2021 N-CSR +17 MF. Honest pin remasured on WAVE AS tip 148383d:
    # 4070 → 4087 (+17 MF; ETF 5y unchanged at 758).
    # WAVE AT leftover: AMG leftover Frontier 2022 + GW&K SMID Growth
    # 2023 Oct 31 N-CSR +5 MF. Honest pin remasured on WAVE AQ tip
    # 4a585a8: 4087 → 4092 (+5 MF; ETF 5y unchanged at 758).
    assert digest.funds_with_5y == 4092
    assert digest.book_funds >= 7200
