from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.models import AmountUnit, EstimateType
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
    UbsSource,
)
from app.sources.parser import parse_distribution_html, split_fund_identity

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_split_fidelity_symbol_cusip() -> None:
    name, ticker, cusip, _cls = split_fund_identity(
        "Blue Chip Growth Symbol FBGRX Cusip 316389303 Fund # 312"
    )
    assert name == "Blue Chip Growth"
    assert ticker == "FBGRX"
    assert cusip == "316389303"


def test_split_ishares_ticker_suffix() -> None:
    name, ticker, _cusip, _cls = split_fund_identity(
        "iShares Disciplined Volatility Equity Active ETF ( BDVL )"
    )
    assert ticker == "BDVL"
    assert "Disciplined Volatility" in name


def test_fidelity_fixture() -> None:
    html = (ROOT / "fidelity" / "estimated_capital_gains.html").read_text(encoding="utf-8")
    records = parse_distribution_html(html, source_url="fixture://fidelity", fund_family="Fidelity")
    fbgrx = [r for r in records if r.ticker == "FBGRX"]
    assert fbgrx
    assert any(r.cusip == "316389303" for r in fbgrx)
    lt = next(r for r in fbgrx if r.estimate_type == EstimateType.long_term_capital_gains)
    assert lt.amount == Decimal("21.021")
    pct = next(r for r in fbgrx if r.amount_unit == AmountUnit.percent_of_nav)
    assert pct.amount == Decimal("7.08")
    assert str(lt.ex_date) == "2026-09-11"
    assert str(lt.as_of) == "2026-07-31"


def test_blackrock_ishares_fixture() -> None:
    html = (ROOT / "blackrock" / "capital_gains_distributions.html").read_text(encoding="utf-8")
    records = parse_distribution_html(html, source_url="fixture://ishares", fund_family="BlackRock / iShares")
    bdvl = [r for r in records if r.ticker == "BDVL"]
    lt = next(r for r in bdvl if r.estimate_type == EstimateType.long_term_capital_gains)
    assert lt.amount == Decimal("0.183738")
    pct = next(r for r in bdvl if r.amount_unit == AmountUnit.percent_of_nav)
    assert pct.amount == Decimal("0.86")
    bemb = next(r for r in records if r.ticker == "BEMB" and r.estimate_type == EstimateType.long_term_capital_gains)
    assert bemb.amount == Decimal("0.393930")


def test_vanguard_fixture() -> None:
    html = (ROOT / "vanguard" / "year_end_distributions.html").read_text(encoding="utf-8")
    records = parse_distribution_html(html, source_url="fixture://vanguard", fund_family="Vanguard")
    vbiax_lt = next(
        r
        for r in records
        if r.ticker == "VBIAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert vbiax_lt.amount == Decimal("1.23884")
    assert str(vbiax_lt.ex_date) == "2025-12-23"
    income = next(r for r in records if r.ticker == "VBIAX" and r.estimate_type == EstimateType.ordinary_income)
    assert income.amount == Decimal("0.27800")
    vfiax = next(r for r in records if r.ticker == "VFIAX")
    assert vfiax.amount == Decimal("1.76960")


def test_t_rowe_split_header_fixture() -> None:
    html = (ROOT / "t_rowe_price" / "2025_year_end_distributions.html").read_text(encoding="utf-8")
    records = parse_distribution_html(html, source_url="fixture://trp", fund_family="T. Rowe Price")
    trbcx = next(
        r
        for r in records
        if r.ticker == "TRBCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert trbcx.amount == Decimal("10.9575")
    st = next(r for r in records if r.ticker == "TRBCX" and r.estimate_type == EstimateType.short_term_capital_gains)
    assert st.amount == Decimal("0.0748")
    iclass = next(r for r in records if r.ticker == "TBCIX" and r.estimate_type == EstimateType.long_term_capital_gains)
    assert iclass.amount == Decimal("10.9575")


def test_state_street_invesco_jpm_gs_pimco_fixtures() -> None:
    ssga = parse_distribution_html(
        (ROOT / "state_street" / "etf_capital_gain_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://ssga",
        fund_family="State Street / SPDR",
    )
    spy = next(r for r in ssga if r.ticker == "SPY")
    assert spy.amount_unit == AmountUnit.percent_of_nav
    sample = next(r for r in ssga if r.ticker == "ZZSSGA" and r.estimate_type == EstimateType.long_term_capital_gains)
    assert sample.amount == Decimal("0.25")

    invesco = parse_distribution_html(
        (ROOT / "invesco" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://invesco",
        fund_family="Invesco",
    )
    franchise = next(
        r
        for r in invesco
        if "American Franchise" in r.fund_name and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert franchise.amount == Decimal("2.89")
    pin = next(r for r in invesco if r.ticker == "PIN" and r.estimate_type == EstimateType.long_term_capital_gains)
    assert pin.amount == Decimal("1.68")

    jpm = parse_distribution_html(
        (ROOT / "jpmorgan" / "section_19a_sample.html").read_text(encoding="utf-8"),
        source_url="fixture://jpm",
        fund_family="J.P. Morgan Asset Management",
    )
    seegx = next(r for r in jpm if r.ticker == "SEEGX" and r.estimate_type == EstimateType.long_term_capital_gains)
    assert seegx.amount == Decimal("9.32525")

    gs = parse_distribution_html(
        (ROOT / "goldman_sachs" / "year_end_distributions_sample.html").read_text(encoding="utf-8"),
        source_url="fixture://gs",
        fund_family="Goldman Sachs Asset Management",
    )
    glcgx = next(r for r in gs if r.ticker == "GLCGX")
    assert glcgx.amount == Decimal("2.74")

    pimco = parse_distribution_html(
        (ROOT / "pimco" / "tax_center_sample.html").read_text(encoding="utf-8"),
        source_url="fixture://pimco",
        fund_family="PIMCO",
    )
    sample_inc = next(r for r in pimco if r.ticker == "ZZPIMI" and r.estimate_type == EstimateType.ordinary_income)
    assert sample_inc.amount == Decimal("0.08")


def test_adapters_fetch_fixture_mode() -> None:
    sources = [
        BlackRockSource(),
        VanguardSource(),
        FidelitySource(),
        StateStreetSource(),
        JPMorganSource(),
        GoldmanSachsSource(),
        PimcoSource(),
        InvescoSource(),
        TRowePriceSource(),
        UbsSource(),
        FranklinTempletonSource(),
        BnyMellonSource(),
        NuveenSource(),
        NorthernTrustSource(),
        MorganStanleySource(),
        SchwabSource(),
        DimensionalSource(),
        ColumbiaThreadneedleSource(),
        AmundiSource(),
    ]
    for source in sources:
        result = source.fetch(mode="fixture")
        assert result.records, f"{source.slug} produced 0 records"
        assert all(r.fund_family == source.display_name for r in result.records)


def test_next_tier_fixtures() -> None:
    ubs = parse_distribution_html(
        (ROOT / "ubs" / "paid_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://ubs",
        fund_family="UBS Asset Management",
    )
    pwtax = next(
        r
        for r in ubs
        if r.ticker == "PWTAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert pwtax.amount == Decimal("4.0999")

    ubs_est = parse_distribution_html(
        (ROOT / "ubs" / "estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://ubs-est",
        fund_family="UBS Asset Management",
    )
    alloc = next(
        r
        for r in ubs_est
        if r.ticker == "PWTAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert alloc.amount_min == Decimal("2.88")
    assert alloc.amount_max == Decimal("4.05")

    ft = parse_distribution_html(
        (ROOT / "franklin_templeton" / "capital_gains_sample.html").read_text(encoding="utf-8"),
        source_url="fixture://ft",
        fund_family="Franklin Templeton",
    )
    ft_row = next(r for r in ft if r.ticker == "FT" and r.estimate_type == EstimateType.ordinary_income)
    assert ft_row.amount == Decimal("0.0358")

    bny = parse_distribution_html(
        (ROOT / "bny_mellon" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://bny",
        fund_family="BNY Mellon / Dreyfus",
    )
    dgagx = next(
        r
        for r in bny
        if r.ticker == "DGAGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dgagx.amount == Decimal("6.29")

    nuveen = parse_distribution_html(
        (ROOT / "nuveen" / "2025_estimated_taxable_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://nuveen",
        fund_family="Nuveen / TIAA",
    )
    tiirx = next(
        r
        for r in nuveen
        if r.ticker == "TIIRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tiirx.amount == Decimal("1.97")

    nt = parse_distribution_html(
        (ROOT / "northern_trust" / "2025_capital_gain_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://nt",
        fund_family="Northern Trust",
    )
    nosix = next(
        r
        for r in nt
        if r.ticker == "NOSIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nosix.amount == Decimal("1.182288")

    msim = parse_distribution_html(
        (ROOT / "morgan_stanley" / "2025_etf_year_end_sample.html").read_text(encoding="utf-8"),
        source_url="fixture://msim",
        fund_family="Morgan Stanley Investment Management",
    )
    cvlc = next(r for r in msim if r.ticker == "CVLC" and r.estimate_type == EstimateType.ordinary_income)
    assert cvlc.amount == Decimal("0.283927")

    schwab = parse_distribution_html(
        (ROOT / "schwab" / "2025_annual_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://schwab",
        fund_family="Charles Schwab Investment Management",
    )
    swlvx = next(
        r
        for r in schwab
        if r.ticker == "SWLVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert swlvx.amount == Decimal("0.0049")

    dfa = parse_distribution_html(
        (ROOT / "dimensional" / "2025_capital_gain_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://dfa",
        fund_family="Dimensional Fund Advisors",
    )
    disvx = next(
        r
        for r in dfa
        if r.ticker == "DISVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert disvx.amount == Decimal("1.060")

    columbia = parse_distribution_html(
        (ROOT / "columbia_threadneedle" / "2025_midyear_estimates.html").read_text(encoding="utf-8"),
        source_url="fixture://columbia",
        fund_family="Columbia Threadneedle",
    )
    ievax = next(r for r in columbia if r.ticker == "IEVAX")
    assert ievax.amount_min == Decimal("0.86")
    assert ievax.amount_max == Decimal("1.25")
    assert ievax.amount_unit == AmountUnit.percent_of_nav

    amundi = parse_distribution_html(
        (ROOT / "amundi" / "2025_capital_gain_estimates.html").read_text(encoding="utf-8"),
        source_url="fixture://amundi",
        fund_family="Amundi US / Pioneer",
    )
    piodx = next(
        r
        for r in amundi
        if r.ticker == "PIODX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert piodx.amount == Decimal("3.73")
    assert piodx.cusip == "92648C512"
