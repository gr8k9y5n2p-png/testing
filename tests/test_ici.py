from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.models import AmountUnit, EstimateType, PublicationStage
from app.sources.aum import LARGE_AUM_TICKERS, filter_large_aum, is_large_aum_ticker
from app.sources.ici import parse_ici_primary
from app.sources.parser import NormalizedRecord

VG = Path(__file__).resolve().parents[1] / "fixtures" / "vanguard"


def test_large_aum_allowlist_covers_heroes() -> None:
    for ticker in (
        "VFIAX",
        "VBIAX",
        "VIGAX",
        "VTSAX",
        "VTIAX",
        "VOO",
        "VTI",
        "VXUS",
        "VWENX",
        "VPMAX",
        "FBGRX",
        "TRBCX",
        "AMCPX",
        "CGHM",
        "NOSIX",
        "DGAGX",
        "SWTSX",
        "SWPPX",
        "DISVX",
        "LBSAX",
        "PIODX",
        "CVLC",
    ):
        assert is_large_aum_ticker(ticker)
    assert not is_large_aum_ticker("ZZTINY")
    assert not is_large_aum_ticker(None)
    assert "VFIAX" in LARGE_AUM_TICKERS


def test_filter_large_aum_drops_micro_classes() -> None:
    kept = NormalizedRecord(
        fund_family="Vanguard",
        fund_name="500 Index Fund Admiral Shares",
        ticker="VFIAX",
        cusip=None,
        share_class="Admiral",
        estimate_type=EstimateType.ordinary_income,
        amount=Decimal("1"),
        amount_min=None,
        amount_max=None,
        amount_unit=AmountUnit.per_share,
        record_date=None,
        ex_date=None,
        payable_date=None,
        as_of=date(2024, 12, 31),
        publication_stage=PublicationStage.final,
        source_url="fixture://ici",
    )
    dropped = replace(kept, ticker="ZZTINY", fund_name="Tiny")
    assert [r.ticker for r in filter_large_aum([kept, dropped])] == ["VFIAX"]


def test_parse_ici_primary_2024_december_flagships() -> None:
    text = (VG / "ici_primary_2024.csv").read_text(encoding="utf-8")
    records = parse_ici_primary(
        text,
        source_url="https://advisors.vanguard.com/content/dam/fas/pdfs/ICI_revised_2024_Primary_layout_spreadsheet.pdf",
        fund_family="Vanguard",
    )
    vfiax = next(
        r for r in records if r.ticker == "VFIAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vfiax.amount == Decimal("1.739200")
    assert str(vfiax.ex_date) == "2024-12-23"
    assert str(vfiax.as_of) == "2024-12-31"
    assert vfiax.publication_stage == PublicationStage.final
    assert vfiax.cusip == "922908710"
    vbiax_lt = next(
        r
        for r in records
        if r.ticker == "VBIAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert vbiax_lt.amount == Decimal("1.298076")
    vigax = next(
        r for r in records if r.ticker == "VIGAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vigax.amount == Decimal("0.270100")
    vtsax = next(
        r for r in records if r.ticker == "VTSAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vtsax.amount == Decimal("0.454900")
    assert str(vtsax.ex_date) == "2024-12-23"
    vtiax = next(
        r for r in records if r.ticker == "VTIAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vtiax.amount == Decimal("0.537000")
    voo = next(
        r for r in records if r.ticker == "VOO" and r.estimate_type == EstimateType.ordinary_income
    )
    assert voo.amount == Decimal("1.738500")
    assert {r.ticker for r in records} <= LARGE_AUM_TICKERS
    assert not any(r.ticker == "VFIAX" and r.estimate_type == EstimateType.long_term_capital_gains for r in records)
    vwenx_lt = next(
        r
        for r in records
        if r.ticker == "VWENX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert vwenx_lt.amount == Decimal("5.925344")
    assert {"VTI", "VXUS", "VEA", "VWO", "VWENX", "VPMAX"} <= {r.ticker for r in records}


def test_parse_ici_primary_2021_and_2025_ongoing() -> None:
    y2021 = parse_ici_primary(
        (VG / "ici_primary_2021.csv").read_text(encoding="utf-8"),
        source_url="https://advisors.vanguard.com/content/dam/fas/pdfs/2021_ICI_Primary_Layout.pdf",
        fund_family="Vanguard",
    )
    vfiax = next(
        r for r in y2021 if r.ticker == "VFIAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vfiax.amount == Decimal("1.535100")
    assert str(vfiax.as_of) == "2021-12-31"

    y2025 = parse_ici_primary(
        (VG / "ici_primary_2025.csv").read_text(encoding="utf-8"),
        source_url="https://advisors.vanguard.com/content/dam/fas/pdfs/ICIprimary_012026.pdf",
        fund_family="Vanguard",
    )
    # Heroes already in the 2025 YE HTML fixture stay out of the ICI 2025 pack.
    assert not any(r.ticker in {"VFIAX", "VBIAX", "VIGAX"} for r in y2025)
    vtsax = next(
        r for r in y2025 if r.ticker == "VTSAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vtsax.amount == Decimal("0.459000")
    assert str(vtsax.ex_date) == "2025-12-22"
    voo = next(
        r for r in y2025 if r.ticker == "VOO" and r.estimate_type == EstimateType.ordinary_income
    )
    assert voo.amount == Decimal("1.771000")
    assert {r.ticker for r in y2025} <= LARGE_AUM_TICKERS
