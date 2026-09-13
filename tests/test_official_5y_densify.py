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
    InvescoSource,
    StateStreetSource,
    TRowePriceSource,
    VanguardSource,
)
from app.sources.dws import DwsSource
from app.sources.eighth_tier import ArielSource, BairdSource, PrimecapSource
from app.sources.eleventh_tier import AmgSource, GuidestoneSource
from app.sources.fifth_tier import (
    GabelliSource,
    OakmarkSource,
    RoyceSource,
    TouchstoneSource,
    VictorySource,
)
from app.sources.fourth_tier import (
    ArtisanSource,
    CalamosSource,
    FirstEagleSource,
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
    DimensionalSource,
    FranklinTempletonSource,
    MorganStanleySource,
    NorthernTrustSource,
    NuveenSource,
    SchwabSource,
)
from app.sources.ninth_tier import AmericanBeaconSource
from app.sources.third_tier import (
    AllianceBernsteinSource,
    AllspringSource,
    AmericanCenturySource,
    DodgeCoxSource,
    FederatedHermesSource,
    JanusHendersonSource,
    LordAbbettSource,
    MfsSource,
    VirtusSource,
)
from app.sources.sixth_tier import (
    AlgerSource,
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
from app.sources.parser import NormalizedRecord
from app.sources.registry import list_sources
from app.sources.seventh_tier import ChamplainSource, DavisSource, HotchkisWileySource


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
    assert digest.funds_with_5y == 3482
    assert digest.funds_with_5y_mf == 2732
    assert digest.funds_with_5y_etf == 750
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
    bacax_2025 = [
        row
        for row in records
        if row.ticker == "BACAX"
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount is not None
    ]
    assert bacax_2025 == []

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

    # Bond Debenture / Total Return leftover years stay JS-unpublished.
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
    twcgx_years = {
        row.ex_date.year
        for row in records
        if row.ticker == "TWCGX"
        and row.ex_date
        and row.publication_stage == PublicationStage.final
        and row.amount is not None
    }
    assert {2023, 2024, 2025} <= twcgx_years
    assert 2021 not in twcgx_years
    assert 2022 not in twcgx_years


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
    for ticker in ("DMCVX", "MIBLX", "MIMSX", "MISCX"):
        paid = [
            row
            for row in bny
            if row.ticker == ticker
            and row.ex_date
            and row.publication_stage == PublicationStage.final
            and row.amount is not None
        ]
        assert paid == [], ticker
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
