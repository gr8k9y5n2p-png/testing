"""Official 5-year paid/final history densify on the existing Aftertax book."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.models import AmountUnit, EstimateType, PublicationStage
from app.services.lookback import LOOKBACK_YEARS, lookback_digest_from_rows
from app.sources.american_funds import AmericanFundsSource
from app.sources.aum import filter_large_aum
from app.sources.families import BlackRockSource, VanguardSource
from app.sources.fifth_tier import VictorySource
from app.sources.fourth_tier import HartfordSource
from app.sources.sixth_tier import FirstTrustSource, VaneckSource, WisdomtreeSource
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
    # 2,741 after official 5y wave 2. Wave 3 First Trust product-page 2021–2023
    # + VanEck tax-center 2021–2022 PDFs + WisdomTree December income / 2023 CG
    # payers raise in-book 5y without inventing unpublished gaps.
    assert digest.funds_with_5y == 2877
    assert digest.funds_with_5y_mf == 2221
    assert digest.funds_with_5y_etf == 656
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
