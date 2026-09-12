"""Official 5-year paid/final history densify on the existing Aftertax book."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models import AmountUnit, EstimateType, PublicationStage
from app.services.lookback import LOOKBACK_YEARS, lookback_digest_from_rows
from app.sources.american_funds import AmericanFundsSource
from app.sources.aum import filter_large_aum
from app.sources.families import BlackRockSource, TRowePriceSource, VanguardSource
from app.sources.eleventh_tier import AmgSource
from app.sources.fifth_tier import RoyceSource, VictorySource
from app.sources.fourth_tier import ArtisanSource, FirstEagleSource, HartfordSource, ThriventSource
from app.sources.next_tier import NorthernTrustSource, SchwabSource
from app.sources.sixth_tier import FirstTrustSource, VaneckSource, WilliamBlairSource, WisdomtreeSource
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
    # 2,949 after official 5y wave 5. Max-reach adds AMG product-page 2021–2024,
    # William Blair 2021–2024 leftover share classes, Royce 2021–2024 leftover
    # share classes, and Artisan official 2021–2023 ICI — no new identities.
    assert digest.funds_with_5y == 3073
    assert digest.funds_with_5y_mf == 2389
    assert digest.funds_with_5y_etf == 684
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
    dgrw_2023 = [
        row
        for row in records
        if row.ticker == "DGRW"
        and row.ex_date
        and row.ex_date.year == 2023
        and row.amount
    ]
    assert dgrw_2023 == []


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
    # Class A product-page leftover is not copied onto Class I / R6.
    sgiix_2021 = [
        row
        for row in records
        if row.ticker == "SGIIX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    ]
    assert sgiix_2021 == []
    fegrx_2021 = [
        row
        for row in records
        if row.ticker == "FEGRX"
        and row.ex_date
        and row.ex_date.year == 2021
        and row.amount
    ]
    assert fegrx_2021 == []


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
