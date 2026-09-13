"""Official 5-year paid/final history densify on the existing Aftertax book."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

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
from app.sources.eleventh_tier import AmgSource
from app.sources.fifth_tier import OakmarkSource, RoyceSource, TouchstoneSource, VictorySource
from app.sources.fourth_tier import (
    ArtisanSource,
    CalamosSource,
    FirstEagleSource,
    HartfordSource,
    PrincipalSource,
    ThriventSource,
)
from app.sources.next_tier import (
    DimensionalSource,
    FranklinTempletonSource,
    MorganStanleySource,
    NorthernTrustSource,
    NuveenSource,
    SchwabSource,
)
from app.sources.ninth_tier import AmericanBeaconSource
from app.sources.third_tier import (
    AllspringSource,
    DodgeCoxSource,
    JanusHendersonSource,
    LordAbbettSource,
    MfsSource,
)
from app.sources.sixth_tier import (
    AlgerSource,
    FirstTrustSource,
    HardingLoevnerSource,
    VaneckSource,
    WilliamBlairSource,
    WisdomtreeSource,
)
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
    # 2021 and Alger 2021/2023/2024 stay unmatched). No new identities.
    assert digest.funds_with_5y == 3351
    assert digest.funds_with_5y_mf == 2613
    assert digest.funds_with_5y_etf == 738
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

