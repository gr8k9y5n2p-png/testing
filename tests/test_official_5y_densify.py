"""Official 5-year paid/final history densify on the existing Aftertax book."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient

from app.models import AmountUnit, EstimateType, PublicationStage
from app.services.lookback import LOOKBACK_YEARS, _year_for_row, lookback_digest_from_rows
from app.sources.american_funds import AmericanFundsSource
from app.sources.aum import filter_large_aum
from app.sources.families import (
    BlackRockSource,
    FidelitySource,
    GoldmanSachsSource,
    InvescoSource,
    JPMorganSource,
    PimcoSource,
    StateStreetSource,
    TRowePriceSource,
    VanguardSource,
)
from app.sources.ark import ArkSource
from app.sources.dws import DwsSource
from app.sources.eighth_tier import (
    ArielSource,
    BairdSource,
    BuffaloSource,
    FmiSource,
    GqgSource,
    HeartlandSource,
    LongleafSource,
    PrimecapSource,
    ThirdAvenueSource,
)
from app.sources.eleventh_tier import (
    AmgSource,
    GuidestoneSource,
    KopernikSource,
    PermanentPortfolioSource,
    TimothyPlanSource,
    TocquevilleSource,
    ValueLineSource,
)
from app.sources.fifth_tier import (
    GabelliSource,
    HarborSource,
    NationwideSource,
    NylifeSource,
    OakmarkSource,
    RoyceSource,
    TouchstoneSource,
    TweedySource,
    VictorySource,
    VoyaSource,
)
from app.sources.fourth_tier import (
    ArtisanSource,
    CalamosSource,
    FirstEagleSource,
    GmoSource,
    HartfordSource,
    JohnHancockSource,
    MacquarieSource,
    PrincipalSource,
    ThriventSource,
    WasatchSource,
)
from app.sources.next_tier import (
    AmundiSource,
    BnyMellonSource,
    ColumbiaThreadneedleSource,
    DimensionalSource,
    FranklinTempletonSource,
    MorganStanleySource,
    NorthernTrustSource,
    NuveenSource,
    SchwabSource,
)
from app.sources.ninth_tier import AmericanBeaconSource, BaillieGiffordSource, BrandesSource
from app.sources.third_tier import (
    AllianceBernsteinSource,
    AllspringSource,
    AmericanCenturySource,
    DodgeCoxSource,
    EatonVanceSource,
    FederatedHermesSource,
    JanusHendersonSource,
    LordAbbettSource,
    MfsSource,
    VirtusSource,
)
from app.sources.sixth_tier import (
    AlgerSource,
    AqrSource,
    BrownAdvisorySource,
    CausewaySource,
    FirstTrustSource,
    HardingLoevnerSource,
    MatthewsAsiaSource,
    SeiSource,
    VaneckSource,
    WilliamBlairSource,
    WisdomtreeSource,
)
from app.sources.seventh_tier import (
    BridgewaySource,
    ChamplainSource,
    DavisSource,
    DiamondHillSource,
    DriehausSource,
    HotchkisWileySource,
    JensenSource,
    MarsicoSource,
    OsterweisSource,
    TcwSource,
)
from app.sources.tenth_tier import (
    BostonPartnersSource,
    HomesteadSource,
    LazardSource,
    LsvSource,
    MadisonSource,
    ManningNapierSource,
    WestwoodSource,
)
from app.sources.impax import ImpaxSource
from app.sources.parser import NormalizedRecord
from app.sources.registry import list_sources


def test_american_funds_midyear_2022_fills_near4_heroes() -> None:
    records = AmericanFundsSource().fetch(mode="fixture").records
    amcfx_2022 = next(
        row
        for row in records
        if row.ticker == "AMCFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
    )
    assert amcfx_2022.amount == Decimal("2.2668")
    assert str(amcfx_2022.ex_date) == "2022-06-15"
    assert amcfx_2022.publication_stage == PublicationStage.final

    abndx_2022_oi = next(
        row
        for row in records
        if row.ticker == "ABNDX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
    )
    assert abndx_2022_oi.amount == Decimal("0.023726")
    abndx_2022_lt = next(
        row
        for row in records
        if row.ticker == "ABNDX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
    )
    assert abndx_2022_lt.amount == Decimal("0.015")

    amcfx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "AMCFX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= amcfx_years


def test_american_funds_fahhx_2022_leftover_completes_5y() -> None:
    records = AmericanFundsSource().fetch(mode="fixture").records
    fahhx_2022 = next(
        row
        for row in records
        if row.ticker == "FAHHX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert fahhx_2022.amount == Decimal("0.0440349")
    assert str(fahhx_2022.ex_date) == "2022-07-29"
    fahhx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "FAHHX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= fahhx_years
    anefx_2022 = [
        row
        for row in records
        if row.ticker == "ANEFX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    ]
    assert anefx_2022 == []


def test_vanguard_leftover_ici_parallel_d_fills() -> None:
    records = VanguardSource().fetch(mode="fixture").records
    vsemx_2025 = {
        (str(row.amount), str(row.ex_date))
        for row in records
        if row.ticker == "VSEMX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    }
    assert ("0.764300", "2025-03-25") in vsemx_2025
    assert ("0.668200", "2025-06-26") in vsemx_2025
    vtspx_2021 = next(
        row
        for row in records
        if row.ticker == "VTSPX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert vtspx_2021.amount == Decimal("0.481000")
    vtspx_2023 = next(
        row
        for row in records
        if row.ticker == "VTSPX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert vtspx_2023.amount == Decimal("0.320200")
    vctxx_2024 = next(
        row
        for row in records
        if row.ticker == "VCTXX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert vctxx_2024.amount == Decimal("0.001951")
    vmrxx_2025 = next(
        row
        for row in records
        if row.ticker == "VMRXX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert vmrxx_2025.amount == Decimal("0.003214")
    vmsxx_2025 = next(
        row
        for row in records
        if row.ticker == "VMSXX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert vmsxx_2025.amount == Decimal("0.002213")
    vedix_2024 = next(
        row
        for row in records
        if row.ticker == "VEDIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert vedix_2024.amount == Decimal("0.586100")
    vedix_2025 = [
        row
        for row in records
        if row.ticker == "VEDIX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    ]
    assert vedix_2025 == []
    for ticker in ("VSEMX", "VTSPX", "VCTXX", "VMRXX", "VMSXX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_vanguard_leftover_ici_parallel_aa_fills() -> None:
    records = VanguardSource().fetch(mode="fixture").records
    bnd_2022 = next(
        row
        for row in records
        if row.ticker == "BND"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2022-12-29"
        and row.amount
    )
    assert bnd_2022.amount == Decimal("0.172311")
    assert bnd_2022.publication_stage == PublicationStage.final
    bnd_2025 = next(
        row
        for row in records
        if row.ticker == "BND"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-22"
        and row.amount
    )
    assert bnd_2025.amount == Decimal("0.246638")
    vbiix_2022 = next(
        row
        for row in records
        if row.ticker == "VBIIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2022-12-01"
        and row.amount
    )
    assert vbiix_2022.amount == Decimal("0.021170")
    vwalx_2022 = next(
        row
        for row in records
        if row.ticker == "VWALX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2022-12-01"
        and row.amount
    )
    assert vwalx_2022.amount == Decimal("0.030387")
    biv_2025 = next(
        row
        for row in records
        if row.ticker == "BIV"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-08-05"
        and row.amount
    )
    assert biv_2025.amount == Decimal("0.265057")
    vbtix_2023 = next(
        row
        for row in records
        if row.ticker == "VBTIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-04-03"
        and row.amount
    )
    assert vbtix_2023.amount == Decimal("0.024227")
    vfirx_2023 = next(
        row
        for row in records
        if row.ticker == "VFIRX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-09-01"
        and row.amount
    )
    assert vfirx_2023.amount == Decimal("0.035085")
    vtbsx_2022 = next(
        row
        for row in records
        if row.ticker == "VTBSX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2022-05-02"
        and row.amount
    )
    assert vtbsx_2022.amount == Decimal("0.018866")
    vclax_2023 = next(
        row
        for row in records
        if row.ticker == "VCLAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-03-01"
        and row.amount
    )
    assert vclax_2023.amount == Decimal("0.029218")
    for ticker in (
        "BIV",
        "BND",
        "VBIIX",
        "VBIMX",
        "VBMFX",
        "VBMPX",
        "VBTIX",
        "VCITX",
        "VCLAX",
        "VFIRX",
        "VFISX",
        "VTBSX",
        "VUSXX",
        "VWALX",
    ):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_aa_leftover_walls_stay_unmatched() -> None:
    records = VanguardSource().fetch(mode="fixture").records
    vflq_liq = [
        row
        for row in records
        if row.ticker == "VFLQ"
        and row.amount == Decimal("99.896787")
    ]
    assert vflq_liq == []
    # WAVE AP fills the AA leftover wrap-absent December rows.
    vbtlx_2023 = next(
        row
        for row in records
        if row.ticker == "VBTLX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-12-01"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert vbtlx_2023.amount == Decimal("0.026521")
    bsv_missing = [
        row
        for row in records
        if row.ticker == "BSV"
        and row.ex_date
        and row.ex_date.year in {2022, 2025}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert bsv_missing == []
    vwehx_2025 = next(
        row
        for row in records
        if row.ticker == "VWEHX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-01"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert vwehx_2025.amount == Decimal("0.028290")
    vedix_2025 = [
        row
        for row in records
        if row.ticker == "VEDIX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount is not None
    ]
    assert vedix_2025 == []

    dfa = DimensionalSource().fetch(mode="fixture").records
    for ticker in ("DISVX", "DFELX", "DFQTX"):
        early = [
            row
            for row in dfa
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year in {2021, 2022}
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert early == [], ticker

    schwab = SchwabSource().fetch(mode="fixture").records
    swbgx_early = [
        row
        for row in schwab
        if row.ticker == "SWBGX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert swbgx_early == []

    nuveen = NuveenSource().fetch(mode="fixture").records
    tinrx_paid_early = [
        row
        for row in nuveen
        if row.ticker == "TINRX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert tinrx_paid_early == []

    ssga = StateStreetSource().fetch(mode="fixture").records
    splg_paid = [
        row
        for row in ssga
        if row.ticker == "SPLG"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert splg_paid == []
    hybl_2021 = [
        row
        for row in ssga
        if row.ticker == "HYBL"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount is not None
    ]
    assert hybl_2021 == []


def test_hartford_class_a_historical_pdf_is_name_keyed() -> None:
    records = HartfordSource().fetch(mode="fixture").records
    ihgix_2021 = next(
        row
        for row in records
        if row.ticker == "IHGIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert ihgix_2021.amount == Decimal("1.50586")
    haiax_2022 = next(
        row
        for row in records
        if row.ticker == "HAIAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert haiax_2022.amount == Decimal("1.11577")
    # Share-class product-page tickers are not copied from the fund-level PDF.
    hdgix_hist = [
        row
        for row in records
        if row.ticker == "HDGIX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
    ]
    assert hdgix_hist == []


def test_victory_2025_official_finals_count_as_final() -> None:
    records = VictorySource().fetch(mode="fixture").records
    mmeax = next(
        row
        for row in records
        if row.ticker == "MMEAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
        and row.publication_stage == PublicationStage.final
    )
    assert mmeax.amount == Decimal("3.922505")


def test_in_book_large_aum_filter_unchanged() -> None:
    from dataclasses import replace

    hero = NormalizedRecord(
        fund_family="Hartford Funds",
        fund_name="The Hartford MidCap Fund Class A",
        ticker="HFMCX",
        cusip=None,
        share_class="A",
        estimate_type=EstimateType.long_term_capital_gains,
        amount=Decimal("1.67"),
        amount_min=None,
        amount_max=None,
        amount_unit=AmountUnit.per_share,
        record_date=None,
        ex_date=date(2024, 12, 11),
        payable_date=None,
        as_of=date(2024, 12, 11),
        publication_stage=PublicationStage.final,
        source_url="fixture://hartford",
    )
    in_book = replace(hero, ticker="HFMIX", fund_name="The Hartford MidCap Fund Class I")
    unknown = replace(hero, ticker="ZZTINY", fund_name="Tiny")
    kept = filter_large_aum([hero, in_book, unknown], {"HFMIX"})
    assert [row.ticker for row in kept] == ["HFMCX", "HFMIX"]


def test_fixture_book_5y_lookback_after_official_densify() -> None:
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
    # 3,252 after #160/#161/#162. Parallel D leftover fills: +6 MF (FAHHX 2022 /
    # VSEMX 2025 / VTSPX 2021+2023 / VCTXX / VMRXX / VMSXX 2024–2025).
    # Parallel E leftover Nuveen Institutional / Class I paid history: +3 MF 5y
    # (TEIHX / TICHX / TSOHX). NSBRX is 4y (2021 unpublished).
    # Parallel C leftover: Northern Trust 2022 ICI CG-dash equity (NMIEX +1 MF).
    # Parallel H leftover: Janus Henderson quarterly / midyear ICI +33 MF
    # (JABAX / HFQAX / JERAX families). Lord Abbett LAGWX is 2y. Putnam /
    # remaining MFS leftover years stay unmatched.
    # Parallel F leftover: T. Rowe TBLYX 2021+2022 YE PDF (+1 MF 5y). TRLAX 2023
    # LT is year-depth only (still missing 2021). ETF 5y unchanged on #167.
    # Parallel G leftover: BlackRock/iShares + SPDR fills raise the pin +2 MF
    # (BIRAX 2021 / MDLOX 2021+2022) and +2 ETF (IBHF 2021–2024 / NZAC 2022–2023).
    # Parallel K leftover: Allspring class-level December income +31 MF 5y
    # (Core Bond / Short-Term Bond Plus / Core Plus / HY Muni / Income Plus /
    # MN+WI tax-free / Spectrum Income + Conservative / WICIX+WICRX).
    # MSIM/EV ETF 2024 leftover is year-depth only. No new identities.
    # Parallel I leftover: Artisan leftover ICI + Calamos Class A paid/product
    # pages raise the pin +20 MF (Victory 2022 RS is year-depth; Dodge Class X
    # 2021 and Alger 2021/2023/2024 stay unmatched).
    # Parallel J leftover: AllianceBernstein Class A product-page paid YE
    # +15 MF (AGRFX / APGAX / ABASX / ABVAX / ADGAX / ALTFX / ASLAX / AUIAX /
    # AUUAX / AWAAX / CABDX / CABNX / GCEAX / SCAVX / WPASX). CHCLX stays 2y.
    # No new identities.
    # Parallel O leftover: VanEck tax-guide + later 2025 paid PDF fill 3
    # leftover ETFs to 5y (EINC 2021–2025 / LFEQ 2023+2025 / RAAX 2023+2025).
    # Year-depth only: EGPT 2024, YUMY 2024, CLOI/CLOB/CMCI 2025, WisdomTree
    # UNIY 2023. First Trust leftover Print=Y years stay empty-year walls;
    # Global X is not in the 10056-ticker book.
    # Parallel M leftover: GuideStone Investor product-page Sitecore paid
    # history +17 MF (GGEZX / GVEZX / GSCZX / GIEZX / GEMZX / GFSZX / GMGZX /
    # GDMZX / GEQZX / GFIZX / GGIZX / GCOZX / GGBZX / GMTZX / GMWZX / GMHZX /
    # GMFZX). GMZXX / GVIZX / GEIZX / GIIZX stay 4y (2021 unpublished).
    # TWCGX 2023–2024 paid is year-depth only. No new identities.
    # Parallel N leftover: Federated Hermes Final Capital Gains API leftover
    # paid YE +44 MF (KLCAX / PMIEX / QALGX families). SEI 2025 final PDF is
    # year-depth only. Macquarie 2021 and Russell Investments stay unmatched.
    # No new identities.
    # Impax / Pax hero-package gap fill: official 2021–2025 paid book for the
    # 22 in-book tickered shells plus the four already-healthy identities
    # unlocks +18 MF 5y. ETF 5y unchanged. No tickers beyond the 22 shells.
    # Parallel L leftover: BNY Mellon leftover Class A / Investor / ETF
    # product-page paid YE +10 MF / +9 ETF, plus Royce RDVIX November 2025
    # +1 MF. DWS leftover 2024 ICI is year-depth only (2y, not 5y). Brown
    # leftover years stay estimate-only / unpublished.
    # Parallel P leftover: Wasatch official product-page paid YE +2 MF
    # (WHOSX / WMCVX). Gabelli leftover 2025 is year-depth only (2y).
    # Matthews Investor leftovers already 5y. Causeway CCENX/CCEVX stay 2y.
    # Parallel S leftover: Davis / PRIMECAP / Ariel / Baird / Hotchkis & Wiley /
    # Champlain leftover paid YE +12 MF (ARGFX / ARAIX / POSKX / POGRX / POAGX /
    # HWLIX / HWAIX / HWNIX / BMDIX / BMDSX / CIPIX / CIPNX). Davis leftovers
    # stay 3–4y (2021 Wayback unpublished; DGFAX 2022 dashed). Baird BSV / CCG /
    # CCW printed None years unmatched. CIPTX 2021–2022 unpublished. ETF 5y
    # unchanged. No new identities.
    # Parallel Q leftover: GMO US Trust Class III NAVs workbooks + Voya
    # Corporate Leaders 100 Class A product-page paid YE +4 MF (GQETX /
    # GMUEX / GTMIX / VYCAX). Nationwide leftover 2021–2023 is 4y (2024
    # estimate wall). NYLI Class I stays estimate-only.
    # Parallel R leftover: Diamond Hill Investor paid HTML +7 MF (DHSCX /
    # DHMAX / DHPAX / DHLAX / DHTAX / DIAMX / DHIAX) and Bridgeway product-
    # page / paid PDF leftover +4 MF (BRUSX / BOSVX / BRAGX / BRSVX). AQR
    # 2023+2025 finals and leftover 2024 N/R6 are year-depth only (3y).
    # Jensen 2021–2023 and TCW 2021–2024 stay unmatched. No new identities.
    # Parallel V leftover: Heartland Investor+Institutional tax-center paid
    # history +6 MF (HRMDX / HNMDX / HRVIX / HNVIX / HRTVX / HNTVX), FMI
    # Common Stock leftover +2 MF (FMIUX / FMIMX), and Brandes Class I
    # product-page paid YE +5 MF (BGVIX / BIIEX / BSCMX / BEMIX / BISMX).
    # Baillie Gifford 2025 Final is year-depth only. GQG leftovers stay
    # estimate-only (no paid/final book). ETF 5y unchanged. No new identities.
    # Parallel W leftover: Manning & Napier December paid YE +27 MF (EXEYX /
    # MNHIX / MNDFX families) and Westwood Institutional paid history +3 MF
    # (WHGLX / WHGMX / WHGSX). Year-depth only: Callodine 3y, RAIIX 4y,
    # RISAX 3y, WWMCX 3y, WQAIX 4y, Boston Partners 2024+2025 / LSV 2024
    # (2y). Lazard / Homestead / Madison leftover years stay unmatched.
    # ETF 5y unchanged. No new identities.
    # Parallel T leftover: Marsico Investor leftover paid YE +5 MF
    # (MFOCX / MGRIX / MXXIX / MIOFX / MGLBX). Institutional leftovers are
    # 4y (2021 unpublished). Harding Loevner leftover 2021/2022 PDFs are
    # year-depth (HLEMX 4y; 2024 leftover Z / HLEMX / HLIDX unpublished).
    # Alger 2021/2023/2024 MF and Driehaus 2021–2024 stay unmatched.
    # All-events leftover (non-MFS, rebased onto #186+#181 tip): official
    # midyear / quarterly typed rows for American Funds, Vanguard, T. Rowe,
    # and iShares. Adopts merged #186 MFS mid-year fills. +1 MF 5y from a
    # published midyear event on the Parallel T tip (3545 / MF 2795 / ETF 750).
    # Parallel U leftover: Tweedy product-page paid YE +4 MF (TBGVX / TWEBX /
    # TBCUX / TBHDX), Osterweis historical PDFs +3 MF (OSTFX / OSTGX / OSTVX),
    # and Longleaf product-page paid 2021–2024 +3 MF (LLPFX / LLSCX / LLGLX).
    # Buffalo 2024–2025 is year-depth only (2y; 2021–2023 unpublished).
    # Third Avenue 2022–2024 is year-depth only (4y; 2021 unpublished).
    # ETF 5y unchanged. No new identities.
    # Parallel AA leftover: Vanguard leftover ICI bond / tax-exempt / MM
    # years +14 (12 MF / 2 ETF): BIV / BND / VBIIX / VBIMX / VBMFX / VBMPX /
    # VBTIX / VCITX / VCLAX / VFIRX / VFISX / VTBSX / VUSXX / VWALX.
    # Schwab / SSGA / DFA / Nuveen leftover re-probes stay walls.
    # Parallel AB leftover (rebased onto tip 3570 / MF 2818 / ETF 752):
    # Oakmark 2024 class-level Wayback YE +22 MF (OAYMX / OANMX / OAZMX
    # families + OAKBX E&I) and Janus Daily leftover ICI month-end income
    # +40 MF (JAFIX / JAHYX / JMUIX / JUCAX families). Year-depth only:
    # LBNDX 2022 / LTRAX 2021. Dodge Class X 2021 / Artisan 2023 Mid Small
    # Focus Discovery / 2022 GOPPS / Lord Daily AJAX stay walls. ETF 5y
    # unchanged from AA. No new identities. Honest pin = tip 3570 + AB +62.
    # Parallel Y leftover: BlackRock / iShares MF Investor A leftover years
    # from live 2021–2024 open-end tax HTML + official stamped 2025 book
    # +16 MF (BABDX / BACAX / BALPX / BARDX / BAREX / BDSAX / BICSX /
    # BROAX / MALRX / MALVX / MCFOX / MDDCX / MDGCX / MDLVX / MDSPX / SHSAX).
    # Invesco 2021–2022 ICI still 404; Franklin DIST-SUMM 2021–2024 still 204;
    # PIMCO has no in-book leftover tickers. ETF 5y unchanged from the AB tip.
    # No new identities.
    # Parallel AC leftover: Principal leftover YEAR finals +12 MF (PFIJX /
    # GEM PEPSX-PIEIX-PIEJX-PIIMX 2024 income; Real Estate PFRSX family
    # 2025 quarterly income). AF YEAR-final JSON, JH ICI 403, Nationwide
    # 2024 estimate PDFs, and Thrivent unpublished CG years stay walls.
    # #188 midyear all-events not redone. ETF 5y unchanged vs Y tip.
    # No new identities.
    # Mass Z leftover (rebased onto #195 AC tip 3660): Columbia Institutional
    # 2021$+2022 leftover+2023 leftover +24 MF and MFS leftover year
    # finals +9 MF. T. Rowe Advisor/R 2023+2025 is year-depth only
    # (2024 wall). Hartford leftover years stay unmatched. Additive on
    # tip fills — no double-count. Honest pin = tip 3660 + Z +33.
    # WAVE X leftover (existing in-book only): Fidelity Advisor Class I DPL2
    # 2022–2024 + FTRIX 2021 N-CSR (+1 MF), American Century Investor N-CSR
    # (+4 MF: TWCGX / AFDIX / TWCIX / TWCUX), JPMorgan Trust II Class A N-CSR
    # (+21 MF), Goldman Sachs Insights Class A / Institutional N-CSR (+2 MF).
    # Year-depth only: Fidelity Advisor Class I leftovers stay 4y (2021 DPL2
    # Class A name-only), TWHIX 4y / ANOIX 3y (N-CSR dashes), PGSGX 4y (2024
    # dashed), JEPQ 4y (2021 commencement), retail DPL6 2022–2023 unpublished.
    # Honest pin remasured after rebase onto #192 tip: 3693 → 3721
    # (+28 MF; ETF 5y unchanged at 752). No new identities.
    # WAVE AF leftover (existing in-book only): Harbor Institutional
    # product-page paid history +8 MF (HACAX / HAVLX / HASCX / HAIDX /
    # HAISX / HAMVX / HAOSX / HMCLX). HSICX 2024–2025 is year-depth
    # (inception 2024-03-01). Calamos CAISX 2024 printed $0 is year-depth
    # (inception 03/31/22). Virtus 2021–2024 calendar PDFs still alias
    # 2025. Transamerica / Neuberger have no in-book leftover identities.
    # Honest pin = tip 3721 + AF +8.
    # WAVE AD leftover (existing in-book only): Macquarie / Delaware Class A
    # N-CSR 2021 +7 MF (DCCAX / DEVLX / DDIAX / DDVAX / DLHAX / FGINX /
    # FIUSX) and Eaton Vance EOI N-CSR 2021–2025 +1 ETF. AB CHCLX 2022
    # N-CSR is year-depth only (2023–2024 dashes). Ivy leftovers, MSIM
    # ETF 2021–2023, and PGIM (no in-book tickers) stay walls.
    # Honest pin remasured after rebase onto #201 tip: 3729 + AD +8
    # (7 MF / 1 ETF) → 3737.
    # WAVE AE leftover (existing in-book only): Invesco ETF Tax Center ICI
    # Primary 2021–2025 leftover December YE for estimate-table identities
    # +5 ETF (PIN / PSCI / IDMO / IVRA / PBP). SSGA / First Trust /
    # WisdomTree leftover re-probes stay walls. Invesco MF Investor A
    # belongs to Y #194 — not redone. Year-depth only: HIYS 2023–2025,
    # BSJW 2024–2025, BSJX / GTOC / IQSZ / MTRA 2025. Honest pin =
    # tip 3737 + AE +5 ETF → 3742. No new identities.
    # WAVE AG leftover (existing in-book only): Victory RS FYE Dec 31 2021
    # N-CSR Financial Highlights unlock +16 MF already on 2022–2025 RS books
    # (RSGRX / RGWCX / RGRYX / RSINX / RIVCX / RSIYX / GPAFX / RCOCX / RCEYX /
    # RSPFX / RSPMX / RSPKX / RSPYX / RSVAX / RVACX / RSVYX). Leftover 2024
    # I/II Class R/Member/R6 is year-depth (2021 I/II still 404). Touchstone
    # leftover JSON years, Putnam CEF DIST-SUMM 204, Fidelity retail DPL6
    # 2022–2023, and USAA FYE March 31 stay walls. Advisor DPL2 / FTRIX not
    # redone. Honest pin remasured after rebase onto #203 tip ba30980:
    # 3742 → 3758 (+16 MF; ETF 5y unchanged at 758). No overlap with AF/AD/AE.
    # WAVE AH leftover (existing in-book only): BNY renamed Midcap Value
    # Class A DMCVX + Investor MIBLX / MIMSX / MISCX product-page paid YE
    # +4 MF. VanEck leftover N-CSR dashes, Royce 2023 dashes, Brown
    # estimate-only, ARK 2022 no-distribution FINAL, GMO ETF estimate-stage,
    # Tweedy / PRIMECAP / Ariel already 5y stay walls / unchanged.
    # Honest pin remasured after rebase onto #204 tip 5b1ffa45:
    # 3758 → 3762 (+4 MF; ETF 5y unchanged at 758). No overlap with AF/AD/AE/AG.
    # WAVE AJ leftover (existing in-book only): Value Line historical YE
    # +10 MF, Permanent Portfolio Class I leftover tax PDFs +3 MF,
    # Kopernik leftover Final memos +4 MF, Tocqueville leftover paid
    # notices +1 MF. Calvert / Domini / Parnassus / Neuberger have no
    # in-book leftovers. Impax / Hartford / Invesco MF leftover years
    # stay walls. VALLX / VLLIX 2023 official dashes stay 4y. Does not
    # redo Gabelli AAA / BNY AH / Victory AG / Harbor AF / Macquarie AD /
    # Invesco ETF AE. Honest pin remasured after rebase onto #205 tip
    # f6bb49ef: 3762 → 3780 (+18 MF; ETF 5y unchanged at 758).
    # WAVE AI leftover (existing in-book only): Gabelli Class AAA FYE Dec 31
    # 2021–2023 N-CSR Financial Highlights unlock +3 MF already on 2024–2025
    # AAA books (GABAX / GABBX / GICPX). GABGX 2021+2023 is year-depth (2022
    # highlights dashes). GABSX / GABEX FYE Sep 30, Allspring leftover FYEs,
    # Federated Kaufmann/MDT/SDG unpublished API years, SEI 2021–2024 final
    # PDFs 404, Voya NLCAX/NMCAX May 31, Wasatch Sep 30, Causeway CCENX, and
    # Cohen/Guggenheim/DoubleLine/Russell (no in-book source) stay walls.
    # Honest pin remasured after additive rebase onto #207 tip 70b8d77a:
    # 3780 → 3783 (+3 MF; ETF 5y unchanged at 758). No overlap with AJ/AH/AG/AE/AD/AF.
    # WAVE AK leftover (existing in-book only): American Century Mutual Funds,
    # Inc. leftover sibling-class FYE Oct 31 N-CSR Financial Highlights unlock
    # +31 MF already on estimate books (Growth / Select / Ultra / Large Cap
    # Equity leftover A/C/I/R/R5/R6/Y plus Ultra G / LCE G; Balanced
    # TWBIX / ABINX / ABGNX). Investor WAVE X leftovers not redone. Growth G
    # ACIHX 2021 commencement, Heritage 2023 dashes, LCE C/R 2021 dashes,
    # Small Cap Growth 2023–2024 dashes, Select G 2024 commencement stay
    # walls. Janus / Principal / Nationwide / Thrivent / EV leftover years
    # stay unmatched. Honest pin remasured after additive rebase onto #206
    # tip 56c52345: 3783 → 3814 (+31 MF; ETF 5y unchanged at 758).
    # WAVE AL leftover (existing in-book only): T. Rowe leftover Advisor / R /
    # Institutional 2024 N-CSR Financial Highlights unlock +36 MF already on
    # WAVE Z 2021–2023+2025 books (PABGX / RRBGX / PACLX / PAFDX / PMEGX /
    # IEMFX and Dec 31 / Oct 31 leftover siblings). FAI 2024 all-class
    # XLSX/PDF still unpublished; iinvestor 2024 is Investor/I only.
    # RRCOX 2024 N-CSR dashed. Retirement / Target May 31 FYE not
    # calendar-safe. Fidelity retail DPL6 2022–2023 still HPDY SPA.
    # JPM Trust I leftover Class A XBRL-nested; PGSGX 2024 dashed; JEPQ
    # 2021 commencement. GS GLCGX / GCGIX already 5y — no leftover
    # identities. No overlap with AF–AK. Honest pin remasured after
    # additive rebase onto #208 tip e8887ce9: 3814 → 3850 (+36 MF;
    # ETF 5y unchanged at 758).
    # WAVE AM leftover (existing in-book only): Columbia official all-class
    # $0 leftover years + Real Estate Equity leftover 2021 N-CSR unlock
    # +12 MF (UMLGX / CSVFX / CREEX / CGEZX / NSEPX / CSCZX 2022; CBALX
    # 2023; CBMZX / CZMGX 2025; CREAX / CRRVX / CREYX 2021+2022). Does
    # not redo AF–AL. Hartford / MFS leftover Excel / Artisan 2023 ICI /
    # Dodge Class X 2021 / Oakmark Bond 2023 / Lord Daily / Franklin
    # DIST-SUMM / PIMCO / BlackRock MDEFX 2021 / Dimensional 2021–2022 /
    # Nuveen NSBRX 2021 / Schwab MM stay walls. Honest pin remasured
    # after additive rebase onto #209 tip e5cbe71d: 3850 → 3862 (+12 MF;
    # ETF 5y unchanged at 758).
    # WAVE AN leftover (existing in-book only): Hartford leftover I/C/F/R/Y
    # + leftover Class A IHOAX Oct 31 N-CSR 2021–2024 +126 MF; Artisan Mid /
    # Small / Focus / Discovery 2023 N-CSR OI +10 MF. Does not redo AF–AM.
    # MFS leftover Excel / Lord LAGWX July 31 / Dodge Class X 2021 / Oakmark
    # Bond 2023 stay walls. Honest pin remasured on #210 tip 51e2b28b:
    # 3862 → 3998 (+136 MF; ETF 5y unchanged at 758).
    # WAVE AO leftover (existing in-book only): Fidelity Advisor leftover
    # Class I December 2021 N-CSR Distributions (Unaudited) pay tables
    # unlock leftover Class I already on WAVE X DPL2 2022–2024 (FIXIX /
    # FOPIX / FIADX / FWIFX / FVIFX / FASOX / EQPGX / FSCIX / FMCCX).
    # Does not redo AF–AN (especially AN Hartford I/C/F/R/Y + Artisan
    # 2023). MFS leftover Excel / Lord LAGWX July 31 / Dodge Class X
    # 2021 / Oakmark Bond 2023 stay walls. Honest pin remasured on
    # WAVE AN tip 9fb7db5: 3998 → 4007 (+9 MF; ETF 5y unchanged at 758).
    # WAVE AP leftover (existing in-book only): Vanguard leftover 4y bond /
    # GNMA / tax-exempt December monthly income the AA leftover ICI extract
    # marked wrap-absent (VWEHX / VFSTX 2025 + VWAHX 2024 + VBTLX 2023 +
    # VWIUX 2022). Preferred Schwab / DFA / Nuveen / BlackRock MDEFX and
    # American Funds ANEFX/SMCWX/CNWCX 2022 remasured as walls. Does not
    # redo AF–AO. Honest pin remasured on WAVE AO tip 058c4ca: 4007 → 4028
    # (+21 MF; ETF 5y unchanged at 758).
    # WAVE AR leftover (existing in-book only): Homestead leftover no-load
    # FYE Dec 31 N-CSR Financial Highlights unlock +5 MF already on the 2025
    # YE book (HSTIX / HOVLX / HNASX / HISIX / HSCSX). Disjoint from AQ
    # (Janus / Putnam / Touchstone / Victory / PGIM / AB / EV / MSIM /
    # Macquarie). Timothy FYE Sep 30 / Calvert / Parnassus / Domini /
    # Eventide / Ave Maria remasured as walls (no in-book leftover or not
    # calendar-safe). Does not redo AF–AP (especially AO Fidelity Class I,
    # AP Vanguard ICI Dec, AN Hartford/Artisan). Honest pin remasured on
    # WAVE AP tip c8dee49: 4028 → 4033 (+5 MF; ETF 5y unchanged at 758).
    # WAVE AS leftover (existing in-book only): Virtus Asset Trust leftover
    # FYE Dec 31 N-CSR Financial Highlights unlock +37 MF already on the
    # 2025 calendar book (Ceredex / SGA International Growth / Silvant
    # Large-Cap Growth / Seix). Disjoint from AQ (Janus / Putnam /
    # Touchstone / Victory / PGIM / AB / EV / MSIM / Macquarie) and AR
    # Homestead. Preferred GMO / Tweedy already 5y; Calamos / First Eagle
    # GRA-Smid / Royce 2023 / Wasatch 2023 / KAR FYE Sep 30 remasured as
    # walls. Does not redo AF–AR (especially AO Fidelity Class I, AP
    # Vanguard ICI Dec, AN Hartford/Artisan, AR Homestead). Honest pin
    # remasured on WAVE AR tip e82c647: 4033 → 4070 (+37 MF; ETF 5y
    # unchanged at 758).
    assert digest.funds_with_5y == 4070
    assert digest.funds_with_5y_mf == 3312
    assert digest.funds_with_5y_etf == 758
    assert digest.book_funds >= 7200
    assert "never invented" in " ".join(digest.notes).lower()


def test_ishares_official_gapfill_adds_missing_years() -> None:
    records = BlackRockSource().fetch(mode="fixture").records
    soxx_2025 = next(
        row
        for row in records
        if row.ticker == "SOXX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert soxx_2025.amount == Decimal("0.436272")
    assert str(soxx_2025.ex_date) == "2025-12-16"
    assert soxx_2025.publication_stage == PublicationStage.final

    mbb_2021 = next(
        row
        for row in records
        if row.ticker == "MBB"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert mbb_2021.amount == Decimal("0.018858")
    assert str(mbb_2021.ex_date) == "2021-10-01"

    eirl_2022 = next(
        row
        for row in records
        if row.ticker == "EIRL"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert eirl_2022.amount == Decimal("0.518078")

    soxx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "SOXX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= soxx_years


def test_vanguard_vtipx_2025_official_ici() -> None:
    records = VanguardSource().fetch(mode="fixture").records
    vtipx_2025 = next(
        row
        for row in records
        if row.ticker == "VTIPX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert vtipx_2025.amount == Decimal("0.350500")
    assert str(vtipx_2025.ex_date) == "2025-12-17"
    vtipx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "VTIPX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= vtipx_years


def test_first_trust_official_product_page_history_fills_missing_years() -> None:
    records = FirstTrustSource().fetch(mode="fixture").records
    fvd_2021 = next(
        row
        for row in records
        if row.ticker == "FVD"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert fvd_2021.amount == Decimal("0.231700")
    assert str(fvd_2021.ex_date) == "2021-12-23"
    assert fvd_2021.publication_stage == PublicationStage.final

    fpe_2022 = next(
        row
        for row in records
        if row.ticker == "FPE"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert fpe_2022.amount == Decimal("0.092500")

    cibr_2023 = next(
        row
        for row in records
        if row.ticker == "CIBR"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert cibr_2023.amount == Decimal("0.165800")

    fvd_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "FVD"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= fvd_years


def test_first_trust_in_book_hero_gapfill_adds_leftover_2024() -> None:
    records = FirstTrustSource().fetch(mode="fixture").records
    fpei_2024 = next(
        row
        for row in records
        if row.ticker == "FPEI"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert fpei_2024.amount == Decimal("0.087000")
    assert str(fpei_2024.ex_date) == "2024-12-13"
    assert fpei_2024.publication_stage == PublicationStage.final

    rfdi_2024 = next(
        row
        for row in records
        if row.ticker == "RFDI"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert rfdi_2024.amount == Decimal("1.151300")

    fta_2024 = next(
        row
        for row in records
        if row.ticker == "FTA"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert fta_2024.amount == Decimal("0.453400")

    igld_2024 = next(
        row
        for row in records
        if row.ticker == "IGLD"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert igld_2024.amount == Decimal("2.404300")
    assert str(igld_2024.ex_date) == "2024-12-02"

    fpei_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "FPEI"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= fpei_years
    # BGLD 2021 is unpublished on the issuer Print=Y page — unmatched, not $0.
    bgld_2021 = [
        row
        for row in records
        if row.ticker == "BGLD"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    ]
    assert bgld_2021 == []


def test_vaneck_official_2021_2022_tax_center_pdfs() -> None:
    records = VaneckSource().fetch(mode="fixture").records
    gdx_2022 = next(
        row
        for row in records
        if row.ticker == "GDX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert gdx_2022.amount == Decimal("0.4762")
    assert str(gdx_2022.ex_date) == "2022-12-19"

    inivx_2021 = next(
        row
        for row in records
        if row.ticker == "INIVX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert inivx_2021.amount == Decimal("0.6603")

    mwmix_2021 = next(
        row
        for row in records
        if row.ticker == "MWMIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert mwmix_2021.amount == Decimal("1.7611")

    inivx_2022 = [
        row
        for row in records
        if row.ticker == "INIVX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    ]
    assert inivx_2022 == []


def test_wisdomtree_official_december_income_and_2023_cg() -> None:
    records = WisdomtreeSource().fetch(mode="fixture").records
    dgrw_2024 = next(
        row
        for row in records
        if row.ticker == "DGRW"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert dgrw_2024.amount == Decimal("0.15525")
    dgrw_2021 = next(
        row
        for row in records
        if row.ticker == "DGRW"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert dgrw_2021.amount == Decimal("0.20349")
    agzd_2023 = next(
        row
        for row in records
        if row.ticker == "AGZD"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert agzd_2023.amount == Decimal("0.50744")
    dgrw_2023 = next(
        row
        for row in records
        if row.ticker == "DGRW"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert dgrw_2023.amount == Decimal("0.10000")
    assert str(dgrw_2023.ex_date) == "2023-11-24"


def test_schwab_in_book_product_page_history_fills_missing_years() -> None:
    records = SchwabSource().fetch(mode="fixture").records
    swanx_2021 = next(
        row
        for row in records
        if row.ticker == "SWANX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert swanx_2021.amount == Decimal("3.8250")
    assert str(swanx_2021.ex_date) == "2021-12-16"
    assert swanx_2021.publication_stage == PublicationStage.final

    snxfx_2021 = next(
        row
        for row in records
        if row.ticker == "SNXFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert snxfx_2021.amount == Decimal("1.2268")

    swlsx_2021 = next(
        row
        for row in records
        if row.ticker == "SWLSX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert swlsx_2021.amount == Decimal("1.6176")

    swanx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "SWANX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= swanx_years


def test_first_trust_leftover_midyear_fills_empty_december_years() -> None:
    records = FirstTrustSource().fetch(mode="fixture").records
    fpx_2021 = next(
        row
        for row in records
        if row.ticker == "FPX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert fpx_2021.amount == Decimal("0.080500")
    assert str(fpx_2021.ex_date) == "2021-09-23"
    assert fpx_2021.publication_stage == PublicationStage.final

    fep_2022 = next(
        row
        for row in records
        if row.ticker == "FEP"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert fep_2022.amount == Decimal("0.170700")

    fsz_2023 = next(
        row
        for row in records
        if row.ticker == "FSZ"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert fsz_2023.amount == Decimal("1.281000")

    fpx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "FPX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= fpx_years
    # BGLD 2021 is still unpublished on the issuer Print=Y page.
    bgld_2021 = [
        row
        for row in records
        if row.ticker == "BGLD"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    ]
    assert bgld_2021 == []


def test_first_trust_parallel_b_leftover_print_y_years() -> None:
    records = FirstTrustSource().fetch(mode="fixture").records
    fny_2025 = next(
        row
        for row in records
        if row.ticker == "FNY"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert fny_2025.amount == Decimal("0.029700")
    assert str(fny_2025.ex_date) == "2025-06-26"
    assert fny_2025.publication_stage == PublicationStage.final

    bnge_2022 = next(
        row
        for row in records
        if row.ticker == "BNGE"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert bnge_2022.amount == Decimal("0.099800")
    assert str(bnge_2022.ex_date) == "2022-06-24"

    emdm_2024 = next(
        row
        for row in records
        if row.ticker == "EMDM"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert emdm_2024.amount == Decimal("0.847300")

    sdvd_2024 = next(
        row
        for row in records
        if row.ticker == "SDVD"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert sdvd_2024.amount == Decimal("0.161200")

    fdni_2023 = next(
        row
        for row in records
        if row.ticker == "FDNI"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert fdni_2023.amount == Decimal("0.089700")
    assert str(fdni_2023.ex_date) == "2023-03-24"

    fny_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "FNY"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2022, 2023, 2024, 2025} <= fny_years
    assert 2021 not in fny_years
    # 4y leftovers still unpublished on Print=Y — unmatched, not $0.
    ftc_2021 = [
        row
        for row in records
        if row.ticker == "FTC"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    ]
    assert ftc_2021 == []


def test_t_rowe_2023_etf_bond_table_leftover() -> None:
    records = TRowePriceSource().fetch(mode="fixture").records
    tagg_2023 = next(
        row
        for row in records
        if row.ticker == "TAGG"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert tagg_2023.amount == Decimal("0.1504")
    assert str(tagg_2023.ex_date) == "2023-12-22"
    assert tagg_2023.publication_stage == PublicationStage.final

    tbux_2023 = next(
        row
        for row in records
        if row.ticker == "TBUX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert tbux_2023.amount == Decimal("0.2257")

    tagg_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "TAGG"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= tagg_years
    # PREFX 2025 official YE row is all em-dash — unmatched, not $0.
    prefx_2025 = [
        row
        for row in records
        if row.ticker == "PREFX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    ]
    assert prefx_2025 == []


def test_first_eagle_class_a_product_page_history_fills_missing_years() -> None:
    records = FirstEagleSource().fetch(mode="fixture").records
    sgenx_2022 = next(
        row
        for row in records
        if row.ticker == "SGENX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert sgenx_2022.amount == Decimal("2.358")
    assert str(sgenx_2022.ex_date) == "2022-12-01"
    assert sgenx_2022.publication_stage == PublicationStage.final

    sgovx_2022_oi = next(
        row
        for row in records
        if row.ticker == "SGOVX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount is not None
    )
    assert sgovx_2022_oi.amount == Decimal("0.018")

    fefax_2023 = next(
        row
        for row in records
        if row.ticker == "FEFAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert fefax_2023.amount == Decimal("1.661")

    sgenx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "SGENX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= sgenx_years
    # Leftover C / I / R6 history is class-level — not copied from Class A.
    sgiix_2021 = next(
        row
        for row in records
        if row.ticker == "SGIIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert sgiix_2021.amount == Decimal("1.409")
    fegrx_2021 = next(
        row
        for row in records
        if row.ticker == "FEGRX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert fegrx_2021.amount == Decimal("1.458")
    assert sgiix_2021.amount != fegrx_2021.amount


def test_northern_trust_2023_ici_fills_cg_dash_equity() -> None:
    records = NorthernTrustSource().fetch(mode="fixture").records
    nsrix_2023 = next(
        row
        for row in records
        if row.ticker == "NSRIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert nsrix_2023.amount == Decimal("0.320700")
    assert str(nsrix_2023.ex_date) == "2023-12-21"
    assert nsrix_2023.publication_stage == PublicationStage.final

    nueix_2023 = next(
        row
        for row in records
        if row.ticker == "NUEIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert nueix_2023.amount == Decimal("0.055796")

    nsrix_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "NSRIX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= nsrix_years


def test_thrivent_paid_2021_2023_fills_in_book_class_s() -> None:
    records = ThriventSource().fetch(mode="fixture").records
    taaix_2023 = next(
        row
        for row in records
        if row.ticker == "TAAIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and (row.ex_date or row.payable_date)
        and (row.ex_date or row.payable_date).year == 2023
        and row.amount
    )
    assert taaix_2023.amount == Decimal("0.41584")
    assert taaix_2023.publication_stage == PublicationStage.final

    iilgx_2022 = next(
        row
        for row in records
        if row.ticker == "IILGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and (row.ex_date or row.payable_date)
        and (row.ex_date or row.payable_date).year == 2022
        and row.amount
    )
    assert iilgx_2022.amount == Decimal("0.50226")

    tmsix_2021 = next(
        row
        for row in records
        if row.ticker == "TMSIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and (row.ex_date or row.payable_date)
        and (row.ex_date or row.payable_date).year == 2021
        and row.amount == Decimal("3.30254")
    )
    assert tmsix_2021.publication_stage == PublicationStage.final

    taaix_years = {
        (row.ex_date or row.payable_date).year
        for row in records
        if row.ticker == "TAAIX"
        and (row.ex_date or row.payable_date)
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= taaix_years
    # Official 2023 paid table did not list Mid Cap Value — unmatched, not $0.
    tmcvx_2023 = [
        row
        for row in records
        if row.ticker == "TMCVX"
        and (row.ex_date or row.payable_date)
        and (row.ex_date or row.payable_date).year == 2023
        and row.amount
    ]
    assert tmcvx_2023 == []


def test_amg_product_page_history_fills_yackx() -> None:
    records = AmgSource().fetch(mode="fixture").records
    yackx_2022_oi = next(
        row
        for row in records
        if row.ticker == "YACKX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert yackx_2022_oi.amount == Decimal("0.3301")
    assert str(yackx_2022_oi.ex_date) == "2022-12-15"
    assert yackx_2022_oi.publication_stage == PublicationStage.final

    yackx_2022_lt = next(
        row
        for row in records
        if row.ticker == "YACKX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert yackx_2022_lt.amount == Decimal("1.2226")

    aridx_2022_lt = next(
        row
        for row in records
        if row.ticker == "ARIDX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert aridx_2022_lt.amount > 0

    yackx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "YACKX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= yackx_years
    # Family 2022 PDF 403 leftover: Systematica / GWSZX unpublished years stay unmatched.
    gwszx_2022 = [
        row
        for row in records
        if row.ticker == "GWSZX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    ]
    assert gwszx_2022 == []


def test_william_blair_official_2021_2024_is_class_level() -> None:
    records = WilliamBlairSource().fetch(mode="fixture").records
    bgfix_2021 = next(
        row
        for row in records
        if row.ticker == "BGFIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert bgfix_2021.amount == Decimal("1.41651")
    assert bgfix_2021.publication_stage == PublicationStage.final
    bgfix_2022 = next(
        row
        for row in records
        if row.ticker == "BGFIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert bgfix_2022.amount == Decimal("0.36515")
    bgfix_2023 = next(
        row
        for row in records
        if row.ticker == "BGFIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert bgfix_2023.amount == Decimal("1.23527")

    # Class N / I / R6 income is class-level — never copy Class I onto R6.
    wilnx_2021 = next(
        row
        for row in records
        if row.ticker == "WILNX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    wilix_2021 = next(
        row
        for row in records
        if row.ticker == "WILIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    wiljx_2021 = next(
        row
        for row in records
        if row.ticker == "WILJX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert wilnx_2021.amount == Decimal("0.00104")
    assert wilix_2021.amount == Decimal("0.04526")
    assert wiljx_2021.amount == Decimal("0.05583")
    assert wilnx_2021.amount != wilix_2021.amount != wiljx_2021.amount

    bgfix_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "BGFIX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= bgfix_years


def test_royce_official_2021_2023_is_class_level() -> None:
    records = RoyceSource().fetch(mode="fixture").records
    rytrx_2021_oi = next(
        row
        for row in records
        if row.ticker == "RYTRX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert rytrx_2021_oi.amount == Decimal("0.0299")
    rytrx_2021_st = next(
        row
        for row in records
        if row.ticker == "RYTRX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert rytrx_2021_st.amount == Decimal("0.5162")
    rytrx_2021_lt = next(
        row
        for row in records
        if row.ticker == "RYTRX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert rytrx_2021_lt.amount == Decimal("2.2441")
    assert rytrx_2021_lt.publication_stage == PublicationStage.final

    ryotx_2021_lt = next(
        row
        for row in records
        if row.ticker == "RYOTX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert ryotx_2021_lt.amount == Decimal("2.7273")

    rytrx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "RYTRX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= rytrx_years


def test_artisan_official_ici_2021_2023() -> None:
    records = ArtisanSource().fetch(mode="fixture").records
    artix_2021 = next(
        row
        for row in records
        if row.ticker == "ARTIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and (row.ex_date or row.as_of)
        and (row.ex_date or row.as_of).year == 2021
        and row.amount
    )
    assert artix_2021.amount == Decimal("5.498")
    assert artix_2021.publication_stage == PublicationStage.final
    artix_2022 = next(
        row
        for row in records
        if row.ticker == "ARTIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and (row.ex_date or row.as_of)
        and (row.ex_date or row.as_of).year == 2022
        and row.amount
    )
    assert artix_2022.amount == Decimal("0.306132")
    artix_2023 = next(
        row
        for row in records
        if row.ticker == "ARTIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and (row.ex_date or row.as_of)
        and (row.ex_date or row.as_of).year == 2023
        and row.amount
    )
    assert artix_2023.amount == Decimal("0.20663")

    artix_years = {
        (row.ex_date or row.as_of).year
        for row in records
        if row.ticker == "ARTIX"
        and (row.ex_date or row.as_of)
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= artix_years
    # All-zero official ICI rows stay unmatched — never stored as invented $0.
    artjx_2022 = [
        row
        for row in records
        if row.ticker == "ARTJX"
        and (row.ex_date or row.as_of)
        and (row.ex_date or row.as_of).year == 2022
        and row.amount
    ]
    assert artjx_2022 == []


def test_first_eagle_leftover_share_class_history_is_class_level() -> None:
    records = FirstEagleSource().fetch(mode="fixture").records
    sgiix_2022_oi = next(
        row
        for row in records
        if row.ticker == "SGIIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount is not None
    )
    assert sgiix_2022_oi.amount == Decimal("0.213")
    assert str(sgiix_2022_oi.ex_date) == "2022-12-01"
    assert sgiix_2022_oi.publication_stage == PublicationStage.final

    fesgx_2021_oi = next(
        row
        for row in records
        if row.ticker == "FESGX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert fesgx_2021_oi.amount == Decimal("0.588")

    sgoix_2025 = next(
        row
        for row in records
        if row.ticker == "SGOIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert sgoix_2025.amount == Decimal("1.717")

    sgiix_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "SGIIX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= sgiix_years
    # GRA / Smid issuer tables start 2022 — 2021 unmatched, not invented.
    ferax_2021 = [
        row
        for row in records
        if row.ticker == "FERAX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    ]
    assert ferax_2021 == []

    allspring = AllspringSource().fetch(mode="fixture").records
    scvnx_2023 = next(
        row
        for row in allspring
        if row.ticker == "SCVNX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert scvnx_2023.amount == Decimal("0.38479")
    assert str(scvnx_2023.ex_date) == "2023-12-22"
    wgbix_2023 = next(
        row
        for row in allspring
        if row.ticker == "WGBIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert wgbix_2023.amount == Decimal("0.07698")
    wscox_2021 = next(
        row
        for row in allspring
        if row.ticker == "WSCOX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert wscox_2021.amount == Decimal("0.08681")
    # WDSAX 2021 is unpublished on the issuer page — unmatched, not $0.
    wdsax_2021 = [
        row
        for row in allspring
        if row.ticker == "WDSAX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    ]
    assert wdsax_2021 == []


def test_wisdomtree_leftover_2023_monthly_income_fills_4y() -> None:
    records = WisdomtreeSource().fetch(mode="fixture").records
    des_2023 = next(
        row
        for row in records
        if row.ticker == "DES"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert des_2023.amount == Decimal("0.06000")
    assert str(des_2023.ex_date) == "2023-11-24"
    aggy_2023 = next(
        row
        for row in records
        if row.ticker == "AGGY"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert aggy_2023.amount == Decimal("0.15000")
    gtr_2023 = next(
        row
        for row in records
        if row.ticker == "GTR"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert gtr_2023.amount == Decimal("0.30000")
    assert str(gtr_2023.ex_date) == "2023-09-25"
    # December 2023 sibling still 404; unpublished leftover names omitted.
    cew_2023 = [
        row
        for row in records
        if row.ticker == "CEW"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.estimate_type == EstimateType.ordinary_income
        and row.amount
    ]
    assert cew_2023 == []


def test_principal_leftover_wayback_2021_2022_fills_3y() -> None:
    records = PrincipalSource().fetch(mode="fixture").records
    pqiax_2022 = next(
        row
        for row in records
        if row.ticker == "PQIAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert pqiax_2022.amount == Decimal("1.3028")
    assert str(pqiax_2022.ex_date) == "2022-12-13"
    pqiax_2021_st = next(
        row
        for row in records
        if row.ticker == "PQIAX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert pqiax_2021_st.amount == Decimal("0.3043")
    pemgx_2022 = next(
        row
        for row in records
        if row.ticker == "PEMGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert pemgx_2022.amount == Decimal("0.9922")
    plgix_2022 = next(
        row
        for row in records
        if row.ticker == "PLGIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert plgix_2022.amount == Decimal("1.5188")
    pcbix_2021_st = next(
        row
        for row in records
        if row.ticker == "PCBIX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert pcbix_2021_st.amount == Decimal("0.1221")
    pinix_2023 = next(
        row
        for row in records
        if row.ticker == "PINIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert pinix_2023.amount == Decimal("0.3959")
    pqiax_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "PQIAX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= pqiax_years
    # Blue Chip leftover still has no issuer 2023 YE — unmatched, not $0.
    pblcx_2023 = [
        row
        for row in records
        if row.ticker == "PBLCX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    ]
    assert pblcx_2023 == []


def test_oakmark_leftover_wayback_2021_2023_fills_investor_5y() -> None:
    records = OakmarkSource().fetch(mode="fixture").records
    oakmx_2021_lt = next(
        row
        for row in records
        if row.ticker == "OAKMX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert oakmx_2021_lt.amount == Decimal("0.7462")
    assert str(oakmx_2021_lt.ex_date) == "2021-12-16"
    oakex_2022_lt = next(
        row
        for row in records
        if row.ticker == "OAKEX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert oakex_2022_lt.amount == Decimal("0.0917")
    oakgx_2023_lt = next(
        row
        for row in records
        if row.ticker == "OAKGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert oakgx_2023_lt.amount == Decimal("0.8688")
    oaklx_2024 = next(
        row
        for row in records
        if row.ticker == "OAKLX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert oaklx_2024.amount == Decimal("0.2462")
    # Class-level — Advisor income is not copied from Investor.
    oaymx_2021 = next(
        row
        for row in records
        if row.ticker == "OAYMX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert oaymx_2021.amount == Decimal("0.8359")
    oakmx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "OAKMX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= oakmx_years
    # Bond Investor has no 2021 or 2023 issuer YE — unmatched, not $0.
    oakcx_2023 = [
        row
        for row in records
        if row.ticker == "OAKCX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount is not None
    ]
    assert oakcx_2023 == []


def test_oakmark_leftover_2024_class_level_fills_5y() -> None:
    records = OakmarkSource().fetch(mode="fixture").records
    oaymx_2024 = next(
        row
        for row in records
        if row.ticker == "OAYMX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-12"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert oaymx_2024.amount == Decimal("1.9817")
    oanmx_2024 = next(
        row
        for row in records
        if row.ticker == "OANMX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-12"
        and row.amount
    )
    assert oanmx_2024.amount == Decimal("2.0405")
    oazmx_2024 = next(
        row
        for row in records
        if row.ticker == "OAZMX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-12"
        and row.amount
    )
    assert oazmx_2024.amount == Decimal("2.1015")
    oayex_2024_lt = next(
        row
        for row in records
        if row.ticker == "OAYEX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert oayex_2024_lt.amount == Decimal("0.7241")
    oakbx_2024 = next(
        row
        for row in records
        if row.ticker == "OAKBX"
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount is not None
    )
    assert oakbx_2024.amount == Decimal("0.0000")
    # Class-level — Advisor income is not copied onto Investor.
    oakmx_2024 = next(
        row
        for row in records
        if row.ticker == "OAKMX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert oakmx_2024.amount == Decimal("1.6971")
    for ticker in ("OAYMX", "OANMX", "OAZMX", "OAYEX", "OAKBX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker
    oakcx_2021 = [
        row
        for row in records
        if row.ticker == "OAKCX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount is not None
    ]
    assert oakcx_2021 == []


def test_harding_loevner_leftover_amg_json_fills_5y() -> None:
    records = HardingLoevnerSource().fetch(mode="fixture").records
    hlmnx_2022 = next(
        row
        for row in records
        if row.ticker == "HLMNX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert hlmnx_2022.amount == Decimal("0.478847")
    assert str(hlmnx_2022.ex_date) == "2022-12-13"
    hlmnx_2021_lt = next(
        row
        for row in records
        if row.ticker == "HLMNX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert hlmnx_2021_lt.amount == Decimal("0.321926")
    hlmnx_2024_st = next(
        row
        for row in records
        if row.ticker == "HLMIX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert hlmnx_2024_st.amount == Decimal("0.207823")
    hlmex_2024_lt = next(
        row
        for row in records
        if row.ticker == "HLMEX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert hlmex_2024_lt.amount == Decimal("2.094041")
    hlmsx_2021_lt = next(
        row
        for row in records
        if row.ticker == "HLMSX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert hlmsx_2021_lt.amount == Decimal("0.605796")
    hlmnx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "HLMNX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= hlmnx_years
    # Global Equity leftover still has no issuer 2022 YE — unmatched, not $0.
    hlmgx_2022 = [
        row
        for row in records
        if row.ticker == "HLMGX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    ]
    assert hlmgx_2022 == []


def test_ishares_leftover_rename_2025_fills_4y() -> None:
    records = BlackRockSource().fetch(mode="fixture").records
    hyxu_2025 = next(
        row
        for row in records
        if row.ticker == "HYXU"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert hyxu_2025.amount == Decimal("1.895899")
    assert str(hyxu_2025.ex_date) == "2025-12-19"
    fill_2025 = next(
        row
        for row in records
        if row.ticker == "FILL"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert fill_2025.amount == Decimal("0.288052")
    # Stamped-PDF dashes are not stored as $0.
    shv_2021 = [
        row
        for row in records
        if row.ticker == "SHV"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.estimate_type == EstimateType.ordinary_income
        and row.amount == Decimal("0")
    ]
    assert shv_2021 == []
    hyxu_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "HYXU"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= hyxu_years


def test_blackrock_lifepath_leftover_2022_investor_a() -> None:
    records = BlackRockSource().fetch(mode="fixture").records
    lprax_2022 = next(
        row
        for row in records
        if row.ticker == "LPRAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount is not None
    )
    assert lprax_2022.amount == Decimal("0.000000")
    assert str(lprax_2022.ex_date) == "2022-07-14"
    lpjax_2022 = next(
        row
        for row in records
        if row.ticker == "LPJAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert lpjax_2022.amount == Decimal("0.018889")
    lphax_2022 = next(
        row
        for row in records
        if row.ticker == "LPHAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert lphax_2022.amount == Decimal("0.052130")
    lprax_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "LPRAX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= lprax_years


def test_principal_leftover_2y_wayback_fills_5y() -> None:
    records = PrincipalSource().fetch(mode="fixture").records
    paltx_2023 = next(
        row
        for row in records
        if row.ticker == "PALTX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert paltx_2023.amount == Decimal("0.2506")
    assert str(paltx_2023.ex_date) == "2023-12-29"
    paltx_2021_lt = next(
        row
        for row in records
        if row.ticker == "PALTX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert paltx_2021_lt.amount == Decimal("0.5565")
    pgbhx_2023 = next(
        row
        for row in records
        if row.ticker == "PGBHX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert pgbhx_2023.amount == Decimal("0.0121")
    # Do not copy R-6 2023 income onto leftover R-5 / R-3.
    pgbgx_2023 = [
        row
        for row in records
        if row.ticker == "PGBGX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    ]
    assert pgbgx_2023 == []
    paltx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "PALTX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= paltx_years


def test_schwab_fnda_2025_wayback_fills_5y() -> None:
    records = SchwabSource().fetch(mode="fixture").records
    fnda_2025 = next(
        row
        for row in records
        if row.ticker == "FNDA"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert fnda_2025.amount == Decimal("0.1521")
    assert str(fnda_2025.ex_date) == "2025-12-10"
    fnda_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "FNDA"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= fnda_years


def test_janus_leftover_emerging_markets_2025_july_ici() -> None:
    records = JanusHendersonSource().fetch(mode="fixture").records
    hemax_2025 = next(
        row
        for row in records
        if row.ticker == "HEMAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert hemax_2025.amount == Decimal("0.00131188")
    assert str(hemax_2025.ex_date) == "2025-07-28"
    hemix_2025 = next(
        row
        for row in records
        if row.ticker == "HEMIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert hemix_2025.amount == Decimal("0.04811006")
    hemsx_2025 = [
        row
        for row in records
        if row.ticker == "HEMSX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.estimate_type == EstimateType.ordinary_income
        and row.amount
    ]
    assert hemsx_2025 == []
    hemax_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "HEMAX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= hemax_years


def test_vaneck_leftover_cm_commodity_2025() -> None:
    records = VaneckSource().fetch(mode="fixture").records
    cmcax_2025 = {
        (str(row.amount), str(row.ex_date))
        for row in records
        if row.ticker == "CMCAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    }
    assert ("1.0825", "2025-12-29") in cmcax_2025
    assert ("5.2074", "2025-12-23") in cmcax_2025
    cmcax_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "CMCAX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= cmcax_years
    ghacx_2025 = [
        row
        for row in records
        if row.ticker == "GHACX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    ]
    assert ghacx_2025 == []


def test_wisdomtree_leftover_3y_2023_monthly_income() -> None:
    records = WisdomtreeSource().fetch(mode="fixture").records
    aivi_2023 = next(
        row
        for row in records
        if row.ticker == "AIVI"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert aivi_2023.amount == Decimal("0.35000")
    assert str(aivi_2023.ex_date) == "2023-09-25"
    wtv_2023 = next(
        row
        for row in records
        if row.ticker == "WTV"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert wtv_2023.amount == Decimal("0.26000")
    qgrw_2023 = [
        row
        for row in records
        if row.ticker == "QGRW"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.estimate_type == EstimateType.ordinary_income
        and row.amount
    ]
    assert qgrw_2023 == []


def test_victory_leftover_2024_share_classes() -> None:
    records = VictorySource().fetch(mode="fixture").records
    vevix_2024 = next(
        row
        for row in records
        if row.ticker == "VEVIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert vevix_2024.amount == Decimal("4.150428")
    assert str(vevix_2024.ex_date) == "2024-12-13"
    vevix_oi = next(
        row
        for row in records
        if row.ticker == "VEVIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount is not None
    )
    assert vevix_oi.amount == Decimal("0.187299")
    vsoix_2024 = next(
        row
        for row in records
        if row.ticker == "VSOIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert vsoix_2024.amount == Decimal("0.408506")
    mmecx_oi = next(
        row
        for row in records
        if row.ticker == "MMECX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount is not None
    )
    assert mmecx_oi.amount == Decimal("0.000000")


def test_nuveen_leftover_product_page_paid_history_fills_institutional_5y() -> None:
    records = NuveenSource().fetch(mode="fixture").records
    teihx_2021_lt = next(
        row
        for row in records
        if row.ticker == "TEIHX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert teihx_2021_lt.amount == Decimal("0.1899")
    assert str(teihx_2021_lt.ex_date) == "2021-12-10"
    assert teihx_2021_lt.publication_stage == PublicationStage.final

    tichx_2021_st = next(
        row
        for row in records
        if row.ticker == "TICHX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert tichx_2021_st.amount == Decimal("0.5315")

    tsohx_2025_oi = next(
        row
        for row in records
        if row.ticker == "TSOHX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert tsohx_2025_oi.amount == Decimal("0.6886")
    assert str(tsohx_2025_oi.ex_date) == "2025-12-12"

    nsbrx_2025_lt = next(
        row
        for row in records
        if row.ticker == "NSBRX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert nsbrx_2025_lt.amount == Decimal("4.9421")
    assert str(nsbrx_2025_lt.ex_date) == "2025-12-15"

    teihx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "TEIHX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= teihx_years
    tichx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "TICHX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= tichx_years
    tsohx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "TSOHX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= tsohx_years
    nsbrx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "NSBRX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2022, 2023, 2024, 2025} <= nsbrx_years
    assert 2021 not in nsbrx_years

    # Class-level — Institutional / Class I amounts are not copied onto Retail / A.
    tinrx_2021 = [
        row
        for row in records
        if row.ticker == "TINRX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert tinrx_2021 == []
    nsbax_2024 = [
        row
        for row in records
        if row.ticker == "NSBAX"
        and row.ex_date
        and row.ex_date.year == 2024
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert nsbax_2024 == []


def test_northern_trust_2022_ici_fills_cg_dash_leftover() -> None:
    records = NorthernTrustSource().fetch(mode="fixture").records
    nmiex_2022 = next(
        row
        for row in records
        if row.ticker == "NMIEX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert nmiex_2022.amount == Decimal("0.157603")
    assert str(nmiex_2022.ex_date) == "2022-12-15"
    assert str(nmiex_2022.payable_date) == "2022-12-15"
    assert nmiex_2022.publication_stage == PublicationStage.final

    nmmex_2022 = next(
        row
        for row in records
        if row.ticker == "NMMEX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert nmmex_2022.amount == Decimal("0.113257")

    nmiex_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "NMIEX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= nmiex_years

    # December 2022 ICI dash / CG-in-total rows stay unmatched.
    ngrex_2022 = [
        row
        for row in records
        if row.ticker == "NGREX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount is not None
    ]
    assert ngrex_2022 == []


def test_parallel_g_ishares_spdr_blackrock_leftover_fills() -> None:
    records = BlackRockSource().fetch(mode="fixture").records
    ibhf_2021 = next(
        row
        for row in records
        if row.ticker == "IBHF"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert ibhf_2021.amount == Decimal("0.090837")
    assert str(ibhf_2021.ex_date) == "2021-12-16"
    assert ibhf_2021.publication_stage == PublicationStage.final
    ibhf_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "IBHF"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= ibhf_years

    birax_2021 = next(
        row
        for row in records
        if row.ticker == "BIRAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert birax_2021.amount == Decimal("0.242429")
    assert str(birax_2021.ex_date) == "2021-12-07"
    mdlox_2022 = next(
        row
        for row in records
        if row.ticker == "MDLOX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert mdlox_2022.amount == Decimal("0.499590")
    assert str(mdlox_2022.ex_date) == "2022-07-14"
    for ticker in ("BIRAX", "MDLOX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker

    iwfh_2024 = next(
        row
        for row in records
        if row.ticker == "IWFH"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert iwfh_2024.amount == Decimal("0.007857")
    # Cash-liquidation-only 2025 rows stay unmatched — not stored as income.
    ccrv_2025 = [
        row
        for row in records
        if row.ticker == "CCRV"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount == Decimal("20.002294")
    ]
    assert ccrv_2025 == []
    hewg_2025 = [
        row
        for row in records
        if row.ticker == "HEWG"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount is not None
    ]
    assert hewg_2025 == []
    # Parallel G left BACAX 2025 unpublished on the live year page; WAVE Y
    # fills it from the official stamped 2025 book (see test_parallel_y).

    ssga = StateStreetSource().fetch(mode="fixture").records
    nzac_2022 = next(
        row
        for row in ssga
        if row.ticker == "NZAC"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and str(row.ex_date) == "2022-12-01"
        and row.amount
    )
    assert nzac_2022.amount == Decimal("0.214724")
    nzac_2023 = next(
        row
        for row in ssga
        if row.ticker == "NZAC"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-12-01"
        and row.amount
    )
    assert nzac_2023.amount == Decimal("0.229707")
    nzac_years = {
        row.ex_date.year
        for row in ssga
        if row.ticker == "NZAC"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= nzac_years
    hybl_2021 = [
        row
        for row in ssga
        if row.ticker == "HYBL"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount is not None
    ]
    assert hybl_2021 == []

    schwab = SchwabSource().fetch(mode="fixture").records
    swbgx_early = [
        row
        for row in schwab
        if row.ticker == "SWBGX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert swbgx_early == []


def test_parallel_c_leftover_walls_stay_unmatched() -> None:
    dfa = DimensionalSource().fetch(mode="fixture").records
    disvx_early = [
        row
        for row in dfa
        if row.ticker == "DISVX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert disvx_early == []

    touchstone = TouchstoneSource().fetch(mode="fixture").records
    tegix_2023 = [
        row
        for row in touchstone
        if row.ticker == "TEGIX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount is not None
    ]
    assert tegix_2023 == []

    beacon = AmericanBeaconSource().fetch(mode="fixture").records
    sfmix_2023 = [
        row
        for row in beacon
        if row.ticker == "SFMIX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount is not None
    ]
    assert sfmix_2023 == []
    ssijx_2024 = [
        row
        for row in beacon
        if row.ticker == "SSIJX"
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount is not None
    ]
    assert ssijx_2024 == []
    spfyx_2025 = [
        row
        for row in beacon
        if row.ticker == "SPFYX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount is not None
    ]
    assert spfyx_2025 == []

    mfs = MfsSource().fetch(mode="fixture").records
    # Official-class Excel has no leftover year. Do not copy sibling-class
    # shareCode=R3|R4|I amounts onto BRSPX / BRWRX / MNWTX / DVRFX.
    brspx_2023 = [
        row
        for row in mfs
        if row.ticker == "BRSPX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount is not None
    ]
    assert brspx_2023 == []
    brwrx_2023 = [
        row
        for row in mfs
        if row.ticker == "BRWRX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount is not None
    ]
    assert brwrx_2023 == []
    mnwtx_2021 = [
        row
        for row in mfs
        if row.ticker == "MNWTX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount is not None
    ]
    assert mnwtx_2021 == []
    dvrfx_early = [
        row
        for row in mfs
        if row.ticker == "DVRFX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022}
        and row.amount is not None
    ]
    assert dvrfx_early == []


def test_janus_leftover_quarterly_midyear_ici_fills_5y() -> None:
    records = JanusHendersonSource().fetch(mode="fixture").records
    jabax_2025 = next(
        row
        for row in records
        if row.ticker == "JABAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount == Decimal("0.20720000")
    )
    assert str(jabax_2025.ex_date) == "2025-03-31"
    assert jabax_2025.publication_stage == PublicationStage.final

    hfqax_2025 = next(
        row
        for row in records
        if row.ticker == "HFQAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount == Decimal("0.09480000")
    )
    assert str(hfqax_2025.ex_date) == "2025-03-31"

    jerax_2025 = next(
        row
        for row in records
        if row.ticker == "JERAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount == Decimal("0.00450000")
    )
    assert str(jerax_2025.ex_date) == "2025-03-31"

    jagax_2024_st = next(
        row
        for row in records
        if row.ticker == "JAGAX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert jagax_2024_st.amount == Decimal("0.32559479")
    assert str(jagax_2024_st.ex_date) == "2024-06-10"
    jagax_2024_lt = next(
        row
        for row in records
        if row.ticker == "JAGAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert jagax_2024_lt.amount == Decimal("0.19461")

    for ticker in ("JABAX", "HFQAX", "JERAX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years

    jagax_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "JAGAX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2021, 2022, 2023, 2024} <= jagax_years
    assert 2025 not in jagax_years

    hfaax_2024 = [
        row
        for row in records
        if row.ticker == "HFAAX"
        and row.ex_date
        and row.ex_date.year == 2024
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert hfaax_2024 == []
    jeasx_2024 = [
        row
        for row in records
        if row.ticker == "JEASX"
        and row.ex_date
        and row.ex_date.year == 2024
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert jeasx_2024 == []


def test_lord_abbett_leftover_product_page_history_is_2y() -> None:
    records = LordAbbettSource().fetch(mode="fixture").records
    lagwx_2021_lt = next(
        row
        for row in records
        if row.ticker == "LAGWX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert lagwx_2021_lt.amount == Decimal("3.3406")
    assert str(lagwx_2021_lt.ex_date) == "2021-11-23"
    assert lagwx_2021_lt.publication_stage == PublicationStage.final

    lagwx_2024_oi = next(
        row
        for row in records
        if row.ticker == "LAGWX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert lagwx_2024_oi.amount == Decimal("0.00570")
    assert str(lagwx_2024_oi.ex_date) == "2024-11-26"

    lagwx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "LAGWX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2021, 2024} <= lagwx_years
    assert 2022 not in lagwx_years
    assert 2023 not in lagwx_years
    assert 2025 not in lagwx_years

    # Bond Debenture 2021 / Total Return 2024 Daily income stay AJAX-unpublished.
    for ticker, year in (("LBNDX", 2021), ("LTRAX", 2024)):
        paid = [
            row
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == year
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert paid == []


def test_janus_leftover_parallel_ab_daily_ici_fills_5y() -> None:
    records = JanusHendersonSource().fetch(mode="fixture").records
    jafix_2025 = next(
        row
        for row in records
        if row.ticker == "JAFIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-01-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert jafix_2025.amount == Decimal("0.03748179")
    jahyx_2025 = next(
        row
        for row in records
        if row.ticker == "JAHYX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-01-31"
        and row.amount
    )
    assert jahyx_2025.amount == Decimal("0.04181576")
    jmuix_2025 = next(
        row
        for row in records
        if row.ticker == "JMUIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-01-31"
        and row.amount
    )
    assert jmuix_2025.amount == Decimal("0.04791137")
    for ticker in ("JAFIX", "JAHYX", "JMUIX", "JASBX", "JUCAX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker
    # Col 14 dash / unpublished leftover years stay unmatched.
    hfaax_2024 = [
        row
        for row in records
        if row.ticker == "HFAAX"
        and row.ex_date
        and row.ex_date.year == 2024
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert hfaax_2024 == []
    jagax_2025 = [
        row
        for row in records
        if row.ticker == "JAGAX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount is not None
    ]
    assert jagax_2025 == []


def test_lord_abbett_leftover_parallel_ab_product_page_is_year_depth() -> None:
    records = LordAbbettSource().fetch(mode="fixture").records
    lbndx_2022 = next(
        row
        for row in records
        if row.ticker == "LBNDX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-07-28"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert lbndx_2022.amount == Decimal("0.0131")
    ltrax_2021 = next(
        row
        for row in records
        if row.ticker == "LTRAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-17"
        and row.amount
    )
    assert ltrax_2021.amount == Decimal("0.0629")
    lbndx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "LBNDX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert 2022 in lbndx_years
    assert 2021 not in lbndx_years
    assert 2023 not in lbndx_years
    assert 2024 not in lbndx_years
    ltrax_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "LTRAX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert 2021 in ltrax_years
    assert 2024 not in ltrax_years


def test_parallel_ab_leftover_walls_stay_unmatched() -> None:
    dodge = DodgeCoxSource().fetch(mode="fixture").records
    for ticker in ("DOXGX", "DOXBX", "DOXIX", "DOXFX", "DOXWX", "DOXLX"):
        paid_2021 = [
            row
            for row in dodge
            if row.ticker == ticker
            and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert paid_2021 == [], ticker

    artisan = ArtisanSource().fetch(mode="fixture").records
    for ticker, year in (
        ("APFDX", 2023),
        ("APDDX", 2023),
        ("ARTRX", 2022),
        ("APDRX", 2022),
        ("APHRX", 2022),
    ):
        paid = [
            row
            for row in artisan
            if row.ticker == ticker
            and (row.ex_date or row.as_of)
            and (row.ex_date or row.as_of).year == year
            and row.amount is not None
        ]
        assert paid == [], f"{ticker} {year}"


def test_parallel_h_leftover_walls_stay_unmatched() -> None:
    mfs = MfsSource().fetch(mode="fixture").records
    membx_2022 = [
        row
        for row in mfs
        if row.ticker == "MEMBX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount is not None
    ]
    assert membx_2022 == []
    brspx_2023 = [
        row
        for row in mfs
        if row.ticker == "BRSPX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount is not None
    ]
    assert brspx_2023 == []

    putnam = FranklinTempletonSource().fetch(mode="fixture").records
    pim_2024 = [
        row
        for row in putnam
        if row.ticker == "PIM"
        and row.ex_date
        and row.ex_date.year == 2024
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert pim_2024 == []


def test_t_rowe_tblyx_leftover_2021_2022_completes_5y() -> None:
    records = TRowePriceSource().fetch(mode="fixture").records
    tblyx_2021 = next(
        row
        for row in records
        if row.ticker == "TBLYX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert tblyx_2021.amount == Decimal("0.071")
    assert str(tblyx_2021.ex_date) == "2021-12-21"
    assert str(tblyx_2021.payable_date) == "2021-12-22"
    assert tblyx_2021.publication_stage == PublicationStage.final

    tblyx_2021_st = next(
        row
        for row in records
        if row.ticker == "TBLYX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert tblyx_2021_st.amount == Decimal("0.072")

    tblyx_2022 = next(
        row
        for row in records
        if row.ticker == "TBLYX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert tblyx_2022.amount == Decimal("0.1296")
    assert str(tblyx_2022.ex_date) == "2022-12-21"
    tblyx_2022_st = next(
        row
        for row in records
        if row.ticker == "TBLYX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert tblyx_2022_st.amount == Decimal("0.0369")
    tblyx_2022_lt = next(
        row
        for row in records
        if row.ticker == "TBLYX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert tblyx_2022_lt.amount == Decimal("0.0145")

    tblyx_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "TBLYX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    tblyx_years.discard(None)
    assert set(LOOKBACK_YEARS) <= tblyx_years

    # Class-level — Investor TBLYX is not copied from I-Class TBLHX amounts.
    tblhx_2021 = next(
        row
        for row in records
        if row.ticker == "TBLHX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert tblhx_2021.amount == Decimal("0.080")

    trlax_2023 = next(
        row
        for row in records
        if row.ticker == "TRLAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert trlax_2023.amount == Decimal("0.1199")
    assert str(trlax_2023.ex_date) == "2023-12-28"
    trlax_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "TRLAX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    trlax_years.discard(None)
    assert {2022, 2023, 2024, 2025} <= trlax_years
    assert 2021 not in trlax_years


def test_parallel_f_leftover_walls_stay_unmatched() -> None:
    af = AmericanFundsSource().fetch(mode="fixture").records
    for ticker, year in (
        ("ANEFX", 2022),
        ("CNWCX", 2022),
        ("SMCWX", 2022),
        ("AAFXX", 2021),
        ("BFICX", 2023),
    ):
        rows = [
            row
            for row in af
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == year
            and row.amount is not None
        ]
        assert rows == [], f"{ticker} {year} should stay unmatched"

    invesco = InvescoSource().fetch(mode="fixture").records
    vafax_early = [
        row
        for row in invesco
        if row.ticker == "VAFAX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022}
        and row.amount is not None
    ]
    assert vafax_early == []

    trowe = TRowePriceSource().fetch(mode="fixture").records
    prgsx_2022 = [
        row
        for row in trowe
        if row.ticker == "PRGSX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount is not None
    ]
    assert prgsx_2022 == []
    prefx_2025 = [
        row
        for row in trowe
        if row.ticker == "PREFX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount is not None
    ]
    assert prefx_2025 == []
    prscx_2023 = [
        row
        for row in trowe
        if row.ticker == "PRSCX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount is not None
    ]
    assert prscx_2023 == []
    trptx_2024 = [
        row
        for row in trowe
        if row.ticker == "TRPTX"
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount is not None
    ]
    assert trptx_2024 == []


def test_parallel_k_allspring_leftover_income_completes_5y() -> None:
    records = AllspringSource().fetch(mode="fixture").records
    mbfix_2023 = next(
        row
        for row in records
        if row.ticker == "MBFIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert mbfix_2023.amount == Decimal("0.039850909")
    assert str(mbfix_2023.ex_date) == "2023-12-29"
    assert mbfix_2023.publication_stage == PublicationStage.final
    # Class-level — Institutional is not copied onto Class A / Class C.
    mbfax_2023 = next(
        row
        for row in records
        if row.ticker == "MBFAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert mbfax_2023.amount == Decimal("0.037858153")
    mbfcx_2023 = next(
        row
        for row in records
        if row.ticker == "MBFCX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert mbfcx_2023.amount == Decimal("0.030347834")

    sstvx_2022 = next(
        row
        for row in records
        if row.ticker == "SSTVX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2022-12-21"
        and row.amount
    )
    assert sstvx_2022.amount == Decimal("0.02809")
    whyix_2025 = next(
        row
        for row in records
        if row.ticker == "WHYIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert whyix_2025.amount == Decimal("0.038519989")
    wsiax_2024 = next(
        row
        for row in records
        if row.ticker == "WSIAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-20"
        and row.amount
    )
    assert wsiax_2024.amount == Decimal("0.06789")
    wicix_2022 = next(
        row
        for row in records
        if row.ticker == "WICIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2022-12-28"
        and row.amount
    )
    assert wicix_2022.amount == Decimal("0.12539")
    wcafx_2023 = next(
        row
        for row in records
        if row.ticker == "WCAFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-12-27"
        and row.amount
    )
    assert wcafx_2023.amount == Decimal("0.08252")

    for ticker in (
        "MBFIX",
        "MBFAX",
        "SSTVX",
        "SSHIX",
        "STYAX",
        "WIPIX",
        "WHYIX",
        "WHYMX",
        "WSIAX",
        "NMTFX",
        "WWTFX",
        "WCAFX",
        "WMBGX",
        "WICIX",
        "WICRX",
    ):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert set(LOOKBACK_YEARS) <= years, ticker

    # Year-depth only — 2021 unpublished on the issuer page.
    aspax_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "ASPAX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    aspax_years.discard(None)
    assert {2022, 2023, 2024, 2025} <= aspax_years
    assert 2021 not in aspax_years
    wrpix_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "WRPIX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    wrpix_years.discard(None)
    assert {2022, 2023, 2024, 2025} <= wrpix_years
    assert 2021 not in wrpix_years


def test_parallel_k_msim_eaton_vance_leftover_2024_etf() -> None:
    records = MorganStanleySource().fetch(mode="fixture").records
    cdei_2024 = next(
        row
        for row in records
        if row.ticker == "CDEI"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-23"
        and row.amount
    )
    assert cdei_2024.amount == Decimal("0.232960")
    assert str(cdei_2024.payable_date) == "2024-12-27"
    assert cdei_2024.publication_stage == PublicationStage.final
    cvie_2024 = next(
        row
        for row in records
        if row.ticker == "CVIE"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert cvie_2024.amount == Decimal("0.522115")
    evim_2024 = next(
        row
        for row in records
        if row.ticker == "EVIM"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert evim_2024.amount == Decimal("0.166867")
    evln_2024 = next(
        row
        for row in records
        if row.ticker == "EVLN"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert evln_2024.amount == Decimal("0.325864")
    # Existing CVLC 2024 row is kept (not overwritten / not sibling-copied).
    cvlc_2024 = next(
        row
        for row in records
        if row.ticker == "CVLC"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert cvlc_2024.amount == Decimal("0.222291")
    for ticker in ("CDEI", "CVIE", "CVSB", "EVIM", "EVLN", "EVSB", "PAPI", "PHEQ"):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert {2024, 2025} <= years, ticker
        assert 2021 not in years
        assert 2022 not in years
        assert 2023 not in years


def test_parallel_k_leftover_walls_stay_unmatched() -> None:
    allspring = AllspringSource().fetch(mode="fixture").records
    for ticker, year in (
        ("EAAFX", 2023),
        ("WDSAX", 2021),
        ("WFSTX", 2023),
        ("WFDAX", 2023),
        ("WEMAX", 2022),
        ("EKGAX", 2023),
        ("SENAX", 2022),
        ("WRPIX", 2021),
        ("ASPAX", 2021),
    ):
        rows = [
            row
            for row in allspring
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == year
            and row.amount is not None
        ]
        assert rows == [], f"{ticker} {year} should stay unmatched"

    msim = MorganStanleySource().fetch(mode="fixture").records
    for ticker in ("EVYM", "EVMO", "XAGG"):
        early = [
            row
            for row in msim
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year in {2021, 2022, 2023, 2024}
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert early == [], f"{ticker} 2021–2024 should stay unmatched"


def test_parallel_i_artisan_leftover_fills() -> None:
    records = ArtisanSource().fetch(mode="fixture").records
    apdix_2025_lt = next(
        row
        for row in records
        if row.ticker == "APDIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert apdix_2025_lt.amount == Decimal("5.017255")
    assert str(apdix_2025_lt.ex_date) == "2025-12-10"
    assert apdix_2025_lt.publication_stage == PublicationStage.final
    aphix_2025_oi = next(
        row
        for row in records
        if row.ticker == "APHIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount
    )
    assert aphix_2025_oi.amount == Decimal("0.673190")
    arthx_2022 = next(
        row
        for row in records
        if row.ticker == "ARTHX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert arthx_2022.amount == Decimal("0.143480")
    artzx_2021 = next(
        row
        for row in records
        if row.ticker == "ARTZX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert artzx_2021.amount == Decimal("0.200000")
    artjx_2022_zero = next(
        row
        for row in records
        if row.ticker == "ARTJX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount is not None
    )
    assert artjx_2022_zero.amount == Decimal("0")
    for ticker in ("APDIX", "APHIX", "ARTHX", "ARTJX", "ARTZX", "APDHX", "APDJX"):
        years = {
            (row.ex_date or row.as_of).year
            for row in records
            if row.ticker == ticker
            and (row.ex_date or row.as_of)
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_i_calamos_leftover_fills() -> None:
    records = CalamosSource().fetch(mode="fixture").records
    cvgrx_2025 = next(
        row
        for row in records
        if row.ticker == "CVGRX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert cvgrx_2025.amount == Decimal("4.17")
    assert str(cvgrx_2025.ex_date) == "2025-12-15"
    cplsx_2021 = next(
        row
        for row in records
        if row.ticker == "CPLSX"
        and row.as_of
        and row.as_of.year == 2021
        and row.amount is not None
    )
    assert cplsx_2021.amount == Decimal("0.0000")
    ccvix_2023 = next(
        row
        for row in records
        if row.ticker == "CCVIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    )
    assert ccvix_2023.amount == Decimal("0.22")
    ccef_2024 = next(
        row
        for row in records
        if row.ticker == "CCEF"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount
    )
    assert ccef_2024.amount == Decimal("0.09")
    for ticker in ("CVGRX", "CPLSX", "CCVIX", "CVTRX", "CAGCX"):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_i_victory_leftover_2022_rs() -> None:
    records = VictorySource().fetch(mode="fixture").records
    rsgrx_2022 = next(
        row
        for row in records
        if row.ticker == "RSGRX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert rsgrx_2022.amount == Decimal("0.397318")
    assert str(rsgrx_2022.ex_date) == "2022-12-14"
    gpafx_2022_oi = next(
        row
        for row in records
        if row.ticker == "GPAFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert gpafx_2022_oi.amount == Decimal("0.430758")
    rsgrx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "RSGRX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2022, 2023, 2024, 2025} <= rsgrx_years
    assert 2021 not in rsgrx_years


def test_parallel_i_leftover_walls_stay_unmatched() -> None:
    dodge = DodgeCoxSource().fetch(mode="fixture").records
    doxg_2021 = [
        row
        for row in dodge
        if row.ticker == "DOXGX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert doxg_2021 == []

    artisan = ArtisanSource().fetch(mode="fixture").records
    apdrx_2022 = [
        row
        for row in artisan
        if row.ticker == "APDRX"
        and (row.ex_date or row.as_of)
        and (row.ex_date or row.as_of).year == 2022
        and row.amount is not None
    ]
    assert apdrx_2022 == []

    victory = VictorySource().fetch(mode="fixture").records
    rsgrx_2021 = [
        row
        for row in victory
        if row.ticker == "RSGRX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount is not None
    ]
    assert rsgrx_2021 == []

    alger = AlgerSource().fetch(mode="fixture").records
    for year in (2021, 2023, 2024):
        chusx = [
            row
            for row in alger
            if row.ticker == "CHUSX"
            and row.ex_date
            and row.ex_date.year == year
            and row.amount is not None
        ]
        assert chusx == [], year

    calamos = CalamosSource().fetch(mode="fixture").records
    canq_early = [
        row
        for row in calamos
        if row.ticker == "CANQ"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.amount is not None
    ]
    assert canq_early == []
    caisx_2021 = [
        row
        for row in calamos
        if row.ticker == "CAISX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
        and row.amount is not None
    ]
    assert caisx_2021 == []
    cmrax_2022 = [
        row
        for row in calamos
        if row.ticker == "CMRAX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount is not None
    ]
    assert cmrax_2022 == []


def test_parallel_j_ab_leftover_class_a_paid_fills_5y() -> None:
    records = AllianceBernsteinSource().fetch(mode="fixture").records
    agrfx_2025_lt = next(
        row
        for row in records
        if row.ticker == "AGRFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-09"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert agrfx_2025_lt.amount == Decimal("16.5000")
    assert str(agrfx_2025_lt.payable_date) == "2025-12-11"
    agrfx_2025_st = next(
        row
        for row in records
        if row.ticker == "AGRFX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-09"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert agrfx_2025_st.amount == Decimal("0.6757")

    apgax_2021_lt = next(
        row
        for row in records
        if row.ticker == "APGAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-07"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert apgax_2021_lt.amount == Decimal("2.2996")

    abasx_2021_oi = next(
        row
        for row in records
        if row.ticker == "ABASX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2021-12-09"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert abasx_2021_oi.amount == Decimal("0.2155")
    abasx_2021_st = next(
        row
        for row in records
        if row.ticker == "ABASX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-09"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert abasx_2021_st.amount == Decimal("1.6382")

    for ticker in (
        "AGRFX",
        "APGAX",
        "ABASX",
        "ABVAX",
        "ADGAX",
        "ALTFX",
        "ASLAX",
        "AUIAX",
        "AUUAX",
        "AWAAX",
        "CABDX",
        "CABNX",
        "GCEAX",
        "SCAVX",
        "WPASX",
    ):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker

    chclx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "CHCLX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    # J leftover paid book is ex_date only (2021 + 2025). AD leftover
    # CHCLX 2022 is N-CSR FYE as_of year-depth — not an ex_date event.
    assert {2021, 2025} <= chclx_years
    assert 2022 not in chclx_years
    assert 2023 not in chclx_years
    assert 2024 not in chclx_years

    # Class-level — Advisor siblings are not copied from leftover Class A.
    agryx_2025 = [
        row
        for row in records
        if row.ticker == "AGRYX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert agryx_2025 == []


def test_parallel_j_leftover_walls_stay_unmatched() -> None:
    virtus = VirtusSource().fetch(mode="fixture").records
    merfx_early = [
        row
        for row in virtus
        if row.ticker == "MERFX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert merfx_early == []
    stvtx_early = [
        row
        for row in virtus
        if row.ticker == "STVTX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023}
        and row.amount is not None
    ]
    assert stvtx_early == []

    pioneer = AmundiSource().fetch(mode="fixture").records
    piodx_early = [
        row
        for row in pioneer
        if row.ticker == "PIODX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert piodx_early == []
    pcodx_2023 = [
        row
        for row in pioneer
        if row.ticker == "PCODX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert pcodx_2023 == []


def test_parallel_o_vaneck_leftover_fills() -> None:
    records = VaneckSource().fetch(mode="fixture").records
    einc_paid = {
        (row.estimate_type, str(row.amount), str(row.ex_date))
        for row in records
        if row.ticker == "EINC"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount
    }
    assert (
        EstimateType.ordinary_income,
        "0.390850",
        "2021-11-19",
    ) in einc_paid
    assert (
        EstimateType.ordinary_income,
        "0.125200",
        "2022-11-07",
    ) in einc_paid
    assert (
        EstimateType.ordinary_income,
        "0.378400",
        "2023-11-07",
    ) in einc_paid
    assert (
        EstimateType.ordinary_income,
        "0.664900",
        "2024-11-06",
    ) in einc_paid
    assert (
        EstimateType.long_term_capital_gains,
        "0.9843",
        "2025-12-29",
    ) in einc_paid

    lfeq_2023 = next(
        row
        for row in records
        if row.ticker == "LFEQ"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-12-29"
        and row.amount
    )
    assert lfeq_2023.amount == Decimal("0.625000")
    lfeq_2025 = next(
        row
        for row in records
        if row.ticker == "LFEQ"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-29"
        and row.amount
    )
    assert lfeq_2025.amount == Decimal("0.4900")

    raax_2023 = next(
        row
        for row in records
        if row.ticker == "RAAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-12-29"
        and row.amount
    )
    assert raax_2023.amount == Decimal("0.935700")
    raax_2025 = next(
        row
        for row in records
        if row.ticker == "RAAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-29"
        and row.amount
    )
    assert raax_2025.amount == Decimal("0.8163")

    for ticker in ("EINC", "LFEQ", "RAAX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker

    egpt_2024 = next(
        row
        for row in records
        if row.ticker == "EGPT"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-03-27"
        and row.amount
    )
    assert egpt_2024.amount == Decimal("0.031200")
    yumy_2024 = next(
        row
        for row in records
        if row.ticker == "YUMY"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-03-21"
        and row.amount
    )
    assert yumy_2024.amount == Decimal("0.050000")

    cloi_2025 = {
        (row.estimate_type, str(row.amount))
        for row in records
        if row.ticker == "CLOI"
        and row.ex_date
        and str(row.ex_date) == "2025-12-29"
        and row.amount
    }
    assert (EstimateType.ordinary_income, "0.2332") in cloi_2025
    assert (EstimateType.short_term_capital_gains, "0.0070") in cloi_2025
    assert (EstimateType.long_term_capital_gains, "0.0279") in cloi_2025
    clob_2025 = {
        (row.estimate_type, str(row.amount))
        for row in records
        if row.ticker == "CLOB"
        and row.ex_date
        and str(row.ex_date) == "2025-12-29"
        and row.amount
    }
    assert (EstimateType.ordinary_income, "0.2630") in clob_2025
    assert (EstimateType.short_term_capital_gains, "0.0641") in clob_2025
    cmci_2025 = next(
        row
        for row in records
        if row.ticker == "CMCI"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-30"
        and row.amount
    )
    assert cmci_2025.amount == Decimal("2.3700")


def test_parallel_o_wisdomtree_uniy_2023() -> None:
    records = WisdomtreeSource().fetch(mode="fixture").records
    uniy_2023 = next(
        row
        for row in records
        if row.ticker == "UNIY"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-11-24"
        and row.amount
    )
    assert uniy_2023.amount == Decimal("0.17700")
    assert str(uniy_2023.record_date) == "2023-11-27"
    assert str(uniy_2023.payable_date) == "2023-11-29"
    uniy_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "UNIY"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2023, 2024, 2025} <= uniy_years
    assert 2021 not in uniy_years
    assert 2022 not in uniy_years


def test_parallel_o_leftover_walls() -> None:
    first_trust = FirstTrustSource().fetch(mode="fixture").records
    for ticker, year in (
        ("FTC", 2021),
        ("ARVR", 2021),
        ("BGLD", 2021),
        ("EIPX", 2021),
        ("FNY", 2021),
        ("CRPT", 2023),
        ("FSGS", 2025),
        ("FBT", 2021),
        ("FBT", 2025),
    ):
        rows = [
            row
            for row in first_trust
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == year
            and row.amount is not None
        ]
        assert rows == [], f"{ticker} {year}"

    wisdomtree = WisdomtreeSource().fetch(mode="fixture").records
    aivi_2021 = [
        row
        for row in wisdomtree
        if row.ticker == "AIVI"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount is not None
    ]
    assert aivi_2021 == []
    cew_2023 = [
        row
        for row in wisdomtree
        if row.ticker == "CEW"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.estimate_type == EstimateType.ordinary_income
        and row.amount
    ]
    assert cew_2023 == []

    vaneck = VaneckSource().fetch(mode="fixture").records
    afk_2024 = [
        row
        for row in vaneck
        if row.ticker == "AFK"
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount is not None
    ]
    assert afk_2024 == []
    remx_2023 = [
        row
        for row in vaneck
        if row.ticker == "REMX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount is not None
    ]
    assert remx_2023 == []
    for ticker in ("GHACX", "MOTE"):
        rows = [
            row
            for row in vaneck
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == 2025
            and row.amount is not None
        ]
        assert rows == [], ticker

    slugs = {source.slug for source in list_sources()}
    assert "global_x" not in slugs
    assert "globalx" not in slugs
    families = {source.display_name.lower() for source in list_sources()}
    assert not any("global x" in name for name in families)


def test_parallel_o_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("vaneck", "wisdomtree", "first_trust"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("EINC", "LFEQ", "RAAX", "UNIY", "EGPT", "FBT", "AIVI", "GHACX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    einc = client.get(
        "/distributions",
        params={"ticker": "EINC", "publication_stage": "final", "page_size": 200},
    ).json()
    einc_2021 = [
        Decimal(row["amount"])
        for row in einc["items"]
        if row.get("ticker") == "EINC"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2021-11-19")
    ]
    assert Decimal("0.390850") in einc_2021
    einc_years = {
        str(row.get("ex_date") or "")[:4]
        for row in einc["items"]
        if row.get("ticker") == "EINC" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= einc_years

    uniy = client.get(
        "/distributions",
        params={"ticker": "UNIY", "publication_stage": "final", "page_size": 200},
    ).json()
    uniy_2023 = [
        Decimal(row["amount"])
        for row in uniy["items"]
        if row.get("ticker") == "UNIY"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2023-11-24")
    ]
    assert Decimal("0.17700") in uniy_2023

    fbt = client.get(
        "/distributions",
        params={"ticker": "FBT", "publication_stage": "final", "page_size": 200},
    ).json()
    fbt_2021 = [
        row
        for row in fbt["items"]
        if row.get("ticker") == "FBT"
        and str(row.get("ex_date") or "").startswith("2021")
        and row.get("amount") is not None
    ]
    assert fbt_2021 == []
    ghacx = client.get(
        "/distributions",
        params={"ticker": "GHACX", "publication_stage": "final", "page_size": 200},
    ).json()
    ghacx_2025 = [
        row
        for row in ghacx["items"]
        if row.get("ticker") == "GHACX"
        and str(row.get("ex_date") or "").startswith("2025")
        and row.get("amount") is not None
    ]
    assert ghacx_2025 == []

def test_parallel_m_guidestone_leftover_product_page_paid_fills_5y() -> None:
    records = GuidestoneSource().fetch(mode="fixture").records
    ggezx_2021_lt = next(
        row
        for row in records
        if row.ticker == "GGEZX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-10"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert ggezx_2021_lt.amount == Decimal("5.2420")
    assert str(ggezx_2021_lt.payable_date) == "2021-12-10"
    ggezx_2025_lt = next(
        row
        for row in records
        if row.ticker == "GGEZX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-05"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert ggezx_2025_lt.amount == Decimal("3.0748")

    gvezx_2021_lt = next(
        row
        for row in records
        if row.ticker == "GVEZX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-10"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gvezx_2021_lt.amount == Decimal("1.5788")
    gvezx_2021_st = next(
        row
        for row in records
        if row.ticker == "GVEZX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-10"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gvezx_2021_st.amount == Decimal("0.4999")

    gsczx_2021_lt = next(
        row
        for row in records
        if row.ticker == "GSCZX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-10"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gsczx_2021_lt.amount == Decimal("1.5220")
    gsczx_2021_st = next(
        row
        for row in records
        if row.ticker == "GSCZX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-10"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gsczx_2021_st.amount == Decimal("1.6391")
    gsczx_2025_lt = next(
        row
        for row in records
        if row.ticker == "GSCZX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-05"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gsczx_2025_lt.amount == Decimal("1.4388")

    for ticker in (
        "GGEZX",
        "GVEZX",
        "GSCZX",
        "GIEZX",
        "GEMZX",
        "GFSZX",
        "GMGZX",
        "GDMZX",
        "GEQZX",
        "GFIZX",
        "GGIZX",
        "GCOZX",
        "GGBZX",
        "GMTZX",
        "GMWZX",
        "GMHZX",
        "GMFZX",
    ):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert set(LOOKBACK_YEARS) <= years, ticker

    # Class-level — Institutional siblings are not copied from leftover Investor.
    for institutional in ("GGEYX", "GVEYX", "GSCYX"):
        copied = [row for row in records if row.ticker == institutional]
        assert copied == [], institutional


def test_parallel_m_aci_twcgx_leftover_paid_year_depth() -> None:
    records = AmericanCenturySource().fetch(mode="fixture").records
    twcgx_2023 = next(
        row
        for row in records
        if row.ticker == "TWCGX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2023-12-19"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert twcgx_2023.amount == Decimal("2.335")
    twcgx_2024 = next(
        row
        for row in records
        if row.ticker == "TWCGX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-17"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert twcgx_2024.amount == Decimal("3.4579")
    twcgx_ex_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "TWCGX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2023, 2024, 2025} <= twcgx_ex_years
    # Product-page calendar rows stay 2023–2025; 2021–2022 are N-CSR as_of.
    assert 2021 not in twcgx_ex_years
    assert 2022 not in twcgx_ex_years
    twcgx_ncsr_2021 = next(
        row
        for row in records
        if row.ticker == "TWCGX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert twcgx_ncsr_2021.amount == Decimal("1.56")
    twcgx_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "TWCGX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    twcgx_years.discard(None)
    assert set(LOOKBACK_YEARS) <= twcgx_years


def test_parallel_m_leftover_walls_stay_unmatched() -> None:
    guidestone = GuidestoneSource().fetch(mode="fixture").records
    for ticker in ("GMZXX", "GVIZX", "GEIZX", "GIIZX"):
        paid_2021 = [
            row
            for row in guidestone
            if row.ticker == ticker
            and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert paid_2021 == [], ticker

    jh = JohnHancockSource().fetch(mode="fixture").records
    for ticker in ("JVLAX", "TAGRX"):
        finals = [
            row
            for row in jh
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert finals == [], ticker

    thrivent = ThriventSource().fetch(mode="fixture").records
    tmcvx_2023 = [
        row
        for row in thrivent
        if row.ticker == "TMCVX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2023
        and row.amount is not None
    ]
    assert tmcvx_2023 == []
    tmaix_2022 = [
        row
        for row in thrivent
        if row.ticker == "TMAIX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2022
        and row.amount is not None
    ]
    assert tmaix_2022 == []


def test_parallel_n_federated_leftover_paid_fills_5y() -> None:
    records = FederatedHermesSource().fetch(mode="fixture").records
    klcax_2025_lt = next(
        row
        for row in records
        if row.ticker == "KLCAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-08"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert klcax_2025_lt.amount == Decimal("4.99671721")
    assert str(klcax_2025_lt.payable_date) == "2025-12-09"

    klcax_2021_lt = next(
        row
        for row in records
        if row.ticker == "KLCAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-06"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert klcax_2021_lt.amount == Decimal("5.11567676")

    pmiex_2025_lt = next(
        row
        for row in records
        if row.ticker == "PMIEX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-22"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert pmiex_2025_lt.amount == Decimal("16.47306553")

    qalgx_2025_lt = next(
        row
        for row in records
        if row.ticker == "QALGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-11"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert qalgx_2025_lt.amount == Decimal("1.32117791")

    kauax_2025_lt = next(
        row
        for row in records
        if row.ticker == "KAUAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-08"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert kauax_2025_lt.amount == Decimal("0.60489673")

    kauax_2021_lt = next(
        row
        for row in records
        if row.ticker == "KAUAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-06"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert kauax_2021_lt.amount == Decimal("0.65472526")

    for ticker in (
        "KLCAX",
        "PMIEX",
        "QALGX",
        "FDERX",
        "FGFAX",
        "FGFCX",
        "FGFLX",
        "FGSAX",
        "FGSCX",
        "FGSIX",
        "FHUMX",
        "FISPX",
        "FMCRX",
        "FMDCX",
        "FMSTX",
        "FMXKX",
        "FMXSX",
        "FSTKX",
        "FSTRX",
        "ISCAX",
        "ISCCX",
        "ISCIX",
        "KLCCX",
        "KLCIX",
        "LEICX",
        "LEIFX",
        "LEISX",
        "LFEIX",
        "MXCCX",
        "PIGDX",
        "PIUIX",
        "PIUXC",
        "QAACX",
        "QASCX",
        "QASGX",
        "QCACX",
        "QCLGX",
        "QCLVX",
        "QCSCX",
        "QCSGX",
        "QIACX",
        "QILGX",
        "QISCX",
        "QISGX",
    ):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker

    kauax_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "KAUAX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2021, 2023, 2024, 2025} <= kauax_years
    assert 2022 not in kauax_years

    # Class-level — leftover Class R6 is not copied from Class A QALGX.
    qrlgx_2025 = [
        row
        for row in records
        if row.ticker == "QRLGX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert qrlgx_2025 == []


def test_parallel_n_sei_leftover_2025_paid_fills() -> None:
    records = SeiSource().fetch(mode="fixture").records
    qalt_st = next(
        row
        for row in records
        if row.ticker == "QALT"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-17"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    qalt_lt = next(
        row
        for row in records
        if row.ticker == "QALT"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-17"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert qalt_st.amount == Decimal("0.248")
    assert qalt_lt.amount == Decimal("0.372")

    simt_st = next(
        row
        for row in records
        if row.fund_name == "SIMT Large Cap Growth"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-17"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    simt_lt = next(
        row
        for row in records
        if row.fund_name == "SIMT Large Cap Growth"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-17"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert simt_st.amount == Decimal("1.370")
    assert simt_lt.amount == Decimal("8.053")

    qalt_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "QALT"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert qalt_years == {2025}


def test_parallel_n_leftover_walls_stay_unmatched() -> None:
    federated = FederatedHermesSource().fetch(mode="fixture").records
    macquarie = MacquarieSource().fetch(mode="fixture").records
    sei = SeiSource().fetch(mode="fixture").records
    dws = DwsSource().fetch(mode="fixture").records
    alger = AlgerSource().fetch(mode="fixture").records
    ishares = BlackRockSource().fetch(mode="fixture").records

    kauax_2022 = [
        row
        for row in federated
        if row.ticker == "KAUAX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert kauax_2022 == []

    vsfax_paid = [
        row
        for row in federated
        if row.ticker == "VSFAX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert vsfax_paid == []
    vsfrx_paid = [
        row
        for row in federated
        if row.ticker == "VSFRX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert vsfrx_paid == []

    wstax_2021 = [
        row
        for row in macquarie
        if row.ticker == "WSTAX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
        and row.amount is not None
    ]
    assert wstax_2021 == []

    qalt_early = [
        row
        for row in sei
        if row.ticker == "QALT"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert qalt_early == []

    # Russell / FTSE leftovers belong to other slices — do not invent fills.
    # Parallel L fills leftover DWS 2024 ICI (DEEF / DEUS / QARP); 2021–2023
    # ICI siblings stay unmatched.
    deef_early = [
        row
        for row in dws
        if row.ticker == "DEEF"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert deef_early == []
    invn_early = [
        row
        for row in alger
        if row.ticker == "INVN"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.amount is not None
    ]
    assert invn_early == []
    iwmw_early = [
        row
        for row in ishares
        if row.ticker == "IWMW"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert iwmw_early == []


def test_parallel_l_bny_leftover_paid_fills_5y() -> None:
    records = BnyMellonSource().fetch(mode="fixture").records
    deqax_2025_lt = next(
        row
        for row in records
        if row.ticker == "DEQAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-16"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert deqax_2025_lt.amount == Decimal("1.3603")
    deqax_2025_oi = next(
        row
        for row in records
        if row.ticker == "DEQAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-16"
        and row.amount
    )
    assert deqax_2025_oi.amount == Decimal("0.0313")
    dwoax_2025_lt = next(
        row
        for row in records
        if row.ticker == "DWOAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-08"
        and row.amount
    )
    assert dwoax_2025_lt.amount == Decimal("2.0710")
    bklc_2025 = next(
        row
        for row in records
        if row.ticker == "BKLC"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-29"
        and row.amount
    )
    assert bklc_2025.amount == Decimal("0.3923")

    for ticker in (
        "DEQAX",
        "DQIAX",
        "DTCAX",
        "PESPX",
        "DBOAX",
        "DISAX",
        "DIEAX",
        "DLQAX",
        "PEOPX",
        "DWOAX",
        "BKLC",
        "BKCG",
        "BKAG",
        "BKEM",
        "BKHY",
        "BKIE",
        "BKMC",
        "BKSE",
        "BKUI",
    ):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_l_dws_leftover_2024_ici_is_year_depth() -> None:
    records = DwsSource().fetch(mode="fixture").records
    ashr_2024 = next(
        row
        for row in records
        if row.ticker == "ASHR"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-20"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert ashr_2024.amount == Decimal("0.299450000")
    dbef_2024 = next(
        row
        for row in records
        if row.ticker == "DBEF"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-20"
        and row.amount
    )
    assert dbef_2024.amount == Decimal("0.297060000")
    ashr_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "ASHR"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2024, 2025} <= ashr_years
    assert 2021 not in ashr_years
    assert 2022 not in ashr_years
    assert 2023 not in ashr_years


def test_parallel_l_royce_rdvix_november_2025_completes_5y() -> None:
    records = RoyceSource().fetch(mode="fixture").records
    rdvix_2025_lt = next(
        row
        for row in records
        if row.ticker == "RDVIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-11-21"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert rdvix_2025_lt.amount == Decimal("3.4237")
    rdvix_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "RDVIX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= rdvix_years
    rydvx_2025 = [
        row
        for row in records
        if row.ticker == "RYDVX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert rydvx_2025 == []


def test_parallel_l_leftover_walls_stay_unmatched() -> None:
    bny = BnyMellonSource().fetch(mode="fixture").records
    dtgrx_mid = [
        row
        for row in bny
        if row.ticker == "DTGRX"
        and row.ex_date
        and row.ex_date.year in {2022, 2023}
        and row.amount is not None
    ]
    assert dtgrx_mid == []
    bkci_2021 = [
        row
        for row in bny
        if row.ticker == "BKCI"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount is not None
    ]
    assert bkci_2021 == []
    bkdv_early = [
        row
        for row in bny
        if row.ticker == "BKDV"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023}
        and row.amount is not None
    ]
    assert bkdv_early == []

    brown = BrownAdvisorySource().fetch(mode="fixture").records
    baffx_paid = [
        row
        for row in brown
        if row.ticker == "BAFFX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert baffx_paid == []

    royce = RoyceSource().fetch(mode="fixture").records
    for ticker in ("RVPHX", "RVPIX", "RYVPX"):
        y2023 = [
            row
            for row in royce
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == 2023
            and row.amount is not None
        ]
        assert y2023 == [], ticker


def test_parallel_l_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("bny_mellon", "dws", "royce", "brown_advisory"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in (
        "DEQAX",
        "DWOAX",
        "BKLC",
        "RDVIX",
        "ASHR",
        "DTGRX",
        "BAFFX",
        "RVPHX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    deqax = client.get(
        "/distributions",
        params={"ticker": "DEQAX", "publication_stage": "final", "page_size": 200},
    ).json()
    deqax_2025 = [
        Decimal(row["amount"])
        for row in deqax["items"]
        if row.get("ticker") == "DEQAX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-16")
    ]
    assert Decimal("1.3603") in deqax_2025
    deqax_years = {
        str(row.get("ex_date") or "")[:4]
        for row in deqax["items"]
        if row.get("ticker") == "DEQAX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= deqax_years

    rdvix = client.get(
        "/distributions",
        params={"ticker": "RDVIX", "publication_stage": "final", "page_size": 200},
    ).json()
    rdvix_2025 = [
        Decimal(row["amount"])
        for row in rdvix["items"]
        if row.get("ticker") == "RDVIX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-11-21")
    ]
    assert Decimal("3.4237") in rdvix_2025

    baffx = client.get(
        "/distributions",
        params={"ticker": "BAFFX", "publication_stage": "final", "page_size": 200},
    ).json()
    baffx_paid = [
        row
        for row in baffx["items"]
        if row.get("ticker") == "BAFFX" and row.get("amount") is not None
    ]
    assert baffx_paid == []


def _paid_lookback_years(records: list[NormalizedRecord], ticker: str) -> set[int]:
    years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == ticker
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount is not None
    }
    years.discard(None)
    return years  # type: ignore[return-value]


def test_parallel_p_wasatch_leftover_fills_5y() -> None:
    records = WasatchSource().fetch(mode="fixture").records
    whosx_2025 = next(
        row
        for row in records
        if row.ticker == "WHOSX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.payable_date
        and str(row.payable_date) == "2025-12-18"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert whosx_2025.amount == Decimal("0.113996")
    wmcvx_2025 = next(
        row
        for row in records
        if row.ticker == "WMCVX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2025-12-18"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert wmcvx_2025.amount == Decimal("0.554075")
    wgrox_2021 = next(
        row
        for row in records
        if row.ticker == "WGROX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2021-12-16"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert wgrox_2021.amount == Decimal("14.455281")

    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, "WHOSX")
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, "WMCVX")
    assert _paid_lookback_years(records, "WGROX") == {2021, 2022, 2024, 2025}
    assert _paid_lookback_years(records, "WAIGX") == {2021, 2024, 2025}
    assert _paid_lookback_years(records, "WAAEX") == {2021, 2025}
    assert _paid_lookback_years(records, "WAIVX") == {2024, 2025}
    assert _paid_lookback_years(records, "FMIEX") == {2023, 2025}


def test_parallel_p_gabelli_leftover_2025_is_year_depth() -> None:
    records = GabelliSource().fetch(mode="fixture").records
    gicpx_2025 = next(
        row
        for row in records
        if row.ticker == "GICPX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-29"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gicpx_2025.amount == Decimal("7.2182")
    gabsx_2025 = next(
        row
        for row in records
        if row.ticker == "GABSX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.as_of
        and row.as_of.year == 2025
        and row.amount
    )
    assert gabsx_2025.amount == Decimal("1.65380")
    gabex_2025 = next(
        row
        for row in records
        if row.ticker == "GABEX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.as_of
        and row.as_of.year == 2025
        and row.amount
    )
    assert gabex_2025.amount == Decimal("0.60540")

    for ticker in ("GICPX", "GABSX", "GABEX", "GABGX", "GABAX", "GABBX"):
        years = _paid_lookback_years(records, ticker)
        assert {2024, 2025} <= years, ticker
    # WAVE AI later fills GABAX / GABBX / GICPX 2021–2023 and GABGX 2021+2023
    # from Dec 31 N-CSR. Equity Series GABSX / GABEX stay 2024–2025 only
    # (FYE September 30 is not calendar-safe).
    for ticker in ("GABSX", "GABEX"):
        years = _paid_lookback_years(records, ticker)
        assert 2021 not in years, ticker
        assert 2022 not in years, ticker
        assert 2023 not in years, ticker


def test_parallel_p_leftover_walls_stay_unmatched() -> None:
    wasatch = WasatchSource().fetch(mode="fixture").records
    for ticker in ("WAEMX", "WAGOX", "WAINX", "WAIOX", "WAMVX", "WAUSX"):
        assert _paid_lookback_years(wasatch, ticker) == set(), ticker
    wgrox_2023 = [
        row
        for row in wasatch
        if row.ticker == "WGROX"
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount is not None
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2023
    ]
    assert wgrox_2023 == []
    for ticker in ("WIGRX", "WIAEX", "WICVX", "WIINX", "WILCX"):
        paid = [
            row
            for row in wasatch
            if row.ticker == ticker
            and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
            and row.amount is not None
        ]
        assert paid == [], ticker

    gabelli = GabelliSource().fetch(mode="fixture").records
    for ticker in ("GABAXA", "GCASX", "GCIGX"):
        assert [row for row in gabelli if row.ticker == ticker] == []

    causeway = CausewaySource().fetch(mode="fixture").records
    for ticker in ("CCENX", "CCEVX"):
        years = _paid_lookback_years(causeway, ticker)
        assert years == {2021, 2022}, ticker
        assert 2023 not in years
        assert 2024 not in years
        assert 2025 not in years

    matthews = MatthewsAsiaSource().fetch(mode="fixture").records
    for ticker in (
        "MAPIX",
        "MAPTX",
        "MASGX",
        "MCHFX",
        "MCSMX",
        "MEGMX",
        "MINDX",
        "MSMLX",
    ):
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(matthews, ticker), ticker


def test_parallel_p_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("wasatch", "gabelli", "causeway", "matthews_asia"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in (
        "WHOSX",
        "WMCVX",
        "WGROX",
        "WAAEX",
        "WAIGX",
        "GICPX",
        "GABSX",
        "GABEX",
        "CCENX",
        "MAPTX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    whosx = client.get(
        "/distributions",
        params={"ticker": "WHOSX", "publication_stage": "final", "page_size": 200},
    ).json()
    whosx_2025 = [
        Decimal(row["amount"])
        for row in whosx["items"]
        if row.get("ticker") == "WHOSX"
        and row.get("estimate_type") == "ordinary_income"
        and (
            str(row.get("payable_date") or "").startswith("2025-12-18")
            or str(row.get("ex_date") or "").startswith("2025-12-18")
        )
    ]
    assert Decimal("0.113996") in whosx_2025
    whosx_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in whosx["items"]
        if row.get("ticker") == "WHOSX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= whosx_years

    gicpx = client.get(
        "/distributions",
        params={"ticker": "GICPX", "publication_stage": "final", "page_size": 200},
    ).json()
    gicpx_2025 = [
        Decimal(row["amount"])
        for row in gicpx["items"]
        if row.get("ticker") == "GICPX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-29")
    ]
    assert Decimal("7.2182") in gicpx_2025

    ccenx = client.get(
        "/distributions",
        params={"ticker": "CCENX", "publication_stage": "final", "page_size": 200},
    ).json()
    ccenx_late = [
        row
        for row in ccenx["items"]
        if row.get("ticker") == "CCENX"
        and row.get("amount") is not None
        and str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        in {"2023", "2024", "2025"}
    ]
    assert ccenx_late == []


def _paid_years(records, ticker: str) -> set[int]:
    years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == ticker
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    years.discard(None)
    return years


def test_parallel_s_ariel_leftover_paid_fills_5y() -> None:
    records = ArielSource().fetch(mode="fixture").records
    argfx_2024_lt = next(
        row
        for row in records
        if row.ticker == "ARGFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2024-12-18"
        and row.ex_date
        and str(row.ex_date) == "2024-12-18"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert argfx_2024_lt.amount == Decimal("3.868892")
    argfx_2024_oi = next(
        row
        for row in records
        if row.ticker == "ARGFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.payable_date
        and str(row.payable_date) == "2024-12-18"
        and row.amount is not None
    )
    assert argfx_2024_oi.amount == Decimal("0.087307")
    argfx_2024_st = next(
        row
        for row in records
        if row.ticker == "ARGFX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2024-12-18"
        and row.amount is not None
    )
    assert argfx_2024_st.amount == Decimal("0.014358")
    for ticker in ("ARGFX", "ARAIX"):
        assert set(LOOKBACK_YEARS) <= _paid_years(records, ticker), ticker
    # Class-level — other Ariel sleeves stay off the leftover page.
    assert [row for row in records if row.ticker == "AGLOX"] == []


def test_parallel_s_primecap_leftover_paid_fills_5y() -> None:
    records = PrimecapSource().fetch(mode="fixture").records
    poskx_2025_lt = next(
        row
        for row in records
        if row.ticker == "POSKX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-15"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert poskx_2025_lt.amount == Decimal("8.59624")
    poskx_2025_oi = next(
        row
        for row in records
        if row.ticker == "POSKX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-15"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert poskx_2025_oi.amount == Decimal("0.37869")
    poskx_2025_st = next(
        row
        for row in records
        if row.ticker == "POSKX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-15"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert poskx_2025_st.amount == Decimal("0.12608")
    for ticker in ("POSKX", "POGRX", "POAGX"):
        assert set(LOOKBACK_YEARS) <= _paid_years(records, ticker), ticker


def test_parallel_s_hotchkis_leftover_paid_fills_5y() -> None:
    records = HotchkisWileySource().fetch(mode="fixture").records
    hwlix_2024_lt = next(
        row
        for row in records
        if row.ticker == "HWLIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-05"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hwlix_2024_lt.amount == Decimal("3.90044000")
    hwlix_2024_oi = next(
        row
        for row in records
        if row.ticker == "HWLIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-05"
        and row.amount is not None
    )
    assert hwlix_2024_oi.amount == Decimal("0.70494537")
    hwlix_2024_st = next(
        row
        for row in records
        if row.ticker == "HWLIX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-05"
        and row.amount is not None
    )
    assert hwlix_2024_st.amount == Decimal("0.05551000")
    for ticker in ("HWLIX", "HWAIX", "HWNIX"):
        assert set(LOOKBACK_YEARS) <= _paid_years(records, ticker), ticker
    # Class-level — leftover Class I is not copied onto Class A.
    hwlaX = [
        row
        for row in records
        if row.ticker == "HWLAX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert hwlaX == []


def test_parallel_s_baird_leftover_paid_fills_and_walls() -> None:
    records = BairdSource().fetch(mode="fixture").records
    bmdix_2021_lt = next(
        row
        for row in records
        if row.ticker == "BMDIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-16"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert bmdix_2021_lt.amount == Decimal("4.39824")
    bmdix_2021_st = next(
        row
        for row in records
        if row.ticker == "BMDIX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-16"
        and row.amount is not None
    )
    assert bmdix_2021_st.amount == Decimal("0.42000")
    for ticker in ("BMDIX", "BMDSX"):
        assert set(LOOKBACK_YEARS) <= _paid_years(records, ticker), ticker

    bsvix_years = _paid_years(records, "BSVIX")
    bsvsx_years = _paid_years(records, "BSVSX")
    assert {2021, 2022, 2024, 2025} <= bsvix_years
    assert {2021, 2022, 2024, 2025} <= bsvsx_years
    assert 2023 not in bsvix_years
    assert 2023 not in bsvsx_years

    ccgix_years = _paid_years(records, "CCGIX")
    ccgsx_years = _paid_years(records, "CCGSX")
    assert {2022, 2024, 2025} <= ccgix_years
    assert {2022, 2024, 2025} <= ccgsx_years
    assert 2021 not in ccgix_years
    assert 2023 not in ccgix_years

    ccwix_years = _paid_years(records, "CCWIX")
    ccwsx_years = _paid_years(records, "CCWSX")
    assert {2022, 2025} <= ccwix_years
    assert {2022, 2025} <= ccwsx_years
    assert 2021 not in ccwix_years
    assert 2023 not in ccwix_years
    assert 2024 not in ccwix_years
    ccwix_2024 = [
        row
        for row in records
        if row.ticker == "CCWIX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2024
        and row.amount is not None
    ]
    assert ccwix_2024 == []
    # Bond / SMID sleeves stay off the leftover page.
    assert [row for row in records if row.ticker in {"BCOIX", "BSGIX"}] == []


def test_parallel_s_champlain_leftover_paid_fills_and_walls() -> None:
    records = ChamplainSource().fetch(mode="fixture").records
    cipix_2021_lt = next(
        row
        for row in records
        if row.ticker == "CIPIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-14"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert cipix_2021_lt.amount == Decimal("1.6369")
    cipix_2021_st = next(
        row
        for row in records
        if row.ticker == "CIPIX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-14"
        and row.amount is not None
    )
    assert cipix_2021_st.amount == Decimal("1.2176")
    for ticker in ("CIPIX", "CIPNX"):
        assert set(LOOKBACK_YEARS) <= _paid_years(records, ticker), ticker

    ciptx_years = _paid_years(records, "CIPTX")
    assert {2023, 2024, 2025} <= ciptx_years
    assert 2021 not in ciptx_years
    assert 2022 not in ciptx_years
    for year in (2021, 2022):
        empty = [
            row
            for row in records
            if row.ticker == "CIPTX"
            and _year_for_row(row.as_of, row.ex_date, row.payable_date) == year
            and row.amount is not None
        ]
        assert empty == [], year
    # Advisor / Emerging Markets not attached.
    assert [row for row in records if row.ticker in {"CIPMX", "CIPSX", "CIPDX"}] == []


def test_parallel_s_davis_leftover_paid_is_year_depth() -> None:
    records = DavisSource().fetch(mode="fixture").records
    nyvtx_2024_lt = next(
        row
        for row in records
        if row.ticker == "NYVTX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-13"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert nyvtx_2024_lt.amount == Decimal("3.00")
    nyvtx_2024_oi = next(
        row
        for row in records
        if row.ticker == "NYVTX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-13"
        and row.amount is not None
    )
    assert nyvtx_2024_oi.amount == Decimal("0.294")
    nyvtx_2024_st = next(
        row
        for row in records
        if row.ticker == "NYVTX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-13"
        and row.amount is not None
    )
    assert nyvtx_2024_st.amount == Decimal("0.0243")

    nyvtx_years = _paid_years(records, "NYVTX")
    rpeax_years = _paid_years(records, "RPEAX")
    dgfax_years = _paid_years(records, "DGFAX")
    assert {2022, 2023, 2024, 2025} <= nyvtx_years
    assert {2022, 2023, 2024, 2025} <= rpeax_years
    assert {2023, 2024, 2025} <= dgfax_years
    assert 2021 not in nyvtx_years
    assert 2021 not in rpeax_years
    assert 2021 not in dgfax_years
    assert 2022 not in dgfax_years
    dgfax_2022 = [
        row
        for row in records
        if row.ticker == "DGFAX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2022
        and row.amount is not None
    ]
    assert dgfax_2022 == []
    # Class-level — leftover Class A is not copied onto Class C / Y.
    assert [row for row in records if row.ticker in {"NYVCX", "NYVYX"}] == []


def test_parallel_s_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("ariel", "primecap", "hotchkis", "baird", "champlain", "davis"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in (
        "ARGFX",
        "POSKX",
        "HWLIX",
        "BMDIX",
        "CIPIX",
        "NYVTX",
        "DGFAX",
        "CIPTX",
        "CCWIX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    argfx = client.get(
        "/distributions",
        params={"ticker": "ARGFX", "publication_stage": "final", "page_size": 200},
    ).json()
    argfx_2024 = [
        Decimal(row["amount"])
        for row in argfx["items"]
        if row.get("ticker") == "ARGFX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("payable_date") or "").startswith("2024-12-18")
    ]
    assert Decimal("3.868892") in argfx_2024
    argfx_years = {
        str(row.get("payable_date") or row.get("ex_date") or "")[:4]
        for row in argfx["items"]
        if row.get("ticker") == "ARGFX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= argfx_years

    poskx = client.get(
        "/distributions",
        params={"ticker": "POSKX", "publication_stage": "final", "page_size": 200},
    ).json()
    poskx_2025 = [
        Decimal(row["amount"])
        for row in poskx["items"]
        if row.get("ticker") == "POSKX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-15")
    ]
    assert Decimal("8.59624") in poskx_2025

    hwlix = client.get(
        "/distributions",
        params={"ticker": "HWLIX", "publication_stage": "final", "page_size": 200},
    ).json()
    hwlix_2024 = [
        Decimal(row["amount"])
        for row in hwlix["items"]
        if row.get("ticker") == "HWLIX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2024-12-05")
    ]
    assert Decimal("3.90044000") in hwlix_2024

    bmdix = client.get(
        "/distributions",
        params={"ticker": "BMDIX", "publication_stage": "final", "page_size": 200},
    ).json()
    bmdix_2021 = [
        Decimal(row["amount"])
        for row in bmdix["items"]
        if row.get("ticker") == "BMDIX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2021-12-16")
    ]
    assert Decimal("4.39824") in bmdix_2021

    cipix = client.get(
        "/distributions",
        params={"ticker": "CIPIX", "publication_stage": "final", "page_size": 200},
    ).json()
    cipix_2021 = [
        Decimal(row["amount"])
        for row in cipix["items"]
        if row.get("ticker") == "CIPIX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2021-12-14")
    ]
    assert Decimal("1.6369") in cipix_2021

    nyvtx = client.get(
        "/distributions",
        params={"ticker": "NYVTX", "publication_stage": "final", "page_size": 200},
    ).json()
    nyvtx_2024 = [
        Decimal(row["amount"])
        for row in nyvtx["items"]
        if row.get("ticker") == "NYVTX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2024-12-13")
    ]
    assert Decimal("3.00") in nyvtx_2024

    dgfax = client.get(
        "/distributions",
        params={"ticker": "DGFAX", "publication_stage": "final", "page_size": 200},
    ).json()
    dgfax_2022 = [
        row
        for row in dgfax["items"]
        if row.get("ticker") == "DGFAX"
        and str(row.get("ex_date") or row.get("payable_date") or "").startswith("2022")
        and row.get("amount") is not None
    ]
    assert dgfax_2022 == []

    ciptx = client.get(
        "/distributions",
        params={"ticker": "CIPTX", "publication_stage": "final", "page_size": 200},
    ).json()
    ciptx_early = [
        row
        for row in ciptx["items"]
        if row.get("ticker") == "CIPTX"
        and str(row.get("ex_date") or "").startswith(("2021", "2022"))
        and row.get("amount") is not None
    ]
    assert ciptx_early == []

    ccwix = client.get(
        "/distributions",
        params={"ticker": "CCWIX", "publication_stage": "final", "page_size": 200},
    ).json()
    ccwix_2024 = [
        row
        for row in ccwix["items"]
        if row.get("ticker") == "CCWIX"
        and str(row.get("ex_date") or "").startswith("2024")
        and row.get("amount") is not None
    ]
    assert ccwix_2024 == []

def test_parallel_q_gmo_trust_leftover_paid_fills_5y() -> None:
    records = GmoSource().fetch(mode="fixture").records
    gqetx_2025_lt = next(
        row
        for row in records
        if row.ticker == "GQETX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-12"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gqetx_2025_lt.amount == Decimal("2.6256")
    gqetx_2025_st = next(
        row
        for row in records
        if row.ticker == "GQETX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-12"
        and row.amount
    )
    assert gqetx_2025_st.amount == Decimal("0.1466")
    gqetx_2025_oi = next(
        row
        for row in records
        if row.ticker == "GQETX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-12"
        and row.amount
    )
    assert gqetx_2025_oi.amount == Decimal("0.2832")

    gmuex_2025_lt = next(
        row
        for row in records
        if row.ticker == "GMUEX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-05"
        and row.amount
    )
    assert gmuex_2025_lt.amount == Decimal("0.9849")
    gmuex_2025_st = [
        row
        for row in records
        if row.ticker == "GMUEX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-05"
        and row.amount is not None
    ]
    assert gmuex_2025_st == []

    gtmix_2025_lt = next(
        row
        for row in records
        if row.ticker == "GTMIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-12"
        and row.amount
    )
    assert gtmix_2025_lt.amount == Decimal("1.5312")

    for ticker in ("GQETX", "GMUEX", "GTMIX"):
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker

    july_2026_paid = [
        row
        for row in records
        if row.ticker in {"GQETX", "GMUEX", "GTMIX"}
        and row.ex_date
        and row.ex_date.year == 2026
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert july_2026_paid == []


def test_parallel_q_voya_vycax_leftover_paid_fills_5y() -> None:
    records = VoyaSource().fetch(mode="fixture").records
    vycax_2025_lt = next(
        row
        for row in records
        if row.ticker == "VYCAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-12"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert vycax_2025_lt.amount == Decimal("1.190900")
    vycax_2025_st = next(
        row
        for row in records
        if row.ticker == "VYCAX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-12"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert vycax_2025_st.amount == Decimal("0.633200")
    vycax_2021_lt = next(
        row
        for row in records
        if row.ticker == "VYCAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-16"
        and row.amount
    )
    assert vycax_2021_lt.amount == Decimal("0.658500")
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, "VYCAX")

    nlcax_2025_lt = next(
        row
        for row in records
        if row.ticker == "NLCAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-12"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert nlcax_2025_lt.amount == Decimal("7.427400")
    nlcax_estimate = next(
        row
        for row in records
        if row.ticker == "NLCAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.publication_stage == PublicationStage.preliminary_estimate
        and row.amount == Decimal("7.259")
    )
    assert nlcax_estimate.amount == Decimal("7.259")
    nlcax_years = _paid_lookback_years(records, "NLCAX")
    assert {2021, 2022, 2024, 2025} <= nlcax_years
    assert 2023 not in nlcax_years

    nmcax_years = _paid_lookback_years(records, "NMCAX")
    assert {2021, 2023, 2024, 2025} <= nmcax_years
    assert 2022 not in nmcax_years


def test_parallel_q_nationwide_leftover_is_4y() -> None:
    records = NationwideSource().fetch(mode="fixture").records
    nwhox_2021_lt = next(
        row
        for row in records
        if row.ticker == "NWHOX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-21"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert nwhox_2021_lt.amount == Decimal("5.429")
    assert nwhox_2021_lt.record_date is None
    nwhjx_2022_lt = next(
        row
        for row in records
        if row.ticker == "NWHJX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-12-21"
        and row.amount is not None
    )
    assert nwhjx_2022_lt.amount == Decimal("0.000")
    ntdax_2023_lt = next(
        row
        for row in records
        if row.ticker == "NTDAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2023-12-22"
        and row.amount
    )
    assert ntdax_2023_lt.amount == Decimal("0.254")

    for ticker in ("NWHOX", "NWHJX", "NTDAX"):
        years = _paid_lookback_years(records, ticker)
        assert {2021, 2022, 2023, 2025} <= years, ticker
        assert 2024 not in years, ticker


def test_parallel_q_leftover_walls_stay_unmatched() -> None:
    voya = VoyaSource().fetch(mode="fixture").records
    nlcax_2023 = [
        row
        for row in voya
        if row.ticker == "NLCAX"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert nlcax_2023 == []
    nmcax_2022 = [
        row
        for row in voya
        if row.ticker == "NMCAX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert nmcax_2022 == []
    vymqx_early = [
        row
        for row in voya
        if row.ticker == "VYMQX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert vymqx_early == []
    for ticker in ("IEDAX", "NAWGX", "VWYFX"):
        early = [
            row
            for row in voya
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year in {2021, 2022, 2023, 2024}
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert early == [], ticker

    nylife = NylifeSource().fetch(mode="fixture").records
    mlaix_paid = [
        row
        for row in nylife
        if row.ticker == "MLAIX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert mlaix_paid == []
    leftover_class_i = {
        "APSGX",
        "CSHZX",
        "EPLCX",
        "EPSYX",
        "FCGIX",
        "FCIUX",
        "FCUIX",
        "KLGIX",
        "MBAIX",
        "MCKIX",
        "MCNVX",
        "MCYIX",
        "MDAIX",
        "MECFX",
        "MGDIX",
        "MGXIX",
        "MLAIX",
        "MMRIX",
        "MNELX",
        "MOEIX",
        "MSOIX",
        "MSPIX",
        "MUBFX",
        "MWFIX",
    }
    nylife_paid_leftovers = [
        row
        for row in nylife
        if row.ticker in leftover_class_i
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert nylife_paid_leftovers == []

    gmo = GmoSource().fetch(mode="fixture").records
    australia = [
        row
        for row in gmo
        if row.ticker
        and "australia" in (row.fund_name or "").lower()
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert australia == []


def test_parallel_q_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("gmo", "voya", "nationwide", "nylife"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        if slug != "nylife":
            assert fetched.json()["created"] > 0

    for ticker in (
        "GQETX",
        "GMUEX",
        "GTMIX",
        "VYCAX",
        "NLCAX",
        "NWHOX",
        "NTDAX",
        "MLAIX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    gqetx = client.get(
        "/distributions",
        params={"ticker": "GQETX", "publication_stage": "final", "page_size": 200},
    ).json()
    gqetx_2025 = [
        Decimal(row["amount"])
        for row in gqetx["items"]
        if row.get("ticker") == "GQETX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-12")
    ]
    assert Decimal("2.6256") in gqetx_2025
    gqetx_years = {
        str(row.get("ex_date") or "")[:4]
        for row in gqetx["items"]
        if row.get("ticker") == "GQETX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= gqetx_years

    vycax = client.get(
        "/distributions",
        params={"ticker": "VYCAX", "publication_stage": "final", "page_size": 200},
    ).json()
    vycax_2025 = [
        Decimal(row["amount"])
        for row in vycax["items"]
        if row.get("ticker") == "VYCAX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-12")
    ]
    assert Decimal("1.190900") in vycax_2025

    mlaix = client.get(
        "/distributions",
        params={"ticker": "MLAIX", "publication_stage": "final", "page_size": 200},
    ).json()
    mlaix_paid = [
        row
        for row in mlaix["items"]
        if row.get("ticker") == "MLAIX" and row.get("amount") is not None
    ]
    assert mlaix_paid == []

def test_parallel_r_aqr_leftover_fills() -> None:
    records = AqrSource().fetch(mode="fixture").records
    aqgix_2025_lt = next(
        row
        for row in records
        if row.ticker == "AQGIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-17"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert aqgix_2025_lt.amount == Decimal("0.5044")
    aqgix_2025_st = next(
        row
        for row in records
        if row.ticker == "AQGIX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-17"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert aqgix_2025_st.amount == Decimal("0.9401")
    aqgix_2023_lt = next(
        row
        for row in records
        if row.ticker == "AQGIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2023-12-18"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert aqgix_2023_lt.amount == Decimal("0.0271")
    aqgnx_2024_lt = next(
        row
        for row in records
        if row.ticker == "AQGNX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-17"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert aqgnx_2024_lt.amount == Decimal("0.5462")
    qdsix_2023_oi = next(
        row
        for row in records
        if row.ticker == "QDSIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-12-27"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert qdsix_2023_oi.amount == Decimal("1.2535")

    aqgix_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "AQGIX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2023, 2024, 2025} <= aqgix_years
    assert 2021 not in aqgix_years
    assert 2022 not in aqgix_years
    qdsix_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "QDSIX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert qdsix_years == {2023}


def test_parallel_r_diamond_hill_leftover_paid_fills_5y() -> None:
    records = DiamondHillSource().fetch(mode="fixture").records
    dhlax_2025_lt = next(
        row
        for row in records
        if row.ticker == "DHLAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-11"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert dhlax_2025_lt.amount == Decimal("1.8730")
    dhscx_2025_lt = next(
        row
        for row in records
        if row.ticker == "DHSCX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-11"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert dhscx_2025_lt.amount == Decimal("1.4076")
    for ticker in (
        "DHSCX",
        "DHMAX",
        "DHPAX",
        "DHLAX",
        "DHTAX",
        "DIAMX",
        "DHIAX",
    ):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_r_bridgeway_leftover_fills() -> None:
    records = BridgewaySource().fetch(mode="fixture").records
    brusx_2025_lt = next(
        row
        for row in records
        if row.ticker == "BRUSX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-16"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert brusx_2025_lt.amount == Decimal("3.2559")
    bosvx_2025_lt = next(
        row
        for row in records
        if row.ticker == "BOSVX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-16"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert bosvx_2025_lt.amount == Decimal("1.5153")
    for ticker in ("BRUSX", "BOSVX", "BRAGX", "BRSVX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker
    brgox_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "BRGOX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert brgox_years == {2024, 2025}
    brsix_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "BRSIX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert brsix_years == {2022, 2024}


def test_parallel_r_leftover_walls_stay_unmatched() -> None:
    aqr = AqrSource().fetch(mode="fixture").records
    for year in (2021, 2022):
        early = [
            row
            for row in aqr
            if row.ex_date
            and row.ex_date.year == year
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert early == [], year
    qdsix_2025 = [
        row
        for row in aqr
        if row.ticker == "QDSIX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert qdsix_2025 == []
    qhfix = [row for row in aqr if row.ticker == "QHFIX"]
    assert qhfix == []

    jensen = JensenSource().fetch(mode="fixture").records
    jensen_early = [
        row
        for row in jensen
        if row.ex_date
        and row.ex_date.year in {2021, 2022, 2023}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert jensen_early == []

    tcw = TcwSource().fetch(mode="fixture").records
    tcw_early = [
        row
        for row in tcw
        if row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert tcw_early == []

    diamond = DiamondHillSource().fetch(mode="fixture").records
    dhsix = [row for row in diamond if row.ticker == "DHSIX"]
    assert dhsix == []

    bridgeway = BridgewaySource().fetch(mode="fixture").records
    brbpx = [row for row in bridgeway if row.ticker == "BRBPX"]
    assert brbpx == []


def test_parallel_r_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("aqr", "diamond_hill", "bridgeway", "jensen", "tcw"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in (
        "AQGIX",
        "DHLAX",
        "JENSX",
        "BRUSX",
        "TGDIX",
        "QDSIX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    aqgix = client.get(
        "/distributions",
        params={"ticker": "AQGIX", "publication_stage": "final", "page_size": 200},
    ).json()
    aqgix_2025 = [
        Decimal(row["amount"])
        for row in aqgix["items"]
        if row.get("ticker") == "AQGIX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-17")
    ]
    assert Decimal("0.5044") in aqgix_2025
    aqgix_years = {
        str(row.get("ex_date") or "")[:4]
        for row in aqgix["items"]
        if row.get("ticker") == "AQGIX" and row.get("amount") is not None
    }
    assert {"2023", "2024", "2025"} <= aqgix_years
    assert "2021" not in aqgix_years
    assert "2022" not in aqgix_years

    dhlax = client.get(
        "/distributions",
        params={"ticker": "DHLAX", "publication_stage": "final", "page_size": 200},
    ).json()
    dhlax_2025 = [
        Decimal(row["amount"])
        for row in dhlax["items"]
        if row.get("ticker") == "DHLAX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-11")
    ]
    assert Decimal("1.8730") in dhlax_2025
    dhlax_years = {
        str(row.get("ex_date") or "")[:4]
        for row in dhlax["items"]
        if row.get("ticker") == "DHLAX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= dhlax_years

    brusx = client.get(
        "/distributions",
        params={"ticker": "BRUSX", "publication_stage": "final", "page_size": 200},
    ).json()
    brusx_2025 = [
        Decimal(row["amount"])
        for row in brusx["items"]
        if row.get("ticker") == "BRUSX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-16")
    ]
    assert Decimal("3.2559") in brusx_2025

    jensx = client.get(
        "/distributions",
        params={"ticker": "JENSX", "publication_stage": "final", "page_size": 200},
    ).json()
    jensx_years = {
        str(row.get("ex_date") or "")[:4]
        for row in jensx["items"]
        if row.get("ticker") == "JENSX" and row.get("amount") is not None
    }
    assert {"2024", "2025"} <= jensx_years
    assert "2021" not in jensx_years
    assert "2022" not in jensx_years
    assert "2023" not in jensx_years

    tgdix = client.get(
        "/distributions",
        params={"ticker": "TGDIX", "publication_stage": "final", "page_size": 200},
    ).json()
    tgdix_years = {
        str(row.get("ex_date") or "")[:4]
        for row in tgdix["items"]
        if row.get("ticker") == "TGDIX" and row.get("amount") is not None
    }
    assert tgdix_years == {"2025"}

    qdsix = client.get(
        "/distributions",
        params={"ticker": "QDSIX", "publication_stage": "final", "page_size": 200},
    ).json()
    qdsix_paid = [
        row
        for row in qdsix["items"]
        if row.get("ticker") == "QDSIX" and row.get("amount") is not None
    ]
    assert qdsix_paid
    assert all(str(row.get("ex_date") or "").startswith("2023") for row in qdsix_paid)

    dhsix = client.get(
        "/distributions",
        params={"ticker": "DHSIX", "publication_stage": "final", "page_size": 200},
    ).json()
    dhsix_paid = [
        row
        for row in dhsix["items"]
        if row.get("ticker") == "DHSIX" and row.get("amount") is not None
    ]
    assert dhsix_paid == []


def test_parallel_v_heartland_leftover_paid_fills_5y() -> None:
    records = HeartlandSource().fetch(mode="fixture").records
    hrtvx_2024_lt = next(
        row
        for row in records
        if row.ticker == "HRTVX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-20"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert hrtvx_2024_lt.amount == Decimal("3.86958")
    hrmdx_2021_lt = next(
        row
        for row in records
        if row.ticker == "HRMDX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-29"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert hrmdx_2021_lt.amount == Decimal("2.10121")
    for ticker in ("HRMDX", "HNMDX", "HRVIX", "HNVIX", "HRTVX", "HNTVX"):
        assert set(LOOKBACK_YEARS) <= _paid_years(records, ticker), ticker


def test_parallel_v_fmi_leftover_paid_fills_5y() -> None:
    records = FmiSource().fetch(mode="fixture").records
    fmiux_2021_lt = next(
        row
        for row in records
        if row.ticker == "FMIUX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-17"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert fmiux_2021_lt.amount == Decimal("3.86103")
    fmimx_2024_lt = next(
        row
        for row in records
        if row.ticker == "FMIMX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-20"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert fmimx_2024_lt.amount == Decimal("0.64647")
    fmiux_2021_st = next(
        row
        for row in records
        if row.ticker == "FMIUX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-17"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert fmiux_2021_st.amount == Decimal("0.00000")
    for ticker in ("FMIUX", "FMIMX"):
        assert set(LOOKBACK_YEARS) <= _paid_years(records, ticker), ticker
    assert [row for row in records if row.ticker == "FMIHX"] == []


def test_parallel_v_brandes_leftover_paid_fills_5y() -> None:
    records = BrandesSource().fetch(mode="fixture").records
    bgvix_2025_lt = next(
        row
        for row in records
        if row.ticker == "BGVIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-10"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert bgvix_2025_lt.amount == Decimal("3.624675")
    bemix_2022_oi = next(
        row
        for row in records
        if row.ticker == "BEMIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2022-12-30"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert bemix_2022_oi.amount == Decimal("0.000000")
    for ticker in ("BGVIX", "BIIEX", "BSCMX", "BEMIX", "BISMX"):
        assert set(LOOKBACK_YEARS) <= _paid_years(records, ticker), ticker
    assert [row for row in records if row.ticker == "BGVAX"] == []


def test_parallel_v_baillie_leftover_is_year_depth() -> None:
    records = BaillieGiffordSource().fetch(mode="fixture").records
    bgakx_2025_lt = next(
        row
        for row in records
        if row.ticker == "BGAKX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-29"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert bgakx_2025_lt.amount == Decimal("5.18723")
    bsgpx_2025_lt = next(
        row
        for row in records
        if row.ticker == "BSGPX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-29"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert bsgpx_2025_lt.amount == Decimal("9.00459")
    for ticker in ("BGAKX", "BINSX", "BGESX", "BSGPX"):
        years = _paid_years(records, ticker)
        assert 2025 in years, ticker
        assert years.isdisjoint({2021, 2022, 2023, 2024}), ticker
    bgcsx_final = [
        row
        for row in records
        if row.ticker == "BGCSX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert bgcsx_final == []


def test_parallel_v_leftover_walls_stay_unmatched() -> None:
    gqg = GqgSource().fetch(mode="fixture").records
    gqg_final = [
        row
        for row in gqg
        if row.publication_stage == PublicationStage.final and row.amount is not None
    ]
    assert gqg_final == []
    fmi = FmiSource().fetch(mode="fixture").records
    assert [row for row in fmi if row.ticker in {"FMIHX", "FMIJX", "FMIYX", "FMIQX"}] == []
    baillie = BaillieGiffordSource().fetch(mode="fixture").records
    assert [
        row
        for row in baillie
        if row.ticker == "BGCSX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ] == []
    brandes = BrandesSource().fetch(mode="fixture").records
    assert [row for row in brandes if row.ticker in {"BGVAX", "BIEAX", "BSCAX"}] == []


def test_parallel_v_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("heartland", "fmi", "brandes", "baillie_gifford", "gqg"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("HRTVX", "HRMDX", "FMIUX", "BGVIX", "BGAKX", "GQEIX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    hrtvx = client.get(
        "/distributions",
        params={"ticker": "HRTVX", "publication_stage": "final", "page_size": 200},
    ).json()
    hrtvx_2024 = [
        Decimal(row["amount"])
        for row in hrtvx["items"]
        if row.get("ticker") == "HRTVX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2024-12-20")
    ]
    assert Decimal("3.86958") in hrtvx_2024
    hrtvx_years = {
        str(row.get("ex_date") or "")[:4]
        for row in hrtvx["items"]
        if row.get("ticker") == "HRTVX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= hrtvx_years

    bgvix = client.get(
        "/distributions",
        params={"ticker": "BGVIX", "publication_stage": "final", "page_size": 200},
    ).json()
    bgvix_2025 = [
        Decimal(row["amount"])
        for row in bgvix["items"]
        if row.get("ticker") == "BGVIX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-10")
    ]
    assert Decimal("3.624675") in bgvix_2025

    gqeix = client.get(
        "/distributions",
        params={"ticker": "GQEIX", "publication_stage": "final", "page_size": 200},
    ).json()
    gqeix_paid = [
        row
        for row in gqeix["items"]
        if row.get("ticker") == "GQEIX" and row.get("amount") is not None
    ]
    assert gqeix_paid == []

def test_parallel_w_manning_leftover_paid_fills_5y() -> None:
    records = ManningNapierSource().fetch(mode="fixture").records
    mnhix_2021_lt = next(
        row
        for row in records
        if row.ticker == "MNHIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-14"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert mnhix_2021_lt.amount == Decimal("0.85360")
    exeyx_2024_lt = next(
        row
        for row in records
        if row.ticker == "EXEYX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-12"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert exeyx_2024_lt.amount == Decimal("1.73250")
    for ticker in (
        "EXEYX",
        "MNHIX",
        "MNDFX",
        "EXBAX",
        "EXHAX",
        "RAIWX",
        "RAIRX",
    ):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_w_westwood_leftover_paid_fills_5y() -> None:
    records = WestwoodSource().fetch(mode="fixture").records
    whglx_2025_lt = next(
        row
        for row in records
        if row.ticker == "WHGLX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-12"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert whglx_2025_lt.amount == Decimal("2.4094")
    for ticker in ("WHGLX", "WHGMX", "WHGSX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker
    wwmcx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "WWMCX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert wwmcx_years == {2023, 2024, 2025}
    wqaix_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "WQAIX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert wqaix_years == {2021, 2022, 2023, 2024}


def test_parallel_w_boston_partners_and_lsv_are_year_depth() -> None:
    boston = BostonPartnersSource().fetch(mode="fixture").records
    bpaix_2025_lt = next(
        row
        for row in boston
        if row.ticker == "BPAIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-12"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert bpaix_2025_lt.amount == Decimal("2.68")
    bpaix_2024_lt = next(
        row
        for row in boston
        if row.ticker == "BPAIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-13"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert bpaix_2024_lt.amount == Decimal("2.81")
    for ticker in ("BPAIX", "BPSIX", "BPGIX", "WPGSX"):
        years = {
            row.ex_date.year
            for row in boston
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert years == {2024, 2025}, ticker

    lsv = LsvSource().fetch(mode="fixture").records
    lsvex_2024_lt = next(
        row
        for row in lsv
        if row.ticker == "LSVEX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-23"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert lsvex_2024_lt.amount == Decimal("1.6848")
    for ticker in ("LSVEX", "LVAEX", "LSVVX", "LSVMX"):
        years = {
            row.ex_date.year
            for row in lsv
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert years == {2024, 2025}, ticker


def test_parallel_w_leftover_walls_stay_unmatched() -> None:
    lazard = LazardSource().fetch(mode="fixture").records
    lazard_paid = [
        row
        for row in lazard
        if row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert lazard_paid == []
    assert [row for row in lazard if row.ticker == "RLCIX"] == []

    # WAVE AR fills Homestead leftover 2021–2024 N-CSR years. Parallel W
    # still documents the unpublished Year-End-Distributions.pdf siblings.

    madison = MadisonSource().fetch(mode="fixture").records
    madison_early = [
        row
        for row in madison
        if row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert madison_early == []

    manning = ManningNapierSource().fetch(mode="fixture").records
    for ticker, missing in (
        ("CEIIX", {2021, 2022}),
        ("MSHIX", {2021, 2022, 2023, 2024}),
        ("RAIIX", {2022}),
        ("RISAX", {2022, 2024}),
    ):
        years = {
            row.ex_date.year
            for row in manning
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert missing.isdisjoint(years), ticker

    boston = BostonPartnersSource().fetch(mode="fixture").records
    assert [row for row in boston if row.ticker in {"BELSX", "WPGHX"}] == []
    boston_early = [
        row
        for row in boston
        if row.ex_date
        and row.ex_date.year in {2021, 2022, 2023}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert boston_early == []

    westwood = WestwoodSource().fetch(mode="fixture").records
    assert [row for row in westwood if row.ticker in {"WWLAX", "WHGQX", "WHGAX"}] == []

    lsv = LsvSource().fetch(mode="fixture").records
    lsv_early = [
        row
        for row in lsv
        if row.ex_date
        and row.ex_date.year in {2021, 2022, 2023}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert lsv_early == []


def test_parallel_w_heroes_are_searchable(client: TestClient) -> None:
    for slug in (
        "manning_napier",
        "westwood",
        "boston_partners",
        "lsv",
        "lazard",
        "homestead",
        "madison",
    ):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in (
        "MNHIX",
        "EXEYX",
        "WHGLX",
        "WHGSX",
        "BPAIX",
        "LSVEX",
        "LZIEX",
        "HOVLX",
        "MNVAX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    mnhix = client.get(
        "/distributions",
        params={"ticker": "MNHIX", "publication_stage": "final", "page_size": 200},
    ).json()
    mnhix_2021 = [
        Decimal(row["amount"])
        for row in mnhix["items"]
        if row.get("ticker") == "MNHIX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2021-12-14")
    ]
    assert Decimal("0.85360") in mnhix_2021
    mnhix_years = {
        str(row.get("ex_date") or row.get("payable_date") or "")[:4]
        for row in mnhix["items"]
        if row.get("ticker") == "MNHIX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= mnhix_years

    whglx = client.get(
        "/distributions",
        params={"ticker": "WHGLX", "publication_stage": "final", "page_size": 200},
    ).json()
    whglx_2025 = [
        Decimal(row["amount"])
        for row in whglx["items"]
        if row.get("ticker") == "WHGLX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-12")
    ]
    assert Decimal("2.4094") in whglx_2025

    lziex = client.get(
        "/distributions",
        params={"ticker": "LZIEX", "publication_stage": "final", "page_size": 200},
    ).json()
    lziex_paid = [
        row
        for row in lziex["items"]
        if row.get("ticker") == "LZIEX" and row.get("amount") is not None
    ]
    assert lziex_paid == []


def test_parallel_t_marsico_leftover_investor_paid_fills_5y() -> None:
    records = MarsicoSource().fetch(mode="fixture").records
    mfocx_2024_lt = next(
        row
        for row in records
        if row.ticker == "MFOCX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-20"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert mfocx_2024_lt.amount == Decimal("1.7590")
    mfocx_2022_lt = next(
        row
        for row in records
        if row.ticker == "MFOCX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-12-16"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert mfocx_2022_lt.amount == Decimal("2.8135")
    mgrix_2021_oct_lt = next(
        row
        for row in records
        if row.ticker == "MGRIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-10-01"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert mgrix_2021_oct_lt.amount == Decimal("6.1495")
    mgrix_2022_zero = next(
        row
        for row in records
        if row.ticker == "MGRIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-12-16"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert mgrix_2022_zero.amount == Decimal("0.0000")
    for ticker in ("MFOCX", "MGRIX", "MXXIX", "MIOFX", "MGLBX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_t_harding_leftover_2021_2022_is_year_depth() -> None:
    records = HardingLoevnerSource().fetch(mode="fixture").records
    hlemx_2021_lt = next(
        row
        for row in records
        if row.ticker == "HLEMX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-14"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert hlemx_2021_lt.amount == Decimal("4.720760")
    hlemx_2022_lt = next(
        row
        for row in records
        if row.ticker == "HLEMX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-12-13"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert hlemx_2022_lt.amount == Decimal("3.125550")
    hlgzx_2021_lt = next(
        row
        for row in records
        if row.ticker == "HLGZX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-14"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert hlgzx_2021_lt.amount == Decimal("6.637289")
    hlemx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "HLEMX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2021, 2022, 2023, 2025} <= hlemx_years
    assert 2024 not in hlemx_years
    hlizx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "HLIZX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2021, 2022, 2023, 2025} <= hlizx_years
    assert 2024 not in hlizx_years


def test_parallel_t_leftover_walls_stay_unmatched() -> None:
    harding = HardingLoevnerSource().fetch(mode="fixture").records
    hlmgx_2022 = [
        row
        for row in harding
        if row.ticker == "HLMGX"
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount is not None
    ]
    assert hlmgx_2022 == []
    for ticker, year in (("HLFZX", 2021), ("HLFZX", 2022), ("HLRZX", 2021), ("HLIDX", 2021)):
        rows = [
            row
            for row in harding
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == year
            and row.amount is not None
        ]
        assert rows == [], (ticker, year)
    hleffx = [row for row in harding if row.ticker == "HLFFX"]
    assert hleffx == []

    marsico = MarsicoSource().fetch(mode="fixture").records
    for ticker in ("MIFOX", "MIGWX", "MIDFX", "MIIOX", "MIGOX"):
        years = {
            row.ex_date.year
            for row in marsico
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert years == {2022, 2023, 2024, 2025}, ticker
        assert 2021 not in years

    alger = AlgerSource().fetch(mode="fixture").records
    for year in (2021, 2023, 2024):
        chusx = [
            row
            for row in alger
            if row.ticker == "CHUSX"
            and row.ex_date
            and row.ex_date.year == year
            and row.amount is not None
        ]
        assert chusx == [], year
    for ticker, year in (("ATFV", 2022), ("ATFV", 2024), ("FRTY", 2022), ("FRTY", 2024)):
        rows = [
            row
            for row in alger
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == year
            and row.amount is not None
        ]
        assert rows == [], (ticker, year)

    driehaus = DriehausSource().fetch(mode="fixture").records
    driehaus_early = [
        row
        for row in driehaus
        if row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert driehaus_early == []
    dmcqx = [row for row in driehaus if row.ticker == "DMCQX"]
    assert dmcqx == []


def test_parallel_t_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("marsico", "harding_loevner", "alger", "driehaus"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("MFOCX", "HLMNX", "CHUSX", "DMCRX", "HLEMX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    mfocx = client.get(
        "/distributions",
        params={"ticker": "MFOCX", "publication_stage": "final", "page_size": 200},
    ).json()
    mfocx_2024 = [
        Decimal(row["amount"])
        for row in mfocx["items"]
        if row.get("ticker") == "MFOCX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2024-12-20")
    ]
    assert Decimal("1.7590") in mfocx_2024
    mfocx_years = {
        str(row.get("ex_date") or "")[:4]
        for row in mfocx["items"]
        if row.get("ticker") == "MFOCX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= mfocx_years

    hlemx = client.get(
        "/distributions",
        params={"ticker": "HLEMX", "publication_stage": "final", "page_size": 200},
    ).json()
    hlemx_2021 = [
        Decimal(row["amount"])
        for row in hlemx["items"]
        if row.get("ticker") == "HLEMX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2021-12-14")
    ]
    assert Decimal("4.720760") in hlemx_2021
    hlemx_years = {
        str(row.get("ex_date") or "")[:4]
        for row in hlemx["items"]
        if row.get("ticker") == "HLEMX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2025"} <= hlemx_years
    assert "2024" not in hlemx_years

    mifox = client.get(
        "/distributions",
        params={"ticker": "MIFOX", "publication_stage": "final", "page_size": 200},
    ).json()
    mifox_years = {
        str(row.get("ex_date") or "")[:4]
        for row in mifox["items"]
        if row.get("ticker") == "MIFOX" and row.get("amount") is not None
    }
    assert {"2022", "2023", "2024", "2025"} <= mifox_years
    assert "2021" not in mifox_years

    chusx = client.get(
        "/distributions",
        params={"ticker": "CHUSX", "publication_stage": "final", "page_size": 200},
    ).json()
    chusx_early = [
        row
        for row in chusx["items"]
        if row.get("ticker") == "CHUSX"
        and str(row.get("ex_date") or "")[:4] in {"2021", "2023", "2024"}
        and row.get("amount") is not None
    ]
    assert chusx_early == []


def test_parallel_u_tweedy_leftover_paid_fills_5y() -> None:
    records = TweedySource().fetch(mode="fixture").records
    tbgvx_2025_lt = next(
        row
        for row in records
        if row.ticker == "TBGVX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-11"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert tbgvx_2025_lt.amount == Decimal("2.793")
    twebx_2025_lt = next(
        row
        for row in records
        if row.ticker == "TWEBX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-11"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert twebx_2025_lt.amount == Decimal("0.464")
    for ticker in ("TBGVX", "TWEBX", "TBCUX", "TBHDX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_u_osterweis_leftover_paid_fills_5y() -> None:
    records = OsterweisSource().fetch(mode="fixture").records
    ostfx_2025_lt = next(
        row
        for row in records
        if row.ticker == "OSTFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-15"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert ostfx_2025_lt.amount == Decimal("1.17276")
    ostgx_2023_lt = next(
        row
        for row in records
        if row.ticker == "OSTGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2023-12-15"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert ostgx_2023_lt.amount == Decimal("0.00000")
    for ticker in ("OSTFX", "OSTGX", "OSTVX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_u_longleaf_leftover_paid_fills_5y() -> None:
    records = LongleafSource().fetch(mode="fixture").records
    llpfx_2024_oi = next(
        row
        for row in records
        if row.ticker == "LLPFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-20"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert llpfx_2024_oi.amount == Decimal("0.2469")
    llpfx_2021_st = next(
        row
        for row in records
        if row.ticker == "LLPFX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-01"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert llpfx_2021_st.amount == Decimal("1.3521")
    for ticker in ("LLPFX", "LLSCX", "LLGLX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_u_buffalo_leftover_is_year_depth() -> None:
    records = BuffaloSource().fetch(mode="fixture").records
    bufex_2025_lt = next(
        row
        for row in records
        if row.ticker == "BUFEX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-04"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert bufex_2025_lt.amount == Decimal("3.35562")
    bufgx_2024_lt = next(
        row
        for row in records
        if row.ticker == "BUFGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-04"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert bufgx_2024_lt.amount == Decimal("2.98029")
    for ticker in ("BUFEX", "BUFBX", "BUFGX", "BUFDX", "BUFIX", "BUFTX", "BUFMX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert years == {2024, 2025}, ticker
    bufox_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "BUFOX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert bufox_years == {2025}


def test_parallel_u_third_avenue_leftover_is_4y() -> None:
    records = ThirdAvenueSource().fetch(mode="fixture").records
    tavfx_2024_lt = next(
        row
        for row in records
        if row.ticker == "TAVFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-11"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert tavfx_2024_lt.amount == Decimal("4.08400")
    tascs_2022_st = next(
        row
        for row in records
        if row.ticker == "TASCX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-12-14"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert tascs_2022_st.amount == Decimal("0.02361")
    for ticker in ("TAVFX", "TASCX", "TAREX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert years == {2022, 2023, 2024, 2025}, ticker
        assert 2021 not in years


def test_parallel_u_leftover_walls_stay_unmatched() -> None:
    tweedy = TweedySource().fetch(mode="fixture").records
    assert [row for row in tweedy if row.ticker == "TBWIX"] == []

    osterweis = OsterweisSource().fetch(mode="fixture").records
    assert [row for row in osterweis if row.ticker == "OSTIX"] == []
    assert [row for row in osterweis if row.ticker == "OSTAX"] == []

    longleaf = LongleafSource().fetch(mode="fixture").records
    assert [row for row in longleaf if row.ticker == "LLINX"] == []
    llscx_nov_2022 = [
        row
        for row in longleaf
        if row.ticker == "LLSCX"
        and row.ex_date
        and str(row.ex_date) == "2022-12-01"
        and row.amount is not None
    ]
    assert llscx_nov_2022 == []

    buffalo = BuffaloSource().fetch(mode="fixture").records
    assert [row for row in buffalo if row.ticker == "BUIEX"] == []
    assert [row for row in buffalo if row.ticker == "BUFHX"] == []
    buffalo_early = [
        row
        for row in buffalo
        if row.ex_date
        and row.ex_date.year in {2021, 2022, 2023}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert buffalo_early == []

    third = ThirdAvenueSource().fetch(mode="fixture").records
    assert [row for row in third if row.ticker == "TVFVX"] == []
    assert [row for row in third if row.ticker == "TAVZX"] == []
    third_2021 = [
        row
        for row in third
        if row.ex_date
        and row.ex_date.year == 2021
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert third_2021 == []


def test_parallel_u_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("tweedy", "osterweis", "longleaf", "buffalo", "third_avenue"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in (
        "TBGVX",
        "TWEBX",
        "OSTFX",
        "LLPFX",
        "BUFEX",
        "TAVFX",
        "BUFOX",
        "OSTIX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        if ticker == "OSTIX":
            assert ticker not in tickers
            continue
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    tbgvx = client.get(
        "/distributions",
        params={"ticker": "TBGVX", "publication_stage": "final", "page_size": 200},
    ).json()
    tbgvx_2025 = [
        Decimal(row["amount"])
        for row in tbgvx["items"]
        if row.get("ticker") == "TBGVX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-11")
    ]
    assert Decimal("2.793") in tbgvx_2025
    tbgvx_years = {
        str(row.get("ex_date") or "")[:4]
        for row in tbgvx["items"]
        if row.get("ticker") == "TBGVX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= tbgvx_years

    ostfx = client.get(
        "/distributions",
        params={"ticker": "OSTFX", "publication_stage": "final", "page_size": 200},
    ).json()
    ostfx_2025 = [
        Decimal(row["amount"])
        for row in ostfx["items"]
        if row.get("ticker") == "OSTFX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-15")
    ]
    assert Decimal("1.17276") in ostfx_2025

    llpfx = client.get(
        "/distributions",
        params={"ticker": "LLPFX", "publication_stage": "final", "page_size": 200},
    ).json()
    llpfx_2024 = [
        Decimal(row["amount"])
        for row in llpfx["items"]
        if row.get("ticker") == "LLPFX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2024-12-20")
    ]
    assert Decimal("0.2469") in llpfx_2024

    bufex = client.get(
        "/distributions",
        params={"ticker": "BUFEX", "publication_stage": "final", "page_size": 200},
    ).json()
    bufex_years = {
        str(row.get("ex_date") or "")[:4]
        for row in bufex["items"]
        if row.get("ticker") == "BUFEX" and row.get("amount") is not None
    }
    assert bufex_years == {"2024", "2025"}

    tavfx = client.get(
        "/distributions",
        params={"ticker": "TAVFX", "publication_stage": "final", "page_size": 200},
    ).json()
    tavfx_years = {
        str(row.get("ex_date") or "")[:4]
        for row in tavfx["items"]
        if row.get("ticker") == "TAVFX" and row.get("amount") is not None
    }
    assert tavfx_years == {"2022", "2023", "2024", "2025"}
    assert "2021" not in tavfx_years

    ostix = client.get(
        "/distributions",
        params={"ticker": "OSTIX", "publication_stage": "final", "page_size": 200},
    ).json()
    ostix_paid = [
        row
        for row in ostix["items"]
        if row.get("ticker") == "OSTIX" and row.get("amount") is not None
    ]
    assert ostix_paid == []


def test_parallel_aa_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "vanguard", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("BND", "BIV", "VBIIX", "VWALX", "VBTIX", "VUSXX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    bnd = client.get(
        "/distributions",
        params={"ticker": "BND", "publication_stage": "final", "page_size": 200},
    ).json()
    bnd_2022 = [
        Decimal(row["amount"])
        for row in bnd["items"]
        if row.get("ticker") == "BND"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2022-12-29")
    ]
    assert Decimal("0.172311") in bnd_2022
    bnd_years = {
        str(row.get("ex_date") or row.get("payable_date") or "")[:4]
        for row in bnd["items"]
        if row.get("ticker") == "BND" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= bnd_years

    vbiix = client.get(
        "/distributions",
        params={"ticker": "VBIIX", "publication_stage": "final", "page_size": 200},
    ).json()
    vbiix_2022 = [
        Decimal(row["amount"])
        for row in vbiix["items"]
        if row.get("ticker") == "VBIIX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2022-12-01")
    ]
    assert Decimal("0.021170") in vbiix_2022

def test_parallel_y_blackrock_leftover_fills_5y() -> None:
    records = BlackRockSource().fetch(mode="fixture").records
    bacax_jul = next(
        row
        for row in records
        if row.ticker == "BACAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-07-17"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert bacax_jul.amount == Decimal("0.141259")
    bacax_dec = next(
        row
        for row in records
        if row.ticker == "BACAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-11"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert bacax_dec.amount == Decimal("0.203450")
    mddcx_2025 = next(
        row
        for row in records
        if row.ticker == "MDDCX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-09"
        and row.amount
    )
    assert mddcx_2025.amount == Decimal("1.114790")
    mdgcx_2025 = [
        row
        for row in records
        if row.ticker == "MDGCX"
        and row.ex_date
        and str(row.ex_date) == "2025-12-09"
        and row.publication_stage == PublicationStage.final
        and row.amount
    ]
    mdgcx_by_type = {row.estimate_type: row.amount for row in mdgcx_2025}
    assert mdgcx_by_type[EstimateType.ordinary_income] == Decimal("0.362241")
    assert mdgcx_by_type[EstimateType.short_term_capital_gains] == Decimal("1.055639")
    assert mdgcx_by_type[EstimateType.long_term_capital_gains] == Decimal("1.047497")
    bardx_2024 = [
        row
        for row in records
        if row.ticker == "BARDX"
        and row.ex_date
        and str(row.ex_date) == "2024-10-10"
        and row.publication_stage == PublicationStage.final
        and row.amount
    ]
    bardx_by_type = {row.estimate_type: row.amount for row in bardx_2024}
    assert bardx_by_type[EstimateType.ordinary_income] == Decimal("0.115751")
    assert bardx_by_type[EstimateType.short_term_capital_gains] == Decimal("0.193089")
    assert bardx_by_type[EstimateType.long_term_capital_gains] == Decimal("1.386730")
    for ticker in (
        "BABDX",
        "BACAX",
        "BALPX",
        "BARDX",
        "BAREX",
        "BDSAX",
        "BICSX",
        "BROAX",
        "MALRX",
        "MALVX",
        "MCFOX",
        "MDDCX",
        "MDGCX",
        "MDLVX",
        "MDSPX",
        "SHSAX",
    ):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_y_leftover_walls_stay_unmatched() -> None:
    records = BlackRockSource().fetch(mode="fixture").records
    for ticker in ("CMLAX", "LILAX", "LELAX"):
        rows_2025 = [
            row
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == 2025
            and row.amount is not None
        ]
        assert rows_2025 == [], ticker
    for ticker, year in (
        ("BAICX", 2024),
        ("BAMBX", 2021),
        ("BHYAX", 2023),
        ("BCBAX", 2024),
    ):
        rows = [
            row
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == year
            and row.amount is not None
        ]
        assert rows == [], f"{ticker} {year} should stay unmatched"

    invesco = InvescoSource().fetch(mode="fixture").records
    vafax_early = [
        row
        for row in invesco
        if row.ticker == "VAFAX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022}
        and row.amount is not None
    ]
    assert vafax_early == []

    franklin = FranklinTempletonSource().fetch(mode="fixture").records
    for ticker in ("FT", "PIM", "PMM"):
        years = {
            row.ex_date.year
            for row in franklin
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert 2025 in years or years == set(), ticker
        assert {2021, 2022, 2023, 2024}.isdisjoint(years), ticker

    pimco = PimcoSource().fetch(mode="fixture").records
    pimco_in_book = [
        row
        for row in pimco
        if row.ticker and not str(row.ticker).startswith("ZZ")
    ]
    assert pimco_in_book == []


def test_parallel_y_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "blackrock", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("BACAX", "MDDCX", "MDGCX", "BARDX", "MCFOX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    bacax = client.get(
        "/distributions",
        params={"ticker": "BACAX", "publication_stage": "final", "page_size": 200},
    ).json()
    bacax_2025 = [
        Decimal(row["amount"])
        for row in bacax["items"]
        if row.get("ticker") == "BACAX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2025-12-11")
    ]
    assert Decimal("0.203450") in bacax_2025
    bacax_years = {
        str(row.get("ex_date") or row.get("payable_date") or "")[:4]
        for row in bacax["items"]
        if row.get("ticker") == "BACAX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= bacax_years

    mdgcx = client.get(
        "/distributions",
        params={"ticker": "MDGCX", "publication_stage": "final", "page_size": 200},
    ).json()
    mdgcx_2025 = [
        Decimal(row["amount"])
        for row in mdgcx["items"]
        if row.get("ticker") == "MDGCX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-09")
    ]
    assert Decimal("1.047497") in mdgcx_2025

    cmlax = client.get(
        "/distributions",
        params={"ticker": "CMLAX", "publication_stage": "final", "page_size": 200},
    ).json()
    cmlax_2025 = [
        row
        for row in cmlax["items"]
        if row.get("ticker") == "CMLAX"
        and str(row.get("ex_date") or "")[:4] == "2025"
        and row.get("amount") is not None
    ]
    assert cmlax_2025 == []


def test_parallel_ac_principal_leftover_paid_fills_5y() -> None:
    records = PrincipalSource().fetch(mode="fixture").records
    pfijx_2024 = next(
        row
        for row in records
        if row.ticker == "PFIJX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert pfijx_2024.amount == Decimal("0.1338")
    pieix_2024 = next(
        row
        for row in records
        if row.ticker == "PIEIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-27"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert pieix_2024.amount == Decimal("0.0733")
    pfrsx_2025 = next(
        row
        for row in records
        if row.ticker == "PFRSX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-29"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert pfrsx_2025.amount == Decimal("0.1804")
    for ticker in (
        "PFIJX",
        "PEPSX",
        "PIEIX",
        "PIEJX",
        "PIIMX",
        "PFRSX",
        "PIREX",
        "PRCEX",
        "PREJX",
        "PREPX",
        "PRERX",
        "PRRAX",
    ):
        years = _paid_lookback_years(records, ticker)
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_ac_leftover_walls_stay_unmatched() -> None:
    principal = PrincipalSource().fetch(mode="fixture").records
    for ticker in (
        "PBLCX",
        "PBCKX",
        "PBCJX",
        "PBLAX",
        "PGBEX",
        "PGBGX",
        "PCSMX",
        "PGRTX",
        "PPNMX",
        "PPNPX",
        "PSIJX",
    ):
        years = _paid_lookback_years(principal, ticker)
        assert 2023 not in years, ticker
    for ticker in ("PEAPX", "PRIAX"):
        years = _paid_lookback_years(principal, ticker)
        assert 2024 not in years, ticker
        pepsx_2024 = [
            row
            for row in principal
            if row.ticker == "PEPSX"
            and row.ex_date
            and str(row.ex_date) == "2024-12-27"
            and row.estimate_type == EstimateType.ordinary_income
            and row.amount == Decimal("0.0363")
        ]
        assert pepsx_2024, "GEM R-5 2024 must stay class-level"

    jh = JohnHancockSource().fetch(mode="fixture").records
    for ticker in ("JVLAX", "TAGRX"):
        finals = [
            row
            for row in jh
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert finals == [], ticker

    nationwide = NationwideSource().fetch(mode="fixture").records
    for ticker in ("NWHOX", "NWHJX", "NTDAX"):
        years = _paid_lookback_years(nationwide, ticker)
        assert {2021, 2022, 2023, 2025} <= years, ticker
        assert 2024 not in years, ticker

    thrivent = ThriventSource().fetch(mode="fixture").records
    tmaix_2022 = [
        row
        for row in thrivent
        if row.ticker == "TMAIX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2022
        and row.amount is not None
    ]
    assert tmaix_2022 == []
    tmcvx_2023 = [
        row
        for row in thrivent
        if row.ticker == "TMCVX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2023
        and row.amount is not None
    ]
    assert tmcvx_2023 == []

    af = AmericanFundsSource().fetch(mode="fixture").records
    anefx_2022 = [
        row
        for row in af
        if row.ticker == "ANEFX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2022
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount is not None
    ]
    assert anefx_2022 == []


def test_parallel_ac_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "principal", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("PFIJX", "PIEIX", "PFRSX", "PEAPX", "PBLCX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    pfrsx = client.get(
        "/distributions",
        params={"ticker": "PFRSX", "publication_stage": "final", "page_size": 200},
    ).json()
    pfrsx_2025 = [
        Decimal(row["amount"])
        for row in pfrsx["items"]
        if row.get("ticker") == "PFRSX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2025-12-29")
    ]
    assert Decimal("0.1804") in pfrsx_2025

def _lookback_years(records, ticker: str) -> set[int]:
    years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == ticker
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount is not None
        and getattr(row.amount_unit, "value", row.amount_unit) == "per_share"
    }
    years.discard(None)
    return years


def test_mass_z_t_rowe_leftover_advisor_is_year_depth() -> None:
    records = TRowePriceSource().fetch(mode="fixture").records
    pabgx_2023 = next(
        row
        for row in records
        if row.ticker == "PABGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2023-12-13"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert pabgx_2023.amount == Decimal("5.2095")
    pabgx_2025_st = next(
        row
        for row in records
        if row.ticker == "PABGX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-11"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert pabgx_2025_st.amount == Decimal("0.0748")
    pabgx_2025_lt = next(
        row
        for row in records
        if row.ticker == "PABGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-11"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert pabgx_2025_lt.amount == Decimal("10.9575")
    trbcx_2025 = next(
        row
        for row in records
        if row.ticker == "TRBCX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2025
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert trbcx_2025.amount == Decimal("10.9575")
    pabgx_years = _lookback_years(records, "PABGX")
    assert {2021, 2022, 2023, 2025} <= pabgx_years
    rrbgx_years = _lookback_years(records, "RRBGX")
    assert {2021, 2022, 2023, 2025} <= rrbgx_years
    # WAVE AL fills official 2024 N-CSR leftover years (PABGX CG $16.42).


def test_mass_z_columbia_institutional_leftover_completes_5y() -> None:
    records = ColumbiaThreadneedleSource().fetch(mode="fixture").records
    gsftx_2021 = next(
        row
        for row in records
        if row.ticker == "GSFTX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-14"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gsftx_2021.amount == Decimal("0.44721")
    smgix_2021_st = next(
        row
        for row in records
        if row.ticker == "SMGIX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-09"
        and row.amount
    )
    assert smgix_2021_st.amount == Decimal("0.54063")
    smgix_2021_lt = next(
        row
        for row in records
        if row.ticker == "SMGIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-09"
        and row.amount
    )
    assert smgix_2021_lt.amount == Decimal("3.85482")
    for ticker in (
        "CPAZX",
        "NBGPX",
        "SMGIX",
        "CCRZX",
        "CLQZX",
        "CVQZX",
        "GSFTX",
        "CDOZX",
        "CMTFX",
        "CEVZX",
        "CDVZX",
        "NMIMX",
        "NINDX",
        "NMPAX",
        "CSVZX",
        "NAMAX",
        "CSSZX",
        "CSGZX",
        "CCIZX",
        "NMSCX",
        "NSVAX",
        "CDAZX",
        "CZMSX",
        "CZMVX",
    ):
        assert set(LOOKBACK_YEARS) <= _lookback_years(records, ticker), ticker
    lbsax_years = _lookback_years(records, "LBSAX")
    assert {2022, 2023, 2024, 2025} <= lbsax_years
    assert 2021 not in lbsax_years


def test_mass_z_mfs_leftover_year_finals_complete_5y() -> None:
    records = MfsSource().fetch(mode="fixture").records
    megbx_2022 = next(
        row
        for row in records
        if row.ticker == "MEGBX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-12-13"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert megbx_2022.amount == Decimal("1.39190")
    migbx_2023 = next(
        row
        for row in records
        if row.ticker == "MIGBX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2023-12-21"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert migbx_2023.amount == Decimal("1.38597")
    for ticker in (
        "MEGBX",
        "MEGRX",
        "MFEHX",
        "MFEJX",
        "MFELX",
        "MIGBX",
        "MIGKX",
        "MIGMX",
        "MIRGX",
    ):
        assert set(LOOKBACK_YEARS) <= _lookback_years(records, ticker), ticker
    mfegx_midyear = next(
        row
        for row in records
        if row.ticker == "MFEGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-07-31"
        and row.amount
    )
    assert mfegx_midyear.amount == Decimal("4.12961")
    mfegx_ye = next(
        row
        for row in records
        if row.ticker == "MFEGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-16"
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount == Decimal("25.35332")
    )
    assert mfegx_ye.amount == Decimal("25.35332")


def test_mass_z_leftover_walls_stay_unmatched() -> None:
    trowe = TRowePriceSource().fetch(mode="fixture").records
    pabgx_2024 = [
        row
        for row in trowe
        if row.ticker == "PABGX"
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount is not None
    ]
    assert pabgx_2024 == []

    columbia = ColumbiaThreadneedleSource().fetch(mode="fixture").records
    lbsax_2021 = [
        row
        for row in columbia
        if row.ticker == "LBSAX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount is not None
    ]
    assert lbsax_2021 == []

    hartford = HartfordSource().fetch(mode="fixture").records
    hdbax_2021 = [
        row
        for row in hartford
        if row.ticker == "HDBAX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount is not None
    ]
    assert hdbax_2021 == []
    ihoax_early = [
        row
        for row in hartford
        if row.ticker == "IHOAX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.amount is not None
    ]
    assert ihoax_early == []
    hdgix_hist = [
        row
        for row in hartford
        if row.ticker == "HDGIX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.amount is not None
    ]
    assert hdgix_hist == []

    mfs = MfsSource().fetch(mode="fixture").records
    for ticker, year in (("MEMBX", 2022), ("BRSPX", 2023), ("MNWTX", 2021)):
        rows = [
            row
            for row in mfs
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == year
            and row.amount is not None
        ]
        assert rows == [], (ticker, year)


def test_mass_z_leftover_tickers_are_in_book_only() -> None:
    leftover_tickers = {
        "PABGX",
        "RRBGX",
        "GSFTX",
        "SMGIX",
        "CPAZX",
        "MEGBX",
        "MIGBX",
        "HDBAX",
        "IHOAX",
        "HDGIX",
    }
    for source in (
        TRowePriceSource(),
        ColumbiaThreadneedleSource(),
        MfsSource(),
        HartfordSource(),
    ):
        records = source.fetch(mode="fixture").records
        family_tickers = {
            (row.ticker or "").strip().upper()
            for row in records
            if row.ticker and not row.ticker.startswith("ZZ")
        }
        overlap = leftover_tickers & family_tickers
        assert overlap, source.slug
        assert leftover_tickers.isdisjoint(
            {t for t in leftover_tickers if t.startswith("ZZ")}
        )


def test_mass_z_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("t_rowe_price", "columbia_threadneedle", "mfs", "hartford"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("PABGX", "GSFTX", "MEGBX", "HDBAX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    pabgx = client.get(
        "/distributions",
        params={"ticker": "PABGX", "publication_stage": "final", "page_size": 200},
    ).json()
    pabgx_2025 = [
        Decimal(row["amount"])
        for row in pabgx["items"]
        if row.get("ticker") == "PABGX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-11")
    ]
    assert Decimal("10.9575") in pabgx_2025
    pabgx_years = {
        str(row.get("ex_date") or "")[:4]
        for row in pabgx["items"]
        if row.get("ticker") == "PABGX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2025"} <= pabgx_years
    assert "2024" not in pabgx_years

    gsftx = client.get(
        "/distributions",
        params={"ticker": "GSFTX", "publication_stage": "final", "page_size": 200},
    ).json()
    gsftx_2021 = [
        Decimal(row["amount"])
        for row in gsftx["items"]
        if row.get("ticker") == "GSFTX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2021-12-14")
    ]
    assert Decimal("0.44721") in gsftx_2021
    gsftx_years = {
        str(row.get("ex_date") or "")[:4]
        for row in gsftx["items"]
        if row.get("ticker") == "GSFTX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= gsftx_years

    megbx = client.get(
        "/distributions",
        params={"ticker": "MEGBX", "publication_stage": "final", "page_size": 200},
    ).json()
    megbx_2022 = [
        Decimal(row["amount"])
        for row in megbx["items"]
        if row.get("ticker") == "MEGBX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2022-12-13")
    ]
    assert Decimal("1.39190") in megbx_2022


def test_parallel_x_fidelity_leftover_fills() -> None:
    records = FidelitySource().fetch(mode="fixture").records
    ftrix_2021_oi = next(
        row
        for row in records
        if row.ticker == "FTRIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-06-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert ftrix_2021_oi.amount == Decimal("0.29")
    ftrix_2021_cg = next(
        row
        for row in records
        if row.ticker == "FTRIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-06-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert ftrix_2021_cg.amount == Decimal("1.00")
    ftrix_2022_mid_lt = next(
        row
        for row in records
        if row.ticker == "FTRIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-08-05"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert ftrix_2022_mid_lt.amount == Decimal("0.45700")
    ftrix_2022_ye_lt = next(
        row
        for row in records
        if row.ticker == "FTRIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-12-09"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert ftrix_2022_ye_lt.amount == Decimal("0.05600")
    eqpgx_2022_lt = next(
        row
        for row in records
        if row.ticker == "EQPGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-12-27"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert eqpgx_2022_lt.amount == Decimal("0.28700")
    eqpgx_2024_lt = next(
        row
        for row in records
        if row.ticker == "EQPGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-26"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert eqpgx_2024_lt.amount == Decimal("2.48300")
    ftrix_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "FTRIX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    ftrix_years.discard(None)
    assert set(LOOKBACK_YEARS) <= ftrix_years
    eqpgx_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "EQPGX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    eqpgx_years.discard(None)
    # WAVE X left EQPGX at 4y (2021 DPL2 Class A name-only). WAVE AO
    # fills Class I December 2021 N-CSR CG $2.262 (pay 12/29/2021).
    assert set(LOOKBACK_YEARS) <= eqpgx_years


def test_parallel_x_aci_leftover_fills() -> None:
    records = AmericanCenturySource().fetch(mode="fixture").records
    afdix_2021_oi = next(
        row
        for row in records
        if row.ticker == "AFDIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert afdix_2021_oi.amount == Decimal("0.16")
    twcix_2025_cg = next(
        row
        for row in records
        if row.ticker == "TWCIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2025-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert twcix_2025_cg.amount == Decimal("4.47")
    twcux_2022_cg = next(
        row
        for row in records
        if row.ticker == "TWCUX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2022-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert twcux_2022_cg.amount == Decimal("5.94")
    for ticker in ("TWCGX", "AFDIX", "TWCIX", "TWCUX"):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert set(LOOKBACK_YEARS) <= years, ticker
    twhix_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "TWHIX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    twhix_years.discard(None)
    assert twhix_years == {2021, 2022, 2024, 2025}
    anoix_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "ANOIX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    anoix_years.discard(None)
    assert anoix_years == {2021, 2022, 2025}


def test_parallel_x_jpm_leftover_fills() -> None:
    records = JPMorganSource().fetch(mode="fixture").records
    oieix_2023_oi = next(
        row
        for row in records
        if row.ticker == "OIEIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-06-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert oieix_2023_oi.amount == Decimal("0.42")
    seegx_2023_cg = next(
        row
        for row in records
        if row.ticker == "SEEGX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2023-06-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert seegx_2023_cg.amount == Decimal("1.35")
    jlgmx_2021_cg = next(
        row
        for row in records
        if row.ticker == "JLGMX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-06-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert jlgmx_2021_cg.amount == Decimal("3.14")
    for ticker in (
        "OIEIX",
        "SEEGX",
        "JLGMX",
        "JICAX",
        "OGEAX",
        "VSCOX",
        "JAMCX",
        "JCMAX",
        "JDEAX",
        "JIGAX",
        "JLCAX",
        "JTUAX",
        "JUEAX",
        "JVAAX",
        "OLVAX",
        "OSGIX",
        "PECAX",
        "PSOAX",
        "VGRIX",
        "VHIAX",
        "VSEAX",
    ):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert set(LOOKBACK_YEARS) <= years, ticker
    pgsgx_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "PGSGX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    pgsgx_years.discard(None)
    assert pgsgx_years == {2021, 2022, 2023, 2025}


def test_parallel_x_gs_leftover_fills() -> None:
    records = GoldmanSachsSource().fetch(mode="fixture").records
    glcgx_2021_cg = next(
        row
        for row in records
        if row.ticker == "GLCGX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert glcgx_2021_cg.amount == Decimal("3.80")
    gcgix_2021_oi = next(
        row
        for row in records
        if row.ticker == "GCGIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gcgix_2021_oi.amount == Decimal("0.11")
    gcgix_2024_cg = next(
        row
        for row in records
        if row.ticker == "GCGIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2024-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gcgix_2024_cg.amount == Decimal("1.94")
    for ticker in ("GLCGX", "GCGIX"):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert set(LOOKBACK_YEARS) <= years, ticker
    # Class-level — 2021 Class A income stayed dashed; Institutional is not copied.
    glcgx_2021_oi = [
        row
        for row in records
        if row.ticker == "GLCGX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-10-31"
        and row.amount is not None
    ]
    assert glcgx_2021_oi == []


def test_parallel_x_leftover_walls_stay_unmatched() -> None:
    fidelity = FidelitySource().fetch(mode="fixture").records
    fbgrx_mid = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in fidelity
        if row.ticker == "FBGRX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    fbgrx_mid.discard(None)
    assert 2022 not in fbgrx_mid
    assert 2023 not in fbgrx_mid
    eqpgx_2021 = [
        row
        for row in fidelity
        if row.ticker == "EQPGX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert eqpgx_2021 == []

    jpm = JPMorganSource().fetch(mode="fixture").records
    jepq_2021 = [
        row
        for row in jpm
        if row.ticker == "JEPQ"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert jepq_2021 == []
    ubvax_early = [
        row
        for row in jpm
        if row.ticker == "UBVAX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) in {2021, 2022, 2023}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert ubvax_early == []
    pgsgx_2024 = [
        row
        for row in jpm
        if row.ticker == "PGSGX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2024
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert pgsgx_2024 == []

    aci = AmericanCenturySource().fetch(mode="fixture").records
    twhix_2023 = [
        row
        for row in aci
        if row.ticker == "TWHIX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2023
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert twhix_2023 == []
    anoix_mid = [
        row
        for row in aci
        if row.ticker == "ANOIX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) in {2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert anoix_mid == []


def test_parallel_x_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("fidelity", "american_century", "jpmorgan", "goldman_sachs"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in (
        "FTRIX",
        "EQPGX",
        "TWCGX",
        "AFDIX",
        "OIEIX",
        "SEEGX",
        "GLCGX",
        "GCGIX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    ftrix = client.get(
        "/distributions",
        params={"ticker": "FTRIX", "publication_stage": "final", "page_size": 200},
    ).json()
    ftrix_2021 = [
        Decimal(row["amount"])
        for row in ftrix["items"]
        if row.get("ticker") == "FTRIX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("as_of") or "").startswith("2021-06-30")
    ]
    assert Decimal("0.29") in ftrix_2021
    ftrix_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in ftrix["items"]
        if row.get("ticker") == "FTRIX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= ftrix_years

    twcgx = client.get(
        "/distributions",
        params={"ticker": "TWCGX", "publication_stage": "final", "page_size": 200},
    ).json()
    twcgx_2021 = [
        Decimal(row["amount"])
        for row in twcgx["items"]
        if row.get("ticker") == "TWCGX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2021-10-31")
    ]
    assert Decimal("1.56") in twcgx_2021

    oieix = client.get(
        "/distributions",
        params={"ticker": "OIEIX", "publication_stage": "final", "page_size": 200},
    ).json()
    oieix_2023 = [
        Decimal(row["amount"])
        for row in oieix["items"]
        if row.get("ticker") == "OIEIX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("as_of") or "").startswith("2023-06-30")
    ]
    assert Decimal("0.42") in oieix_2023

    glcgx = client.get(
        "/distributions",
        params={"ticker": "GLCGX", "publication_stage": "final", "page_size": 200},
    ).json()
    glcgx_2021 = [
        Decimal(row["amount"])
        for row in glcgx["items"]
        if row.get("ticker") == "GLCGX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2021-10-31")
    ]
    assert Decimal("3.80") in glcgx_2021


def test_parallel_af_harbor_leftover_fills() -> None:
    records = HarborSource().fetch(mode="fixture").records
    hacax_2021_lt = next(
        row
        for row in records
        if row.ticker == "HACAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-19"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert hacax_2021_lt.amount == Decimal("18.78540")
    hacax_2024_lt = next(
        row
        for row in records
        if row.ticker == "HACAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-19"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert hacax_2024_lt.amount == Decimal("12.36068")
    hacax_2025_lt = next(
        row
        for row in records
        if row.ticker == "HACAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-10"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert hacax_2025_lt.amount == Decimal("13.12011")
    hacax_2022_zero = next(
        row
        for row in records
        if row.ticker == "HACAX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-12-18"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hacax_2022_zero.amount == Decimal("0.00000")
    havlx_2025_lt = next(
        row
        for row in records
        if row.ticker == "HAVLX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-18"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert havlx_2025_lt.amount == Decimal("3.88137")
    for ticker in (
        "HACAX",
        "HAVLX",
        "HASCX",
        "HAIDX",
        "HAISX",
        "HAMVX",
        "HAOSX",
        "HMCLX",
    ):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_parallel_af_calamos_caisx_2024_zero() -> None:
    records = CalamosSource().fetch(mode="fixture").records
    caisx_2024 = next(
        row
        for row in records
        if row.ticker == "CAISX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2024-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert caisx_2024.amount == Decimal("0.0000")
    years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "CAISX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    years.discard(None)
    assert {2022, 2023, 2024, 2025} <= years
    assert 2021 not in years


def test_parallel_af_leftover_walls_stay_unmatched() -> None:
    harbor = HarborSource().fetch(mode="fixture").records
    hsicx_early = [
        row
        for row in harbor
        if row.ticker == "HSICX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) in {2021, 2022, 2023}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert hsicx_early == []
    # Investor sibling is not copied from leftover Institutional HACAX.
    hcaix = [
        row
        for row in harbor
        if row.ticker == "HCAIX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert hcaix == []

    calamos = CalamosSource().fetch(mode="fixture").records
    cmrax_early = [
        row
        for row in calamos
        if row.ticker == "CMRAX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) in {2021, 2022}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert cmrax_early == []

    virtus = VirtusSource().fetch(mode="fixture").records
    merfx_early = [
        row
        for row in virtus
        if row.ticker == "MERFX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert merfx_early == []
    stvtx_early = [
        row
        for row in virtus
        if row.ticker == "STVTX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023}
        and row.amount is not None
    ]
    assert stvtx_early == []

    # Transamerica / Neuberger have no registered leftover identities.
    slugs = {source.slug for source in list_sources()}
    assert "transamerica" not in slugs
    assert "neuberger" not in slugs
    assert "neuberger_berman" not in slugs


def test_parallel_af_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "harbor", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("HACAX", "HAVLX", "HASCX", "HAISX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    hacax = client.get(
        "/distributions",
        params={"ticker": "HACAX", "publication_stage": "final", "page_size": 200},
    ).json()
    hacax_2021 = [
        Decimal(row["amount"])
        for row in hacax["items"]
        if row.get("ticker") == "HACAX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2021-12-19")
    ]
    assert Decimal("18.78540") in hacax_2021
    hacax_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in hacax["items"]
        if row.get("ticker") == "HACAX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= hacax_years

    havlx = client.get(
        "/distributions",
        params={"ticker": "HAVLX", "publication_stage": "final", "page_size": 200},
    ).json()
    havlx_2025 = [
        Decimal(row["amount"])
        for row in havlx["items"]
        if row.get("ticker") == "HAVLX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-18")
    ]
    assert Decimal("3.88137") in havlx_2025


def test_parallel_ad_macquarie_leftover_ncsr_2021_fills_5y() -> None:
    records = MacquarieSource().fetch(mode="fixture").records
    dccax_2021_cg = next(
        row
        for row in records
        if row.ticker == "DCCAX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-11-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert dccax_2021_cg.amount == Decimal("0.19")
    devlx_2021_oi = next(
        row
        for row in records
        if row.ticker == "DEVLX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-11-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert devlx_2021_oi.amount == Decimal("0.41")
    ddvax_2021_oi = next(
        row
        for row in records
        if row.ticker == "DDVAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-11-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert ddvax_2021_oi.amount == Decimal("0.35")
    fginx_2021_cg = next(
        row
        for row in records
        if row.ticker == "FGINX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-09-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert fginx_2021_cg.amount == Decimal("0.70")
    for ticker in ("DCCAX", "DEVLX", "DDIAX", "DDVAX", "DLHAX", "FGINX", "FIUSX"):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert set(LOOKBACK_YEARS) <= years, ticker
    # Ivy leftover Class A 2021 N-CSR tables stay unmatched this slice.
    wstax_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "WSTAX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    wstax_years.discard(None)
    assert wstax_years == {2022, 2023, 2024, 2025}


def test_parallel_ad_ab_chclx_ncsr_2022_is_year_depth() -> None:
    records = AllianceBernsteinSource().fetch(mode="fixture").records
    chclx_2022_cg = next(
        row
        for row in records
        if row.ticker == "CHCLX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2022-07-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert chclx_2022_cg.amount == Decimal("2.32")
    chclx_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "CHCLX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    chclx_years.discard(None)
    assert chclx_years == {2021, 2022, 2025}


def test_parallel_ad_eoi_ncsr_fills_5y() -> None:
    records = EatonVanceSource().fetch(mode="fixture").records
    eoi_2021_oi = next(
        row
        for row in records
        if row.ticker == "EOI"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-09-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert eoi_2021_oi.amount == Decimal("0.075")
    eoi_2021_roc = next(
        row
        for row in records
        if row.ticker == "EOI"
        and row.estimate_type == EstimateType.return_of_capital
        and row.as_of
        and str(row.as_of) == "2021-09-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert eoi_2021_roc.amount == Decimal("0.034")
    eoi_2025_cg = next(
        row
        for row in records
        if row.ticker == "EOI"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2025-09-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert eoi_2025_cg.amount == Decimal("1.61")
    eoi_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "EOI"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    eoi_years.discard(None)
    assert set(LOOKBACK_YEARS) <= eoi_years
    # Existing March 2025 19(b) estimate stays estimate-stage.
    eoi_19b = next(
        row
        for row in records
        if row.ticker == "EOI"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2025-03-31"
        and row.amount
    )
    assert eoi_19b.amount == Decimal("0.1338")
    assert eoi_19b.publication_stage != PublicationStage.final


def test_parallel_ad_leftover_walls_stay_unmatched() -> None:
    macquarie = MacquarieSource().fetch(mode="fixture").records
    for ticker in ("WSTAX", "WASAX", "IRSAX", "WLGAX", "WMGAX", "WSGAX", "WCEAX"):
        rows_2021 = [
            row
            for row in macquarie
            if row.ticker == ticker
            and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert rows_2021 == [], f"{ticker} 2021 should stay unmatched"

    ab = AllianceBernsteinSource().fetch(mode="fixture").records
    for year in (2023, 2024):
        chclx = [
            row
            for row in ab
            if row.ticker == "CHCLX"
            and _year_for_row(row.as_of, row.ex_date, row.payable_date) == year
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert chclx == [], f"CHCLX {year} should stay unmatched"

    msim = MorganStanleySource().fetch(mode="fixture").records
    for ticker in ("CVLC", "CDEI", "EVIM"):
        early = [
            row
            for row in msim
            if row.ticker == ticker
            and _year_for_row(row.as_of, row.ex_date, row.payable_date) in {2021, 2022, 2023}
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert early == [], f"{ticker} 2021–2023 should stay unmatched"

    # PGIM / Prudential is not an in-book family — no new identities.
    slugs = {source.slug for source in list_sources()}
    assert "pgim" not in slugs
    assert "prudential" not in slugs


def test_parallel_ad_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("macquarie", "ab", "eaton_vance"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("DCCAX", "DEVLX", "DDVAX", "FGINX", "CHCLX", "EOI"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    dccax = client.get(
        "/distributions",
        params={"ticker": "DCCAX", "publication_stage": "final", "page_size": 200},
    ).json()
    dccax_2021 = [
        Decimal(row["amount"])
        for row in dccax["items"]
        if row.get("ticker") == "DCCAX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2021-11-30")
    ]
    assert Decimal("0.19") in dccax_2021

    eoi = client.get(
        "/distributions",
        params={"ticker": "EOI", "publication_stage": "final", "page_size": 200},
    ).json()
    eoi_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in eoi["items"]
        if row.get("ticker") == "EOI" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= eoi_years


def test_wave_ae_invesco_etf_leftover_ici_fills_5y() -> None:
    records = InvescoSource().fetch(mode="fixture").records
    pin_2021_lt = next(
        row
        for row in records
        if row.ticker == "PIN"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert pin_2021_lt.amount == Decimal("1.31763")
    assert str(pin_2021_lt.ex_date) == "2021-12-20"
    assert pin_2021_lt.publication_stage == PublicationStage.final
    pin_2022_lt = next(
        row
        for row in records
        if row.ticker == "PIN"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount
    )
    assert pin_2022_lt.amount == Decimal("2.99469")
    idmo_2021 = next(
        row
        for row in records
        if row.ticker == "IDMO"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert idmo_2021.amount == Decimal("0.218")
    ivra_2021_st = next(
        row
        for row in records
        if row.ticker == "IVRA"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert ivra_2021_st.amount == Decimal("0.36875")
    pbp_2021_st = next(
        row
        for row in records
        if row.ticker == "PBP"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert pbp_2021_st.amount == Decimal("1.24053")
    psci_2021 = next(
        row
        for row in records
        if row.ticker == "PSCI"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    )
    assert psci_2021.amount == Decimal("0.18503")
    for ticker in ("PIN", "PSCI", "IDMO", "IVRA", "PBP"):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_wave_ae_leftover_walls_stay_unmatched() -> None:
    ssga = StateStreetSource().fetch(mode="fixture").records
    hybl_2021 = [
        row
        for row in ssga
        if row.ticker == "HYBL"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert hybl_2021 == []
    spdg_early = [
        row
        for row in ssga
        if row.ticker == "SPDG"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) in {2021, 2022}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert spdg_early == []

    first_trust = FirstTrustSource().fetch(mode="fixture").records
    for ticker, year in (("FNY", 2021), ("ARVR", 2021), ("CRPT", 2023)):
        rows = [
            row
            for row in first_trust
            if row.ticker == ticker
            and _year_for_row(row.as_of, row.ex_date, row.payable_date) == year
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert rows == [], f"{ticker} {year} should stay unmatched"

    wisdomtree = WisdomtreeSource().fetch(mode="fixture").records
    cew_2023 = [
        row
        for row in wisdomtree
        if row.ticker == "CEW"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2023
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert cew_2023 == []
    aivi_2021 = [
        row
        for row in wisdomtree
        if row.ticker == "AIVI"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert aivi_2021 == []

    invesco = InvescoSource().fetch(mode="fixture").records
    vafax_early = [
        row
        for row in invesco
        if row.ticker == "VAFAX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022}
        and row.amount is not None
    ]
    assert vafax_early == []
    hiys_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in invesco
        if row.ticker == "HIYS"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    hiys_years.discard(None)
    assert hiys_years == {2023, 2024, 2025}
    bsjw_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in invesco
        if row.ticker == "BSJW"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    bsjw_years.discard(None)
    assert bsjw_years == {2024, 2025}


def test_wave_ae_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "invesco", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("PIN", "PSCI", "IDMO", "IVRA", "PBP"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    pin = client.get(
        "/distributions",
        params={"ticker": "PIN", "publication_stage": "final", "page_size": 200},
    ).json()
    pin_2021 = [
        Decimal(row["amount"])
        for row in pin["items"]
        if row.get("ticker") == "PIN"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2021-12-20")
    ]
    assert Decimal("1.31763") in pin_2021
    pin_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in pin["items"]
        if row.get("ticker") == "PIN" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= pin_years

    idmo = client.get(
        "/distributions",
        params={"ticker": "IDMO", "publication_stage": "final", "page_size": 200},
    ).json()
    idmo_2021 = [
        Decimal(row["amount"])
        for row in idmo["items"]
        if row.get("ticker") == "IDMO"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2021-12-20")
    ]
    assert Decimal("0.218") in idmo_2021

def test_wave_ag_victory_leftover_rs_2021() -> None:
    records = VictorySource().fetch(mode="fixture").records
    rsgrx_2021_oi = next(
        row
        for row in records
        if row.ticker == "RSGRX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert rsgrx_2021_oi.amount == Decimal("0.02")
    rsgrx_2021_cg = next(
        row
        for row in records
        if row.ticker == "RSGRX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert rsgrx_2021_cg.amount == Decimal("2.35")
    gpafx_2021_oi = next(
        row
        for row in records
        if row.ticker == "GPAFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.amount
    )
    assert gpafx_2021_oi.amount == Decimal("0.57")
    rspyx_2021_oi = next(
        row
        for row in records
        if row.ticker == "RSPYX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.amount
    )
    assert rspyx_2021_oi.amount == Decimal("0.05")
    rsvax_2021_oi = next(
        row
        for row in records
        if row.ticker == "RSVAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.amount
    )
    assert rsvax_2021_oi.amount == Decimal("0.11")
    for ticker in (
        "RSGRX",
        "RGWCX",
        "RGRYX",
        "RSINX",
        "RIVCX",
        "RSIYX",
        "GPAFX",
        "RCOCX",
        "RCEYX",
        "RSPFX",
        "RSPMX",
        "RSPKX",
        "RSPYX",
        "RSVAX",
        "RVACX",
        "RSVYX",
    ):
        years = {
            _year_for_row(row.as_of, row.ex_date, row.payable_date)
            for row in records
            if row.ticker == ticker
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        years.discard(None)
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_wave_ag_victory_leftover_2024_r_member_r6() -> None:
    records = VictorySource().fetch(mode="fixture").records
    getgx_2024 = next(
        row
        for row in records
        if row.ticker == "GETGX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-13"
        and row.amount
    )
    assert getgx_2024.amount == Decimal("0.130481")
    gogfx_2024_lt = next(
        row
        for row in records
        if row.ticker == "GOGFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-13"
        and row.amount
    )
    assert gogfx_2024_lt.amount == Decimal("3.571324")
    grinx_2024_oi = next(
        row
        for row in records
        if row.ticker == "GRINX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-13"
        and row.amount is not None
    )
    assert grinx_2024_oi.amount == Decimal("0.000000")
    getgx_years = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in records
        if row.ticker == "GETGX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    getgx_years.discard(None)
    assert {2022, 2023, 2024, 2025} <= getgx_years
    assert 2021 not in getgx_years


def test_wave_ag_leftover_walls_stay_unmatched() -> None:
    victory = VictorySource().fetch(mode="fixture").records
    usspx_2021 = [
        row
        for row in victory
        if row.ticker == "USSPX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert usspx_2021 == []
    mmeax_2021 = [
        row
        for row in victory
        if row.ticker == "MMEAX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert mmeax_2021 == []

    touchstone = TouchstoneSource().fetch(mode="fixture").records
    tegix_2023 = [
        row
        for row in touchstone
        if row.ticker == "TEGIX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2023
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert tegix_2023 == []

    franklin = FranklinTempletonSource().fetch(mode="fixture").records
    pim_early = [
        row
        for row in franklin
        if row.ticker == "PIM"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert pim_early == []

    fidelity = FidelitySource().fetch(mode="fixture").records
    fbgrx_mid = {
        _year_for_row(row.as_of, row.ex_date, row.payable_date)
        for row in fidelity
        if row.ticker == "FBGRX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    fbgrx_mid.discard(None)
    assert 2022 not in fbgrx_mid
    assert 2023 not in fbgrx_mid


def test_wave_ag_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "victory", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("RSGRX", "GPAFX", "RSPYX", "RSVAX", "GETGX", "GOGFX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    rsgrx = client.get(
        "/distributions",
        params={"ticker": "RSGRX", "publication_stage": "final", "page_size": 200},
    ).json()
    rsgrx_2021 = [
        Decimal(row["amount"])
        for row in rsgrx["items"]
        if row.get("ticker") == "RSGRX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2021-12-31")
    ]
    assert Decimal("2.35") in rsgrx_2021
    rsgrx_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in rsgrx["items"]
        if row.get("ticker") == "RSGRX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= rsgrx_years

    getgx = client.get(
        "/distributions",
        params={"ticker": "GETGX", "publication_stage": "final", "page_size": 200},
    ).json()
    getgx_2024 = [
        Decimal(row["amount"])
        for row in getgx["items"]
        if row.get("ticker") == "GETGX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2024-12-13")
    ]
    assert Decimal("0.130481") in getgx_2024


def test_wave_ah_bny_leftover_paid_fills_5y() -> None:
    records = BnyMellonSource().fetch(mode="fixture").records
    dmcvx_2025_lt = next(
        row
        for row in records
        if row.ticker == "DMCVX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-10"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert dmcvx_2025_lt.amount == Decimal("3.8546")
    dmcvx_2025_oi = next(
        row
        for row in records
        if row.ticker == "DMCVX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-10"
        and row.amount
    )
    assert dmcvx_2025_oi.amount == Decimal("0.1850")
    miblx_2025_oi = next(
        row
        for row in records
        if row.ticker == "MIBLX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-31"
        and row.amount
    )
    assert miblx_2025_oi.amount == Decimal("0.3130")
    mimsx_2025_lt = next(
        row
        for row in records
        if row.ticker == "MIMSX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-16"
        and row.amount
    )
    assert mimsx_2025_lt.amount == Decimal("12.5997")
    miscx_2025_oi = next(
        row
        for row in records
        if row.ticker == "MISCX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-17"
        and row.amount
    )
    assert miscx_2025_oi.amount == Decimal("0.0561")
    for ticker in ("DMCVX", "MIBLX", "MIMSX", "MISCX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker
    for sibling in ("DVLIX", "DMCYX", "MPBLX", "MPMCX", "MPSSX"):
        sibling_rows = [row for row in records if row.ticker == sibling]
        assert sibling_rows == [], sibling


def test_wave_ah_leftover_walls_stay_unmatched() -> None:
    vaneck = VaneckSource().fetch(mode="fixture").records
    for ticker, year in (
        ("AFK", 2024),
        ("VNM", 2024),
        ("REMX", 2023),
        ("GLIN", 2021),
        ("GMET", 2021),
        ("INIVX", 2022),
        ("MOTE", 2025),
        ("GHACX", 2025),
    ):
        rows = [
            row
            for row in vaneck
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == year
            and row.amount is not None
        ]
        assert rows == [], f"{ticker} {year}"

    royce = RoyceSource().fetch(mode="fixture").records
    for ticker in ("RVPHX", "RVPIX", "RYVPX"):
        y2023 = [
            row
            for row in royce
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == 2023
            and row.amount is not None
        ]
        assert y2023 == [], ticker

    brown = BrownAdvisorySource().fetch(mode="fixture").records
    baffx_paid = [
        row
        for row in brown
        if row.ticker == "BAFFX"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert baffx_paid == []

    ark = ArkSource().fetch(mode="fixture").records
    arkk_later = [
        row
        for row in ark
        if row.ticker == "ARKK"
        and row.ex_date
        and row.ex_date.year in {2022, 2023, 2024, 2025}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert arkk_later == []

    bny = BnyMellonSource().fetch(mode="fixture").records
    dtgrx_mid = [
        row
        for row in bny
        if row.ticker == "DTGRX"
        and row.ex_date
        and row.ex_date.year in {2022, 2023}
        and row.amount is not None
    ]
    assert dtgrx_mid == []


def test_wave_ah_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("bny_mellon", "vaneck", "royce", "brown_advisory"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("DMCVX", "MIBLX", "MIMSX", "MISCX", "AFK", "RVPHX", "BAFFX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    dmcvx = client.get(
        "/distributions",
        params={"ticker": "DMCVX", "publication_stage": "final", "page_size": 200},
    ).json()
    dmcvx_2025 = [
        Decimal(row["amount"])
        for row in dmcvx["items"]
        if row.get("ticker") == "DMCVX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-12-10")
    ]
    assert Decimal("3.8546") in dmcvx_2025
    dmcvx_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in dmcvx["items"]
        if row.get("ticker") == "DMCVX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= dmcvx_years


def test_wave_aj_value_line_leftover_paid_fills_5y() -> None:
    records = ValueLineSource().fetch(mode="fixture").records
    vleox_2021 = next(
        row
        for row in records
        if row.ticker == "VLEOX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-14"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert vleox_2021.amount == Decimal("3.27482")
    vleox_2024 = next(
        row
        for row in records
        if row.ticker == "VLEOX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-18"
        and row.amount
    )
    assert vleox_2024.amount == Decimal("0.05432")
    vlaax_2022_oi = next(
        row
        for row in records
        if row.ticker == "VLAAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2022-12-14"
        and row.amount
    )
    assert vlaax_2022_oi.amount == Decimal("0.32727")
    vlaax_2022_cg = [
        row
        for row in records
        if row.ticker == "VLAAX"
        and row.estimate_type
        in {EstimateType.short_term_capital_gains, EstimateType.long_term_capital_gains}
        and row.ex_date
        and row.ex_date.year == 2022
        and row.amount is not None
    ]
    assert vlaax_2022_cg == []
    for ticker in (
        "VLEOX",
        "VLEIX",
        "VLIFX",
        "VLMIX",
        "VALSX",
        "VILSX",
        "VLAAX",
        "VLAIX",
        "VALIX",
        "VLIIX",
    ):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker
    for ticker in ("VALLX", "VLLIX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert years == {2021, 2022, 2024, 2025}, ticker


def test_wave_aj_permanent_portfolio_leftover_paid_fills_5y() -> None:
    records = PermanentPortfolioSource().fetch(mode="fixture").records
    prpfx_2021_lt = next(
        row
        for row in records
        if row.ticker == "PRPFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-08"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert prpfx_2021_lt.amount == Decimal("0.82485")
    prpfx_2021_oi = next(
        row
        for row in records
        if row.ticker == "PRPFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2021-12-08"
        and row.amount
    )
    assert prpfx_2021_oi.amount == Decimal("0.18070")
    pagrx_2021_st = next(
        row
        for row in records
        if row.ticker == "PAGRX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-08"
        and row.amount
    )
    assert pagrx_2021_st.amount == Decimal("4.34332")
    for ticker in ("PRPFX", "PRVBX", "PAGRX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker
    assert [row for row in records if row.ticker == "PRTBX"] == []


def test_wave_aj_kopernik_leftover_paid_fills_5y() -> None:
    records = KopernikSource().fetch(mode="fixture").records
    kggix_2021_oi = next(
        row
        for row in records
        if row.ticker == "KGGIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2021-12-30"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert kggix_2021_oi.amount == Decimal("0.7679")
    kggix_2021_st = next(
        row
        for row in records
        if row.ticker == "KGGIX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2021-12-22"
        and row.amount
    )
    assert kggix_2021_st.amount == Decimal("0.4856")
    kggix_2024_lt = next(
        row
        for row in records
        if row.ticker == "KGGIX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-20"
        and row.amount
    )
    assert kggix_2024_lt.amount == Decimal("0.1144")
    kggix_2024_st = [
        row
        for row in records
        if row.ticker == "KGGIX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
        and row.amount is not None
    ]
    assert kggix_2024_st == []
    for ticker in ("KGGIX", "KGGAX", "KGIIX", "KGIRX"):
        years = {
            row.ex_date.year
            for row in records
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        }
        assert set(LOOKBACK_YEARS) <= years, ticker


def test_wave_aj_tocqueville_leftover_paid_fills_5y() -> None:
    records = TocquevilleSource().fetch(mode="fixture").records
    tocqx_2024_lt = next(
        row
        for row in records
        if row.ticker == "TOCQX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2024-12-06"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert tocqx_2024_lt.amount == Decimal("3.813")
    tocqx_2021_oi = next(
        row
        for row in records
        if row.ticker == "TOCQX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2021-12-10"
        and row.amount
    )
    assert tocqx_2021_oi.amount == Decimal("0.200")
    years = {
        row.ex_date.year
        for row in records
        if row.ticker == "TOCQX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert set(LOOKBACK_YEARS) <= years
    for sibling in ("TOPPX", "TOPHX"):
        assert [row for row in records if row.ticker == sibling] == []


def test_wave_aj_leftover_walls_stay_unmatched() -> None:
    value_line = ValueLineSource().fetch(mode="fixture").records
    for ticker in ("VALLX", "VLLIX"):
        y2023 = [
            row
            for row in value_line
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == 2023
            and row.amount is not None
        ]
        assert y2023 == [], ticker

    hartford = HartfordSource().fetch(mode="fixture").records
    hdbax_2021 = [
        row
        for row in hartford
        if row.ticker == "HDBAX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount is not None
    ]
    assert hdbax_2021 == []

    impax = ImpaxSource().fetch(mode="fixture").records
    for ticker in ("PXSAX", "PXSCX", "PXSIX"):
        y2023 = [
            row
            for row in impax
            if row.ticker == ticker
            and row.ex_date
            and row.ex_date.year == 2023
            and row.amount is not None
        ]
        assert y2023 == [], ticker


def test_wave_aj_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("value_line", "permanent_portfolio", "kopernik", "tocqueville"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("VLEOX", "VLAAX", "VALLX", "PRPFX", "KGGIX", "TOCQX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    vleox = client.get(
        "/distributions",
        params={"ticker": "VLEOX", "publication_stage": "final", "page_size": 200},
    ).json()
    vleox_2021 = [
        Decimal(row["amount"])
        for row in vleox["items"]
        if row.get("ticker") == "VLEOX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2021-12-14")
    ]
    assert Decimal("3.27482") in vleox_2021
    vleox_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in vleox["items"]
        if row.get("ticker") == "VLEOX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= vleox_years

def test_wave_ai_gabelli_leftover_ncsr_fills_5y() -> None:
    records = GabelliSource().fetch(mode="fixture").records
    gabax_2021_cg = next(
        row
        for row in records
        if row.ticker == "GABAX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gabax_2021_cg.amount == Decimal("5.53")
    gabax_2023_oi = next(
        row
        for row in records
        if row.ticker == "GABAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gabax_2023_oi.amount == Decimal("0.16")
    gabbx_2022_roc = next(
        row
        for row in records
        if row.ticker == "GABBX"
        and row.estimate_type == EstimateType.return_of_capital
        and row.as_of
        and str(row.as_of) == "2022-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gabbx_2022_roc.amount == Decimal("0.04")
    gicpx_2021_cg = next(
        row
        for row in records
        if row.ticker == "GICPX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gicpx_2021_cg.amount == Decimal("2.28")
    gabgx_2023_cg = next(
        row
        for row in records
        if row.ticker == "GABGX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2023-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert gabgx_2023_cg.amount == Decimal("1.45")

    for ticker in ("GABAX", "GABBX", "GICPX"):
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker
    assert _paid_lookback_years(records, "GABGX") == {2021, 2023, 2024, 2025}


def test_wave_ai_leftover_walls_stay_unmatched() -> None:
    gabelli = GabelliSource().fetch(mode="fixture").records
    gabgx_2022 = [
        row
        for row in gabelli
        if row.ticker == "GABGX"
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount is not None
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2022
    ]
    assert gabgx_2022 == []
    for ticker in ("GABSX", "GABEX"):
        years = _paid_lookback_years(gabelli, ticker)
        assert years == {2024, 2025}, ticker
    # Class-level AAA only — sibling A/C/I tickers stay out of the NAV book.
    for ticker in ("GATAX", "GATCX", "GABIX", "GGCAX"):
        assert [row for row in gabelli if row.ticker == ticker] == [], ticker

    federated = FederatedHermesSource().fetch(mode="fixture").records
    for ticker in ("KAUAX", "FKASX", "FKAIX"):
        years = _paid_lookback_years(federated, ticker)
        assert 2022 not in years, ticker
        assert {2021, 2023, 2024, 2025} <= years, ticker
    for ticker in ("QABGX", "QCBGX", "QIBGX"):
        years = _paid_lookback_years(federated, ticker)
        assert 2023 not in years, ticker
    for ticker in ("FHEQX", "FHESX"):
        years = _paid_lookback_years(federated, ticker)
        assert 2021 not in years, ticker

    allspring = AllspringSource().fetch(mode="fixture").records
    for ticker, missing in (
        ("ASPAX", 2021),
        ("EAAFX", 2023),
        ("EKJAX", 2022),
        ("WDSAX", 2021),
        ("WFDAX", 2023),
        ("WFSTX", 2023),
    ):
        years = _paid_lookback_years(allspring, ticker)
        assert missing not in years, ticker
        assert len(years) == 4, ticker

    sei = SeiSource().fetch(mode="fixture").records
    simt = [
        row
        for row in sei
        if row.fund_name == "SIMT Large Cap Growth"
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount is not None
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) in {2021, 2022, 2023, 2024}
    ]
    assert simt == []

    voya = VoyaSource().fetch(mode="fixture").records
    assert 2023 not in _paid_lookback_years(voya, "NLCAX")
    assert 2022 not in _paid_lookback_years(voya, "NMCAX")

    wasatch = WasatchSource().fetch(mode="fixture").records
    assert 2023 not in _paid_lookback_years(wasatch, "WGROX")

    causeway = CausewaySource().fetch(mode="fixture").records
    for ticker in ("CCENX", "CCEVX"):
        assert _paid_lookback_years(causeway, ticker) == {2021, 2022}


def test_wave_ai_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "gabelli", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("GABAX", "GABBX", "GICPX", "GABGX", "GABSX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    gabax = client.get(
        "/distributions",
        params={"ticker": "GABAX", "publication_stage": "final", "page_size": 200},
    ).json()
    gabax_2021 = [
        Decimal(row["amount"])
        for row in gabax["items"]
        if row.get("ticker") == "GABAX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2021-12-31")
    ]
    assert Decimal("5.53") in gabax_2021
    gabax_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in gabax["items"]
        if row.get("ticker") == "GABAX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= gabax_years

    gabgx = client.get(
        "/distributions",
        params={"ticker": "GABGX", "publication_stage": "final", "page_size": 200},
    ).json()
    gabgx_2022 = [
        row
        for row in gabgx["items"]
        if row.get("ticker") == "GABGX"
        and str(row.get("as_of") or row.get("ex_date") or "").startswith("2022")
        and row.get("amount") is not None
        and row.get("publication_stage") == "final"
    ]
    assert gabgx_2022 == []


def test_wave_ak_aci_leftover_sibling_ncsr_fills_5y() -> None:
    records = AmericanCenturySource().fetch(mode="fixture").records
    twgix_2021_cg = next(
        row
        for row in records
        if row.ticker == "TWGIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert twgix_2021_cg.amount == Decimal("1.56")
    twgix_2023_oi = next(
        row
        for row in records
        if row.ticker == "TWGIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert twgix_2023_oi.amount == Decimal("0.05")
    agywx_2023_oi = next(
        row
        for row in records
        if row.ticker == "AGYWX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert agywx_2023_oi.amount == Decimal("0.11")
    acihx_2022_cg = next(
        row
        for row in records
        if row.ticker == "ACIHX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2022-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert acihx_2022_cg.amount == Decimal("1.01")
    twbix_2021_oi = next(
        row
        for row in records
        if row.ticker == "TWBIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert twbix_2021_oi.amount == Decimal("0.17")
    twsix_2025_cg = next(
        row
        for row in records
        if row.ticker == "TWSIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2025-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert twsix_2025_cg.amount == Decimal("4.47")
    afeix_2025_cg = next(
        row
        for row in records
        if row.ticker == "AFEIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2025-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert afeix_2025_cg.amount == Decimal("3.22")
    for ticker in (
        "TCRAX",
        "TWRCX",
        "TWGIX",
        "AGWRX",
        "AGWUX",
        "AGRDX",
        "AGYWX",
        "TWCAX",
        "ACSLX",
        "TWSIX",
        "ASERX",
        "ASLGX",
        "ASDEX",
        "ASLWX",
        "TWUAX",
        "TWCCX",
        "TWUIX",
        "AULRX",
        "AULGX",
        "AULDX",
        "AULYX",
        "AULNX",
        "AFDAX",
        "AFEIX",
        "AFYDX",
        "AFDGX",
        "AFEDX",
        "AFEGX",
        "TWBIX",
        "ABINX",
        "ABGNX",
    ):
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker


def test_wave_ak_leftover_walls_stay_unmatched() -> None:
    aci = AmericanCenturySource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(aci, "ACIHX")
    assert _paid_lookback_years(aci, "ACIHX") == {2022, 2023, 2024, 2025}
    assert 2023 not in _paid_lookback_years(aci, "ATHIX")
    assert _paid_lookback_years(aci, "ATHIX") == {2021, 2022, 2024, 2025}
    assert 2021 not in _paid_lookback_years(aci, "AFDCX")
    assert 2021 not in _paid_lookback_years(aci, "AFDRX")
    assert _paid_lookback_years(aci, "ANOAX") == {2021, 2022}
    assert _paid_lookback_years(aci, "ASLDX") == {2024, 2025}
    # Class-level G stub — never copied from Investor 2022 CG $6.32.
    acihx_2022 = [
        row.amount
        for row in aci
        if row.ticker == "ACIHX"
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount is not None
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2022
    ]
    assert acihx_2022 == [Decimal("1.01")]

    janus = JanusHendersonSource().fetch(mode="fixture").records
    assert 2024 not in _paid_lookback_years(janus, "HFAAX")
    assert 2024 not in _paid_lookback_years(janus, "JEASX")
    assert 2025 not in _paid_lookback_years(janus, "JAGAX")

    principal = PrincipalSource().fetch(mode="fixture").records
    assert 2023 not in _paid_lookback_years(principal, "PBLCX")
    for ticker in ("PEAPX", "PRIAX"):
        assert 2024 not in _paid_lookback_years(principal, ticker), ticker

    nationwide = NationwideSource().fetch(mode="fixture").records
    for ticker in ("NWHOX", "NWHJX", "NTDAX"):
        assert 2024 not in _paid_lookback_years(nationwide, ticker), ticker

    thrivent = ThriventSource().fetch(mode="fixture").records
    assert 2022 not in _paid_lookback_years(thrivent, "TMAIX")

    ev = EatonVanceSource().fetch(mode="fixture").records
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(ev, "EOI")


def test_wave_ak_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "american_century", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("TWGIX", "TCRAX", "TWBIX", "TWSIX", "AFEIX", "ACIHX", "ATHIX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    twgix = client.get(
        "/distributions",
        params={"ticker": "TWGIX", "publication_stage": "final", "page_size": 200},
    ).json()
    twgix_2021 = [
        Decimal(row["amount"])
        for row in twgix["items"]
        if row.get("ticker") == "TWGIX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2021-10-31")
    ]
    assert Decimal("1.56") in twgix_2021
    twgix_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in twgix["items"]
        if row.get("ticker") == "TWGIX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= twgix_years

    acihx = client.get(
        "/distributions",
        params={"ticker": "ACIHX", "publication_stage": "final", "page_size": 200},
    ).json()
    acihx_2021 = [
        row
        for row in acihx["items"]
        if row.get("ticker") == "ACIHX"
        and str(row.get("as_of") or row.get("ex_date") or "").startswith("2021")
        and row.get("amount") is not None
        and row.get("publication_stage") == "final"
    ]
    assert acihx_2021 == []


WAVE_AL_TROWE_LEFTOVER_2024 = (
    "PABGX",
    "RRBGX",
    "PACLX",
    "PACOX",
    "PAFDX",
    "RRFDX",
    "PAGEX",
    "PAMCX",
    "RRMGX",
    "PAREX",
    "PASSX",
    "PASVX",
    "PAULX",
    "PAVLX",
    "PAWAX",
    "TADGX",
    "TAMVX",
    "RRMVX",
    "TQAAX",
    "TQSAX",
    "TQVAX",
    "TRSAX",
    "RRGSX",
    "PMEGX",
    "TPLGX",
    "TRSSX",
    "PAAOX",
    "PAFGX",
    "PAGLX",
    "PAIGX",
    "RRIGX",
    "PAIJX",
    "PAITX",
    "RRITX",
    "PRNCX",
    "IEMFX",
)


def test_wave_al_t_rowe_leftover_ncsr_fills_5y() -> None:
    records = TRowePriceSource().fetch(mode="fixture").records
    pabgx_2024_cg = next(
        row
        for row in records
        if row.ticker == "PABGX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2024-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert pabgx_2024_cg.amount == Decimal("16.42")
    rrbgx_2024_cg = next(
        row
        for row in records
        if row.ticker == "RRBGX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2024-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert rrbgx_2024_cg.amount == Decimal("16.15")
    paclx_2024_oi = next(
        row
        for row in records
        if row.ticker == "PACLX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2024-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert paclx_2024_oi.amount == Decimal("0.71")
    paclx_2024_cg = next(
        row
        for row in records
        if row.ticker == "PACLX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2024-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert paclx_2024_cg.amount == Decimal("2.79")
    pafdx_2024_oi = next(
        row
        for row in records
        if row.ticker == "PAFDX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2024-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert pafdx_2024_oi.amount == Decimal("0.63")
    pmegx_2024_cg = next(
        row
        for row in records
        if row.ticker == "PMEGX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2024-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert pmegx_2024_cg.amount == Decimal("8.52")
    iemfx_2024_oi = next(
        row
        for row in records
        if row.ticker == "IEMFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2024-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount
    )
    assert iemfx_2024_oi.amount == Decimal("0.60")
    # Class-level — never copied from Investor TRBCX 2024 YE LT $16.1515
    # or N-CSR Investor $16.91.
    trbcx_2024_ncsr = [
        row.amount
        for row in records
        if row.ticker == "TRBCX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2024-12-31"
        and row.amount is not None
    ]
    assert trbcx_2024_ncsr == []
    assert pabgx_2024_cg.amount != Decimal("16.91")
    assert pabgx_2024_cg.amount != Decimal("16.1515")
    for ticker in WAVE_AL_TROWE_LEFTOVER_2024:
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker


def test_wave_al_leftover_walls_stay_unmatched() -> None:
    trowe = TRowePriceSource().fetch(mode="fixture").records
    assert 2024 not in _paid_lookback_years(trowe, "RRCOX")
    assert {2021, 2022, 2023, 2025} <= _paid_lookback_years(trowe, "RRCOX")
    # Retirement leftovers stay 4y — May 31 FYE not calendar-safe and the
    # FAI 2024 Year-End all-class XLSX/PDF still unpublished.
    assert 2024 not in _paid_lookback_years(trowe, "PARIX")
    assert {2021, 2022, 2023, 2025} <= _paid_lookback_years(trowe, "PARIX")

    fidelity = FidelitySource().fetch(mode="fixture").records
    fbgrx_years = _paid_lookback_years(fidelity, "FBGRX")
    assert 2022 not in fbgrx_years
    assert 2023 not in fbgrx_years

    jpm = JPMorganSource().fetch(mode="fixture").records
    assert 2024 not in _paid_lookback_years(jpm, "PGSGX")
    assert 2021 not in _paid_lookback_years(jpm, "JEPQ")
    for ticker in ("JSEAX", "IUAEX", "JFAMX"):
        assert 2021 not in _paid_lookback_years(jpm, ticker), ticker

    gs = GoldmanSachsSource().fetch(mode="fixture").records
    for ticker in ("GLCGX", "GCGIX"):
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(gs, ticker), ticker


def test_wave_al_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "t_rowe_price", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("PABGX", "RRBGX", "PACLX", "PAFDX", "PMEGX", "IEMFX", "RRCOX", "PARIX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    pabgx = client.get(
        "/distributions",
        params={"ticker": "PABGX", "publication_stage": "final", "page_size": 200},
    ).json()
    pabgx_2024 = [
        Decimal(row["amount"])
        for row in pabgx["items"]
        if row.get("ticker") == "PABGX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2024-12-31")
    ]
    assert Decimal("16.42") in pabgx_2024
    pabgx_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in pabgx["items"]
        if row.get("ticker") == "PABGX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= pabgx_years

    rrcox = client.get(
        "/distributions",
        params={"ticker": "RRCOX", "publication_stage": "final", "page_size": 200},
    ).json()
    rrcox_2024 = [
        row
        for row in rrcox["items"]
        if row.get("ticker") == "RRCOX"
        and str(row.get("as_of") or row.get("ex_date") or "").startswith("2024")
        and row.get("amount") is not None
        and row.get("publication_stage") == "final"
    ]
    assert rrcox_2024 == []


WAVE_AM_COLUMBIA_LEFTOVER_5Y = (
    "UMLGX",
    "CSVFX",
    "CREEX",
    "CGEZX",
    "NSEPX",
    "CSCZX",
    "CBALX",
    "CBMZX",
    "CZMGX",
    "CREAX",
    "CRRVX",
    "CREYX",
)


def test_wave_am_columbia_leftover_official_zero_and_ncsr_fills_5y() -> None:
    records = ColumbiaThreadneedleSource().fetch(mode="fixture").records
    umlgx_2022_lt = next(
        row
        for row in records
        if row.ticker == "UMLGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2022-12-08"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert umlgx_2022_lt.amount == Decimal("0.00")
    cbalx_2023_lt = next(
        row
        for row in records
        if row.ticker == "CBALX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2023-12-08"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert cbalx_2023_lt.amount == Decimal("0.00")
    cbmzx_2025_lt = next(
        row
        for row in records
        if row.ticker == "CBMZX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2025-12-19"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert cbmzx_2025_lt.amount == Decimal("0.00")
    creax_2021_oi = next(
        row
        for row in records
        if row.ticker == "CREAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert creax_2021_oi.amount == Decimal("0.17")
    creax_2021_cg = next(
        row
        for row in records
        if row.ticker == "CREAX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert creax_2021_cg.amount == Decimal("0.84")
    crrvx_2021_cg = next(
        row
        for row in records
        if row.ticker == "CRRVX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert crrvx_2021_cg.amount == Decimal("0.84")
    creyx_2021_oi = next(
        row
        for row in records
        if row.ticker == "CREYX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert creyx_2021_oi.amount == Decimal("0.23")
    # Class-level — never sibling-copy Institutional CREEX 2021 onto leftover A / 2 / 3.
    creex_2021_ncsr = [
        row.amount
        for row in records
        if row.ticker == "CREEX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.amount is not None
    ]
    assert creex_2021_ncsr == []
    for ticker in WAVE_AM_COLUMBIA_LEFTOVER_5Y:
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker


def test_wave_am_leftover_walls_stay_unmatched() -> None:
    columbia = ColumbiaThreadneedleSource().fetch(mode="fixture").records
    # Class A / C / R 2021 $ still unpublished (Institutional-only YE PDF).
    lbsax_2021 = [
        row
        for row in columbia
        if row.ticker == "LBSAX"
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount is not None
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
    ]
    assert lbsax_2021 == []
    assert {2022, 2023, 2024, 2025} <= _paid_lookback_years(columbia, "LBSAX")

    hartford = HartfordSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(hartford, "HDBAX")
    # WAVE AN fills leftover I/C/F/R/Y + IHOAX 2021–2024 from Oct 31 N-CSR.
    # HDBAX 2021 stays unpublished / pre-inception on those books.

    mfs = MfsSource().fetch(mode="fixture").records
    assert 2022 not in _paid_lookback_years(mfs, "MEMBX")
    assert 2023 not in _paid_lookback_years(mfs, "BRSPX")
    assert 2023 not in _paid_lookback_years(mfs, "BRSHX")
    assert 2021 not in _paid_lookback_years(mfs, "MNWTX")
    assert 2021 not in _paid_lookback_years(mfs, "UIVIX")

    artisan = ArtisanSource().fetch(mode="fixture").records
    # WAVE AN fills Mid / Small / Focus / Discovery 2023 N-CSR OI.
    # APFDX / APDDX 2023 N-CSR dashes stay unmatched.
    assert 2023 not in _paid_lookback_years(artisan, "APFDX")
    assert 2023 not in _paid_lookback_years(artisan, "APDDX")

    dodge = DodgeCoxSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(dodge, "DOXGX")
    assert {2022, 2023, 2024, 2025} <= _paid_lookback_years(dodge, "DOXGX")

    oakmark = OakmarkSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(oakmark, "OAKCX")
    # Bond 2023 unpublished on Wayback YE HTML (Investor OAKCX and siblings).
    assert 2023 not in _paid_lookback_years(oakmark, "OAKCX")

    lord = LordAbbettSource().fetch(mode="fixture").records
    assert 2022 not in _paid_lookback_years(lord, "LAGWX")
    assert 2023 not in _paid_lookback_years(lord, "LAGWX")

    dfa = DimensionalSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(dfa, "DISVX")
    assert 2022 not in _paid_lookback_years(dfa, "DISVX")

    nuveen = NuveenSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(nuveen, "NSBRX")

    br = BlackRockSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(br, "MDEFX")

    # WAVE AL wall — do not redo T. Rowe Advisor/R/Inst leftovers.
    trowe = TRowePriceSource().fetch(mode="fixture").records
    assert 2024 not in _paid_lookback_years(trowe, "RRCOX")


def test_wave_am_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "columbia_threadneedle", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("UMLGX", "CREAX", "CRRVX", "CREYX", "CBALX", "CBMZX", "LBSAX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    umlgx = client.get(
        "/distributions",
        params={"ticker": "UMLGX", "publication_stage": "final", "page_size": 200},
    ).json()
    umlgx_2022 = [
        Decimal(row["amount"])
        for row in umlgx["items"]
        if row.get("ticker") == "UMLGX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2022-12-08")
    ]
    assert Decimal("0.00") in umlgx_2022
    umlgx_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in umlgx["items"]
        if row.get("ticker") == "UMLGX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= umlgx_years

    creax = client.get(
        "/distributions",
        params={"ticker": "CREAX", "publication_stage": "final", "page_size": 200},
    ).json()
    creax_2021 = [
        Decimal(row["amount"])
        for row in creax["items"]
        if row.get("ticker") == "CREAX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2021-12-31")
    ]
    assert Decimal("0.84") in creax_2021
    creax_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in creax["items"]
        if row.get("ticker") == "CREAX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= creax_years

    lbsax = client.get(
        "/distributions",
        params={"ticker": "LBSAX", "publication_stage": "final", "page_size": 200},
    ).json()
    lbsax_2021 = [
        row
        for row in lbsax["items"]
        if row.get("ticker") == "LBSAX"
        and str(row.get("as_of") or row.get("ex_date") or "").startswith("2021")
        and row.get("amount") is not None
        and row.get("publication_stage") == "final"
    ]
    assert lbsax_2021 == []


WAVE_AN_HARTFORD_LEFTOVER_5Y = (
    "HDGIX",
    "IHOAX",
    "HFMIX",
    "HGIIX",
    "ITHIX",
)

WAVE_AN_ARTISAN_LEFTOVER_5Y = (
    "ARTMX",
    "APDMX",
    "APHMX",
    "ARTSX",
    "APDSX",
    "APHSX",
    "ARTTX",
    "APDTX",
    "APHTX",
    "APHDX",
)


def test_wave_an_hartford_leftover_ncsr_fills_5y() -> None:
    records = HartfordSource().fetch(mode="fixture").records
    hdgix_2021_oi = next(
        row
        for row in records
        if row.ticker == "HDGIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hdgix_2021_oi.amount == Decimal("0.41")
    hdgix_2021_cg = next(
        row
        for row in records
        if row.ticker == "HDGIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hdgix_2021_cg.amount == Decimal("0.57")
    hdgix_2022_cg = next(
        row
        for row in records
        if row.ticker == "HDGIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2022-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hdgix_2022_cg.amount == Decimal("1.62")
    hdgix_2023_oi = next(
        row
        for row in records
        if row.ticker == "HDGIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hdgix_2023_oi.amount == Decimal("0.47")
    hdgix_2023_cg = next(
        row
        for row in records
        if row.ticker == "HDGIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2023-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hdgix_2023_cg.amount == Decimal("1.37")
    hdgix_2024_oi = next(
        row
        for row in records
        if row.ticker == "HDGIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2024-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hdgix_2024_oi.amount == Decimal("0.58")
    hdgix_2024_cg = next(
        row
        for row in records
        if row.ticker == "HDGIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2024-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hdgix_2024_cg.amount == Decimal("0.11")
    ihoax_2021_oi = next(
        row
        for row in records
        if row.ticker == "IHOAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert ihoax_2021_oi.amount == Decimal("0.07")
    ihoax_2022_oi = next(
        row
        for row in records
        if row.ticker == "IHOAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2022-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert ihoax_2022_oi.amount == Decimal("0.25")
    ihoax_2022_cg = next(
        row
        for row in records
        if row.ticker == "IHOAX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2022-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert ihoax_2022_cg.amount == Decimal("1.75")
    ihoax_2023_oi = next(
        row
        for row in records
        if row.ticker == "IHOAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert ihoax_2023_oi.amount == Decimal("0.09")
    ihoax_2024_oi = next(
        row
        for row in records
        if row.ticker == "IHOAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2024-10-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert ihoax_2024_oi.amount == Decimal("0.24")
    # Class-level — never sibling-copy Class A historical PDF onto HDGIX
    # (IHGIX 2023 calendar PDF is not HDGIX N-CSR $1.37).
    ihgix_2023_ncsr = [
        row.amount
        for row in records
        if row.ticker == "IHGIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2023-10-31"
        and row.amount is not None
    ]
    assert ihgix_2023_ncsr == []
    for ticker in WAVE_AN_HARTFORD_LEFTOVER_5Y:
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker


def test_wave_an_artisan_leftover_ncsr_fills_5y() -> None:
    records = ArtisanSource().fetch(mode="fixture").records
    artmx_2023 = next(
        row
        for row in records
        if row.ticker == "ARTMX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-09-30"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert artmx_2023.amount == Decimal("0.08")
    aphmx_2023 = next(
        row
        for row in records
        if row.ticker == "APHMX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-09-30"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert aphmx_2023.amount == Decimal("0.16")
    artsx_2023 = next(
        row
        for row in records
        if row.ticker == "ARTSX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-09-30"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert artsx_2023.amount == Decimal("0.08")
    arttx_2023 = next(
        row
        for row in records
        if row.ticker == "ARTTX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-09-30"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert arttx_2023.amount == Decimal("0.05")
    aphdX_2023 = next(
        row
        for row in records
        if row.ticker == "APHDX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2023-09-30"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert aphdX_2023.amount == Decimal("0.02")
    # Class-level — never sibling-copy Institutional APHMX onto Investor ARTMX.
    assert artmx_2023.amount != aphmx_2023.amount
    for ticker in WAVE_AN_ARTISAN_LEFTOVER_5Y:
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker


def test_wave_an_leftover_walls_stay_unmatched() -> None:
    hartford = HartfordSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(hartford, "HDBAX")
    assert {2022, 2023, 2024, 2025} <= _paid_lookback_years(hartford, "HDBAX")
    # Class Y leftovers whose N-CSR books omit Y — never copy Class I.
    assert 2021 not in _paid_lookback_years(hartford, "HBAIX")
    assert 2021 not in _paid_lookback_years(hartford, "HCKIX")
    assert _paid_lookback_years(hartford, "HBAIX") == {2025}
    assert _paid_lookback_years(hartford, "HCKIX") == {2025}

    mfs = MfsSource().fetch(mode="fixture").records
    assert 2022 not in _paid_lookback_years(mfs, "MEMBX")
    assert 2023 not in _paid_lookback_years(mfs, "BRSPX")
    assert 2023 not in _paid_lookback_years(mfs, "BRSHX")
    assert 2021 not in _paid_lookback_years(mfs, "MNWTX")
    assert 2021 not in _paid_lookback_years(mfs, "UIVIX")

    artisan = ArtisanSource().fetch(mode="fixture").records
    assert 2023 not in _paid_lookback_years(artisan, "APFDX")
    assert 2023 not in _paid_lookback_years(artisan, "APDDX")
    assert {2021, 2022, 2024, 2025} <= _paid_lookback_years(artisan, "APFDX")

    dodge = DodgeCoxSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(dodge, "DOXGX")
    assert {2022, 2023, 2024, 2025} <= _paid_lookback_years(dodge, "DOXGX")

    oakmark = OakmarkSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(oakmark, "OAKCX")
    assert 2023 not in _paid_lookback_years(oakmark, "OAKCX")

    lord = LordAbbettSource().fetch(mode="fixture").records
    assert 2022 not in _paid_lookback_years(lord, "LAGWX")
    assert 2023 not in _paid_lookback_years(lord, "LAGWX")

    # Do not redo WAVE AM Columbia leftover years / Class A 2021 wall.
    columbia = ColumbiaThreadneedleSource().fetch(mode="fixture").records
    lbsax_2021 = [
        row
        for row in columbia
        if row.ticker == "LBSAX"
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount is not None
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2021
    ]
    assert lbsax_2021 == []

    # WAVE AL wall — do not redo T. Rowe Advisor/R/Inst leftovers.
    trowe = TRowePriceSource().fetch(mode="fixture").records
    assert 2024 not in _paid_lookback_years(trowe, "RRCOX")


def test_wave_an_heroes_are_searchable(client: TestClient) -> None:
    for family in ("hartford", "artisan"):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": family, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in (
        "HDGIX",
        "IHOAX",
        "HFMIX",
        "HGIIX",
        "ARTMX",
        "ARTSX",
        "ARTTX",
        "APHDX",
        "HDBAX",
        "APFDX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    hdgix = client.get(
        "/distributions",
        params={"ticker": "HDGIX", "publication_stage": "final", "page_size": 200},
    ).json()
    hdgix_2023 = [
        Decimal(row["amount"])
        for row in hdgix["items"]
        if row.get("ticker") == "HDGIX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2023-10-31")
    ]
    assert Decimal("1.37") in hdgix_2023
    hdgix_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in hdgix["items"]
        if row.get("ticker") == "HDGIX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= hdgix_years

    ihoax = client.get(
        "/distributions",
        params={"ticker": "IHOAX", "publication_stage": "final", "page_size": 200},
    ).json()
    ihoax_2022 = [
        Decimal(row["amount"])
        for row in ihoax["items"]
        if row.get("ticker") == "IHOAX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2022-10-31")
    ]
    assert Decimal("1.75") in ihoax_2022
    ihoax_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in ihoax["items"]
        if row.get("ticker") == "IHOAX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= ihoax_years

    artmx = client.get(
        "/distributions",
        params={"ticker": "ARTMX", "publication_stage": "final", "page_size": 200},
    ).json()
    artmx_2023 = [
        Decimal(row["amount"])
        for row in artmx["items"]
        if row.get("ticker") == "ARTMX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("as_of") or "").startswith("2023-09-30")
    ]
    assert Decimal("0.08") in artmx_2023
    artmx_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in artmx["items"]
        if row.get("ticker") == "ARTMX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= artmx_years

    hdbax = client.get(
        "/distributions",
        params={"ticker": "HDBAX", "publication_stage": "final", "page_size": 200},
    ).json()
    hdbax_2021 = [
        row
        for row in hdbax["items"]
        if row.get("ticker") == "HDBAX"
        and str(row.get("as_of") or row.get("ex_date") or "").startswith("2021")
        and row.get("amount") is not None
        and row.get("publication_stage") == "final"
    ]
    assert hdbax_2021 == []

    apfdx = client.get(
        "/distributions",
        params={"ticker": "APFDX", "publication_stage": "final", "page_size": 200},
    ).json()
    apfdx_2023_ncsr = [
        row
        for row in apfdx["items"]
        if row.get("ticker") == "APFDX"
        and str(row.get("as_of") or "").startswith("2023-09-30")
        and row.get("amount") is not None
        and row.get("publication_stage") == "final"
    ]
    assert apfdx_2023_ncsr == []
    apfdx_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in apfdx["items"]
        if row.get("ticker") == "APFDX" and row.get("amount") is not None
    }
    assert "2023" not in apfdx_years


WAVE_AO_FIDELITY_LEFTOVER_5Y = (
    "FIXIX",
    "FOPIX",
    "FIADX",
    "FWIFX",
    "FVIFX",
    "FASOX",
    "EQPGX",
    "FSCIX",
    "FMCCX",
)


def test_wave_ao_fidelity_leftover_ncsr_fills_5y() -> None:
    records = FidelitySource().fetch(mode="fixture").records
    fixix_2021_oi = next(
        row
        for row in records
        if row.ticker == "FIXIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.payable_date
        and str(row.payable_date) == "2021-12-06"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert fixix_2021_oi.amount == Decimal("0.717")
    fixix_2021_cg = next(
        row
        for row in records
        if row.ticker == "FIXIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2021-12-06"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert fixix_2021_cg.amount == Decimal("1.522")
    fopix_2021_cg = next(
        row
        for row in records
        if row.ticker == "FOPIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2021-12-06"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert fopix_2021_cg.amount == Decimal("2.309")
    fiadx_2021_oi = next(
        row
        for row in records
        if row.ticker == "FIADX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.payable_date
        and str(row.payable_date) == "2021-12-06"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert fiadx_2021_oi.amount == Decimal("1.418")
    fwifx_2021_cg = next(
        row
        for row in records
        if row.ticker == "FWIFX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2021-12-06"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert fwifx_2021_cg.amount == Decimal("4.425")
    fvifx_2021_oi = next(
        row
        for row in records
        if row.ticker == "FVIFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.payable_date
        and str(row.payable_date) == "2021-12-06"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert fvifx_2021_oi.amount == Decimal("0.249")
    fasox_2021_oi = next(
        row
        for row in records
        if row.ticker == "FASOX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.payable_date
        and str(row.payable_date) == "2021-12-29"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert fasox_2021_oi.amount == Decimal("0.507")
    eqpgx_2021_cg = next(
        row
        for row in records
        if row.ticker == "EQPGX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2021-12-29"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert eqpgx_2021_cg.amount == Decimal("2.262")
    fscix_2021_cg = next(
        row
        for row in records
        if row.ticker == "FSCIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2021-12-29"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert fscix_2021_cg.amount == Decimal("3.595")
    fmccx_2021_cg = next(
        row
        for row in records
        if row.ticker == "FMCCX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.payable_date
        and str(row.payable_date) == "2021-12-29"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert fmccx_2021_cg.amount == Decimal("5.496")
    # Class-level — never sibling-copy retail / A / C onto Class I.
    # EQPGX 2021 CG $2.262 is the printed Class I row, not Class A $2.217.
    for ticker in WAVE_AO_FIDELITY_LEFTOVER_5Y:
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker


def test_wave_ao_leftover_walls_stay_unmatched() -> None:
    fidelity = FidelitySource().fetch(mode="fixture").records
    # Class I leftovers whose official Dec 2021 pay table is unpublished
    # or not calendar-2021 — never invent $0 / never use Feb 2022 as 2021.
    assert 2021 not in _paid_lookback_years(fidelity, "FFRIX")
    assert 2021 not in _paid_lookback_years(fidelity, "FIVQX")
    assert 2021 not in _paid_lookback_years(fidelity, "FICCX")
    assert 2021 not in _paid_lookback_years(fidelity, "FIIMX")
    assert 2021 not in _paid_lookback_years(fidelity, "FSRIX")
    assert 2021 not in _paid_lookback_years(fidelity, "FINSX")
    assert 2021 not in _paid_lookback_years(fidelity, "FGZMX")
    assert {2022, 2023, 2024, 2025} <= _paid_lookback_years(fidelity, "FFRIX")
    # WAVE X FTRIX June 30 2021 not overwritten / not redone.
    assert 2021 in _paid_lookback_years(fidelity, "FTRIX")

    # AN leftover walls — do not redo / do not invent.
    hartford = HartfordSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(hartford, "HDBAX")
    artisan = ArtisanSource().fetch(mode="fixture").records
    assert 2023 not in _paid_lookback_years(artisan, "APFDX")
    mfs = MfsSource().fetch(mode="fixture").records
    assert 2023 not in _paid_lookback_years(mfs, "BRSPX")
    assert 2022 not in _paid_lookback_years(mfs, "MEMBX")
    dodge = DodgeCoxSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(dodge, "DOXGX")
    oakmark = OakmarkSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(oakmark, "OAKCX")
    lord = LordAbbettSource().fetch(mode="fixture").records
    assert 2022 not in _paid_lookback_years(lord, "LAGWX")
    assert 2023 not in _paid_lookback_years(lord, "LAGWX")


def test_wave_ao_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "fidelity", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("FIXIX", "FOPIX", "FIADX", "EQPGX", "FASOX", "FMCCX", "FFRIX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    fixix = client.get(
        "/distributions",
        params={"ticker": "FIXIX", "publication_stage": "final", "page_size": 200},
    ).json()
    fixix_2021 = [
        Decimal(row["amount"])
        for row in fixix["items"]
        if row.get("ticker") == "FIXIX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("payable_date") or "").startswith("2021-12-06")
    ]
    assert Decimal("0.717") in fixix_2021
    fixix_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in fixix["items"]
        if row.get("ticker") == "FIXIX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= fixix_years

    eqpgx = client.get(
        "/distributions",
        params={"ticker": "EQPGX", "publication_stage": "final", "page_size": 200},
    ).json()
    eqpgx_2021 = [
        Decimal(row["amount"])
        for row in eqpgx["items"]
        if row.get("ticker") == "EQPGX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("payable_date") or "").startswith("2021-12-29")
    ]
    assert Decimal("2.262") in eqpgx_2021

    ffrix = client.get(
        "/distributions",
        params={"ticker": "FFRIX", "publication_stage": "final", "page_size": 200},
    ).json()
    ffrix_2021 = [
        row
        for row in ffrix["items"]
        if row.get("ticker") == "FFRIX"
        and str(row.get("payable_date") or row.get("as_of") or row.get("ex_date") or "").startswith(
            "2021"
        )
        and row.get("amount") is not None
        and row.get("publication_stage") == "final"
    ]
    assert ffrix_2021 == []


WAVE_AP_VANGUARD_LEFTOVER_5Y = (
    "VWEHX",
    "VWEAX",
    "VWETX",
    "VFIJX",
    "VFSTX",
    "VFSUX",
    "VFSIX",
    "VSGBX",
    "VCAIX",
    "VCADX",
    "VBISX",
    "VBITX",
    "VBIPX",
    "VWAHX",
    "VFICX",
    "VFIDX",
    "VBLAX",
    "VBLIX",
    "VWITX",
    "VBTLX",
    "VWIUX",
)


def test_wave_ap_vanguard_leftover_ici_fills_5y() -> None:
    records = VanguardSource().fetch(mode="fixture").records
    vwehx_2025 = next(
        row
        for row in records
        if row.ticker == "VWEHX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-01"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert vwehx_2025.amount == Decimal("0.028290")
    vweax_2025 = next(
        row
        for row in records
        if row.ticker == "VWEAX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-01"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert vweax_2025.amount == Decimal("0.028744")
    vfstx_2025 = next(
        row
        for row in records
        if row.ticker == "VFSTX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-12-01"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert vfstx_2025.amount == Decimal("0.039275")
    vwahx_2024 = next(
        row
        for row in records
        if row.ticker == "VWAHX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2024-12-02"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert vwahx_2024.amount == Decimal("0.033860")
    vbtlx_2023 = next(
        row
        for row in records
        if row.ticker == "VBTLX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2023-12-01"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert vbtlx_2023.amount == Decimal("0.026521")
    vwiux_2022 = next(
        row
        for row in records
        if row.ticker == "VWIUX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2022-12-01"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert vwiux_2022.amount == Decimal("0.029810")
    # Class-level — Investor VWEHX is not copied from Admiral VWEAX.
    assert vwehx_2025.amount != vweax_2025.amount
    for ticker in WAVE_AP_VANGUARD_LEFTOVER_5Y:
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker


def test_wave_ap_leftover_walls_stay_unmatched() -> None:
    vanguard = VanguardSource().fetch(mode="fixture").records
    assert 2025 not in _paid_lookback_years(vanguard, "VEDIX")
    assert {2021, 2022, 2023, 2024} <= _paid_lookback_years(vanguard, "VEDIX")

    af = AmericanFundsSource().fetch(mode="fixture").records
    anefx_2022 = [
        row
        for row in af
        if row.ticker == "ANEFX"
        and _year_for_row(row.as_of, row.ex_date, row.payable_date) == 2022
        and row.publication_stage in {PublicationStage.final, PublicationStage.paid}
        and row.amount is not None
    ]
    assert anefx_2022 == []
    assert 2022 not in _paid_lookback_years(af, "SMCWX")
    assert 2022 not in _paid_lookback_years(af, "CNWCX")

    schwab = SchwabSource().fetch(mode="fixture").records
    # Money-market leftover years stay unpublished — never invent $0.
    assert 2021 not in _paid_lookback_years(schwab, "SGUXX")
    assert _paid_lookback_years(schwab, "SGUXX") == {2025}

    dfa = DimensionalSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(dfa, "DISVX")
    assert 2022 not in _paid_lookback_years(dfa, "DISVX")

    nuveen = NuveenSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(nuveen, "NSBRX")

    blackrock = BlackRockSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(blackrock, "MDEFX")

    # Do not redo WAVE AO Fidelity Class I December 2021 — FIXIX stays 5y.
    fidelity = FidelitySource().fetch(mode="fixture").records
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(fidelity, "FIXIX")
    assert 2021 not in _paid_lookback_years(fidelity, "FFRIX")


def test_wave_ap_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "vanguard", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("VWEHX", "VFSTX", "VBTLX", "VWIUX", "VEDIX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    vwehx = client.get(
        "/distributions",
        params={"ticker": "VWEHX", "publication_stage": "final", "page_size": 200},
    ).json()
    vwehx_2025 = [
        Decimal(row["amount"])
        for row in vwehx["items"]
        if row.get("ticker") == "VWEHX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2025-12-01")
    ]
    assert Decimal("0.028290") in vwehx_2025
    vwehx_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in vwehx["items"]
        if row.get("ticker") == "VWEHX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= vwehx_years

    vbtlx = client.get(
        "/distributions",
        params={"ticker": "VBTLX", "publication_stage": "final", "page_size": 200},
    ).json()
    vbtlx_2023 = [
        Decimal(row["amount"])
        for row in vbtlx["items"]
        if row.get("ticker") == "VBTLX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2023-12-01")
    ]
    assert Decimal("0.026521") in vbtlx_2023

    vedix = client.get(
        "/distributions",
        params={"ticker": "VEDIX", "publication_stage": "final", "page_size": 200},
    ).json()
    vedix_2025 = [
        row
        for row in vedix["items"]
        if row.get("ticker") == "VEDIX"
        and str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "").startswith(
            "2025"
        )
        and row.get("amount") is not None
        and row.get("publication_stage") == "final"
    ]
    assert vedix_2025 == []


WAVE_AR_HOMESTEAD_LEFTOVER_5Y = (
    "HSTIX",
    "HOVLX",
    "HNASX",
    "HISIX",
    "HSCSX",
)


def test_wave_ar_homestead_leftover_ncsr_fills_5y() -> None:
    records = HomesteadSource().fetch(mode="fixture").records
    hovlx_2021_cg = next(
        row
        for row in records
        if row.ticker == "HOVLX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hovlx_2021_cg.amount == Decimal("4.06")
    hovlx_2021_oi = next(
        row
        for row in records
        if row.ticker == "HOVLX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hovlx_2021_oi.amount == Decimal("0.64")
    hnasx_2024_cg = next(
        row
        for row in records
        if row.ticker == "HNASX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2024-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hnasx_2024_cg.amount == Decimal("1.16")
    hstix_2022_oi = next(
        row
        for row in records
        if row.ticker == "HSTIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2022-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert hstix_2022_oi.amount == Decimal("0.34")
    # 2025 stays on the existing YE PDF — not re-emitted from N-CSR.
    ncsr_2025 = [
        row
        for row in records
        if row.ticker in WAVE_AR_HOMESTEAD_LEFTOVER_5Y
        and row.as_of
        and row.as_of.year == 2025
        and row.source_url
        and "8dd5cf6f78f6691" in row.source_url
    ]
    assert ncsr_2025 == []
    # Bond / money-market names are not in-book leftovers.
    assert [row for row in records if row.ticker in {"HOSGX", "HOSBX", "HDIXX"}] == []
    for ticker in WAVE_AR_HOMESTEAD_LEFTOVER_5Y:
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker


def test_wave_ar_leftover_walls_stay_unmatched() -> None:
    homestead = HomesteadSource().fetch(mode="fixture").records
    # HSCSX 2022 OI is an official less-than-$0.01 — omitted, not invented $0.
    hscsx_2022_oi = [
        row
        for row in homestead
        if row.ticker == "HSCSX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2022-12-31"
        and row.amount is not None
    ]
    assert hscsx_2022_oi == []
    # HNASX leftover OI highlights are dashes.
    hnasx_oi = [
        row
        for row in homestead
        if row.ticker == "HNASX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and row.as_of.year in {2021, 2022, 2023, 2024}
        and row.amount is not None
    ]
    assert hnasx_oi == []

    timothy = TimothyPlanSource().fetch(mode="fixture").records
    timothy_early = [
        row
        for row in timothy
        if row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert timothy_early == []

    # Do not redo WAVE AO Fidelity Class I / AP Vanguard ICI Dec / AN Hartford.
    fidelity = FidelitySource().fetch(mode="fixture").records
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(fidelity, "FIXIX")
    assert 2021 not in _paid_lookback_years(fidelity, "FFRIX")

    vanguard = VanguardSource().fetch(mode="fixture").records
    assert 2025 not in _paid_lookback_years(vanguard, "VEDIX")
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(vanguard, "VWEHX")

    hartford = HartfordSource().fetch(mode="fixture").records
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(hartford, "IHOAX")


def test_wave_ar_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "homestead", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("HOVLX", "HNASX", "HSTIX", "HISIX", "HSCSX", "TMVIX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        if ticker == "TMVIX":
            continue
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    timothy = client.post(
        "/ingest/fetch", json={"fund_family": "timothy_plan", "mode": "fixture"}
    )
    assert timothy.status_code == 200, timothy.text
    tmvi = client.get("/funds", params={"q": "TMVIX"}).json()
    assert "TMVIX" in [item["ticker"] for item in tmvi["items"]]

    hovlx = client.get(
        "/distributions",
        params={"ticker": "HOVLX", "publication_stage": "final", "page_size": 200},
    ).json()
    hovlx_2021 = [
        Decimal(row["amount"])
        for row in hovlx["items"]
        if row.get("ticker") == "HOVLX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2021-12-31")
    ]
    assert Decimal("4.06") in hovlx_2021
    hovlx_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in hovlx["items"]
        if row.get("ticker") == "HOVLX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= hovlx_years

    hnasx = client.get(
        "/distributions",
        params={"ticker": "HNASX", "publication_stage": "final", "page_size": 200},
    ).json()
    hnasx_2024 = [
        Decimal(row["amount"])
        for row in hnasx["items"]
        if row.get("ticker") == "HNASX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2024-12-31")
    ]
    assert Decimal("1.16") in hnasx_2024

    tmvi_dist = client.get(
        "/distributions",
        params={"ticker": "TMVIX", "publication_stage": "final", "page_size": 200},
    ).json()
    tmvi_early = [
        row
        for row in tmvi_dist["items"]
        if row.get("ticker") == "TMVIX"
        and str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        in {"2021", "2022", "2023", "2024"}
        and row.get("amount") is not None
        and row.get("publication_stage") == "final"
    ]
    assert tmvi_early == []


WAVE_AS_VIRTUS_LEFTOVER_5Y = (
    "STVTX",
    "STVZX",
    "SVIFX",
    "SVIIX",
    "SAMVX",
    "SMVFX",
    "SMVTX",
    "SMVZX",
    "SASVX",
    "SCETX",
    "STCEX",
    "VVERX",
    "SCIIX",
    "SCIZX",
    "STITX",
    "STGIX",
    "STGZX",
    "STIGX",
    "SAMBX",
    "SFRAX",
    "SFRCX",
    "SFRZX",
    "SCFTX",
    "SFLTX",
    "HYIZX",
    "HYPSX",
    "SAMHX",
    "SISIX",
    "STTBX",
    "CBPSX",
    "SAMFX",
    "SAMZX",
    "SIGVX",
    "SIGZX",
    "STCAX",
    "STCIX",
    "STCZX",
)


def test_wave_as_virtus_leftover_ncsr_fills_5y() -> None:
    records = VirtusSource().fetch(mode="fixture").records
    stvtx_2021_cg = next(
        row
        for row in records
        if row.ticker == "STVTX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert stvtx_2021_cg.amount == Decimal("3.88")
    stvtx_2021_oi = next(
        row
        for row in records
        if row.ticker == "STVTX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert stvtx_2021_oi.amount == Decimal("0.15")
    sviiix_2021_oi = next(
        row
        for row in records
        if row.ticker == "SVIIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert sviiix_2021_oi.amount == Decimal("0.10")
    stcix_2024_cg = next(
        row
        for row in records
        if row.ticker == "STCIX"
        and row.estimate_type == EstimateType.total_capital_gains
        and row.as_of
        and str(row.as_of) == "2024-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert stcix_2024_cg.amount == Decimal("0.08")
    stgix_2022_oi = next(
        row
        for row in records
        if row.ticker == "STGIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and str(row.as_of) == "2022-12-31"
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    )
    assert stgix_2022_oi.amount == Decimal("0.22")
    # 2025 stays on the existing calendar PDF — not re-emitted from N-CSR.
    ncsr_2025 = [
        row
        for row in records
        if row.ticker in WAVE_AS_VIRTUS_LEFTOVER_5Y
        and row.as_of
        and row.as_of.year == 2025
        and row.source_url
        and "d65653dncsr" in row.source_url
    ]
    assert ncsr_2025 == []
    # Zevenbergen Innovative Growth / SGA International Class C are not
    # in-book leftovers (Eric freeze).
    assert [row for row in records if row.ticker in {"SAGAX", "SCICX"}] == []
    for ticker in WAVE_AS_VIRTUS_LEFTOVER_5Y:
        assert set(LOOKBACK_YEARS) <= _paid_lookback_years(records, ticker), ticker


def test_wave_as_leftover_walls_stay_unmatched() -> None:
    virtus = VirtusSource().fetch(mode="fixture").records
    # SSAGX 2021 leftover highlights are official footnote-only dashes.
    ssagx_2021 = [
        row
        for row in virtus
        if row.ticker == "SSAGX"
        and row.as_of
        and str(row.as_of) == "2021-12-31"
        and row.amount is not None
    ]
    assert ssagx_2021 == []
    # SGA International leftover OI highlights are dashes.
    sciix_oi = [
        row
        for row in virtus
        if row.ticker == "SCIIX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.as_of
        and row.as_of.year in {2021, 2022, 2023, 2024}
        and row.amount is not None
    ]
    assert sciix_oi == []
    # Merger Fund / KAR Equity Trust leftovers stay unmatched (calendar PDFs
    # alias 2025; KAR FYE September 30 is not calendar-safe).
    merfx_early = [
        row
        for row in virtus
        if row.ticker == "MERFX"
        and row.ex_date
        and row.ex_date.year in {2021, 2022, 2023, 2024}
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert merfx_early == []
    pksax_early = [
        row
        for row in virtus
        if row.ticker == "PKSAX"
        and (
            (row.as_of and row.as_of.year in {2021, 2022, 2023, 2024})
            or (row.ex_date and row.ex_date.year in {2021, 2022, 2023, 2024})
        )
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    ]
    assert pksax_early == []

    first_eagle = FirstEagleSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(first_eagle, "FERAX")
    assert 2021 not in _paid_lookback_years(first_eagle, "FESMX")

    calamos = CalamosSource().fetch(mode="fixture").records
    assert 2021 not in _paid_lookback_years(calamos, "CAISX")

    royce = RoyceSource().fetch(mode="fixture").records
    assert 2023 not in _paid_lookback_years(royce, "RVPHX")

    wasatch = WasatchSource().fetch(mode="fixture").records
    assert 2023 not in _paid_lookback_years(wasatch, "WGROX")

    # Do not redo WAVE AO Fidelity Class I / AP Vanguard ICI Dec / AN Hartford
    # / AR Homestead.
    fidelity = FidelitySource().fetch(mode="fixture").records
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(fidelity, "FIXIX")
    assert 2021 not in _paid_lookback_years(fidelity, "FFRIX")

    vanguard = VanguardSource().fetch(mode="fixture").records
    assert 2025 not in _paid_lookback_years(vanguard, "VEDIX")
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(vanguard, "VWEHX")

    hartford = HartfordSource().fetch(mode="fixture").records
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(hartford, "IHOAX")

    homestead = HomesteadSource().fetch(mode="fixture").records
    assert set(LOOKBACK_YEARS) <= _paid_lookback_years(homestead, "HOVLX")


def test_wave_as_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "virtus", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("STVTX", "SVIIX", "STCIX", "SCIIX", "STGIX", "SAMBX", "MERFX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    stvtx = client.get(
        "/distributions",
        params={"ticker": "STVTX", "publication_stage": "final", "page_size": 200},
    ).json()
    stvtx_2021 = [
        Decimal(row["amount"])
        for row in stvtx["items"]
        if row.get("ticker") == "STVTX"
        and row.get("estimate_type") == "total_capital_gains"
        and str(row.get("as_of") or "").startswith("2021-12-31")
    ]
    assert Decimal("3.88") in stvtx_2021
    stvtx_years = {
        str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        for row in stvtx["items"]
        if row.get("ticker") == "STVTX" and row.get("amount") is not None
    }
    assert {"2021", "2022", "2023", "2024", "2025"} <= stvtx_years

    sviiix = client.get(
        "/distributions",
        params={"ticker": "SVIIX", "publication_stage": "final", "page_size": 200},
    ).json()
    sviiix_2021 = [
        Decimal(row["amount"])
        for row in sviiix["items"]
        if row.get("ticker") == "SVIIX"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("as_of") or "").startswith("2021-12-31")
    ]
    assert Decimal("0.10") in sviiix_2021

    merfx_dist = client.get(
        "/distributions",
        params={"ticker": "MERFX", "publication_stage": "final", "page_size": 200},
    ).json()
    merfx_early = [
        row
        for row in merfx_dist["items"]
        if row.get("ticker") == "MERFX"
        and str(row.get("ex_date") or row.get("payable_date") or row.get("as_of") or "")[:4]
        in {"2021", "2022", "2023", "2024"}
        and row.get("amount") is not None
        and row.get("publication_stage") == "final"
    ]
    assert merfx_early == []

