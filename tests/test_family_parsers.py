from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from app.models import AmountUnit, EstimateType, PublicationStage
from app.sources.ark import ArkSource
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
from app.sources.sixth_tier import (
    AlgerSource,
    AqrSource,
    BrownAdvisorySource,
    CausewaySource,
    HardingLoevnerSource,
    MatthewsAsiaSource,
    SeiSource,
    FirstTrustSource,
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
from app.sources.eighth_tier import (
    ArielSource,
    BairdSource,
    BuffaloSource,
    FmiSource,
    GqgSource,
    HeartlandSource,
    ImpaxSource,
    LongleafSource,
    PrimecapSource,
    ThirdAvenueSource,
)
from app.sources.ninth_tier import (
    AmericanBeaconSource,
    BaillieGiffordSource,
    BostonTrustSource,
    BrandesSource,
    FamSource,
    GrandeurPeakSource,
    HennessySource,
    KineticsSource,
    MairsPowerSource,
    MeridianSource,
)
from app.sources.tenth_tier import (
    BostonPartnersSource,
    HomesteadSource,
    LazardSource,
    LkcmSource,
    LsvSource,
    MadisonSource,
    ManningNapierSource,
    OberweisSource,
    RiverparkSource,
    WestwoodSource,
)
from app.sources.eleventh_tier import (
    AmgSource,
    ConestogaSource,
    GuidestoneSource,
    HodgesSource,
    KopernikSource,
    LocorrSource,
    PermanentPortfolioSource,
    TimothyPlanSource,
    TocquevilleSource,
    ValueLineSource,
)
from app.sources.dws import DwsSource
from app.sources.ici import parse_ici_primary
from app.sources.parser import parse_distribution_html, split_fund_identity

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_split_fidelity_symbol_cusip() -> None:
    name, ticker, cusip, _cls = split_fund_identity(
        "Blue Chip Growth Symbol FBGRX Cusip 316389303 Fund # 312"
    )
    assert name == "Blue Chip Growth"
    assert ticker == "FBGRX"
    assert cusip == "316389303"


def test_skip_sma_and_separate_account_rows() -> None:
    html = """
    <html><head><title>Mixed book</title><meta name="date" content="2025-12-15"></head>
    <body>
    <table>
      <tr><th>Fund Name</th><th>Ticker</th><th>Long-Term</th></tr>
      <tr><td>Example Growth Fund</td><td>EXMPX</td><td>1.25</td></tr>
      <tr><td>Example SMA High Yield Bond Fund</td><td>EXSMA</td><td>0.40</td></tr>
      <tr><td>Example Separate Account Sleeve</td><td>EXSEP</td><td>0.55</td></tr>
    </table>
    </body></html>
    """
    records = parse_distribution_html(html, source_url="fixture://sma", fund_family="Example")
    tickers = {r.ticker for r in records}
    assert "EXMPX" in tickers
    assert "EXSMA" not in tickers
    assert "EXSEP" not in tickers
    assert not any("SMA" in (r.fund_name or "") for r in records)


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
    assert lt.record_date is None
    fbcvx = next(
        r
        for r in records
        if r.ticker == "FBCVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert fbcvx.record_date is None
    assert str(fbcvx.ex_date) == "2026-09-11"


def test_blackrock_ishares_fixture() -> None:
    html = (ROOT / "blackrock" / "capital_gains_distributions.html").read_text(encoding="utf-8")
    records = parse_distribution_html(html, source_url="fixture://ishares", fund_family="BlackRock / iShares")
    bdvl = [r for r in records if r.ticker == "BDVL"]
    lt = next(r for r in bdvl if r.estimate_type == EstimateType.long_term_capital_gains)
    assert lt.amount == Decimal("0.183738")
    assert lt.publication_stage == PublicationStage.paid
    pct = next(r for r in bdvl if r.amount_unit == AmountUnit.percent_of_nav)
    assert pct.amount == Decimal("0.86")
    bemb = next(r for r in records if r.ticker == "BEMB" and r.estimate_type == EstimateType.long_term_capital_gains)
    assert bemb.amount == Decimal("0.393930")
    assert bemb.publication_stage == PublicationStage.final

    oef = parse_distribution_html(
        (ROOT / "blackrock" / "2025_open_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://blackrock-oef",
        fund_family="BlackRock / iShares",
    )
    equity_div = next(
        r
        for r in oef
        if "Equity Dividend" in r.fund_name and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert equity_div.amount == Decimal("0.999925")
    assert not any("SMA" in (r.fund_name or "") for r in oef)

    oef_2024 = parse_distribution_html(
        (ROOT / "blackrock" / "2024_open_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://blackrock-oef-2024",
        fund_family="BlackRock / iShares",
    )
    equity_div_2024 = next(
        r
        for r in oef_2024
        if "Equity Dividend" in r.fund_name and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert equity_div_2024.amount == Decimal("0.728360")
    assert equity_div_2024.publication_stage == PublicationStage.final
    assert str(equity_div_2024.as_of) == "2024-12-30"

    oef_2023 = parse_distribution_html(
        (ROOT / "blackrock" / "2023_open_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://blackrock-oef-2023",
        fund_family="BlackRock / iShares",
    )
    equity_div_2023 = next(
        r
        for r in oef_2023
        if "Equity Dividend" in r.fund_name and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert equity_div_2023.amount == Decimal("0.481929")
    assert str(equity_div_2023.as_of) == "2023-12-29"
    assert not any("SMA" in (r.fund_name or "") for r in oef_2024 + oef_2023)

    oef_2022 = parse_distribution_html(
        (ROOT / "blackrock" / "2022_open_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://blackrock-oef-2022",
        fund_family="BlackRock / iShares",
    )
    equity_div_2022 = next(
        r
        for r in oef_2022
        if "Equity Dividend" in r.fund_name and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert equity_div_2022.amount == Decimal("0.740291")
    assert equity_div_2022.publication_stage == PublicationStage.final
    assert str(equity_div_2022.as_of) == "2022-12-30"
    assert not any("Variable Series" in (r.fund_name or "") for r in oef_2022)

    oef_2021 = parse_distribution_html(
        (ROOT / "blackrock" / "2021_open_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://blackrock-oef-2021",
        fund_family="BlackRock / iShares",
    )
    equity_div_2021 = next(
        r
        for r in oef_2021
        if "Equity Dividend" in r.fund_name and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert equity_div_2021.amount == Decimal("1.089256")
    assert str(equity_div_2021.as_of) == "2021-12-31"
    assert not any("SMA" in (r.fund_name or "") for r in oef_2022 + oef_2021)

    ishares_ici = parse_ici_primary(
        (ROOT / "blackrock" / "ici_primary_2025.csv").read_text(encoding="utf-8"),
        source_url="fixture://ishares-ici-2025",
        fund_family="BlackRock / iShares",
    )
    ivv_ici = next(
        r
        for r in ishares_ici
        if r.ticker == "IVV" and r.estimate_type == EstimateType.ordinary_income
    )
    assert ivv_ici.amount == Decimal("2.413592")
    itot_ici = next(
        r
        for r in ishares_ici
        if r.ticker == "ITOT" and r.estimate_type == EstimateType.ordinary_income
    )
    assert itot_ici.amount == Decimal("0.486672")


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
    vigax = next(
        r
        for r in records
        if r.ticker == "VIGAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vigax.amount == Decimal("0.251100")
    assert str(vigax.record_date) == "2025-12-19"
    assert str(vigax.ex_date) == "2025-12-22"
    assert str(vigax.payable_date) == "2025-12-23"


def test_vanguard_wave_ap_leftover_ici() -> None:
    records = parse_ici_primary(
        (ROOT / "vanguard" / "leftover_ici_primary_wave_ap.csv").read_text(encoding="utf-8"),
        source_url="fixture://vanguard-wave-ap",
        fund_family="Vanguard",
    )
    vwehx = next(
        r
        for r in records
        if r.ticker == "VWEHX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vwehx.amount == Decimal("0.028290")
    assert str(vwehx.ex_date) == "2025-12-01"
    vweax = next(
        r
        for r in records
        if r.ticker == "VWEAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vweax.amount == Decimal("0.028744")
    assert vwehx.amount != vweax.amount
    vbtlx = next(
        r
        for r in records
        if r.ticker == "VBTLX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vbtlx.amount == Decimal("0.026521")
    assert str(vbtlx.ex_date) == "2023-12-01"
    vwiux = next(
        r
        for r in records
        if r.ticker == "VWIUX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vwiux.amount == Decimal("0.029810")
    assert str(vwiux.ex_date) == "2022-12-01"


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

    ssga_paid = parse_distribution_html(
        (ROOT / "state_street" / "2025_historical_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://ssga-2025-xlsx",
        fund_family="State Street / SPDR",
    )
    spy_paid = next(
        r
        for r in ssga_paid
        if r.ticker == "SPY" and r.estimate_type == EstimateType.ordinary_income
    )
    assert spy_paid.amount == Decimal("1.993368")
    allw_lt = next(
        r
        for r in ssga_paid
        if r.ticker == "ALLW" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert allw_lt.amount == Decimal("0.172577")
    assert "SPYM" in {r.ticker for r in ssga_paid}
    gld = next(
        r
        for r in ssga_paid
        if r.ticker == "GLD" and r.estimate_type == EstimateType.ordinary_income
    )
    assert gld.amount == Decimal("0.000000")

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

    qqq = parse_distribution_html(
        (ROOT / "invesco" / "qqq_annual_report_distributions.html").read_text(encoding="utf-8"),
        source_url="https://www.invesco.com/content/dam/invesco/hk/en/pdf/annual-report/Invesco_QQQ_AnnualReport.pdf",
        fund_family="Invesco",
    )
    qqq_2025 = next(
        r
        for r in qqq
        if r.ticker == "QQQ"
        and r.estimate_type == EstimateType.ordinary_income
        and r.amount == Decimal("2.84")
    )
    assert str(qqq_2025.as_of) == "2025-09-30"
    assert {r.as_of.year for r in qqq if r.as_of} == {2021, 2022, 2023, 2024, 2025}

    jpm = parse_distribution_html(
        (ROOT / "jpmorgan" / "section_19a_sample.html").read_text(encoding="utf-8"),
        source_url="fixture://jpm",
        fund_family="J.P. Morgan Asset Management",
    )
    seegx = next(r for r in jpm if r.ticker == "SEEGX" and r.estimate_type == EstimateType.long_term_capital_gains)
    assert seegx.amount == Decimal("9.32525")

    jpm_2024 = parse_distribution_html(
        (ROOT / "jpmorgan" / "2024_section_19a.html").read_text(encoding="utf-8"),
        source_url="fixture://jpm-2024",
        fund_family="J.P. Morgan Asset Management",
    )
    jepi_ncsr = parse_distribution_html(
        (ROOT / "jpmorgan" / "jepi_ncsr_financial_highlights.html").read_text(encoding="utf-8"),
        source_url="https://www.sec.gov/Archives/edgar/data/1485894/000119312525193891/d66956dncsr.htm",
        fund_family="J.P. Morgan Asset Management",
    )
    jepi_2025 = next(
        r
        for r in jepi_ncsr
        if r.ticker == "JEPI"
        and r.estimate_type == EstimateType.ordinary_income
        and r.amount == Decimal("4.67")
    )
    assert str(jepi_2025.as_of) == "2025-06-30"
    assert {r.as_of.year for r in jepi_ncsr if r.ticker == "JEPI" and r.as_of} == {
        2021,
        2022,
        2023,
        2024,
        2025,
    }
    jepq_2025 = next(
        r
        for r in jepi_ncsr
        if r.ticker == "JEPQ"
        and r.estimate_type == EstimateType.ordinary_income
        and r.amount == Decimal("6.11")
    )
    assert str(jepq_2025.as_of) == "2025-06-30"

    seegx_2024 = next(
        r
        for r in jpm_2024
        if r.ticker == "SEEGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert seegx_2024.amount == Decimal("0.79868")

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
        AllspringSource(),
        JanusHendersonSource(),
        AmericanCenturySource(),
        DodgeCoxSource(),
        MfsSource(),
        LordAbbettSource(),
        AllianceBernsteinSource(),
        FederatedHermesSource(),
        VirtusSource(),
        EatonVanceSource(),
        JohnHancockSource(),
        PrincipalSource(),
        ThriventSource(),
        HartfordSource(),
        MacquarieSource(),
        FirstEagleSource(),
        GmoSource(),
        ArtisanSource(),
        CalamosSource(),
        WasatchSource(),
        HarborSource(),
        NationwideSource(),
        VoyaSource(),
        OakmarkSource(),
        TweedySource(),
        GabelliSource(),
        RoyceSource(),
        NylifeSource(),
        TouchstoneSource(),
        VictorySource(),
        SeiSource(),
        BrownAdvisorySource(),
        WilliamBlairSource(),
        VaneckSource(),
        WisdomtreeSource(),
        FirstTrustSource(),
        DwsSource(),
        AqrSource(),
        CausewaySource(),
        AlgerSource(),
        HardingLoevnerSource(),
        MatthewsAsiaSource(),
        TcwSource(),
        BridgewaySource(),
        JensenSource(),
        DiamondHillSource(),
        ChamplainSource(),
        DriehausSource(),
        HotchkisWileySource(),
        MarsicoSource(),
        OsterweisSource(),
        DavisSource(),
        PrimecapSource(),
        ArielSource(),
        BairdSource(),
        LongleafSource(),
        BuffaloSource(),
        GqgSource(),
        ThirdAvenueSource(),
        HeartlandSource(),
        FmiSource(),
        ImpaxSource(),
        AmericanBeaconSource(),
        BaillieGiffordSource(),
        BrandesSource(),
        MairsPowerSource(),
        BostonTrustSource(),
        GrandeurPeakSource(),
        HennessySource(),
        FamSource(),
        MeridianSource(),
        KineticsSource(),
        LazardSource(),
        ManningNapierSource(),
        WestwoodSource(),
        BostonPartnersSource(),
        HomesteadSource(),
        MadisonSource(),
        LsvSource(),
        LkcmSource(),
        OberweisSource(),
        RiverparkSource(),
        AmgSource(),
        GuidestoneSource(),
        ValueLineSource(),
        PermanentPortfolioSource(),
        ConestogaSource(),
        KopernikSource(),
        LocorrSource(),
        TimothyPlanSource(),
        HodgesSource(),
        TocquevilleSource(),
        ArkSource(),
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
    ftf_row = next(r for r in ft if r.ticker == "FTF" and r.estimate_type == EstimateType.ordinary_income)
    assert ftf_row.amount == Decimal("0.0418")
    tei_st = next(
        r for r in ft if r.ticker == "TEI" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert tei_st.amount == Decimal("0.0648")
    smdlx_roc = next(
        r for r in ft if r.ticker == "SMDLX" and r.estimate_type == EstimateType.return_of_capital
    )
    assert smdlx_roc.amount == Decimal("0.073334")

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
    nsbax_st = next(
        r
        for r in nuveen
        if r.ticker == "NSBAX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    nsbax_lt = next(
        r
        for r in nuveen
        if r.ticker == "NSBAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nsbax_st.amount == Decimal("0.04")
    assert nsbax_lt.amount == Decimal("4.89")
    tinrx_st = next(
        r
        for r in nuveen
        if r.ticker == "TINRX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert tinrx_st.amount == Decimal("0.21")
    nuveen_tickers = {r.ticker for r in nuveen if r.ticker}
    assert len(nuveen_tickers) >= 500
    assert not any("Managed Account" in (r.fund_name or "") for r in nuveen)

    ft_summ = parse_distribution_html(
        (ROOT / "franklin_templeton" / "2025_cef_distribution_summary.html").read_text(encoding="utf-8"),
        source_url="https://www.franklintempleton.com/forms-literature/download/DIST-SUMM",
        fund_family="Franklin Templeton",
    )
    ft_ye = next(
        r for r in ft_summ if r.ticker == "FT" and r.estimate_type == EstimateType.ordinary_income
    )
    assert ft_ye.amount == Decimal("0.341")
    ft_lt = next(
        r
        for r in ft_summ
        if r.ticker == "FT" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert ft_lt.amount == Decimal("0.145")
    emo_roc = next(
        r
        for r in ft_summ
        if r.ticker == "EMO" and r.estimate_type == EstimateType.return_of_capital
    )
    assert emo_roc.amount == Decimal("3.504")
    assert {r.ticker for r in ft_summ if r.ticker} >= {"FT", "FTF", "TEI", "EMO", "WDI", "PIM"}
    assert "RMT" not in {r.ticker for r in ft_summ}

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
    nt_2025_official = parse_distribution_html(
        (ROOT / "northern_trust" / "2025_capital_gain_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://ntam.northerntrust.com/content/dam/ntam/us/en/documents/"
            "account-resources/tax-center/all-investor/estimated-capital-gains-2025.pdf"
        ),
        fund_family="Northern Trust",
    )
    nosix_2025_official = next(
        r
        for r in nt_2025_official
        if r.ticker == "NOSIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nosix_2025_official.publication_stage == PublicationStage.final
    nomix = next(
        r
        for r in nt
        if r.ticker == "NOMIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nomix.amount == Decimal("1.011150")

    msim = parse_distribution_html(
        (ROOT / "morgan_stanley" / "2025_etf_year_end_sample.html").read_text(encoding="utf-8"),
        source_url="fixture://msim",
        fund_family="Morgan Stanley Investment Management",
    )
    cvlc = next(r for r in msim if r.ticker == "CVLC" and r.estimate_type == EstimateType.ordinary_income)
    assert cvlc.amount == Decimal("0.283927")
    msim_leftover_2024 = parse_distribution_html(
        (ROOT / "morgan_stanley" / "leftover_etf_year_end_2024.html").read_text(encoding="utf-8"),
        source_url="fixture://msim-leftover-2024",
        fund_family="Morgan Stanley Investment Management",
    )
    cdei_2024 = next(
        r
        for r in msim_leftover_2024
        if r.ticker == "CDEI" and r.estimate_type == EstimateType.ordinary_income
    )
    assert cdei_2024.amount == Decimal("0.232960")
    evim_2024 = next(
        r
        for r in msim_leftover_2024
        if r.ticker == "EVIM" and r.estimate_type == EstimateType.ordinary_income
    )
    assert evim_2024.amount == Decimal("0.166867")

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
    assert ievax.publication_stage == PublicationStage.preliminary_estimate

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
    assert {r.ticker for r in amundi} >= {
        "PIODX",
        "PIGFX",
        "PEQIX",
        "PIOTX",
        "AOBLX",
        "PINDX",
        "CVFCX",
        "GLOSX",
        "PIIFX",
        "PCGRX",
        "PGOFX",
        "PIALX",
    }
    aoblx_st = next(
        r
        for r in amundi
        if r.ticker == "AOBLX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert aoblx_st.amount == Decimal("0.03")

    amundi_final = parse_distribution_html(
        (ROOT / "amundi" / "2025_final_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://amundi-final",
        fund_family="Amundi US / Pioneer",
    )
    piodx_final = next(
        r
        for r in amundi_final
        if r.ticker == "PIODX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert piodx_final.amount == Decimal("3.4776")
    assert not any(r.ticker == "XILSX" for r in amundi_final)
    acbax = next(
        r
        for r in amundi_final
        if r.ticker == "ACBAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert acbax.amount == Decimal("0.9951")
    assert not any(
        r.ticker == "ACBAX" and r.estimate_type == EstimateType.long_term_capital_gains
        for r in amundi_final
    )

    amundi_2024 = parse_distribution_html(
        (ROOT / "amundi" / "2024_final_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://amundi-2024",
        fund_family="Amundi US / Pioneer",
    )
    piodx_2024 = next(
        r
        for r in amundi_2024
        if r.ticker == "PIODX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert piodx_2024.amount == Decimal("4.1900")
    assert {r.ticker for r in amundi_2024} >= {"PGSVX", "PISVX", "AOBLX"}

    amundi_ncsr_bq = parse_distribution_html(
        (ROOT / "amundi" / "leftover_ncsr_2021_2022_wave_bq.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/78713/"
            "000119312524058913/d793426dncsr.htm"
        ),
        fund_family="Amundi US / Pioneer",
    )
    piodx_2022_oi = next(
        r
        for r in amundi_ncsr_bq
        if r.ticker == "PIODX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2022-12-31"
    )
    assert piodx_2022_oi.amount == Decimal("0.17")
    assert piodx_2022_oi.publication_stage == PublicationStage.final
    piodx_2021_cg = next(
        r
        for r in amundi_ncsr_bq
        if r.ticker == "PIODX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert piodx_2021_cg.amount == Decimal("6.07")
    piotx_2022_oi = next(
        r
        for r in amundi_ncsr_bq
        if r.ticker == "PIOTX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2022-12-31"
    )
    assert piotx_2022_oi.amount == Decimal("0.16")
    assert {r.ticker for r in amundi_ncsr_bq} == {"PIODX", "PIOTX"}
    assert not any(
        r.ticker
        in {
            "PCODX",
            "PIGFX",
            "PEQIX",
            "GHQIX",
            "KTRAX",
            "KGDAX",
            "TOLLX",
            "KTCAX",
        }
        for r in amundi_ncsr_bq
    )

    amundi_ncsr_bs = parse_distribution_html(
        (ROOT / "amundi" / "leftover_ncsr_2021_2022_wave_bs.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/869356/"
            "000119312524001420/d578736dncsr.htm"
        ),
        fund_family="Amundi US / Pioneer",
    )
    peqix_2022_oi = next(
        r
        for r in amundi_ncsr_bs
        if r.ticker == "PEQIX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2022-10-31"
    )
    assert peqix_2022_oi.amount == Decimal("0.59")
    assert peqix_2022_oi.publication_stage == PublicationStage.final
    peqix_2022_cg = next(
        r
        for r in amundi_ncsr_bs
        if r.ticker == "PEQIX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2022-10-31"
    )
    assert peqix_2022_cg.amount == Decimal("3.26")
    peqix_2021_oi = next(
        r
        for r in amundi_ncsr_bs
        if r.ticker == "PEQIX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert peqix_2021_oi.amount == Decimal("0.51")
    # 2021 CG is an official dash — never invent $0.
    assert not any(
        r.ticker == "PEQIX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-10-31"
        for r in amundi_ncsr_bs
    )
    assert {r.ticker for r in amundi_ncsr_bs} == {"PEQIX"}
    assert not any(
        r.ticker
        in {
            "PCEQX",
            "PYEQX",
            "PEQKX",
            "PQIRX",
            "PIODX",
            "PIOTX",
            "PIGFX",
            "GPEIX",
            "GHQIX",
            "KTRAX",
        }
        for r in amundi_ncsr_bs
    )

    amundi_ncsr_ca_fund = parse_distribution_html(
        (ROOT / "amundi" / "leftover_ncsr_pcodx_pyodx_piokx_2021_2024_wave_ca.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/78713/"
            "000119312525040547/d908634dncsr.htm"
        ),
        fund_family="Amundi US / Pioneer",
    )
    pcodx_2024_oi = next(
        r
        for r in amundi_ncsr_ca_fund
        if r.ticker == "PCODX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert pcodx_2024_oi.amount == Decimal("0.01")
    assert pcodx_2024_oi.publication_stage == PublicationStage.final
    pcodx_2021_cg = next(
        r
        for r in amundi_ncsr_ca_fund
        if r.ticker == "PCODX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert pcodx_2021_cg.amount == Decimal("6.07")
    assert not any(
        r.ticker == "PCODX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-12-31"
        for r in amundi_ncsr_ca_fund
    )
    assert {r.ticker for r in amundi_ncsr_ca_fund} == {"PCODX", "PYODX", "PIOKX"}
    assert not any(
        r.ticker
        in {
            "PIODX",
            "PIORX",
            "PCEQX",
            "PYEQX",
            "PEQKX",
            "PCCGX",
            "GLIFX",
        }
        for r in amundi_ncsr_ca_fund
    )

    amundi_ncsr_ca_core = parse_distribution_html(
        (ROOT / "amundi" / "leftover_ncsr_pcotx_pvfyx_pcekx_2021_2024_wave_ca.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/78758/"
            "000119312525040555/d921606dncsr.htm"
        ),
        fund_family="Amundi US / Pioneer",
    )
    pcotx_2024_oi = next(
        r
        for r in amundi_ncsr_ca_core
        if r.ticker == "PCOTX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert pcotx_2024_oi.amount == Decimal("0.08")
    pcekx_2021_oi = next(
        r
        for r in amundi_ncsr_ca_core
        if r.ticker == "PCEKX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert pcekx_2021_oi.amount == Decimal("0.19")
    assert {r.ticker for r in amundi_ncsr_ca_core} == {"PCOTX", "PVFYX", "PCEKX"}
    assert not any(
        r.ticker in {"PIOTX", "CERPX", "PCEQX", "PIODX", "PCODX"}
        for r in amundi_ncsr_ca_core
    )

    amundi_ncsr_bz = parse_distribution_html(
        (ROOT / "amundi" / "leftover_ncsr_pceqx_pyeqx_peqkx_2021_2024_wave_bz.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/869356/"
            "000119312525002069/d869528dncsr.htm"
        ),
        fund_family="Amundi US / Pioneer",
    )
    pceqx_2024_oi = next(
        r
        for r in amundi_ncsr_bz
        if r.ticker == "PCEQX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-10-31"
    )
    assert pceqx_2024_oi.amount == Decimal("0.38")
    assert pceqx_2024_oi.publication_stage == PublicationStage.final
    pyeqx_2023_cg = next(
        r
        for r in amundi_ncsr_bz
        if r.ticker == "PYEQX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2023-10-31"
    )
    assert pyeqx_2023_cg.amount == Decimal("3.55")
    peqkx_2021_oi = next(
        r
        for r in amundi_ncsr_bz
        if r.ticker == "PEQKX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert peqkx_2021_oi.amount == Decimal("0.66")
    # 2021 CG is an official dash — never invent $0.
    assert not any(
        r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-10-31"
        for r in amundi_ncsr_bz
    )
    assert {r.ticker for r in amundi_ncsr_bz} == {"PCEQX", "PYEQX", "PEQKX"}
    assert not any(
        r.ticker
        in {
            "PEQIX",
            "PQIRX",
            "PCCGX",
            "PYCGX",
            "PMCKX",
            "LZIEX",
            "GLIFX",
            "RAIIX",
            "HMDCX",
            "PCODX",
            "PYODX",
            "PIOKX",
            "PCOTX",
            "PVFYX",
            "PCEKX",
        }
        for r in amundi_ncsr_bz
    )

    amundi_ncsr_cc_fund = parse_distribution_html(
        (ROOT / "amundi" / "leftover_ncsr_piorx_2021_2024_wave_cc.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/78713/"
            "000119312525040547/d908634dncsr.htm#class-r"
        ),
        fund_family="Amundi US / Pioneer",
    )
    piorx_2024_oi = next(
        r
        for r in amundi_ncsr_cc_fund
        if r.ticker == "PIORX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert piorx_2024_oi.amount == Decimal("0.03")
    assert piorx_2024_oi.publication_stage == PublicationStage.final
    piorx_2021_cg = next(
        r
        for r in amundi_ncsr_cc_fund
        if r.ticker == "PIORX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert piorx_2021_cg.amount == Decimal("6.07")
    assert not any(
        r.ticker == "PIORX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-12-31"
        for r in amundi_ncsr_cc_fund
    )
    assert {r.ticker for r in amundi_ncsr_cc_fund} == {"PIORX"}
    assert not any(
        r.ticker in {"PIODX", "PCODX", "PYODX", "PIOKX", "RLEMX", "RLIEX"}
        for r in amundi_ncsr_cc_fund
    )

    amundi_ncsr_cc_ei = parse_distribution_html(
        (ROOT / "amundi" / "leftover_ncsr_pqirx_2021_2024_wave_cc.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/869356/"
            "000119312525002069/d869528dncsr.htm#class-r"
        ),
        fund_family="Amundi US / Pioneer",
    )
    pqirx_2024_oi = next(
        r
        for r in amundi_ncsr_cc_ei
        if r.ticker == "PQIRX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-10-31"
    )
    assert pqirx_2024_oi.amount == Decimal("0.48")
    assert not any(
        r.ticker == "PQIRX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-10-31"
        for r in amundi_ncsr_cc_ei
    )
    assert {r.ticker for r in amundi_ncsr_cc_ei} == {"PQIRX"}
    assert not any(
        r.ticker in {"PEQIX", "PCEQX", "PYEQX", "PEQKX", "RLEMX", "GLFOX"}
        for r in amundi_ncsr_cc_ei
    )

    ft_2024 = parse_distribution_html(
        (ROOT / "franklin_templeton" / "2024_section_19a.html").read_text(encoding="utf-8"),
        source_url="fixture://ft-2024",
        fund_family="Franklin Templeton",
    )
    ft_2024_inc = next(
        r for r in ft_2024 if r.ticker == "FT" and r.estimate_type == EstimateType.ordinary_income
    )
    assert ft_2024_inc.amount == Decimal("0.0387")
    assert str(ft_2024_inc.as_of) == "2024-11-30"

    bny_2024 = parse_distribution_html(
        (ROOT / "bny_mellon" / "2024_paid_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://bny-2024",
        fund_family="BNY Mellon / Dreyfus",
    )
    dgagx_2024 = next(
        r
        for r in bny_2024
        if r.ticker == "DGAGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dgagx_2024.amount == Decimal("5.6247")
    assert dgagx_2024.publication_stage == PublicationStage.final

    nt_2024 = parse_distribution_html(
        (ROOT / "northern_trust" / "2024_capital_gain_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://nt-2024",
        fund_family="Northern Trust",
    )
    nosix_2024 = next(
        r
        for r in nt_2024
        if r.ticker == "NOSIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nosix_2024.amount == Decimal("0.699110")
    assert str(nosix_2024.as_of) == "2024-12-19"
    nt_2024_official = parse_distribution_html(
        (ROOT / "northern_trust" / "2024_capital_gain_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://ntam.northerntrust.com/content/dam/northerntrust/"
            "investment-management/global/en/documents/account-resources/"
            "tax-center/estimated-capital-gains-2024.pdf"
        ),
        fund_family="Northern Trust",
    )
    nosix_2024_official = next(
        r
        for r in nt_2024_official
        if r.ticker == "NOSIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nosix_2024_official.publication_stage == PublicationStage.final

    nt_2021 = parse_distribution_html(
        (ROOT / "northern_trust" / "2021_capital_gain_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://nt-2021",
        fund_family="Northern Trust",
    )
    nosix_2021 = next(
        r
        for r in nt_2021
        if r.ticker == "NOSIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nosix_2021.amount == Decimal("0.985777")
    assert str(nosix_2021.record_date) == "2021-12-15"
    assert str(nosix_2021.payable_date) == "2021-12-16"
    assert nosix_2021.publication_stage == PublicationStage.final
    assert len({r.ticker for r in nt_2021 if r.ticker}) >= 15

    nt_2022 = parse_distribution_html(
        (ROOT / "northern_trust" / "2022_capital_gain_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://nt-2022",
        fund_family="Northern Trust",
    )
    nosix_2022 = next(
        r
        for r in nt_2022
        if r.ticker == "NOSIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nosix_2022.amount == Decimal("1.243605")
    nengx_2022 = next(
        r
        for r in nt_2022
        if r.ticker == "NENGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nengx_2022.amount == Decimal("1.892337")
    assert len({r.ticker for r in nt_2022 if r.ticker}) >= 15

    nt_2023 = parse_distribution_html(
        (ROOT / "northern_trust" / "2023_capital_gain_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://nt-2023",
        fund_family="Northern Trust",
    )
    nmi_2023 = next(
        r
        for r in nt_2023
        if r.ticker == "NMIEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nmi_2023.amount == Decimal("0.434841")
    assert len({r.ticker for r in nt_2023 if r.ticker}) >= 10

    assert nosix_2024.amount == Decimal("0.699110")
    nsgrx_2024 = next(
        r
        for r in nt_2024
        if r.ticker == "NSGRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nsgrx_2024.amount == Decimal("4.052773")
    nosgx_2024 = next(
        r
        for r in nt_2024
        if r.ticker == "NOSGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nosgx_2024.amount == Decimal("7.263053")
    assert len({r.ticker for r in nt_2024 if r.ticker}) >= 14

    msim_2024 = parse_distribution_html(
        (ROOT / "morgan_stanley" / "2024_etf_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://msim-2024",
        fund_family="Morgan Stanley Investment Management",
    )
    cvlc_2024 = next(
        r for r in msim_2024 if r.ticker == "CVLC" and r.estimate_type == EstimateType.ordinary_income
    )
    assert cvlc_2024.amount == Decimal("0.222291")

    schwab_2024 = parse_distribution_html(
        (ROOT / "schwab" / "2024_annual_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://schwab-2024",
        fund_family="Charles Schwab Investment Management",
    )
    swtsx_2024 = next(
        r
        for r in schwab_2024
        if r.ticker == "SWTSX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert swtsx_2024.amount == Decimal("1.2252")

    schwab_2021 = parse_distribution_html(
        (ROOT / "schwab" / "2021_annual_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://schwab-2021",
        fund_family="Charles Schwab Investment Management",
    )
    swtsx_2021 = next(
        r
        for r in schwab_2021
        if r.ticker == "SWTSX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert swtsx_2021.amount == Decimal("0.2022")
    swppx_2021 = next(
        r
        for r in schwab_2021
        if r.ticker == "SWPPX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert swppx_2021.amount == Decimal("0.0678")

    schwab_2025 = parse_distribution_html(
        (ROOT / "schwab" / "2025_annual_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://schwab-2025",
        fund_family="Charles Schwab Investment Management",
    )
    swlsx_2025 = next(
        r
        for r in schwab_2025
        if r.ticker == "SWLSX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert swlsx_2025.amount == Decimal("0.4957")
    swanx_2025 = next(
        r
        for r in schwab_2025
        if r.ticker == "SWANX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert swanx_2025.amount == Decimal("1.5191")
    swssx_2025 = next(
        r
        for r in schwab_2025
        if r.ticker == "SWSSX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert swssx_2025.amount == Decimal("0.5123")
    assert len({r.ticker for r in schwab_2025 if r.ticker}) >= 70

    schwab_etf = parse_distribution_html(
        (ROOT / "schwab" / "etf_product_page_distributions.html").read_text(encoding="utf-8"),
        source_url="https://www.schwabassetmanagement.com/products/schd",
        fund_family="Charles Schwab Investment Management",
    )
    schd_2025 = next(
        r
        for r in schwab_etf
        if r.ticker == "SCHD"
        and r.estimate_type == EstimateType.ordinary_income
        and r.amount == Decimal("0.2782")
    )
    assert str(schd_2025.ex_date) == "2025-12-10"
    assert {"SCHD", "SCHX", "SCHB", "SCHF", "SCHG"} <= {r.ticker for r in schwab_etf}

    dfa_2024 = parse_distribution_html(
        (ROOT / "dimensional" / "2024_capital_gain_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://dfa-2024",
        fund_family="Dimensional Fund Advisors",
    )
    disvx_2024 = next(
        r
        for r in dfa_2024
        if r.ticker == "DISVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert disvx_2024.amount == Decimal("0.184")
    dfelx_2024 = next(
        r
        for r in dfa_2024
        if r.ticker == "DFELX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dfelx_2024.amount == Decimal("0.012")
    dfqtx_2024_inc = next(
        r
        for r in dfa_2024
        if r.ticker == "DFQTX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert dfqtx_2024_inc.amount == Decimal("0.101")
    assert len({r.ticker for r in dfa_2024 if r.ticker}) >= 130

    columbia_2024 = parse_distribution_html(
        (ROOT / "columbia_threadneedle" / "2024_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://columbia-2024",
        fund_family="Columbia Threadneedle",
    )
    lbsax = next(
        r
        for r in columbia_2024
        if r.ticker == "LBSAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert lbsax.amount == Decimal("1.38581")
    assert lbsax.publication_stage == PublicationStage.final
    elgax_2024 = next(
        r
        for r in columbia_2024
        if r.ticker == "ELGAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert elgax_2024.amount == Decimal("0.72066")
    legax_2024 = next(
        r
        for r in columbia_2024
        if r.ticker == "LEGAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert legax_2024.amount == Decimal("4.05105")
    gsftx_2024 = next(
        r
        for r in columbia_2024
        if r.ticker == "GSFTX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert gsftx_2024.amount == Decimal("1.38581")
    assert len({r.ticker for r in columbia_2024 if r.ticker}) >= 180

    columbia_2025 = parse_distribution_html(
        (ROOT / "columbia_threadneedle" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://columbia-2025",
        fund_family="Columbia Threadneedle",
    )
    lbsax_2025 = next(
        r
        for r in columbia_2025
        if r.ticker == "LBSAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert lbsax_2025.amount == Decimal("1.33133")
    cblax_2025 = next(
        r
        for r in columbia_2025
        if r.ticker == "CBLAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cblax_2025.amount == Decimal("2.11142")
    cblax_2025_st = next(
        r
        for r in columbia_2025
        if r.ticker == "CBLAX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert cblax_2025_st.amount == Decimal("0.38493")
    legax_2025 = next(
        r
        for r in columbia_2025
        if r.ticker == "LEGAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert legax_2025.amount == Decimal("6.79982")
    elgax_2025 = next(
        r
        for r in columbia_2025
        if r.ticker == "ELGAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert elgax_2025.amount == Decimal("0.87597")
    cddrx_2025 = next(
        r
        for r in columbia_2025
        if r.ticker == "CDDRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cddrx_2025.amount == Decimal("1.33133")
    assert len({r.ticker for r in columbia_2025 if r.ticker}) >= 200

    columbia_2022 = parse_distribution_html(
        (ROOT / "columbia_threadneedle" / "2022_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://columbia-2022",
        fund_family="Columbia Threadneedle",
    )
    lbsax_2022 = next(
        r
        for r in columbia_2022
        if r.ticker == "LBSAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert lbsax_2022.amount == Decimal("0.56114")
    cblax_2022 = next(
        r
        for r in columbia_2022
        if r.ticker == "CBLAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cblax_2022.amount == Decimal("1.55549")
    assert lbsax_2022.publication_stage == PublicationStage.final
    assert len({r.ticker for r in columbia_2022 if r.ticker}) >= 30

    columbia_wave_am = parse_distribution_html(
        (ROOT / "columbia_threadneedle" / "leftover_paid_year_end_wave_am.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.columbiathreadneedleus.com/binaries/content/assets/"
            "cti/public/2022_cap_gains_year_end.pdf"
        ),
        fund_family="Columbia Threadneedle",
    )
    umlgx_2022_lt = next(
        r
        for r in columbia_wave_am
        if r.ticker == "UMLGX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2022-12-08"
    )
    assert umlgx_2022_lt.amount == Decimal("0.00")
    assert umlgx_2022_lt.publication_stage == PublicationStage.final
    creax_2021_cg = next(
        r
        for r in columbia_wave_am
        if r.ticker == "CREAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert creax_2021_cg.amount == Decimal("0.84")
    creax_2021_oi = next(
        r
        for r in columbia_wave_am
        if r.ticker == "CREAX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert creax_2021_oi.amount == Decimal("0.17")
    crrvx_2021_cg = next(
        r
        for r in columbia_wave_am
        if r.ticker == "CRRVX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert crrvx_2021_cg.amount == Decimal("0.84")
    creyx_2021_oi = next(
        r
        for r in columbia_wave_am
        if r.ticker == "CREYX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert creyx_2021_oi.amount == Decimal("0.23")
    assert {r.ticker for r in columbia_wave_am if r.ticker} >= {
        "UMLGX",
        "CSVFX",
        "CREEX",
        "CREAX",
        "CRRVX",
        "CREYX",
        "CGEZX",
        "NSEPX",
        "CSCZX",
        "CBALX",
        "CBMZX",
        "CZMGX",
    }
    # Class-level — WAVE Z Institutional CREEX 2021 is not re-emitted here.
    assert not any(
        r.ticker == "CREEX" and r.as_of and str(r.as_of) == "2021-12-31"
        for r in columbia_wave_am
    )

    bny_2021 = parse_distribution_html(
        (ROOT / "bny_mellon" / "2021_paid_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://bny-2021",
        fund_family="BNY Mellon / Dreyfus",
    )
    dgagx_2021 = next(
        r
        for r in bny_2021
        if r.ticker == "DGAGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dgagx_2021.amount == Decimal("1.6171")
    dagvx_2021 = next(
        r
        for r in bny_2021
        if r.ticker == "DAGVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dagvx_2021.amount == Decimal("6.714")
    assert {r.ticker for r in bny_2021 if r.ticker} >= {
        "DGAGX",
        "DAGVX",
        "DREVX",
        "DREQX",
        "DNLDX",
        "PGROX",
        "DGLAX",
    }

    dfa_2023 = parse_distribution_html(
        (ROOT / "dimensional" / "2023_tax_sheet_paid.html").read_text(encoding="utf-8"),
        source_url="fixture://dfa-2023",
        fund_family="Dimensional Fund Advisors",
    )
    disvx_2023 = next(
        r
        for r in dfa_2023
        if r.ticker == "DISVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert disvx_2023.amount == Decimal("0.02562")
    dfqtx_2023 = next(
        r
        for r in dfa_2023
        if r.ticker == "DFQTX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dfqtx_2023.amount == Decimal("0.13191")
    assert disvx_2023.publication_stage == PublicationStage.final
    assert not any(r.amount_unit.value == "percent" for r in dfa_2023)

    dfa_2025_paid = parse_distribution_html(
        (ROOT / "dimensional" / "2025_tax_sheet_paid.html").read_text(encoding="utf-8"),
        source_url="fixture://dfa-2025-paid",
        fund_family="Dimensional Fund Advisors",
    )
    disvx_2025_paid = next(
        r
        for r in dfa_2025_paid
        if r.ticker == "DISVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert disvx_2025_paid.amount == Decimal("1.05997")
    dfelx_2025_paid = next(
        r
        for r in dfa_2025_paid
        if r.ticker == "DFELX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dfelx_2025_paid.amount == Decimal("1.23371")


def test_third_tier_fixtures() -> None:
    allspring = parse_distribution_html(
        (ROOT / "allspring" / "2025_paid_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://allspring",
        fund_family="Allspring",
    )
    wfmix = next(
        r
        for r in allspring
        if r.ticker == "WFMIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wfmix.amount == Decimal("4.26857")

    janus = parse_distribution_html(
        (ROOT / "janus_henderson" / "2025_final_distribution_estimates.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://janus",
        fund_family="Janus Henderson",
    )
    jdcax = next(
        r
        for r in janus
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jdcax.amount == Decimal("6.92")
    assert jdcax.cusip == "47103A674"

    aci = parse_distribution_html(
        (ROOT / "american_century" / "2025_estimated_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://aci",
        fund_family="American Century",
    )
    twcgx = next(
        r
        for r in aci
        if r.ticker == "TWCGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert twcgx.amount == Decimal("10.4978")

    dodge = parse_distribution_html(
        (ROOT / "dodge_cox" / "1q2026_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://dodge",
        fund_family="Dodge & Cox",
    )
    dodgx = next(
        r
        for r in dodge
        if r.ticker == "DODGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dodgx.amount == Decimal("0.16")
    assert not any(r.ticker == "DODIX" for r in dodge)

    dodge_paid = parse_distribution_html(
        (ROOT / "dodge_cox" / "2025_supplemental_tax_letter.html").read_text(encoding="utf-8"),
        source_url="https://www.dodgeandcox.com/content/dam/dc/us/en/pdf/guides/dc_us_supplemental_tax_letter.pdf",
        fund_family="Dodge & Cox",
    )
    dodix = [
        r
        for r in dodge_paid
        if r.ticker == "DODIX" and r.estimate_type == EstimateType.ordinary_income
    ]
    assert len(dodix) == 1
    assert dodix[0].amount == Decimal("0.1347")
    assert str(dodix[0].record_date) == "2025-12-17"
    assert not any(
        r.ticker == "DODIX"
        and r.estimate_type
        in {EstimateType.short_term_capital_gains, EstimateType.long_term_capital_gains}
        for r in dodge_paid
    )

    dodge_2021 = parse_distribution_html(
        (ROOT / "dodge_cox" / "2021_supplemental_tax_letter.html").read_text(encoding="utf-8"),
        source_url="https://api-v1.dodgeandcox.com/api/funds-distribution",
        fund_family="Dodge & Cox",
    )
    dodix_2021 = next(
        r
        for r in dodge_2021
        if r.ticker == "DODIX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert dodix_2021.amount == Decimal("0.0570")
    assert str(dodix_2021.as_of) == "2021-12-20"
    dodgx_2021 = next(
        r
        for r in dodge_2021
        if r.ticker == "DODGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dodgx_2021.amount == Decimal("3.3800")

    dodge_2022 = parse_distribution_html(
        (ROOT / "dodge_cox" / "2022_supplemental_tax_letter.html").read_text(encoding="utf-8"),
        source_url="https://api-v1.dodgeandcox.com/api/funds-distribution",
        fund_family="Dodge & Cox",
    )
    assert next(
        r
        for r in dodge_2022
        if r.ticker == "DODIX" and r.estimate_type == EstimateType.ordinary_income
    ).amount == Decimal("0.1010")

    dodge_2023 = parse_distribution_html(
        (ROOT / "dodge_cox" / "2023_supplemental_tax_letter.html").read_text(encoding="utf-8"),
        source_url="https://api-v1.dodgeandcox.com/api/funds-distribution",
        fund_family="Dodge & Cox",
    )
    assert next(
        r
        for r in dodge_2023
        if r.ticker == "DODIX" and r.estimate_type == EstimateType.ordinary_income
    ).amount == Decimal("0.1290")
    assert not any(
        r.ticker == "DODIX"
        and r.estimate_type
        in {EstimateType.short_term_capital_gains, EstimateType.long_term_capital_gains}
        for r in dodge_2023
    )

    mfs = parse_distribution_html(
        (ROOT / "mfs" / "2025_capital_gain_estimates.html").read_text(encoding="utf-8"),
        source_url="fixture://mfs",
        fund_family="MFS Investment Management",
    )
    mighx = next(
        r
        for r in mfs
        if r.ticker == "MIGHX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mighx.amount_min == Decimal("8")
    assert mighx.amount_max == Decimal("9")
    assert mighx.amount_unit == AmountUnit.percent_of_nav
    assert len({(r.ticker or "").upper() or r.fund_name for r in mfs}) >= 80
    mfs_value = next(
        r
        for r in mfs
        if "Value Fund" in r.fund_name and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mfs_value.amount_min == Decimal("6")
    assert mfs_value.amount_max == Decimal("7")

    lord = parse_distribution_html(
        (ROOT / "lord_abbett" / "2025_funds_not_expected_to_pay.html").read_text(encoding="utf-8"),
        source_url="fixture://lord",
        fund_family="Lord Abbett",
    )
    lbndx = next(
        r
        for r in lord
        if r.ticker == "LBNDX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert lbndx.amount == Decimal("0.00")

    ab = parse_distribution_html(
        (ROOT / "ab" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://ab",
        fund_family="AllianceBernstein",
    )
    agrfx = next(
        r
        for r in ab
        if r.ticker == "AGRFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert agrfx.amount == Decimal("16.36")

    federated = parse_distribution_html(
        (ROOT / "federated_hermes" / "2025_section_19a_sample.html").read_text(encoding="utf-8"),
        source_url="fixture://federated",
        fund_family="Federated Hermes",
    )
    payr = next(
        r
        for r in federated
        if r.ticker == "PAYR" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert payr.amount == Decimal("0.015178")

    federated_prelim = parse_distribution_html(
        (ROOT / "federated_hermes" / "2025_preliminary_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://federated-prelim",
        fund_family="Federated Hermes",
    )
    kauax = next(
        r
        for r in federated_prelim
        if r.ticker == "KAUAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert kauax.amount == Decimal("0.638052")
    assert kauax.publication_stage == PublicationStage.preliminary_estimate
    assert len({r.ticker for r in federated_prelim if r.ticker}) >= 80

    federated_leftover = parse_distribution_html(
        (ROOT / "federated_hermes" / "leftover_paid_year_end_parallel_n.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://www.federatedhermes.com/external/open/corpwebsite/v1/api/FinalCapitalGains",
        fund_family="Federated Hermes",
    )
    klcax_paid = next(
        r
        for r in federated_leftover
        if r.ticker == "KLCAX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2025-12-08"
    )
    assert klcax_paid.amount == Decimal("4.99671721")
    assert klcax_paid.publication_stage == PublicationStage.final
    assert "QRLGX" not in {r.ticker for r in federated_leftover}

    federated_ncsr = parse_distribution_html(
        (ROOT / "federated_hermes" / "leftover_ncsr_kaufmann_sdg_2021_2022_wave_aw.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/745968/"
            "000162363222001593/fef632-form.htm"
        ),
        fund_family="Federated Hermes",
    )
    kauax_ncsr = next(
        r
        for r in federated_ncsr
        if r.ticker == "KAUAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2022-10-31"
    )
    assert kauax_ncsr.amount == Decimal("0.65")
    assert kauax_ncsr.publication_stage == PublicationStage.final
    fkasx_ncsr = next(
        r
        for r in federated_ncsr
        if r.ticker == "FKASX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2022-10-31"
    )
    assert fkasx_ncsr.amount == Decimal("4.93")
    fheqx_ncsr = next(
        r
        for r in federated_ncsr
        if r.ticker == "FHEQX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert fheqx_ncsr.amount == Decimal("0.11")
    assert {r.ticker for r in federated_ncsr} == {
        "KAUAX",
        "KAUCX",
        "KAUFX",
        "KAUIX",
        "FKASX",
        "FKCSX",
        "FKAIX",
        "FHEQX",
        "FHESX",
    }

    federated_ncsr_ci = parse_distribution_html(
        (ROOT / "federated_hermes" / "leftover_ncsr_svalx_2021_2025_wave_ci.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/745968/"
            "000162363225001789/fef2029-form.htm#svalx-r6"
        ),
        fund_family="Federated Hermes",
    )
    svalx_2025_oi = next(
        r
        for r in federated_ncsr_ci
        if r.ticker == "SVALX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2025-10-31"
    )
    assert svalx_2025_oi.amount == Decimal("0.22")
    assert svalx_2025_oi.publication_stage == PublicationStage.final
    svalx_2025_cg = next(
        r
        for r in federated_ncsr_ci
        if r.ticker == "SVALX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2025-10-31"
    )
    assert svalx_2025_cg.amount == Decimal("0.11")
    svalx_2023_oi = next(
        r
        for r in federated_ncsr_ci
        if r.ticker == "SVALX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2023-10-31"
    )
    assert svalx_2023_oi.amount == Decimal("0.24")
    svalx_2021_oi = next(
        r
        for r in federated_ncsr_ci
        if r.ticker == "SVALX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2021-10-31"
    )
    assert svalx_2021_oi.amount == Decimal("0.21")
    assert not any(
        r.ticker == "SVALX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and r.as_of.year in {2021, 2022, 2024}
        for r in federated_ncsr_ci
    )
    assert {r.ticker for r in federated_ncsr_ci} == {"SVALX"}
    assert not any(
        r.ticker
        in {
            "SVAAX",
            "SVACX",
            "SVAIX",
            "HLEMX",
            "HLGZX",
            "HLIZX",
            "HLFZX",
            "RALIX",
            "ALBAX",
            "ALBCX",
            "AGIZX",
        }
        for r in federated_ncsr_ci
    )

    virtus = parse_distribution_html(
        (ROOT / "virtus" / "2026_june_capital_gain_estimates.html").read_text(encoding="utf-8"),
        source_url="fixture://virtus",
        fund_family="Virtus",
    )
    unwgx = next(
        r
        for r in virtus
        if r.ticker == "UNWGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert unwgx.amount == Decimal("2.4917")

    ev = parse_distribution_html(
        (ROOT / "eaton_vance" / "2025_cef_section_19b_sample.html").read_text(encoding="utf-8"),
        source_url="fixture://ev",
        fund_family="Eaton Vance",
    )
    eoi = next(
        r
        for r in ev
        if r.ticker == "EOI" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert eoi.amount == Decimal("0.1338")

    allspring_2024 = parse_distribution_html(
        (ROOT / "allspring" / "2024_paid_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://allspring-2024",
        fund_family="Allspring",
    )
    wfmix_2024 = next(
        r
        for r in allspring_2024
        if r.ticker == "WFMIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wfmix_2024.amount == Decimal("2.93497")
    assert wfmix_2024.publication_stage == PublicationStage.final

    allspring_2021 = parse_distribution_html(
        (ROOT / "allspring" / "2021_paid_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://allspring-2021",
        fund_family="Allspring",
    )
    wfmix_2021 = next(
        r
        for r in allspring_2021
        if r.ticker == "WFMIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    sgrnx_2021 = next(
        r
        for r in allspring_2021
        if r.ticker == "SGRNX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wfmix_2021.amount == Decimal("3.75956")
    assert sgrnx_2021.amount == Decimal("8.36656")
    eivix_2021 = next(
        r
        for r in allspring_2021
        if r.ticker == "EIVIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert eivix_2021.amount == Decimal("2.51286")
    emgnx_2021 = next(
        r
        for r in allspring_2021
        if r.ticker == "EMGNX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert emgnx_2021.amount == Decimal("0.18764")

    janus_2024 = parse_distribution_html(
        (ROOT / "janus_henderson" / "2024_distribution_estimates.html").read_text(encoding="utf-8"),
        source_url="fixture://janus-2024",
        fund_family="Janus Henderson",
    )
    jdcax_2024 = next(
        r
        for r in janus_2024
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jdcax_2024.amount == Decimal("5.42")
    assert str(jdcax_2024.as_of) == "2024-11-01"

    janus_2023 = parse_distribution_html(
        (ROOT / "janus_henderson" / "2023_final_distribution_estimates.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://janus-2023",
        fund_family="Janus Henderson",
    )
    jdcax_2023 = next(
        r
        for r in janus_2023
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jdcax_2023.amount == Decimal("3.87")

    janus_ici_2023 = parse_ici_primary(
        (ROOT / "janus_henderson" / "ici_primary_2023.csv").read_text(encoding="utf-8"),
        source_url="fixture://janus-ici-2023",
        fund_family="Janus Henderson",
    )
    jdcax_ici_2023 = next(
        r
        for r in janus_ici_2023
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jdcax_ici_2023.amount == Decimal("3.88875")
    assert jdcax_ici_2023.publication_stage == PublicationStage.final
    assert str(jdcax_ici_2023.as_of) == "2023-12-31"
    assert len({r.ticker for r in janus_ici_2023 if r.ticker}) >= 140

    janus_ici_2024 = parse_ici_primary(
        (ROOT / "janus_henderson" / "ici_primary_2024.csv").read_text(encoding="utf-8"),
        source_url="fixture://janus-ici-2024",
        fund_family="Janus Henderson",
    )
    jdcax_ici_2024 = next(
        r
        for r in janus_ici_2024
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jdcax_ici_2024.amount == Decimal("5.46939")
    jdcax_ici_2024_st = next(
        r
        for r in janus_ici_2024
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert jdcax_ici_2024_st.amount == Decimal("0.19019347")

    janus_ici_2025 = parse_ici_primary(
        (ROOT / "janus_henderson" / "ici_primary_2025.csv").read_text(encoding="utf-8"),
        source_url="fixture://janus-ici-2025",
        fund_family="Janus Henderson",
    )
    jdcax_ici_2025 = next(
        r
        for r in janus_ici_2025
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jdcax_ici_2025.amount == Decimal("6.96694")
    assert len({r.ticker for r in janus_ici_2025 if r.ticker}) >= 140

    janus_ici_2022 = parse_ici_primary(
        (ROOT / "janus_henderson" / "ici_primary_2022.csv").read_text(encoding="utf-8"),
        source_url="fixture://janus-ici-2022",
        fund_family="Janus Henderson",
    )
    jdcax_ici_2022 = next(
        r
        for r in janus_ici_2022
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jdcax_ici_2022.amount == Decimal("0.02107")
    assert str(jdcax_ici_2022.as_of) == "2022-12-31"
    assert len({r.ticker for r in janus_ici_2022 if r.ticker}) >= 140

    janus_ici_2021 = parse_ici_primary(
        (ROOT / "janus_henderson" / "ici_primary_2021.csv").read_text(encoding="utf-8"),
        source_url="fixture://janus-ici-2021",
        fund_family="Janus Henderson",
    )
    jdcax_ici_2021 = next(
        r
        for r in janus_ici_2021
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jdcax_ici_2021.amount == Decimal("4.95363")
    jdcax_ici_2021_st = next(
        r
        for r in janus_ici_2021
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert jdcax_ici_2021_st.amount == Decimal("0.25332800")
    assert str(jdcax_ici_2021.as_of) == "2021-12-31"
    assert len({r.ticker for r in janus_ici_2021 if r.ticker}) >= 170

    janus_2022 = parse_distribution_html(
        (ROOT / "janus_henderson" / "2022_final_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://janus-2022-final",
        fund_family="Janus Henderson",
    )
    jdcax_2022 = next(
        r
        for r in janus_2022
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jdcax_2022.amount == Decimal("0.02107")
    assert jdcax_2022.publication_stage == PublicationStage.final
    assert str(jdcax_2022.as_of) == "2022-12-20"
    jdcax_2022_income = next(
        r
        for r in janus_2022
        if r.ticker == "JDCAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert jdcax_2022_income.amount == Decimal("0")

    janus_2021 = parse_distribution_html(
        (ROOT / "janus_henderson" / "2021_final_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://janus-2021-final",
        fund_family="Janus Henderson",
    )
    jdbax_2021 = next(
        r
        for r in janus_2021
        if r.ticker == "JDBAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jdbax_2021.amount == Decimal("1.50790")
    assert jdbax_2021.publication_stage == PublicationStage.final
    assert str(jdbax_2021.as_of) == "2021-12-22"
    assert not any(r.ticker == "JDCAX" for r in janus_2021)

    aci_paid = parse_distribution_html(
        (ROOT / "american_century" / "2025_paid_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://aci-paid",
        fund_family="American Century",
    )
    aci_2023 = parse_distribution_html(
        (ROOT / "american_century" / "2023_estimated_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://aci-2023",
        fund_family="American Century",
    )
    twcgx_2023 = next(
        r
        for r in aci_2023
        if r.ticker == "TWCGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert twcgx_2023.amount == Decimal("2.4201")
    assert twcgx_2023.publication_stage == PublicationStage.preliminary_estimate
    assert str(twcgx_2023.as_of) == "2023-10-31"
    twcgx_2023_st = next(
        r
        for r in aci_2023
        if r.ticker == "TWCGX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert twcgx_2023_st.amount == Decimal("0.0349")
    assert len({r.ticker for r in aci_2023 if r.ticker}) >= 300

    aci_2022 = parse_distribution_html(
        (ROOT / "american_century" / "2022_estimated_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://aci-2022",
        fund_family="American Century",
    )
    twcgx_2022 = next(
        r
        for r in aci_2022
        if r.ticker == "TWCGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert twcgx_2022.amount == Decimal("0.7247")
    assert twcgx_2022.publication_stage == PublicationStage.preliminary_estimate
    assert str(twcgx_2022.as_of) == "2022-09-30"
    assert len({r.ticker for r in aci_2022 if r.ticker}) >= 250

    twcgx_paid = next(
        r
        for r in aci_paid
        if r.ticker == "TWCGX" and r.estimate_type == EstimateType.total_capital_gains
    )
    assert twcgx_paid.amount == Decimal("9.7631")

    dodge_2024 = parse_distribution_html(
        (ROOT / "dodge_cox" / "2024_supplemental_tax_letter.html").read_text(encoding="utf-8"),
        source_url="fixture://dodge-2024",
        fund_family="Dodge & Cox",
    )
    dodgx_2024 = next(
        r
        for r in dodge_2024
        if r.ticker == "DODGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dodgx_2024.amount == Decimal("12.036")
    assert str(dodgx_2024.as_of) == "2024-12-18"

    dodge_2025_gx = next(
        r
        for r in dodge_paid
        if r.ticker == "DODGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dodge_2025_gx.amount == Decimal("1.1999")

    mfs_paid = parse_distribution_html(
        (ROOT / "mfs" / "2025_paid_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://mfs-paid",
        fund_family="MFS Investment Management",
    )
    mighx_paid = next(
        r
        for r in mfs_paid
        if r.ticker == "MIGHX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mighx_paid.amount == Decimal("4.20618")
    mrgax_paid = next(
        r
        for r in mfs_paid
        if r.ticker == "MRGAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mrgax_paid.amount == Decimal("6.24390")
    magwx_paid = next(
        r
        for r in mfs_paid
        if r.ticker == "MAGWX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert magwx_paid.amount == Decimal("1.26392")

    mighx_years = {}
    for year, fname, expected in (
        (2024, "2024_paid_year_end.html", Decimal("3.30240")),
        (2023, "2023_paid_year_end.html", Decimal("1.38597")),
        (2022, "2022_paid_year_end.html", Decimal("1.28192")),
        (2021, "2021_paid_year_end.html", Decimal("3.35892")),
    ):
        rows = parse_distribution_html(
            (ROOT / "mfs" / fname).read_text(encoding="utf-8"),
            source_url=f"fixture://mfs-{year}",
            fund_family="MFS Investment Management",
        )
        lt = next(
            r
            for r in rows
            if r.ticker == "MIGHX" and r.estimate_type == EstimateType.long_term_capital_gains
        )
        assert lt.amount == expected
        mighx_years[year] = str(lt.as_of)[:4]
    assert mighx_years == {2024: "2024", 2023: "2023", 2022: "2022", 2021: "2021"}

    meiax_2021 = parse_distribution_html(
        (ROOT / "mfs" / "2021_paid_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://mfs-2021",
        fund_family="MFS Investment Management",
    )
    meiax_lt = next(
        r
        for r in meiax_2021
        if r.ticker == "MEIAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert meiax_lt.amount == Decimal("1.01429")
    mdidx_2021 = next(
        r
        for r in meiax_2021
        if r.ticker == "MDIDX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mdidx_2021.amount == Decimal("0.20404")
    mrgax_2021 = next(
        r
        for r in meiax_2021
        if r.ticker == "MRGAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mrgax_2021.amount == Decimal("2.03573")
    assert str(meiax_lt.record_date) == "2021-12-15"
    assert str(meiax_lt.ex_date) == "2021-12-16"
    assert str(meiax_lt.payable_date) == "2021-12-17"
    mfegx_2024 = parse_distribution_html(
        (ROOT / "mfs" / "2024_paid_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://mfs-2024",
        fund_family="MFS Investment Management",
    )
    mfegx_lt = next(
        r
        for r in mfegx_2024
        if r.ticker == "MFEGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mfegx_lt.amount == Decimal("25.50349")
    assert len({r.ticker for r in mfegx_2024 if r.ticker}) >= 10

    ab_2023 = parse_distribution_html(
        (ROOT / "ab" / "2023_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://ab-2023",
        fund_family="AllianceBernstein",
    )
    agrfx_2023 = next(
        r
        for r in ab_2023
        if r.ticker == "AGRFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert agrfx_2023.amount == Decimal("6.95")
    assert str(agrfx_2023.as_of) == "2023-10-31"
    apgax_2023 = next(
        r
        for r in ab_2023
        if r.ticker == "APGAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert apgax_2023.amount == Decimal("1.50")
    abasx_2023 = next(
        r
        for r in ab_2023
        if r.ticker == "ABASX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert abasx_2023.amount == Decimal("1.32")
    assert len({(r.ticker or "").upper() or r.fund_name for r in ab_2023}) >= 14

    virtus_2025 = parse_distribution_html(
        (ROOT / "virtus" / "2025_paid_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://virtus-2025",
        fund_family="Virtus",
    )
    stvtx_2025 = next(
        r
        for r in virtus_2025
        if r.ticker == "STVTX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert stvtx_2025.amount == Decimal("0.427834")

    virtus_2024 = parse_distribution_html(
        (ROOT / "virtus" / "2024_section_19a.html").read_text(encoding="utf-8"),
        source_url="fixture://virtus-2024",
        fund_family="Virtus",
    )
    stvtx_2024 = next(
        r
        for r in virtus_2024
        if r.ticker == "STVTX" and r.estimate_type == EstimateType.total_capital_gains
    )
    assert stvtx_2024.amount == Decimal("1.907616")

    virtus_ncsr = parse_distribution_html(
        (ROOT / "virtus" / "leftover_ncsr_asset_trust_2021_2024_wave_as.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1018593/"
            "000119312526093483/d65653dncsr.htm"
        ),
        fund_family="Virtus",
    )
    stvtx_ncsr = next(
        r
        for r in virtus_ncsr
        if r.ticker == "STVTX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert stvtx_ncsr.amount == Decimal("3.88")
    assert stvtx_ncsr.publication_stage == PublicationStage.final
    sviiix_ncsr = next(
        r
        for r in virtus_ncsr
        if r.ticker == "SVIIX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert sviiix_ncsr.amount == Decimal("0.10")
    assert {r.ticker for r in virtus_ncsr if r.as_of and r.as_of.year == 2025} == set()


def test_thrivent_live_header_shape() -> None:
    html = """
    <html><body>
    <table>
      <thead>
        <tr>
          <th>Thrivent Mutual Fund</th>
          <th>Record Date</th>
          <th>Payment Date</th>
          <th>Short-Term Capital Gain (Per Share)</th>
          <th>Long-Term Capital Gain (Per Share)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Mid Cap Stock Fund</td>
          <td>12/10/2025</td>
          <td>12/11/2025</td>
          <td>$ -</td>
          <td>$4.02</td>
        </tr>
      </tbody>
    </table>
    </body></html>
    """
    records = parse_distribution_html(html, source_url="https://www.thriventfunds.com/support/tax-resource-center/capital-gains.html", fund_family="Thrivent")
    lt = next(r for r in records if r.estimate_type == EstimateType.long_term_capital_gains)
    assert "Mid Cap Stock" in lt.fund_name
    assert lt.amount == Decimal("4.02")


def test_fourth_tier_fixtures() -> None:
    jh = parse_distribution_html(
        (ROOT / "john_hancock" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://jh",
        fund_family="John Hancock / Manulife",
    )
    tagrx = next(
        r
        for r in jh
        if r.ticker == "TAGRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tagrx.amount_min == Decimal("6.85")
    assert tagrx.amount_max == Decimal("7.60")

    principal = parse_distribution_html(
        (ROOT / "principal" / "2025_paid_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://principal",
        fund_family="Principal",
    )
    pqiax = next(
        r
        for r in principal
        if r.ticker == "PQIAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert pqiax.amount == Decimal("3.3687")

    principal_2024 = parse_distribution_html(
        (ROOT / "principal" / "2024_paid_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://principal-2024",
        fund_family="Principal",
    )
    pqiax_2024 = next(
        r
        for r in principal_2024
        if r.ticker == "PQIAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert pqiax_2024.amount == Decimal("3.6805")
    pemgx_2024 = next(
        r
        for r in principal_2024
        if r.ticker == "PEMGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert pemgx_2024.amount == Decimal("1.3963")

    principal_2023 = parse_distribution_html(
        (ROOT / "principal" / "2023_paid_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://principal-2023",
        fund_family="Principal",
    )
    pqiax_2023 = next(
        r
        for r in principal_2023
        if r.ticker == "PQIAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert pqiax_2023.amount == Decimal("0.2649")

    thrivent = parse_distribution_html(
        (ROOT / "thrivent" / "2025_paid_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://thrivent",
        fund_family="Thrivent",
    )
    tmsix = next(
        r
        for r in thrivent
        if r.ticker == "TMSIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tmsix.amount == Decimal("4.02")

    thrivent_2024 = parse_distribution_html(
        (ROOT / "thrivent" / "2024_paid_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://thrivent-2024",
        fund_family="Thrivent",
    )
    tmsix_2024 = next(
        r
        for r in thrivent_2024
        if r.ticker == "TMSIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tmsix_2024.amount == Decimal("1.33794")

    hartford = parse_distribution_html(
        (ROOT / "hartford" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://hartford",
        fund_family="Hartford Funds",
    )
    hfmcx = next(
        r
        for r in hartford
        if r.ticker == "HFMCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hfmcx.amount == Decimal("5.36")

    macquarie = parse_distribution_html(
        (ROOT / "macquarie" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://macquarie",
        fund_family="Macquarie / Delaware Funds",
    )
    wstax = next(
        r
        for r in macquarie
        if r.ticker == "WSTAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wstax.amount == Decimal("10.051")

    mac_2025_paid = parse_distribution_html(
        (ROOT / "macquarie" / "2025_paid_capital_gains.html").read_text(encoding="utf-8"),
        source_url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT",
        fund_family="Macquarie / Delaware Funds",
    )
    wstax_2025_paid = next(
        r
        for r in mac_2025_paid
        if r.ticker == "WSTAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wstax_2025_paid.amount == Decimal("10.603")
    assert wstax_2025_paid.publication_stage == PublicationStage.final

    first_eagle = parse_distribution_html(
        (ROOT / "first_eagle" / "2025_estimated_income_and_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://fei",
        fund_family="First Eagle",
    )
    sgenx = next(
        r
        for r in first_eagle
        if r.ticker == "SGENX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert sgenx.amount_min == Decimal("4.12")
    assert sgenx.amount_max == Decimal("4.17")
    sgenx_oi = next(
        r
        for r in first_eagle
        if r.ticker == "SGENX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert sgenx_oi.amount_min == Decimal("2.80")
    assert sgenx_oi.amount_max == Decimal("2.85")
    assert len({(r.ticker or "").upper() or r.fund_name for r in first_eagle}) >= 10
    fevax = next(
        r
        for r in first_eagle
        if r.ticker == "FEVAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert fevax.amount_min == Decimal("1.77")
    assert fevax.amount_max == Decimal("1.82")

    gmo = parse_distribution_html(
        (ROOT / "gmo" / "2026_july_distribution_estimates.html").read_text(encoding="utf-8"),
        source_url="fixture://gmo",
        fund_family="GMO",
    )
    gqetx = next(
        r
        for r in gmo
        if r.ticker == "GQETX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert gqetx.amount == Decimal("0.7242")

    gmo_etf = parse_distribution_html(
        (ROOT / "gmo" / "2025_etf_year_end_tax.html").read_text(encoding="utf-8"),
        source_url="fixture://gmo-etf-2025",
        fund_family="GMO",
    )
    bchi = next(
        r
        for r in gmo_etf
        if r.ticker == "BCHI" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert bchi.amount == Decimal("0.290000")
    invg = next(
        r
        for r in gmo_etf
        if r.ticker == "INVG" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert invg.amount == Decimal("0.065400")

    artisan = parse_distribution_html(
        (ROOT / "artisan" / "ytd_paid_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://artisan",
        fund_family="Artisan Partners",
    )
    artkx = next(
        r
        for r in artisan
        if r.ticker == "ARTKX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert artkx.amount == Decimal("0.338342")
    artisan_ici = parse_ici_primary(
        (ROOT / "artisan" / "ici_primary_2025.csv").read_text(encoding="utf-8"),
        source_url=(
            "https://www.artisanpartners.com/content/dam/documents/distributions/"
            "Year-End-Tax-Reporting-Information-2025.pdf"
        ),
        fund_family="Artisan Partners",
    )
    artix_lt = next(
        r
        for r in artisan_ici
        if r.ticker == "ARTIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert artix_lt.amount == Decimal("5.017255")
    artkx_lt = next(
        r
        for r in artisan_ici
        if r.ticker == "ARTKX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert artkx_lt.amount == Decimal("2.725068")
    assert len({r.ticker for r in artisan_ici}) >= 50

    artisan_ici_2024 = parse_ici_primary(
        (ROOT / "artisan" / "ici_primary_2024.csv").read_text(encoding="utf-8"),
        source_url=(
            "https://www.artisanpartners.com/content/dam/documents/distributions/"
            "Year-End-Tax-Reporting-Information-2024.pdf"
        ),
        fund_family="Artisan Partners",
    )
    artix_2024_lt = next(
        r
        for r in artisan_ici_2024
        if r.ticker == "ARTIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert artix_2024_lt.amount == Decimal("2.067175")
    artix_2024_st = next(
        r
        for r in artisan_ici_2024
        if r.ticker == "ARTIX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert artix_2024_st.amount == Decimal("0.456695")
    assert len({r.ticker for r in artisan_ici_2024}) >= 40

    calamos = parse_distribution_html(
        (ROOT / "calamos" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://calamos",
        fund_family="Calamos",
    )
    cvgrx = next(
        r
        for r in calamos
        if r.ticker == "CVGRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cvgrx.amount == Decimal("4.07")

    wasatch = parse_distribution_html(
        (ROOT / "wasatch" / "2025_year_end_distribution_estimates.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://wasatch",
        fund_family="Wasatch",
    )
    wgrox = next(
        r
        for r in wasatch
        if r.ticker == "WGROX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wgrox.amount == Decimal("6.01")

    jh_2024 = parse_distribution_html(
        (ROOT / "john_hancock" / "2024_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://jh-2024",
        fund_family="John Hancock / Manulife",
    )
    tagrx_2024 = next(
        r
        for r in jh_2024
        if r.ticker == "TAGRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tagrx_2024.amount_min == Decimal("7.80")
    assert tagrx_2024.amount_max == Decimal("8.80")

    jh_2022 = parse_distribution_html(
        (ROOT / "john_hancock" / "2022_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://jh-2022",
        fund_family="John Hancock / Manulife",
    )
    tagrx_2022 = next(
        r
        for r in jh_2022
        if r.ticker == "TAGRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tagrx_2022.amount_min == Decimal("3.00")
    assert tagrx_2022.amount_max == Decimal("3.60")

    hartford_final = parse_distribution_html(
        (ROOT / "hartford" / "2025_final_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://hartford-2025-final",
        fund_family="Hartford Funds",
    )
    hfmcx_final = next(
        r
        for r in hartford_final
        if r.ticker == "HFMCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hfmcx_final.amount == Decimal("5.44")
    assert hfmcx_final.publication_stage == PublicationStage.final

    hartford_2024 = parse_distribution_html(
        (ROOT / "hartford" / "2024_final_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://hartford-2024",
        fund_family="Hartford Funds",
    )
    hfmcx_2024 = next(
        r
        for r in hartford_2024
        if r.ticker == "HFMCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hfmcx_2024.amount == Decimal("1.67")
    haiax_2024 = next(
        r
        for r in hartford_2024
        if r.ticker == "HAIAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert haiax_2024.amount == Decimal("4.43")
    assert len({(r.ticker or "").upper() or r.fund_name for r in hartford_2024}) >= 14

    hartford_an = parse_distribution_html(
        (ROOT / "hartford" / "leftover_ncsr_share_classes_wave_an.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1006415/"
            "000119312524000389/d647714dncsr.htm"
        ),
        fund_family="Hartford Funds",
    )
    hdgix_2023_an = next(
        r
        for r in hartford_an
        if r.ticker == "HDGIX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2023-10-31"
    )
    assert hdgix_2023_an.amount == Decimal("1.37")
    assert hdgix_2023_an.publication_stage == PublicationStage.final
    hdgix_2021_an = next(
        r
        for r in hartford_an
        if r.ticker == "HDGIX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2021-10-31"
    )
    assert hdgix_2021_an.amount == Decimal("0.41")
    ihoax_2022_an = next(
        r
        for r in hartford_an
        if r.ticker == "IHOAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2022-10-31"
    )
    assert ihoax_2022_an.amount == Decimal("1.75")
    ihoax_2021_an = next(
        r
        for r in hartford_an
        if r.ticker == "IHOAX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2021-10-31"
    )
    assert ihoax_2021_an.amount == Decimal("0.07")
    assert "HDBAX" not in {r.ticker for r in hartford_an}
    assert "HBAIX" not in {r.ticker for r in hartford_an}
    assert "HCKIX" not in {r.ticker for r in hartford_an}

    hartford_bv = parse_distribution_html(
        (ROOT / "hartford" / "leftover_ncsr_hmdcx_2024_wave_bv.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1006415/"
            "000119312525001898/d905284dncsr.htm"
        ),
        fund_family="Hartford Funds",
    )
    hmdcx_2024_bv = next(
        r
        for r in hartford_bv
        if r.ticker == "HMDCX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2024-10-31"
    )
    assert hmdcx_2024_bv.amount == Decimal("0.59")
    assert hmdcx_2024_bv.publication_stage == PublicationStage.final
    hmdcx_2024_oi_bv = [
        r
        for r in hartford_bv
        if r.ticker == "HMDCX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2024-10-31"
    ]
    assert hmdcx_2024_oi_bv == []
    assert {r.ticker for r in hartford_bv} == {"HMDCX"}

    manning_bw = parse_distribution_html(
        (ROOT / "manning_napier" / "leftover_ncsr_raiix_2022_wave_bw.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/751173/"
            "000199937126000259/mn-ncsr_103125.htm"
        ),
        fund_family="Manning & Napier",
    )
    raiix_2022_bw = next(
        r
        for r in manning_bw
        if r.ticker == "RAIIX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2022-10-31"
    )
    assert raiix_2022_bw.amount == Decimal("0.51")
    assert raiix_2022_bw.publication_stage == PublicationStage.final
    raiix_2022_oi_bw = [
        r
        for r in manning_bw
        if r.ticker == "RAIIX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2022-10-31"
    ]
    assert raiix_2022_oi_bw == []
    assert {r.ticker for r in manning_bw} == {"RAIIX"}

    artisan_an = parse_distribution_html(
        (ROOT / "artisan" / "leftover_ncsr_2023_wave_an.html").read_text(encoding="utf-8"),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/935015/"
            "000199937123000698/artisan-ncsr_093023.htm"
        ),
        fund_family="Artisan Partners",
    )
    artmx_2023_an = next(
        r
        for r in artisan_an
        if r.ticker == "ARTMX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2023-09-30"
    )
    assert artmx_2023_an.amount == Decimal("0.08")
    assert artmx_2023_an.publication_stage == PublicationStage.final
    aphmx_2023_an = next(
        r
        for r in artisan_an
        if r.ticker == "APHMX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2023-09-30"
    )
    assert aphmx_2023_an.amount == Decimal("0.16")
    aphsx_2023_an = next(
        r
        for r in artisan_an
        if r.ticker == "APHSX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2023-09-30"
    )
    assert aphsx_2023_an.amount == Decimal("0.15")
    aphtx_2023_an = next(
        r
        for r in artisan_an
        if r.ticker == "APHTX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2023-09-30"
    )
    assert aphtx_2023_an.amount == Decimal("0.10")
    aphdX_2023_an = next(
        r
        for r in artisan_an
        if r.ticker == "APHDX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2023-09-30"
    )
    assert aphdX_2023_an.amount == Decimal("0.02")
    assert {r.ticker for r in artisan_an} == {
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
    }
    assert "APFDX" not in {r.ticker for r in artisan_an}
    assert "APDDX" not in {r.ticker for r in artisan_an}

    mac_2024 = parse_distribution_html(
        (ROOT / "macquarie" / "2024_paid_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://mac-2024",
        fund_family="Macquarie / Delaware Funds",
    )
    wstax_2024 = next(
        r
        for r in mac_2024
        if r.ticker == "WSTAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wstax_2024.amount == Decimal("8.135")
    wstax_2024_st = next(
        r
        for r in mac_2024
        if r.ticker == "WSTAX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert wstax_2024_st.amount == Decimal("1.108")
    wlgax_2024 = next(
        r
        for r in mac_2024
        if r.ticker == "WLGAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wlgax_2024.amount == Decimal("0.591")
    assert len({r.ticker for r in mac_2024 if r.ticker}) >= 15

    mac_2023 = parse_distribution_html(
        (ROOT / "macquarie" / "2023_paid_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://mac-2023",
        fund_family="Macquarie / Delaware Funds",
    )
    wstax_2023 = next(
        r
        for r in mac_2023
        if r.ticker == "WSTAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wstax_2023.amount == Decimal("5.331")

    mac_2022 = parse_distribution_html(
        (ROOT / "macquarie" / "2022_paid_capital_gains.html").read_text(encoding="utf-8"),
        source_url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET-ACT-2022",
        fund_family="Macquarie / Delaware Funds",
    )
    wstax_2022 = next(
        r
        for r in mac_2022
        if r.ticker == "WSTAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wstax_2022.amount == Decimal("12.373")
    assert wstax_2022.publication_stage == PublicationStage.final
    assert str(wstax_2023.record_date) == "2023-12-01"
    assert str(wstax_2023.ex_date) == "2023-12-04"
    assert str(wstax_2023.payable_date) == "2023-12-05"
    assert wstax_2023.publication_stage == PublicationStage.final
    assert len({r.ticker for r in mac_2023 if r.ticker}) >= 18

    fei_2024 = parse_distribution_html(
        (ROOT / "first_eagle" / "2024_paid_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://fei-2024",
        fund_family="First Eagle",
    )
    sgenx_2024 = next(
        r
        for r in fei_2024
        if r.ticker == "SGENX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert sgenx_2024.amount == Decimal("2.038")

    fei_2025_paid = parse_distribution_html(
        (ROOT / "first_eagle" / "2025_paid_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://fei-2025-paid",
        fund_family="First Eagle",
    )
    sgenx_2025_paid = next(
        r
        for r in fei_2025_paid
        if r.ticker == "SGENX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert sgenx_2025_paid.amount == Decimal("4.654")
    fefax_2025 = next(
        r
        for r in fei_2025_paid
        if r.ticker == "FEFAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert fefax_2025.amount == Decimal("2.015")
    fefax_st = next(
        r
        for r in fei_2025_paid
        if r.ticker == "FEFAX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert fefax_st.amount == Decimal("0.339")

    calamos_2024 = parse_distribution_html(
        (ROOT / "calamos" / "2024_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://calamos-2024",
        fund_family="Calamos",
    )
    cvgrx_2024 = next(
        r
        for r in calamos_2024
        if r.ticker == "CVGRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cvgrx_2024.amount == Decimal("1.84")

    wasatch_2024 = parse_distribution_html(
        (ROOT / "wasatch" / "2024_paid_year_end.html").read_text(encoding="utf-8"),
        source_url="fixture://wasatch-2024",
        fund_family="Wasatch",
    )
    wgrox_2024 = next(
        r
        for r in wasatch_2024
        if r.ticker == "WGROX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wgrox_2024.amount == Decimal("8.282696")

    wasatch_leftover = parse_distribution_html(
        (ROOT / "wasatch" / "leftover_paid_year_end_parallel_p.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://wasatchglobal.com/wasatch-small-cap-growth-fund-investor/",
        fund_family="Wasatch",
    )
    whosx_2025 = next(
        r
        for r in wasatch_leftover
        if r.ticker == "WHOSX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.payable_date
        and str(r.payable_date) == "2025-12-18"
    )
    assert whosx_2025.amount == Decimal("0.113996")
    assert whosx_2025.publication_stage == PublicationStage.final
    wmcvx_2025 = next(
        r
        for r in wasatch_leftover
        if r.ticker == "WMCVX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.payable_date
        and str(r.payable_date) == "2025-12-18"
    )
    assert wmcvx_2025.amount == Decimal("0.554075")
    assert "WIGRX" not in {r.ticker for r in wasatch_leftover}


def test_fifth_tier_fixtures() -> None:
    harbor = parse_distribution_html(
        (ROOT / "harbor" / "2025_estimated_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://harbor",
        fund_family="Harbor",
    )
    hacax = next(
        r
        for r in harbor
        if r.ticker == "HACAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hacax.amount == Decimal("11.89")
    hsicx = next(
        r
        for r in harbor
        if r.ticker == "HSICX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hsicx.amount == Decimal("0.00")
    havlx = next(
        r
        for r in harbor
        if r.ticker == "HAVLX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert havlx.amount == Decimal("3.69")

    nationwide = parse_distribution_html(
        (ROOT / "nationwide" / "2025_capital_gains_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://nationwide",
        fund_family="Nationwide",
    )
    nwhox = next(
        r
        for r in nationwide
        if r.ticker == "NWHOX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nwhox.amount == Decimal("3.7231")

    voya = parse_distribution_html(
        (ROOT / "voya" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://voya",
        fund_family="Voya",
    )
    nlcax = next(
        r
        for r in voya
        if r.ticker == "NLCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nlcax.amount == Decimal("7.259")

    voya_2024 = parse_distribution_html(
        (ROOT / "voya" / "2024_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://voya-2024",
        fund_family="Voya",
    )
    nlcax_24 = next(
        r
        for r in voya_2024
        if r.ticker == "NLCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nlcax_24.amount == Decimal("1.905")
    assert str(nlcax_24.as_of)[:4] == "2024"

    oakmark = parse_distribution_html(
        (ROOT / "oakmark" / "2025_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://oakmark",
        fund_family="Oakmark / Harris Associates",
    )
    oakex = next(
        r
        for r in oakmark
        if r.ticker == "OAKEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert oakex.amount == Decimal("0.7640")

    oakmark_2024 = parse_distribution_html(
        (ROOT / "oakmark" / "2024_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://oakmark-2024",
        fund_family="Oakmark / Harris Associates",
    )
    oakex_24 = next(
        r
        for r in oakmark_2024
        if r.ticker == "OAKEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert oakex_24.amount == Decimal("0.7241")
    assert str(oakex_24.as_of)[:4] == "2024"

    tweedy = parse_distribution_html(
        (ROOT / "tweedy" / "2025_estimated_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://tweedy",
        fund_family="Tweedy, Browne",
    )
    tbgvx = next(
        r
        for r in tweedy
        if r.ticker == "TBGVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tbgvx.amount == Decimal("2.516")

    tweedy_2024 = parse_distribution_html(
        (ROOT / "tweedy" / "2024_estimated_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://tweedy-2024",
        fund_family="Tweedy, Browne",
    )
    tbgvx_24 = next(
        r
        for r in tweedy_2024
        if r.ticker == "TBGVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tbgvx_24.amount == Decimal("1.706")
    assert str(tbgvx_24.as_of)[:4] == "2024"

    tweedy_leftover = parse_distribution_html(
        (ROOT / "tweedy" / "leftover_paid_year_end_parallel_u.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://www.tweedyfunds.com/mutual-funds/international-value-fund-distributions/",
        fund_family="Tweedy, Browne",
    )
    tbgvx_paid_2025 = next(
        r
        for r in tweedy_leftover
        if r.ticker == "TBGVX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2025-12-11"
    )
    assert tbgvx_paid_2025.amount == Decimal("2.793")
    assert tbgvx_paid_2025.publication_stage == PublicationStage.final

    gabelli = parse_distribution_html(
        (ROOT / "gabelli" / "2025_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://gabelli",
        fund_family="Gabelli",
    )
    gabgx = next(
        r
        for r in gabelli
        if r.ticker == "GABGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert gabgx.amount == Decimal("6.8575")

    gabelli_2024 = parse_distribution_html(
        (ROOT / "gabelli" / "2024_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://gabelli-2024",
        fund_family="Gabelli",
    )
    gabgx_24 = next(
        r
        for r in gabelli_2024
        if r.ticker == "GABGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert gabgx_24.amount == Decimal("6.96640")
    assert str(gabgx_24.as_of)[:4] == "2024"

    gabelli_leftover = parse_distribution_html(
        (ROOT / "gabelli" / "leftover_paid_year_end_parallel_p.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://gabelli.com/wp-content/uploads/2025/12/Distribution-memo-12.29.2025.pdf",
        fund_family="Gabelli",
    )
    gicpx_2025 = next(
        r
        for r in gabelli_leftover
        if r.ticker == "GICPX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2025-12-29"
    )
    assert gicpx_2025.amount == Decimal("7.2182")
    assert gicpx_2025.publication_stage == PublicationStage.final
    gabsx_2025 = next(
        r
        for r in gabelli_leftover
        if r.ticker == "GABSX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert gabsx_2025.amount == Decimal("1.65380")
    assert str(gabsx_2025.as_of)[:4] == "2025"
    gabex_2025 = next(
        r
        for r in gabelli_leftover
        if r.ticker == "GABEX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert gabex_2025.amount == Decimal("0.60540")
    assert "GABGX" not in {r.ticker for r in gabelli_leftover}

    gabelli_ncsr = parse_distribution_html(
        (ROOT / "gabelli" / "leftover_ncsr_aaa_2021_2023.html").read_text(encoding="utf-8"),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/783898/"
            "000182912624001467/gabelliasset_ncsr.htm"
        ),
        fund_family="Gabelli",
    )
    gabax_ncsr = next(
        r
        for r in gabelli_ncsr
        if r.ticker == "GABAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert gabax_ncsr.amount == Decimal("5.53")
    assert gabax_ncsr.publication_stage == PublicationStage.final
    assert "GATAX" not in {r.ticker for r in gabelli_ncsr}

    royce = parse_distribution_html(
        (ROOT / "royce" / "2025_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://royce",
        fund_family="Royce",
    )
    rytrx = next(
        r
        for r in royce
        if r.ticker == "RYTRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert rytrx.amount == Decimal("0.7656")

    royce_2024 = parse_distribution_html(
        (ROOT / "royce" / "2024_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://royce-2024",
        fund_family="Royce",
    )
    rytrx_24 = next(
        r
        for r in royce_2024
        if r.ticker == "RYTRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert rytrx_24.amount == Decimal("0.2980")
    assert str(rytrx_24.as_of)[:4] == "2024"

    nylife = parse_distribution_html(
        (ROOT / "nylife" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://nylife",
        fund_family="New York Life Investments / MainStay",
    )
    mlaix = next(
        r
        for r in nylife
        if r.ticker == "MLAIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mlaix.amount_min == Decimal("1.01")
    assert mlaix.amount_max == Decimal("3.00")

    touchstone = parse_distribution_html(
        (ROOT / "touchstone" / "2025_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://touchstone",
        fund_family="Touchstone",
    )
    tvlax = next(
        r
        for r in touchstone
        if r.ticker == "TVLAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tvlax.amount == Decimal("1.28631")

    victory = parse_distribution_html(
        (ROOT / "victory" / "2025_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://victory",
        fund_family="Victory Capital",
    )
    mmeax = next(
        r
        for r in victory
        if r.ticker == "MMEAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mmeax.amount == Decimal("3.876127")
    vetax_est = next(
        r
        for r in victory
        if r.ticker == "VETAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert vetax_est.amount == Decimal("1.622252")

    victory_final = parse_distribution_html(
        (ROOT / "victory" / "2025_final_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://victory-2025-final",
        fund_family="Victory Capital",
    )
    mmeax_final = next(
        r
        for r in victory_final
        if r.ticker == "MMEAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mmeax_final.amount == Decimal("3.922505")
    vetax_final = next(
        r
        for r in victory_final
        if r.ticker == "VETAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert vetax_final.amount == Decimal("1.677515")

    victory_rs = parse_distribution_html(
        (ROOT / "victory" / "2025_rs_final_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://victory-rs-2025",
        fund_family="Victory Capital",
    )
    rsgrx = next(
        r
        for r in victory_rs
        if r.ticker == "RSGRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert rsgrx.amount == Decimal("1.817625")

    victory_iii = parse_distribution_html(
        (ROOT / "victory" / "2025_portfolios_iii_final_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://victory-iii-2025",
        fund_family="Victory Capital",
    )
    usspx = next(
        r
        for r in victory_iii
        if r.ticker == "USSPX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert usspx.amount == Decimal("2.615144")

    victory_2024 = parse_distribution_html(
        (ROOT / "victory" / "2024_final_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://victory-2024",
        fund_family="Victory Capital",
    )
    mmeax_24 = next(
        r
        for r in victory_2024
        if r.ticker == "MMEAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mmeax_24.amount == Decimal("3.015874")
    assert str(mmeax_24.as_of)[:4] == "2024"

    victory_2023 = parse_distribution_html(
        (ROOT / "victory" / "2023_final_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://victory-2023",
        fund_family="Victory Capital",
    )
    mmeax_23 = next(
        r
        for r in victory_2023
        if r.ticker == "MMEAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mmeax_23.amount == Decimal("0.390522")
    assert mmeax_23.publication_stage == PublicationStage.final
    assert str(mmeax_23.as_of)[:4] == "2023"
    vetax_23 = next(
        r
        for r in victory_2023
        if r.ticker == "VETAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert vetax_23.amount == Decimal("2.095967")

    victory_2022 = parse_distribution_html(
        (ROOT / "victory" / "2022_final_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://victory-2022",
        fund_family="Victory Capital",
    )
    mmeax_22 = next(
        r
        for r in victory_2022
        if r.ticker == "MMEAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mmeax_22.amount == Decimal("2.389672")
    assert mmeax_22.publication_stage == PublicationStage.final
    assert str(mmeax_22.as_of)[:4] == "2022"
    vetax_22 = next(
        r
        for r in victory_2022
        if r.ticker == "VETAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert vetax_22.amount == Decimal("2.782434")
    assert {r.ticker for r in victory_2022 if r.ticker} >= {"MMEAX", "VETAX", "SSGSX"}

    victory_rs_2023 = parse_distribution_html(
        (ROOT / "victory" / "2023_rs_final_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://victory-rs-2023",
        fund_family="Victory Capital",
    )
    rsgrx_23 = next(
        r
        for r in victory_rs_2023
        if r.ticker == "RSGRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert rsgrx_23.amount == Decimal("0.036599")
    assert not any("VIP" in (r.fund_name or "") for r in victory_rs_2023)

    victory_iii_2023 = parse_distribution_html(
        (ROOT / "victory" / "2023_portfolios_iii_final_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://victory-iii-2023",
        fund_family="Victory Capital",
    )
    usspx_23 = next(
        r
        for r in victory_iii_2023
        if r.ticker == "USSPX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert usspx_23.amount == Decimal("0.515883")


def test_sixth_tier_fixtures() -> None:
    sei = parse_distribution_html(
        (ROOT / "sei" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://sei",
        fund_family="SEI",
    )
    slcg = next(
        r
        for r in sei
        if "Large Cap Growth" in r.fund_name
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert slcg.amount == Decimal("8.018")

    sei_2024 = parse_distribution_html(
        (ROOT / "sei" / "2024_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://sei-2024",
        fund_family="SEI",
    )
    slcg_24 = next(
        r
        for r in sei_2024
        if "Large Cap Growth" in r.fund_name
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert slcg_24.amount == Decimal("7.596")
    assert str(slcg_24.as_of)[:4] == "2024"

    sei_paid = parse_distribution_html(
        (ROOT / "sei" / "2025_paid_capital_gains.html").read_text(encoding="utf-8"),
        source_url=(
            "https://www.seic.com/sites/default/files/2025-12/"
            "2025%20SEI%20Capital%20gains%20distribution_Final.pdf"
        ),
        fund_family="SEI",
    )
    qalt_paid = next(
        r
        for r in sei_paid
        if r.ticker == "QALT" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert qalt_paid.amount == Decimal("0.372")
    assert qalt_paid.publication_stage == PublicationStage.final
    slcg_paid = next(
        r
        for r in sei_paid
        if r.fund_name == "SIMT Large Cap Growth"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert slcg_paid.amount == Decimal("8.053")

    brown = parse_distribution_html(
        (ROOT / "brown_advisory" / "2025_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://brown_advisory",
        fund_family="Brown Advisory",
    )
    baffx = next(
        r
        for r in brown
        if r.ticker == "BAFFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert baffx.amount == Decimal("2.17")

    brown_2024 = parse_distribution_html(
        (ROOT / "brown_advisory" / "2024_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://brown_advisory-2024",
        fund_family="Brown Advisory",
    )
    baffx_24 = next(
        r
        for r in brown_2024
        if r.ticker == "BAFFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert baffx_24.amount == Decimal("1.72")
    assert str(baffx_24.as_of)[:4] == "2024"

    blair = parse_distribution_html(
        (ROOT / "william_blair" / "2025_annual_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://william_blair",
        fund_family="William Blair",
    )
    bgfix = next(
        r
        for r in blair
        if r.ticker == "BGFIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bgfix.amount == Decimal("2.91999")

    blair_2024 = parse_distribution_html(
        (ROOT / "william_blair" / "2024_annual_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://william_blair-2024",
        fund_family="William Blair",
    )
    bgfix_24 = next(
        r
        for r in blair_2024
        if r.ticker == "BGFIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bgfix_24.amount == Decimal("3.03562")
    assert str(bgfix_24.as_of)[:4] == "2024"

    vaneck = parse_distribution_html(
        (ROOT / "vaneck" / "2025_estimated_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://vaneck",
        fund_family="VanEck",
    )
    mwmix = next(
        r
        for r in vaneck
        if r.ticker == "MWMIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mwmix.amount == Decimal("1.68")

    vaneck_etf_2025 = parse_distribution_html(
        (ROOT / "vaneck" / "2025_etf_year_end_estimates.html").read_text(encoding="utf-8"),
        source_url="fixture://vaneck-etf-2025",
        fund_family="VanEck",
    )
    cloi_2025 = next(
        r
        for r in vaneck_etf_2025
        if r.ticker == "CLOI" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cloi_2025.amount == Decimal("0.029")

    vaneck_etf_2024 = parse_distribution_html(
        (ROOT / "vaneck" / "2024_etf_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://vaneck-etf-2024",
        fund_family="VanEck",
    )
    gdx = next(
        r
        for r in vaneck_etf_2024
        if r.ticker == "GDX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert gdx.amount == Decimal("0.4025")
    ibot = next(
        r
        for r in vaneck_etf_2024
        if r.ticker == "IBOT" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert ibot.amount == Decimal("0.9104")
    assert len({r.ticker for r in vaneck_etf_2024 if r.ticker}) >= 40

    vaneck_mf_2024 = parse_distribution_html(
        (ROOT / "vaneck" / "2024_funds_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://vaneck-mf-2024",
        fund_family="VanEck",
    )
    mwmix_2024 = next(
        r
        for r in vaneck_mf_2024
        if r.ticker == "MWMIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mwmix_2024.amount == Decimal("1.4325")
    inivx_2024 = next(
        r
        for r in vaneck_mf_2024
        if r.ticker == "INIVX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert inivx_2024.amount == Decimal("0.7750")

    vaneck_etf_2023 = parse_distribution_html(
        (ROOT / "vaneck" / "2023_etf_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://vaneck-etf-2023",
        fund_family="VanEck",
    )
    gdx_2023 = next(
        r
        for r in vaneck_etf_2023
        if r.ticker == "GDX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert gdx_2023.amount == Decimal("0.5001")
    ibot_2023 = next(
        r
        for r in vaneck_etf_2023
        if r.ticker == "IBOT" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert ibot_2023.amount == Decimal("0.6716")

    vaneck_mf_2023 = parse_distribution_html(
        (ROOT / "vaneck" / "2023_funds_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://vaneck-mf-2023",
        fund_family="VanEck",
    )
    inivx_2023 = next(
        r
        for r in vaneck_mf_2023
        if r.ticker == "INIVX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert inivx_2023.amount == Decimal("0.0102")
    mwmix_2023 = next(
        r
        for r in vaneck_mf_2023
        if r.ticker == "MWMIX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert mwmix_2023.amount == Decimal("1.6352")

    vaneck_mf_2025_paid = parse_distribution_html(
        (ROOT / "vaneck" / "2025_funds_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://vaneck-mf-2025-paid",
        fund_family="VanEck",
    )
    inivx_2025_paid = next(
        r
        for r in vaneck_mf_2025_paid
        if r.ticker == "INIVX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert inivx_2025_paid.amount == Decimal("1.5675")
    mwmix_2025_lt = next(
        r
        for r in vaneck_mf_2025_paid
        if r.ticker == "MWMIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mwmix_2025_lt.amount == Decimal("1.6944")

    vaneck_etf_2025_paid = parse_distribution_html(
        (ROOT / "vaneck" / "2025_etf_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://vaneck-etf-2025-paid",
        fund_family="VanEck",
    )
    gdx_2025_paid = next(
        r
        for r in vaneck_etf_2025_paid
        if r.ticker == "GDX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert gdx_2025_paid.amount == Decimal("0.6331")
    motg_2025_lt = next(
        r
        for r in vaneck_etf_2025_paid
        if r.ticker == "MOTG" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert motg_2025_lt.amount == Decimal("4.0549")

    vaneck_parallel_o_tax = parse_distribution_html(
        (ROOT / "vaneck" / "leftover_parallel_o_tax_guide_paid.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://vaneck-parallel-o-tax",
        fund_family="VanEck",
    )
    einc_2021 = next(
        r
        for r in vaneck_parallel_o_tax
        if r.ticker == "EINC"
        and r.estimate_type == EstimateType.ordinary_income
        and r.ex_date
        and r.ex_date.year == 2021
    )
    assert einc_2021.amount == Decimal("0.390850")
    lfeq_2023 = next(
        r
        for r in vaneck_parallel_o_tax
        if r.ticker == "LFEQ" and r.estimate_type == EstimateType.ordinary_income
    )
    assert lfeq_2023.amount == Decimal("0.625000")
    raax_2023 = next(
        r
        for r in vaneck_parallel_o_tax
        if r.ticker == "RAAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert raax_2023.amount == Decimal("0.935700")

    vaneck_parallel_o_2025 = parse_distribution_html(
        (ROOT / "vaneck" / "leftover_parallel_o_2025_later_paid.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://vaneck-parallel-o-2025",
        fund_family="VanEck",
    )
    einc_2025_lt = next(
        r
        for r in vaneck_parallel_o_2025
        if r.ticker == "EINC" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert einc_2025_lt.amount == Decimal("0.9843")
    cloi_2025_oi = next(
        r
        for r in vaneck_parallel_o_2025
        if r.ticker == "CLOI" and r.estimate_type == EstimateType.ordinary_income
    )
    assert cloi_2025_oi.amount == Decimal("0.2332")

    first_eagle_etf = parse_distribution_html(
        (ROOT / "first_eagle" / "2025_etf_paid_year_end.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://first-eagle-etf-2025",
        fund_family="First Eagle",
    )
    fege = next(
        r
        for r in first_eagle_etf
        if r.ticker == "FEGE" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fege.amount == Decimal("0.589")
    fege_lt = next(
        r
        for r in first_eagle_etf
        if r.ticker == "FEGE" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert fege_lt.amount == Decimal("0.000")

    wisdomtree = parse_distribution_html(
        (ROOT / "wisdomtree" / "2025_final_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://wisdomtree",
        fund_family="WisdomTree",
    )
    xc = next(
        r
        for r in wisdomtree
        if r.ticker == "XC" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert xc.amount == Decimal("2.49286")

    wisdomtree_2024 = parse_distribution_html(
        (ROOT / "wisdomtree" / "2024_final_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://wisdomtree-2024",
        fund_family="WisdomTree",
    )
    gtr_2024 = next(
        r
        for r in wisdomtree_2024
        if r.ticker == "GTR" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert gtr_2024.amount == Decimal("0.51992")

    wisdomtree_dec = parse_distribution_html(
        (ROOT / "wisdomtree" / "2025_december_etf_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://wisdomtree-dec-2025",
        fund_family="WisdomTree",
    )
    dgrw = next(
        r
        for r in wisdomtree_dec
        if r.ticker == "DGRW" and r.estimate_type == EstimateType.ordinary_income
    )
    assert dgrw.amount == Decimal("0.23270")
    dhs = next(
        r
        for r in wisdomtree_dec
        if r.ticker == "DHS" and r.estimate_type == EstimateType.ordinary_income
    )
    assert dhs.amount == Decimal("0.58476")
    xc_inc = next(
        r
        for r in wisdomtree_dec
        if r.ticker == "XC" and r.estimate_type == EstimateType.ordinary_income
    )
    assert xc_inc.amount == Decimal("0.22721")
    epi_zero = next(
        r
        for r in wisdomtree_dec
        if r.ticker == "EPI" and r.estimate_type == EstimateType.ordinary_income
    )
    assert epi_zero.amount == Decimal("0.00000")
    assert len({r.ticker for r in wisdomtree_dec if r.ticker}) >= 80
    assert not any(
        r.estimate_type
        in {EstimateType.short_term_capital_gains, EstimateType.long_term_capital_gains}
        for r in wisdomtree_dec
    )

    wisdomtree_parallel_o = parse_distribution_html(
        (ROOT / "wisdomtree" / "leftover_parallel_o_2023_monthly.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://wisdomtree-parallel-o-2023",
        fund_family="WisdomTree",
    )
    uniy_2023 = next(
        r
        for r in wisdomtree_parallel_o
        if r.ticker == "UNIY" and r.estimate_type == EstimateType.ordinary_income
    )
    assert uniy_2023.amount == Decimal("0.17700")
    assert str(uniy_2023.ex_date) == "2023-11-24"

    first_trust = parse_distribution_html(
        (ROOT / "first_trust" / "2025_section_19a_notice.html").read_text(encoding="utf-8"),
        source_url="fixture://first-trust",
        fund_family="First Trust",
    )
    bfap = next(
        r
        for r in first_trust
        if r.ticker == "BFAP" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bfap.amount == Decimal("3.1933")
    bgld_st = next(
        r
        for r in first_trust
        if r.ticker == "BGLD" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert bgld_st.amount == Decimal("2.7353")
    igld_roc = next(
        r
        for r in first_trust
        if r.ticker == "IGLD" and r.estimate_type == EstimateType.return_of_capital
    )
    assert igld_roc.amount == Decimal("0.3525")

    first_trust_sept = parse_distribution_html(
        (ROOT / "first_trust" / "2025_september_etf_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://first-trust-sept-2025",
        fund_family="First Trust",
    )
    fvd = next(
        r
        for r in first_trust_sept
        if r.ticker == "FVD" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fvd.amount == Decimal("0.2519")
    fthi = next(
        r
        for r in first_trust_sept
        if r.ticker == "FTHI" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fthi.amount == Decimal("0.1710")
    fpe = next(
        r
        for r in first_trust_sept
        if r.ticker == "FPE" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fpe.amount == Decimal("0.0845")
    cibr = next(
        r
        for r in first_trust_sept
        if r.ticker == "CIBR" and r.estimate_type == EstimateType.ordinary_income
    )
    assert cibr.amount == Decimal("0.0006")
    assert len({r.ticker for r in first_trust_sept if r.ticker}) >= 140
    assert not any(
        r.estimate_type == EstimateType.long_term_capital_gains for r in first_trust_sept
    )

    first_trust_dec_2025 = parse_distribution_html(
        (ROOT / "first_trust" / "2025_december_etf_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://first-trust-dec-2025",
        fund_family="First Trust",
    )
    fvd_dec = next(
        r
        for r in first_trust_dec_2025
        if r.ticker == "FVD" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fvd_dec.amount == Decimal("0.3186")
    fthi_dec = next(
        r
        for r in first_trust_dec_2025
        if r.ticker == "FTHI" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fthi_dec.amount == Decimal("0.1770")
    ftcb_lt = next(
        r
        for r in first_trust_dec_2025
        if r.ticker == "FTCB" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert ftcb_lt.amount == Decimal("0.0473")
    wcme = next(
        r
        for r in first_trust_dec_2025
        if r.ticker == "WCME" and r.estimate_type == EstimateType.ordinary_income
    )
    assert wcme.amount == Decimal("0.0142")
    assert len({r.ticker for r in first_trust_dec_2025 if r.ticker}) >= 150

    first_trust_dec_2024 = parse_distribution_html(
        (ROOT / "first_trust" / "2024_december_etf_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://first-trust-dec-2024",
        fund_family="First Trust",
    )
    fvd_2024 = next(
        r
        for r in first_trust_dec_2024
        if r.ticker == "FVD" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fvd_2024.amount == Decimal("0.2752")
    fthi_2024 = next(
        r
        for r in first_trust_dec_2024
        if r.ticker == "FTHI" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fthi_2024.amount == Decimal("0.1720")
    assert len({r.ticker for r in first_trust_dec_2024 if r.ticker}) >= 140

    aqr = parse_distribution_html(
        (ROOT / "aqr" / "2025_estimated_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://aqr",
        fund_family="AQR",
    )
    aqgix = next(
        r
        for r in aqr
        if r.ticker == "AQGIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert aqgix.amount == Decimal("0.4747")

    causeway = parse_distribution_html(
        (ROOT / "causeway" / "2025_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://causeway",
        fund_family="Causeway",
    )
    civix = next(
        r
        for r in causeway
        if r.ticker == "CIVIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert civix.amount == Decimal("1.5537")

    alger = parse_distribution_html(
        (ROOT / "alger" / "2025_dividends_and_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://alger",
        fund_family="Alger / Fred Alger",
    )
    chusx = next(
        r
        for r in alger
        if r.ticker == "CHUSX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert chusx.amount == Decimal("2.4670")

    alger_2022 = parse_distribution_html(
        (ROOT / "alger" / "2022_dividends_and_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://alger/2022",
        fund_family="Alger / Fred Alger",
    )
    acaax_22 = next(
        r
        for r in alger_2022
        if r.ticker == "ACAAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert acaax_22.amount == Decimal("0.8384")
    assert acaax_22.publication_stage == PublicationStage.final
    assert str(acaax_22.as_of)[:4] == "2022"
    alarx_22 = next(
        r
        for r in alger_2022
        if r.ticker == "ALARX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert alarx_22.amount == Decimal("0.9783")
    specx_22 = next(
        r
        for r in alger_2022
        if r.ticker == "SPECX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert specx_22.amount == Decimal("0.3918")
    assert not any(r.ticker == "CHUSX" for r in alger_2022)
    assert {r.ticker for r in alger_2022 if r.ticker} >= {"ACAAX", "ALARX", "SPECX", "ALBAX"}

    alger_etf_2025 = parse_distribution_html(
        (ROOT / "alger" / "2025_etf_dividends_and_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://alger/etf-2025",
        fund_family="Alger / Fred Alger",
    )
    aweg = next(
        r
        for r in alger_etf_2025
        if r.ticker == "AWEG" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert aweg.amount == Decimal("0.45647")

    alger_etf_2021 = parse_distribution_html(
        (ROOT / "alger" / "2021_etf_dividends_and_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://alger/etf-2021",
        fund_family="Alger / Fred Alger",
    )
    frty_21 = next(
        r
        for r in alger_etf_2021
        if r.ticker == "FRTY" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert frty_21.amount == Decimal("1.0687")
    assert frty_21.publication_stage == PublicationStage.final

    alger_ncsr_cf = parse_distribution_html(
        (ROOT / "alger" / "leftover_ncsr_spegx_2021_2024_wave_cf.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/92751/"
            "000113322824011661/tgfii-efp13341_ncsr.htm#responsible-investing"
        ),
        fund_family="Alger / Fred Alger",
    )
    spegx_2024_cg = next(
        r
        for r in alger_ncsr_cf
        if r.ticker == "SPEGX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2024-10-31"
    )
    assert spegx_2024_cg.amount == Decimal("0.44")
    assert spegx_2024_cg.publication_stage == PublicationStage.final
    spegx_2021_cg = next(
        r
        for r in alger_ncsr_cf
        if r.ticker == "SPEGX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2021-10-31"
    )
    assert spegx_2021_cg.amount == Decimal("1.04")
    assert {r.ticker for r in alger_ncsr_cf} == {"SPEGX", "AGFCX", "AGIFX", "ALGZX"}
    assert not any(
        r.ticker in {"CHUSX", "ALGAX", "ALSRX", "ACAAX", "SPECX", "PIORX"}
        for r in alger_ncsr_cf
    )
    assert not any(
        r.estimate_type == EstimateType.ordinary_income for r in alger_ncsr_cf
    )

    harding = parse_distribution_html(
        (ROOT / "harding_loevner" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://harding_loevner",
        fund_family="Harding Loevner",
    )
    hlmgx = next(
        r
        for r in harding
        if r.ticker == "HLMGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hlmgx.amount == Decimal("6.192933")
    assert {r.ticker for r in harding if r.ticker} >= {
        "HLMGX",
        "HLMNX",
        "HLEMX",
        "HLMIX",
        "HLMVX",
    }

    harding_ncsr = parse_distribution_html(
        (ROOT / "harding_loevner" / "leftover_ncsr_global_equity_2022_wave_aw.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1018170/"
            "000119312523002209/d363948dncsr.htm"
        ),
        fund_family="Harding Loevner",
    )
    hlmgx_ncsr = next(
        r
        for r in harding_ncsr
        if r.ticker == "HLMGX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2022-10-31"
    )
    assert hlmgx_ncsr.amount == Decimal("7.41")
    assert hlmgx_ncsr.publication_stage == PublicationStage.final
    assert {r.ticker for r in harding_ncsr} == {"HLMGX", "HLMVX", "HLGZX"}

    harding_ncsr_ch = parse_distribution_html(
        (ROOT / "harding_loevner" / "leftover_ncsr_hlemx_2024_wave_ch.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1018170/"
            "000089843025000008/8dd25e24ef2e8b3.htm#hlemx-2024"
        ),
        fund_family="Harding Loevner",
    )
    hlemx_2024_cg = next(
        r
        for r in harding_ncsr_ch
        if r.ticker == "HLEMX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2024-10-31"
    )
    assert hlemx_2024_cg.amount == Decimal("0.69")
    assert hlemx_2024_cg.publication_stage == PublicationStage.final
    hlfzx_2021_oi = next(
        r
        for r in harding_ncsr_ch
        if r.ticker == "HLFZX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2021-10-31"
    )
    assert hlfzx_2021_oi.amount == Decimal("0.14")
    assert {r.ticker for r in harding_ncsr_ch} == {"HLEMX", "HLGZX", "HLIZX", "HLFZX"}
    assert not any(r.ticker in {"HLMGX", "HLMVX", "HLIDX", "HLRZX", "RALIX"} for r in harding_ncsr_ch)

    matthews = parse_distribution_html(
        (ROOT / "matthews_asia" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://matthews_asia",
        fund_family="Matthews Asia",
    )
    megmx = next(
        r
        for r in matthews
        if r.ticker == "MEGMX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert megmx.amount == Decimal("0.08706")
    mapix_2025 = next(
        r
        for r in matthews
        if r.ticker == "MAPIX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert mapix_2025.amount == Decimal("0.26050")
    msmlx_2025 = next(
        r
        for r in matthews
        if r.ticker == "MSMLX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert msmlx_2025.amount == Decimal("0.38648")

    aqr_2024 = parse_distribution_html(
        (ROOT / "aqr" / "2024_final_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://aqr-2024",
        fund_family="AQR",
    )
    aqgix_2024 = next(
        r
        for r in aqr_2024
        if r.ticker == "AQGIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert aqgix_2024.amount == Decimal("0.5462")
    aueix_2024 = next(
        r
        for r in aqr_2024
        if r.ticker == "AUEIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert aueix_2024.amount == Decimal("4.3691")

    causeway_2024 = parse_distribution_html(
        (ROOT / "causeway" / "2024_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://causeway-2024",
        fund_family="Causeway",
    )
    civix_2024 = next(
        r
        for r in causeway_2024
        if r.ticker == "CIVIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert civix_2024.amount == Decimal("1.1868")

    causeway_2023 = parse_distribution_html(
        (ROOT / "causeway" / "2023_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://causeway-2023",
        fund_family="Causeway",
    )
    civix_2023 = next(
        r
        for r in causeway_2023
        if r.ticker == "CIVIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert civix_2023.amount == Decimal("0.1748")
    assert civix_2023.publication_stage == PublicationStage.final

    causeway_2022 = parse_distribution_html(
        (ROOT / "causeway" / "2022_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://causeway-2022",
        fund_family="Causeway",
    )
    civix_2022 = next(
        r
        for r in causeway_2022
        if r.ticker == "CIVIX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert civix_2022.amount == Decimal("0.2834")
    ccenx_2022 = next(
        r
        for r in causeway_2022
        if r.ticker == "CCENX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert ccenx_2022.amount == Decimal("0.0716")

    causeway_2021 = parse_distribution_html(
        (ROOT / "causeway" / "2021_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://causeway-2021",
        fund_family="Causeway",
    )
    civix_2021 = next(
        r
        for r in causeway_2021
        if r.ticker == "CIVIX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert civix_2021.amount == Decimal("0.3170")
    cemix_2021 = next(
        r
        for r in causeway_2021
        if r.ticker == "CEMIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cemix_2021.amount == Decimal("2.4046")
    cemix_st = next(
        r
        for r in causeway_2024
        if r.ticker == "CEMIX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert cemix_st.amount == Decimal("0.0000")

    matthews_2024 = parse_distribution_html(
        (ROOT / "matthews_asia" / "2024_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://matthews-2024",
        fund_family="Matthews Asia",
    )
    maptx_2024 = next(
        r
        for r in matthews_2024
        if r.ticker == "MAPTX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert maptx_2024.amount == Decimal("0.99319")
    mindx_2024 = next(
        r
        for r in matthews_2024
        if r.ticker == "MINDX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert mindx_2024.amount == Decimal("1.41120")

    matthews_2021 = parse_distribution_html(
        (ROOT / "matthews_asia" / "2021_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://matthews-2021",
        fund_family="Matthews Asia",
    )
    maptx_2021 = next(
        r
        for r in matthews_2021
        if r.ticker == "MAPTX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert maptx_2021.amount == Decimal("5.35902")
    mapix_2021 = next(
        r
        for r in matthews_2021
        if r.ticker == "MAPIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mapix_2021.amount == Decimal("2.31785")
    mchfx_2021 = next(
        r
        for r in matthews_2021
        if r.ticker == "MCHFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mchfx_2021.amount == Decimal("1.62473")
    masgx_2021 = next(
        r
        for r in matthews_2021
        if r.ticker == "MASGX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert masgx_2021.amount == Decimal("0.70374")
    mcsmx_2021 = next(
        r
        for r in matthews_2021
        if r.ticker == "MCSMX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert mcsmx_2021.amount == Decimal("1.77913")


def test_seventh_tier_fixtures() -> None:
    tcw = parse_distribution_html(
        (ROOT / "tcw" / "2025_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://tcw",
        fund_family="TCW",
    )
    tgdix = next(
        r
        for r in tcw
        if r.ticker == "TGDIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tgdix.amount == Decimal("3.4797")

    tcw_ncsr = parse_distribution_html(
        (ROOT / "tcw" / "leftover_ncsr_2021_2024_wave_bh.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/892071/"
            "000119312525000202/d911056dncsr.htm"
        ),
        fund_family="TCW",
    )
    tgdix_2024 = next(
        r
        for r in tcw_ncsr
        if r.ticker == "TGDIX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-10-31"
    )
    assert tgdix_2024.amount == Decimal("0.20")
    assert tgdix_2024.publication_stage == PublicationStage.final
    tgpcx_2023_cg = next(
        r
        for r in tcw_ncsr
        if r.ticker == "TGPCX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2023-10-31"
    )
    assert tgpcx_2023_cg.amount == Decimal("0.28")
    assert {r.ticker for r in tcw_ncsr} == {"TGDIX", "TGVOX", "TGCEX", "TGPCX"}
    assert not any(r.ticker in {"TGDVX", "TGVNX", "TGCNX", "TGPNX"} for r in tcw_ncsr)
    assert not any(
        r.ticker == "TGCEX" and r.estimate_type == EstimateType.ordinary_income
        for r in tcw_ncsr
    )

    bridgeway = parse_distribution_html(
        (ROOT / "bridgeway" / "2025_estimated_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://bridgeway",
        fund_family="Bridgeway",
    )
    bragx = next(
        r
        for r in bridgeway
        if r.ticker == "BRAGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bragx.amount == Decimal("17.63983")

    bridgeway_2024 = parse_distribution_html(
        (ROOT / "bridgeway" / "2024_estimated_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://bridgeway-2024",
        fund_family="Bridgeway",
    )
    bragx_2024 = next(
        r
        for r in bridgeway_2024
        if r.ticker == "BRAGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bragx_2024.amount == Decimal("2.54426")
    brusx_st = next(
        r
        for r in bridgeway_2024
        if r.ticker == "BRUSX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert brusx_st.amount == Decimal("1.13357")

    jensen = parse_distribution_html(
        (ROOT / "jensen" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://jensen",
        fund_family="Jensen",
    )
    jensx = next(
        r
        for r in jensen
        if r.ticker == "JENSX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jensx.amount == Decimal("16.65")

    jensen_2024 = parse_distribution_html(
        (ROOT / "jensen" / "2024_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://jensen-2024",
        fund_family="Jensen",
    )
    jensx_2024 = next(
        r
        for r in jensen_2024
        if r.ticker == "JENSX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jensx_2024.amount == Decimal("6.77")
    jenix_2024 = next(
        r
        for r in jensen_2024
        if r.ticker == "JENIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert jenix_2024.amount == Decimal("6.77")
    assert not any(
        r.estimate_type == EstimateType.short_term_capital_gains for r in jensen_2024
    )

    diamond = parse_distribution_html(
        (ROOT / "diamond_hill" / "2025_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://diamond_hill",
        fund_family="Diamond Hill",
    )
    dhpax = next(
        r
        for r in diamond
        if r.ticker == "DHPAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dhpax.amount == Decimal("2.698")
    dhmax = next(
        r
        for r in diamond
        if r.ticker == "DHMAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dhmax.amount == Decimal("1.590")

    diamond_2024 = parse_distribution_html(
        (ROOT / "diamond_hill" / "2024_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://diamond_hill-2024",
        fund_family="Diamond Hill",
    )
    dhlax_2024 = next(
        r
        for r in diamond_2024
        if r.ticker == "DHLAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dhlax_2024.amount == Decimal("2.900")
    dhlax_st_2024 = next(
        r
        for r in diamond_2024
        if r.ticker == "DHSCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dhlax_st_2024.amount == Decimal("2.511")

    champlain = parse_distribution_html(
        (ROOT / "champlain" / "2025_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://champlain",
        fund_family="Champlain",
    )
    cipix = next(
        r
        for r in champlain
        if r.ticker == "CIPIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cipix.amount == Decimal("3.5103")

    driehaus = parse_distribution_html(
        (ROOT / "driehaus" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://driehaus",
        fund_family="Driehaus",
    )
    dmcrx = next(
        r
        for r in driehaus
        if r.ticker == "DMCRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert dmcrx.amount == Decimal("2.073159")
    dregx = next(
        r
        for r in driehaus
        if r.ticker == "DREGX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert dregx.amount == Decimal("0.796054")

    hotchkis = parse_distribution_html(
        (ROOT / "hotchkis" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://hotchkis",
        fund_family="Hotchkis & Wiley",
    )
    hwlix = next(
        r
        for r in hotchkis
        if r.ticker == "HWLIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hwlix.amount == Decimal("2.83442")

    marsico = parse_distribution_html(
        (ROOT / "marsico" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://marsico",
        fund_family="Marsico",
    )
    mfocx = next(
        r
        for r in marsico
        if r.ticker == "MFOCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mfocx.amount == Decimal("4.9890")

    osterweis = parse_distribution_html(
        (ROOT / "osterweis" / "2025_estimated_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://osterweis",
        fund_family="Osterweis",
    )
    ostfx = next(
        r
        for r in osterweis
        if r.ticker == "OSTFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert ostfx.amount == Decimal("1.10")

    osterweis_leftover = parse_distribution_html(
        (ROOT / "osterweis" / "leftover_paid_history_parallel_u.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://www.osterweis.com/files/OSTFX_Historical_Distributions.pdf",
        fund_family="Osterweis",
    )
    ostfx_paid = next(
        r
        for r in osterweis_leftover
        if r.ticker == "OSTFX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2025-12-15"
    )
    assert ostfx_paid.amount == Decimal("1.17276")
    assert ostfx_paid.publication_stage == PublicationStage.final

    davis = parse_distribution_html(
        (ROOT / "davis" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://davis",
        fund_family="Davis Funds",
    )
    nyvtx_ye = next(
        r
        for r in davis
        if r.ticker == "NYVTX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-12-12"
    )
    assert nyvtx_ye.amount == Decimal("0.89")
    assert nyvtx_ye.publication_stage == PublicationStage.final
    nyvtx_mid = next(
        r
        for r in davis
        if r.ticker == "NYVTX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-06-25"
    )
    assert nyvtx_mid.amount == Decimal("2.10")
    assert nyvtx_mid.publication_stage == PublicationStage.paid
    nyvtx_semi = next(
        r
        for r in davis
        if r.ticker == "NYVTX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2026-06-24"
    )
    assert nyvtx_semi.amount == Decimal("1.60")
    assert nyvtx_semi.publication_stage == PublicationStage.paid


def test_eighth_tier_fixtures() -> None:
    primecap = parse_distribution_html(
        (ROOT / "primecap" / "2025_distribution_estimates.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://primecap",
        fund_family="PRIMECAP Odyssey",
    )
    poskx = next(
        r
        for r in primecap
        if r.ticker == "POSKX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert poskx.amount == Decimal("8.25")

    ariel = parse_distribution_html(
        (ROOT / "ariel" / "2025_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://ariel",
        fund_family="Ariel",
    )
    argfx = next(
        r
        for r in ariel
        if r.ticker == "ARGFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert argfx.amount == Decimal("8.152412")

    baird = parse_distribution_html(
        (ROOT / "baird" / "2025_final_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://baird",
        fund_family="Baird",
    )
    bmdix = next(
        r
        for r in baird
        if r.ticker == "BMDIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bmdix.amount == Decimal("2.19832")

    longleaf = parse_distribution_html(
        (ROOT / "longleaf" / "2025_partners_fund_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://longleaf",
        fund_family="Longleaf Partners",
    )
    llpfx = next(
        r
        for r in longleaf
        if r.ticker == "LLPFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert llpfx.amount == Decimal("1.7935")

    longleaf_leftover = parse_distribution_html(
        (ROOT / "longleaf" / "leftover_paid_year_end_parallel_u.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://southeasternasset.com/investment-offerings/longleaf-partners-fund/",
        fund_family="Longleaf Partners",
    )
    llpfx_2024 = next(
        r
        for r in longleaf_leftover
        if r.ticker == "LLPFX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.ex_date
        and str(r.ex_date) == "2024-12-20"
    )
    assert llpfx_2024.amount == Decimal("0.2469")
    assert llpfx_2024.publication_stage == PublicationStage.final

    buffalo = parse_distribution_html(
        (ROOT / "buffalo" / "2025_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://buffalo",
        fund_family="Buffalo",
    )
    bufex = next(
        r
        for r in buffalo
        if r.ticker == "BUFEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bufex.amount == Decimal("3.35047")

    buffalo_leftover = parse_distribution_html(
        (ROOT / "buffalo" / "leftover_paid_year_end_parallel_u.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://buffalofunds.com/overview/",
        fund_family="Buffalo",
    )
    bufex_paid = next(
        r
        for r in buffalo_leftover
        if r.ticker == "BUFEX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2025-12-04"
    )
    assert bufex_paid.amount == Decimal("3.35562")
    assert bufex_paid.publication_stage == PublicationStage.final

    gqg = parse_distribution_html(
        (ROOT / "gqg" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://gqg",
        fund_family="GQG Partners",
    )
    gqeix = next(
        r
        for r in gqg
        if r.ticker == "GQEIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert gqeix.amount == Decimal("0.81")

    third_avenue = parse_distribution_html(
        (ROOT / "third_avenue" / "2025_income_capital_gain_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://third_avenue",
        fund_family="Third Avenue",
    )
    tavfx = next(
        r
        for r in third_avenue
        if r.ticker == "TAVFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tavfx.amount == Decimal("3.34191")

    third_avenue_leftover = parse_distribution_html(
        (ROOT / "third_avenue" / "leftover_paid_year_end_parallel_u.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://www.thirdave.com/2024-income-capital-gain-distributions",
        fund_family="Third Avenue",
    )
    tavfx_2024 = next(
        r
        for r in third_avenue_leftover
        if r.ticker == "TAVFX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2024-12-11"
    )
    assert tavfx_2024.amount == Decimal("4.08400")
    assert tavfx_2024.publication_stage == PublicationStage.final

    third_avenue_ncsr = parse_distribution_html(
        (ROOT / "third_avenue" / "leftover_ncsr_2021_wave_av.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1031661/000119312522001631/"
            "d245346dncsr.htm"
        ),
        fund_family="Third Avenue",
    )
    tavfx_2021 = next(
        r
        for r in third_avenue_ncsr
        if r.ticker == "TAVFX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert tavfx_2021.amount == Decimal("0.30")
    assert tavfx_2021.publication_stage == PublicationStage.final
    assert [r for r in third_avenue_ncsr if r.ticker in {"TVFVX", "TAVZX"}] == []

    heartland = parse_distribution_html(
        (ROOT / "heartland" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://heartland",
        fund_family="Heartland",
    )
    hrtvx = next(
        r
        for r in heartland
        if r.ticker == "HRTVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hrtvx.amount == Decimal("4.34950")

    fmi = parse_distribution_html(
        (ROOT / "fmi" / "2025_distribution_summary.html").read_text(encoding="utf-8"),
        source_url="fixture://fmi",
        fund_family="FMI",
    )
    fmiux = next(
        r
        for r in fmi
        if r.ticker == "FMIUX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert fmiux.amount == Decimal("3.8237")

    impax = parse_distribution_html(
        (ROOT / "impax" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://impax",
        fund_family="Impax / Pax",
    )
    paxlx = next(
        r
        for r in impax
        if r.ticker == "PAXLX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert paxlx.amount == Decimal("3.19835")


def test_ninth_tier_fixtures() -> None:
    beacon = parse_distribution_html(
        (ROOT / "american_beacon" / "2025_annual_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://american_beacon",
        fund_family="American Beacon",
    )
    aadex = next(
        r
        for r in beacon
        if r.ticker == "AADEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert aadex.amount == Decimal("2.3846")
    assert {r.ticker for r in beacon if r.ticker} >= {"AADEX", "SFMIX", "ABCIX", "AVFIX"}

    beacon_2021 = parse_distribution_html(
        (ROOT / "american_beacon" / "2021_annual_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://american_beacon/2021",
        fund_family="American Beacon",
    )
    aadex_2021 = next(
        r
        for r in beacon_2021
        if r.ticker == "AADEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert aadex_2021.amount == Decimal("2.2327")
    assert aadex_2021.publication_stage == PublicationStage.final
    assert aadex_2021.as_of == date(2021, 12, 23)
    assert not any(
        r.ticker == "AADEX" and r.estimate_type == EstimateType.long_term_capital_gains
        and r.amount == Decimal("0")
        for r in beacon_2021
    )

    beacon_2022 = parse_distribution_html(
        (ROOT / "american_beacon" / "2022_annual_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://american_beacon/2022",
        fund_family="American Beacon",
    )
    aadex_2022_st = next(
        r
        for r in beacon_2022
        if r.ticker == "AADEX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert aadex_2022_st.amount == Decimal("0.0001")
    aadex_2022_lt = next(
        r
        for r in beacon_2022
        if r.ticker == "AADEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert aadex_2022_lt.amount == Decimal("2.3936")

    beacon_2023 = parse_distribution_html(
        (ROOT / "american_beacon" / "2023_annual_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://american_beacon/2023",
        fund_family="American Beacon",
    )
    aadex_2023 = next(
        r
        for r in beacon_2023
        if r.ticker == "AADEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert aadex_2023.amount == Decimal("0.8312")
    assert not any(r.ticker == "SFMIX" for r in beacon_2023)

    beacon_2024 = parse_distribution_html(
        (ROOT / "american_beacon" / "2024_annual_ordinary_income_and_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://american_beacon/2024",
        fund_family="American Beacon",
    )
    aadex_2024 = next(
        r
        for r in beacon_2024
        if r.ticker == "AADEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert aadex_2024.amount == Decimal("2.5614")

    beacon_ncsr_bp = parse_distribution_html(
        (ROOT / "american_beacon" / "leftover_ncsr_2021_2022_wave_bp.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/809593/"
            "000119312526005743/d77694dncsr.htm"
        ),
        fund_family="American Beacon",
    )
    ghqix_2022_oi = next(
        r
        for r in beacon_ncsr_bp
        if r.ticker == "GHQIX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2022-10-31"
    )
    assert ghqix_2022_oi.amount == Decimal("0.21")
    assert ghqix_2022_oi.publication_stage == PublicationStage.final
    ghqix_2021_cg = next(
        r
        for r in beacon_ncsr_bp
        if r.ticker == "GHQIX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert ghqix_2021_cg.amount == Decimal("0.19")
    ghqpx_2022_oi = next(
        r
        for r in beacon_ncsr_bp
        if r.ticker == "GHQPX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2022-10-31"
    )
    assert ghqpx_2022_oi.amount == Decimal("0.18")
    assert {r.ticker for r in beacon_ncsr_bp} == {"GHQIX", "GHQYX", "GHQPX", "GHQRX"}
    assert not any(
        r.ticker
        in {
            "KTRAX",
            "KGDAX",
            "TOLLX",
            "KTCAX",
            "BTIEX",
            "SXPAX",
            "CCGIX",
            "SFMIX",
            "SHOAX",
            "NISAX",
            "SSIJX",
        }
        for r in beacon_ncsr_bp
    )
    assert not any(
        r.ticker in {"GHQIX", "GHQYX", "GHQPX", "GHQRX"}
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and r.as_of.year == 2022
        for r in beacon_ncsr_bp
    )

    bg = parse_distribution_html(
        (ROOT / "baillie_gifford" / "2025_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://baillie_gifford",
        fund_family="Baillie Gifford",
    )
    bgakx = next(
        r
        for r in bg
        if r.ticker == "BGAKX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bgakx.amount == Decimal("4.8350")
    bgcsx = next(
        r
        for r in bg
        if r.ticker == "BGCSX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bgcsx.amount == Decimal("1.6704")

    brandes = parse_distribution_html(
        (ROOT / "brandes" / "2025_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://brandes",
        fund_family="Brandes",
    )
    bgvix = next(
        r
        for r in brandes
        if r.ticker == "BGVIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bgvix.amount == Decimal("3.88")
    bismx = next(
        r
        for r in brandes
        if r.ticker == "BISMX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert bismx.amount == Decimal("0.16")

    mairs = parse_distribution_html(
        (ROOT / "mairs_power" / "2025_capital_gains_and_dividends.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://mairs_power",
        fund_family="Mairs & Power",
    )
    mpgfx = next(
        r
        for r in mairs
        if r.ticker == "MPGFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mpgfx.amount == Decimal("6.77074")

    boston = parse_distribution_html(
        (ROOT / "boston_trust" / "2025_distribution_factors.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://boston_trust",
        fund_family="Boston Trust Walden",
    )
    btbfx = next(
        r
        for r in boston
        if r.ticker == "BTBFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert btbfx.amount == Decimal("6.205293")

    grandeur = parse_distribution_html(
        (ROOT / "grandeur_peak" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://grandeur_peak",
        fund_family="Grandeur Peak",
    )
    gpeix = next(
        r
        for r in grandeur
        if r.ticker == "GPEIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert gpeix.amount == Decimal("2.30240")

    grandeur_br = parse_distribution_html(
        (ROOT / "grandeur_peak" / "leftover_paid_year_end_2021_2024_wave_br.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://grandeurpeakglobal.com/distributions/",
        fund_family="Grandeur Peak",
    )
    gpeix_2021_lt = next(
        r
        for r in grandeur_br
        if r.ticker == "GPEIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2021-12-28"
    )
    assert gpeix_2021_lt.amount == Decimal("1.96306")
    assert gpeix_2021_lt.publication_stage == PublicationStage.final
    gpgcx_2021_st = next(
        r
        for r in grandeur_br
        if r.ticker == "GPGCX"
        and r.estimate_type == EstimateType.short_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2021-12-28"
    )
    assert gpgcx_2021_st.amount == Decimal("0.47077")
    gprox_2024_oi = next(
        r
        for r in grandeur_br
        if r.ticker == "GPROX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.ex_date
        and str(r.ex_date) == "2024-12-20"
    )
    assert gprox_2024_oi.amount == Decimal("0.25570")
    assert {r.ticker for r in grandeur_br} == {"GPEIX", "GPGCX", "GPROX"}
    assert not any(
        r.ticker
        in {
            "GPEOX",
            "GPRIX",
            "GPGOX",
            "GPGIX",
            "GHQIX",
            "KTRAX",
            "KGDAX",
            "CCGIX",
            "TOLLX",
            "KTCAX",
            "PIODX",
            "PIOTX",
            "LCGFX",
            "VALLX",
            "CHUSX",
        }
        for r in grandeur_br
    )
    assert not any(r.ex_date and r.ex_date.year == 2025 for r in grandeur_br)

    hennessy = parse_distribution_html(
        (ROOT / "hennessy" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://hennessy",
        fund_family="Hennessy",
    )
    hfcsx = next(
        r
        for r in hennessy
        if r.ticker == "HFCSX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hfcsx.amount == Decimal("17.84742")

    hennessy_ncsr = parse_distribution_html(
        (ROOT / "hennessy" / "leftover_ncsr_2021_2024_wave_ay.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/891944/000199937126000464/"
            "hft-ncsr_103125.htm"
        ),
        fund_family="Hennessy",
    )
    hfcsx_2021 = next(
        r
        for r in hennessy_ncsr
        if r.ticker == "HFCSX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert hfcsx_2021.amount == Decimal("22.03")
    assert hfcsx_2021.publication_stage == PublicationStage.final
    hfcix_2021 = next(
        r
        for r in hennessy_ncsr
        if r.ticker == "HFCIX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert hfcix_2021.amount == Decimal("22.83")
    assert {r.ticker for r in hennessy_ncsr if r.as_of and r.as_of.year == 2025} == set()
    assert "HFCGX" not in {r.ticker for r in hennessy_ncsr}

    fam = parse_distribution_html(
        (ROOT / "fam" / "2025_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://fam",
        fund_family="FAM / Fenimore",
    )
    famvx = next(
        r
        for r in fam
        if r.ticker == "FAMVX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert famvx.amount == Decimal("4.8682")
    famfx = next(
        r
        for r in fam
        if r.ticker == "FAMFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert famfx.amount == Decimal("0.773")
    famdx = next(
        r
        for r in fam
        if r.ticker == "FAMDX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert famdx.amount == Decimal("0.773")

    meridian = parse_distribution_html(
        (ROOT / "meridian" / "2025_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://meridian",
        fund_family="Meridian",
    )
    mvalx = next(
        r
        for r in meridian
        if r.ticker == "MVALX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mvalx.amount == Decimal("4.10477")

    kinetics = parse_distribution_html(
        (ROOT / "kinetics" / "2025_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://kinetics",
        fund_family="Kinetics",
    )
    wwnpx = next(
        r
        for r in kinetics
        if r.ticker == "WWNPX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wwnpx.amount == Decimal("8.68572")

    leftover = parse_distribution_html(
        (ROOT / "kinetics" / "leftover_ncsr_2021_2024_wave_az.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://kineticsfunds.com/files/annual-report",
        fund_family="Kinetics",
    )
    leftover_wwwfx_2024 = next(
        r
        for r in leftover
        if r.ticker == "WWWFX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert leftover_wwwfx_2024.amount == Decimal("0.21")
    leftover_wwnpx_2024 = next(
        r
        for r in leftover
        if r.ticker == "WWNPX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert leftover_wwnpx_2024.amount == Decimal("3.86")
    leftover_2025 = [
        r
        for r in leftover
        if r.as_of and r.as_of.year == 2025
    ]
    assert leftover_2025 == []


def test_tenth_tier_fixtures() -> None:
    lazard = parse_distribution_html(
        (ROOT / "lazard" / "2025_estimated_annual_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://lazard",
        fund_family="Lazard",
    )
    lziex = next(
        r
        for r in lazard
        if r.ticker == "LZIEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert lziex.amount == Decimal("1.50")
    assert {r.ticker for r in lazard if r.ticker} >= {"LZIEX", "LEAIX", "ICMPX", "LISIX"}

    lazard_ncsr_cb = parse_distribution_html(
        (ROOT / "lazard" / "leftover_ncsr_open_2021_2025_wave_cb.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/874964/"
            "000093041326000617/c114847_ncsr-ixbrl.htm#open"
        ),
        fund_family="Lazard",
    )
    lziox_2025_oi = next(
        r
        for r in lazard_ncsr_cb
        if r.ticker == "LZIOX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2025-12-31"
    )
    assert lziox_2025_oi.amount == Decimal("0.43")
    assert lziox_2025_oi.publication_stage == PublicationStage.final
    lziox_2025_cg = next(
        r
        for r in lazard_ncsr_cb
        if r.ticker == "LZIOX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2025-12-31"
    )
    assert lziox_2025_cg.amount == Decimal("1.84")
    lisox_2021_roc = next(
        r
        for r in lazard_ncsr_cb
        if r.ticker == "LISOX"
        and r.estimate_type == EstimateType.return_of_capital
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert lisox_2021_roc.amount == Decimal("0.29")
    assert not any(
        r.ticker == "OCMPX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-12-31"
        for r in lazard_ncsr_cb
    )
    assert {r.ticker for r in lazard_ncsr_cb} == {
        "GLFOX",
        "LCAOX",
        "LDMOX",
        "LEAOX",
        "LEOOX",
        "LISOX",
        "LZFOX",
        "LZIOX",
        "LZOEX",
        "LZSCX",
        "LZSIX",
        "LZSMX",
        "LZUOX",
        "OCMPX",
    }
    assert not any(
        r.ticker
        in {
            "LZIEX",
            "GLIFX",
            "LZEMX",
            "PCEQX",
            "PYEQX",
            "PEQKX",
            "PCODX",
            "RCMPX",
            "CONIX",
            "RLEMX",
            "RLIEX",
            "RLITX",
            "RLUSX",
            "RLSMX",
        }
        for r in lazard_ncsr_cb
    )

    lazard_ncsr_cd = parse_distribution_html(
        (ROOT / "lazard" / "leftover_ncsr_r6_2021_2025_wave_cd.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/874964/"
            "000093041326000617/c114847_ncsr-ixbrl.htm#r6"
        ),
        fund_family="Lazard",
    )
    rliex_2025_oi = next(
        r
        for r in lazard_ncsr_cd
        if r.ticker == "RLIEX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2025-12-31"
    )
    assert rliex_2025_oi.amount == Decimal("0.48")
    assert rliex_2025_oi.publication_stage == PublicationStage.final
    rliex_2025_cg = next(
        r
        for r in lazard_ncsr_cd
        if r.ticker == "RLIEX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2025-12-31"
    )
    assert rliex_2025_cg.amount == Decimal("1.84")
    rliex_2024_oi = next(
        r
        for r in lazard_ncsr_cd
        if r.ticker == "RLIEX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert rliex_2024_oi.amount == Decimal("0.57")
    rlitx_2021_roc = next(
        r
        for r in lazard_ncsr_cd
        if r.ticker == "RLITX"
        and r.estimate_type == EstimateType.return_of_capital
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert rlitx_2021_roc.amount == Decimal("0.31")
    assert not any(
        r.ticker == "RLEMX"
        and r.estimate_type == EstimateType.total_capital_gains
        for r in lazard_ncsr_cd
    )
    assert not any(
        r.ticker == "RLSMX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
        for r in lazard_ncsr_cd
    )
    assert {r.ticker for r in lazard_ncsr_cd} == {
        "RLEMX",
        "RLIEX",
        "RLITX",
        "RLUSX",
        "RLSMX",
    }
    assert not any(
        r.ticker
        in {
            "LZIEX",
            "LZIOX",
            "GLIFX",
            "GLFOX",
            "LZEMX",
            "LZOEX",
            "PCEQX",
            "PYEQX",
            "PEQKX",
            "PCODX",
            "RCMPX",
            "READX",
            "CONIX",
        }
        for r in lazard_ncsr_cd
    )

    lazard_ncsr_cg = parse_distribution_html(
        (ROOT / "lazard" / "leftover_ncsr_real_assets_2021_2025_wave_cg.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/874964/"
            "000093041326000617/c114847_ncsr-ixbrl.htm#real-assets"
        ),
        fund_family="Lazard",
    )
    ralix_2025_oi = next(
        r
        for r in lazard_ncsr_cg
        if r.ticker == "RALIX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2025-12-31"
    )
    assert ralix_2025_oi.amount == Decimal("0.86")
    assert ralix_2025_oi.publication_stage == PublicationStage.final
    ralox_2025_oi = next(
        r
        for r in lazard_ncsr_cg
        if r.ticker == "RALOX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2025-12-31"
    )
    assert ralox_2025_oi.amount == Decimal("0.84")
    ralix_2022_cg = next(
        r
        for r in lazard_ncsr_cg
        if r.ticker == "RALIX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2022-12-31"
    )
    assert ralix_2022_cg.amount == Decimal("0.01")
    ralox_2021_oi = next(
        r
        for r in lazard_ncsr_cg
        if r.ticker == "RALOX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert ralox_2021_oi.amount == Decimal("1.23")
    assert not any(
        r.ticker == "RALIX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2025-12-31"
        for r in lazard_ncsr_cg
    )
    assert not any(
        r.ticker == "RALOX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2023-12-31"
        for r in lazard_ncsr_cg
    )
    assert {r.ticker for r in lazard_ncsr_cg} == {"RALIX", "RALOX"}
    assert not any(
        r.ticker
        in {
            "RALYX",
            "CONIX",
            "CONOX",
            "RLUEX",
            "READX",
            "RCMPX",
            "RLEMX",
            "RLIEX",
            "LZIOX",
            "LZIEX",
            "SPEGX",
            "AGFCX",
            "PIORX",
            "PQIRX",
        }
        for r in lazard_ncsr_cg
    )

    manning = parse_distribution_html(
        (ROOT / "manning_napier" / "2025_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://manning_napier",
        fund_family="Manning & Napier",
    )
    mnhix = next(
        r
        for r in manning
        if r.ticker == "MNHIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mnhix.amount == Decimal("2.56840")
    raiix = next(
        r
        for r in manning
        if r.ticker == "RAIIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert raiix.amount == Decimal("0.10760")

    westwood = parse_distribution_html(
        (ROOT / "westwood" / "2025_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://westwood",
        fund_family="Westwood",
    )
    whglx = next(
        r
        for r in westwood
        if r.ticker == "WHGLX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert whglx.amount == Decimal("2.235")

    boston = parse_distribution_html(
        (ROOT / "boston_partners" / "2025_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://boston_partners",
        fund_family="Boston Partners",
    )
    bpaix = next(
        r
        for r in boston
        if r.ticker == "BPAIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert bpaix.amount == Decimal("2.73")

    homestead = parse_distribution_html(
        (ROOT / "homestead" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://homestead",
        fund_family="Homestead",
    )
    hovlx = next(
        r
        for r in homestead
        if r.ticker == "HOVLX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hovlx.amount == Decimal("3.7449")

    homestead_ncsr = parse_distribution_html(
        (ROOT / "homestead" / "leftover_ncsr_2021_2024_wave_ar.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/865733/"
            "000114554925016761/8dd5cf6f78f6691.htm"
        ),
        fund_family="Homestead",
    )
    hovlx_ncsr = next(
        r
        for r in homestead_ncsr
        if r.ticker == "HOVLX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert hovlx_ncsr.amount == Decimal("4.06")
    assert hovlx_ncsr.publication_stage == PublicationStage.final
    assert {r.ticker for r in homestead_ncsr} == {
        "HSTIX",
        "HOVLX",
        "HNASX",
        "HISIX",
        "HSCSX",
    }

    madison = parse_distribution_html(
        (ROOT / "madison" / "2025_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://madison",
        fund_family="Madison",
    )
    mnvax = next(
        r
        for r in madison
        if r.ticker == "MNVAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mnvax.amount == Decimal("1.92670046")

    madison_ncsr = parse_distribution_html(
        (ROOT / "madison" / "leftover_ncsr_2021_2024_wave_ba.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1040612/"
            "000175392626000073/g211434_ncsr.htm"
        ),
        fund_family="Madison",
    )
    magsx_2021 = next(
        r
        for r in madison_ncsr
        if r.ticker == "MAGSX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert magsx_2021.amount == Decimal("0.94")
    assert magsx_2021.publication_stage == PublicationStage.final
    mnvax_2021 = next(
        r
        for r in madison_ncsr
        if r.ticker == "MNVAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert mnvax_2021.amount == Decimal("2.37")
    gtsgx_2022_oi = [
        r
        for r in madison_ncsr
        if r.ticker == "GTSGX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and r.as_of.year == 2022
    ]
    assert gtsgx_2022_oi == []
    assert {r.ticker for r in madison_ncsr if r.as_of and r.as_of.year == 2025} == set()
    assert "MAGG" not in {r.ticker for r in madison_ncsr}
    assert "MSTI" not in {r.ticker for r in madison_ncsr}

    lsv = parse_distribution_html(
        (ROOT / "lsv" / "2025_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://lsv",
        fund_family="LSV",
    )
    lsvex = next(
        r
        for r in lsv
        if r.ticker == "LSVEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert lsvex.amount == Decimal("4.4395")

    lsv_ncsr = parse_distribution_html(
        (ROOT / "lsv" / "leftover_ncsr_2021_2023_wave_au.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/878719/"
            "000119312524005240/d676331dncsr.htm"
        ),
        fund_family="LSV",
    )
    lsvex_ncsr = next(
        r
        for r in lsv_ncsr
        if r.ticker == "LSVEX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert lsvex_ncsr.amount == Decimal("0.62")
    assert lsvex_ncsr.publication_stage == PublicationStage.final
    lvaex_ncsr = next(
        r
        for r in lsv_ncsr
        if r.ticker == "LVAEX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert lvaex_ncsr.amount == Decimal("0.58")
    assert {r.ticker for r in lsv_ncsr} == {
        "LSVEX",
        "LVAEX",
        "LSVVX",
        "LVAVX",
        "LSVQX",
        "LVAQX",
        "LSVMX",
        "LVAMX",
        "LSVZX",
        "LVAZX",
        "LSVFX",
        "LVAFX",
        "LSVGX",
        "LVAGX",
    }

    lkcm = parse_distribution_html(
        (ROOT / "lkcm" / "2025_estimated_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://lkcm",
        fund_family="LKCM",
    )
    lkeqx = next(
        r
        for r in lkcm
        if r.ticker == "LKEQX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert lkeqx.amount == Decimal("3.8475")

    oberweis = parse_distribution_html(
        (ROOT / "oberweis" / "2025_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://oberweis",
        fund_family="Oberweis",
    )
    obegx = next(
        r
        for r in oberweis
        if r.ticker == "OBEGX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert obegx.amount == Decimal("3.9791")

    riverpark = parse_distribution_html(
        (ROOT / "riverpark" / "2025_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://riverpark",
        fund_family="RiverPark",
    )
    rpxix = next(
        r
        for r in riverpark
        if r.ticker == "RPXIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert rpxix.amount == Decimal("2.6688")

    riverpark_leftover = parse_distribution_html(
        (ROOT / "riverpark" / "leftover_paid_year_end_2021_2024_wave_bj.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.riverparkfunds.com/assets/pdfs/news/"
            "Year_End_Final_Distribution_Information_2021.pdf"
        ),
        fund_family="RiverPark",
    )
    rwgix_2021_lt = next(
        r
        for r in riverpark_leftover
        if r.ticker == "RWGIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2021-12-15"
    )
    assert rwgix_2021_lt.amount == Decimal("0.6912")
    assert rwgix_2021_lt.publication_stage == PublicationStage.final
    rpxix_2022_oi = next(
        r
        for r in riverpark_leftover
        if r.ticker == "RPXIX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2022-12-29"
    )
    assert rpxix_2022_oi.amount == Decimal("0.0011")
    assert {r.ticker for r in riverpark_leftover} == {
        "RWGIX",
        "RWGFX",
        "RPXIX",
        "RPXFX",
    }
    assert not any(
        r.ticker in {"RPNLX", "RPNRX", "RLSIX", "RPHIX", "RPNIX", "RPNCX"}
        for r in riverpark_leftover
    )
    assert not any(
        r.ticker == "RPXIX"
        and r.ex_date
        and r.ex_date.year == 2023
        for r in riverpark_leftover
    )


def test_parallel_w_leftover_paid_fixtures() -> None:
    manning = parse_distribution_html(
        (ROOT / "manning_napier" / "leftover_paid_year_end_parallel_w.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://manning-leftover-w",
        fund_family="Manning & Napier",
    )
    mnhix_2021_lt = next(
        r
        for r in manning
        if r.ticker == "MNHIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2021-12-14"
    )
    assert mnhix_2021_lt.amount == Decimal("0.85360")
    assert mnhix_2021_lt.publication_stage == PublicationStage.final
    assert "MSHIX" not in {r.ticker for r in manning}
    assert {r.ticker for r in manning if r.ticker} <= {
        "CEIIX",
        "CEISX",
        "CEIZX",
        "EXBAX",
        "EXEYX",
        "EXHAX",
        "MDFSX",
        "MDVWX",
        "MDVZX",
        "MEYWX",
        "MHYWX",
        "MHYZX",
        "MNBAX",
        "MNBIX",
        "MNBRX",
        "MNBWX",
        "MNDFX",
        "MNECX",
        "MNHAX",
        "MNHCX",
        "MNHIX",
        "MNHRX",
        "MNHWX",
        "MNHYX",
        "MNMCX",
        "MNMIX",
        "MNMRX",
        "MNMWX",
        "RAIIX",
        "RAIRX",
        "RAIWX",
        "RISAX",
    }

    westwood = parse_distribution_html(
        (ROOT / "westwood" / "leftover_paid_history_parallel_w.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://westwood-leftover-w",
        fund_family="Westwood",
    )
    whglx_2025_lt = next(
        r
        for r in westwood
        if r.ticker == "WHGLX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-12-12"
    )
    assert whglx_2025_lt.amount == Decimal("2.4094")
    assert {r.ticker for r in westwood} == {"WHGLX", "WWMCX", "WHGMX", "WHGSX", "WQAIX"}
    assert not any(r.ticker in {"WWLAX", "WHGQX", "WHGAX"} for r in westwood)

    boston = parse_distribution_html(
        (ROOT / "boston_partners" / "leftover_paid_finals_parallel_w.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://boston-leftover-w",
        fund_family="Boston Partners",
    )
    bpaix_2025_lt = next(
        r
        for r in boston
        if r.ticker == "BPAIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-12-12"
    )
    assert bpaix_2025_lt.amount == Decimal("2.68")
    assert not any(r.ticker in {"BELSX", "WPGHX"} for r in boston)

    lsv = parse_distribution_html(
        (ROOT / "lsv" / "leftover_paid_year_end_parallel_w.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://lsv-leftover-w",
        fund_family="LSV",
    )
    lsvex_2024_lt = next(
        r
        for r in lsv
        if r.ticker == "LSVEX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2024-12-23"
    )
    assert lsvex_2024_lt.amount == Decimal("1.6848")
    assert lsvex_2024_lt.publication_stage == PublicationStage.final


def test_parallel_x_leftover_paid_fixtures() -> None:
    dpl2 = parse_distribution_html(
        (ROOT / "fidelity" / "leftover_dpl2_class_i_2022_2024.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://fidelity-leftover-x-dpl2",
        fund_family="Fidelity",
    )
    ftrix_2022_mid = next(
        r
        for r in dpl2
        if r.ticker == "FTRIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2022-08-05"
    )
    assert ftrix_2022_mid.amount == Decimal("0.45700")
    assert ftrix_2022_mid.publication_stage == PublicationStage.final
    ftrix_2022_ye = next(
        r
        for r in dpl2
        if r.ticker == "FTRIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2022-12-09"
    )
    assert ftrix_2022_ye.amount == Decimal("0.05600")
    eqpgx_2024 = next(
        r
        for r in dpl2
        if r.ticker == "EQPGX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2024-12-26"
    )
    assert eqpgx_2024.amount == Decimal("2.48300")
    assert {r.ex_date.year for r in dpl2 if r.ticker == "EQPGX" and r.ex_date} == {
        2022,
        2023,
        2024,
    }

    ftrix_ncsr = parse_distribution_html(
        (ROOT / "fidelity" / "leftover_ftrix_ncsr_2021.html").read_text(encoding="utf-8"),
        source_url="fixture://fidelity-leftover-x-ftrix",
        fund_family="Fidelity",
    )
    ftrix_2021_oi = next(
        r
        for r in ftrix_ncsr
        if r.ticker == "FTRIX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert ftrix_2021_oi.amount == Decimal("0.29")
    assert str(ftrix_2021_oi.as_of) == "2021-06-30"
    assert ftrix_2021_oi.publication_stage == PublicationStage.final
    assert {r.ticker for r in ftrix_ncsr} == {"FTRIX"}

    wave_ao = parse_distribution_html(
        (ROOT / "fidelity" / "leftover_ncsr_class_i_2021_wave_ao.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://fidelity-leftover-ao-ncsr",
        fund_family="Fidelity",
    )
    fixix_ao = next(
        r
        for r in wave_ao
        if r.ticker == "FIXIX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fixix_ao.amount == Decimal("0.717")
    assert str(fixix_ao.payable_date) == "2021-12-06"
    assert str(fixix_ao.record_date) == "2021-12-03"
    assert fixix_ao.publication_stage == PublicationStage.final
    fopix_ao = next(
        r
        for r in wave_ao
        if r.ticker == "FOPIX"
        and r.estimate_type == EstimateType.total_capital_gains
    )
    assert fopix_ao.amount == Decimal("2.309")
    eqpgx_ao = next(
        r
        for r in wave_ao
        if r.ticker == "EQPGX"
        and r.estimate_type == EstimateType.total_capital_gains
    )
    assert eqpgx_ao.amount == Decimal("2.262")
    assert str(eqpgx_ao.payable_date) == "2021-12-29"
    assert {r.ticker for r in wave_ao} == {
        "FIXIX",
        "FOPIX",
        "FIADX",
        "FWIFX",
        "FVIFX",
        "FASOX",
        "EQPGX",
        "FSCIX",
        "FMCCX",
    }

    aci = parse_distribution_html(
        (ROOT / "american_century" / "leftover_ncsr_investor_2021_2025.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://aci-leftover-x",
        fund_family="American Century",
    )
    twcgx_2021 = next(
        r
        for r in aci
        if r.ticker == "TWCGX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2021-10-31"
    )
    assert twcgx_2021.amount == Decimal("1.56")
    assert twcgx_2021.publication_stage == PublicationStage.final
    assert {r.ticker for r in aci} == {
        "TWCGX",
        "AFDIX",
        "TWCIX",
        "TWCUX",
        "TWHIX",
        "ANOIX",
    }
    assert not any(
        r.ticker == "TWHIX" and r.as_of and r.as_of.year == 2023 for r in aci
    )

    jpm = parse_distribution_html(
        (ROOT / "jpmorgan" / "leftover_ncsr_class_a_2021_2024.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://jpm-leftover-x",
        fund_family="J.P. Morgan Asset Management",
    )
    oieix_2023 = next(
        r
        for r in jpm
        if r.ticker == "OIEIX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2023-06-30"
    )
    assert oieix_2023.amount == Decimal("0.42")
    assert oieix_2023.publication_stage == PublicationStage.final
    assert "UBVAX" not in {r.ticker for r in jpm}
    assert not any(
        r.ticker == "PGSGX" and r.as_of and r.as_of.year == 2024 for r in jpm
    )

    gs = parse_distribution_html(
        (ROOT / "goldman_sachs" / "leftover_ncsr_insights_2021_2024.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://gs-leftover-x",
        fund_family="Goldman Sachs Asset Management",
    )
    glcgx_2021 = next(
        r
        for r in gs
        if r.ticker == "GLCGX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2021-10-31"
    )
    assert glcgx_2021.amount == Decimal("3.80")
    assert glcgx_2021.publication_stage == PublicationStage.final
    assert {r.ticker for r in gs} == {"GLCGX", "GCGIX"}

    trowe_al = parse_distribution_html(
        (ROOT / "t_rowe_price" / "leftover_ncsr_advisor_r_inst_wave_al.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/902259/"
            "000119312525031529/d927665dncsr.htm"
        ),
        fund_family="T. Rowe Price",
    )
    pabgx_al = next(
        r
        for r in trowe_al
        if r.ticker == "PABGX"
        and r.estimate_type == EstimateType.total_capital_gains
        and str(r.as_of) == "2024-12-31"
    )
    assert pabgx_al.amount == Decimal("16.42")
    assert pabgx_al.publication_stage == PublicationStage.final
    iemfx_al = next(
        r
        for r in trowe_al
        if r.ticker == "IEMFX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.as_of) == "2024-10-31"
    )
    assert iemfx_al.amount == Decimal("0.60")
    assert "RRCOX" not in {r.ticker for r in trowe_al}
    assert "TRBCX" not in {r.ticker for r in trowe_al}
    assert {r.ticker for r in trowe_al} == {
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
    }


def test_eleventh_tier_fixtures() -> None:
    amg = parse_distribution_html(
        (ROOT / "amg" / "2025_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://amg",
        fund_family="AMG",
    )
    yackx = next(
        r
        for r in amg
        if r.ticker == "YACKX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert yackx.amount == Decimal("2.8135")
    assert {r.ticker for r in amg if r.ticker} >= {"YACKX", "YAFIX", "MCGIX", "ARIDX"}

    amg_frontier_ncsr = parse_distribution_html(
        (ROOT / "amg" / "leftover_ncsr_frontier_2022_wave_at.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/882443/"
            "000119312523003421/d398011dncsr.htm"
        ),
        fund_family="AMG",
    )
    mssvx_ncsr = next(
        r
        for r in amg_frontier_ncsr
        if r.ticker == "MSSVX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2022-10-31"
    )
    assert mssvx_ncsr.amount == Decimal("3.91")
    assert mssvx_ncsr.publication_stage == PublicationStage.final
    assert [
        r
        for r in amg_frontier_ncsr
        if r.ticker == "MSSVX" and r.estimate_type == EstimateType.ordinary_income
    ] == []
    assert {r.ticker for r in amg_frontier_ncsr if r.as_of and r.as_of.year == 2025} == set()

    amg_gwk_ncsr = parse_distribution_html(
        (ROOT / "amg" / "leftover_ncsr_gwk_smid_2023_wave_at.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1089951/"
            "000119312524003306/d110485dncsr.htm"
        ),
        fund_family="AMG",
    )
    acwdx_ncsr = next(
        r
        for r in amg_gwk_ncsr
        if r.ticker == "ACWDX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2023-10-31"
    )
    assert acwdx_ncsr.amount == Decimal("0.27")
    assert acwdx_ncsr.publication_stage == PublicationStage.final
    assert {r.ticker for r in amg_gwk_ncsr} == {"ACWDX", "ACWIX", "ACWZX"}

    guidestone = parse_distribution_html(
        (ROOT / "guidestone" / "2025_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://guidestone",
        fund_family="GuideStone",
    )
    ggezx = next(
        r
        for r in guidestone
        if r.ticker == "GGEZX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert ggezx.amount == Decimal("3.279591")
    gmzxx = next(
        r
        for r in guidestone
        if r.ticker == "GMZXX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert gmzxx.amount == Decimal("0.000031")
    assert {r.ticker for r in guidestone if r.ticker} >= {
        "GGEZX",
        "GVEZX",
        "GSCZX",
        "GMZXX",
        "GVIZX",
        "GEIZX",
        "GFSZX",
        "GMGZX",
    }

    value_line = parse_distribution_html(
        (ROOT / "value_line" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://value_line",
        fund_family="Value Line",
    )
    vleox = next(
        r
        for r in value_line
        if r.ticker == "VLEOX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert vleox.amount == Decimal("3.79637")

    permanent = parse_distribution_html(
        (ROOT / "permanent_portfolio" / "2025_supplemental_tax_information.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://permanent_portfolio",
        fund_family="Permanent Portfolio",
    )
    prpfx = next(
        r
        for r in permanent
        if r.ticker == "PRPFX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert prpfx.amount == Decimal("1.561510")

    conestoga = parse_distribution_html(
        (ROOT / "conestoga" / "2026_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://conestoga",
        fund_family="Conestoga",
    )
    ccalx = next(
        r
        for r in conestoga
        if r.ticker == "CCALX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert ccalx.amount == Decimal("19.71")
    assert ccalx.record_date is None
    assert ccalx.ex_date is None
    assert ccalx.payable_date is None
    cmirx = next(
        r
        for r in conestoga
        if r.ticker == "CMIRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cmirx.amount == Decimal("0.31")
    assert cmirx.record_date is None

    kopernik = parse_distribution_html(
        (ROOT / "kopernik" / "2025_final_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://kopernik",
        fund_family="Kopernik",
    )
    kggix = next(
        r
        for r in kopernik
        if r.ticker == "KGGIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert kggix.amount == Decimal("1.2488")

    locorr = parse_distribution_html(
        (ROOT / "locorr" / "2025_annual_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://locorr",
        fund_family="LoCorr",
    )
    leqix = next(
        r
        for r in locorr
        if r.ticker == "LEQIX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert leqix.amount == Decimal("2.0297")

    locorr_ncsr = parse_distribution_html(
        (ROOT / "locorr" / "leftover_ncsr_2021_2024_wave_bd.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1506768/"
            "000113322826003096/lit-efp22581_ncsr.htm"
        ),
        fund_family="LoCorr",
    )
    lfmix_2021 = next(
        r
        for r in locorr_ncsr
        if r.ticker == "LFMIX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert lfmix_2021.amount == Decimal("0.41")
    assert lfmix_2021.publication_stage == PublicationStage.final
    lfmix_2022_cg = next(
        r
        for r in locorr_ncsr
        if r.ticker == "LFMIX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2022-12-31"
    )
    assert lfmix_2022_cg.amount == Decimal("0.94")
    lfmix_2024_roc = next(
        r
        for r in locorr_ncsr
        if r.ticker == "LFMIX"
        and r.estimate_type == EstimateType.return_of_capital
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert lfmix_2024_roc.amount == Decimal("0.01")
    leqix_2021_cg = next(
        r
        for r in locorr_ncsr
        if r.ticker == "LEQIX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert leqix_2021_cg.amount == Decimal("0.78")
    assert {r.ticker for r in locorr_ncsr if r.as_of and r.as_of.year == 2025} == set()
    assert "LFMAX" not in {r.ticker for r in locorr_ncsr}
    assert "LSPIX" not in {r.ticker for r in locorr_ncsr}
    assert "LSAIX" not in {r.ticker for r in locorr_ncsr}

    timothy = parse_distribution_html(
        (ROOT / "timothy_plan" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://timothy_plan",
        fund_family="Timothy Plan",
    )
    tmvix = next(
        r
        for r in timothy
        if r.ticker == "TMVIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tmvix.amount == Decimal("0.1303")

    hodges = parse_distribution_html(
        (ROOT / "hodges" / "2025_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://hodges",
        fund_family="Hodges",
    )
    hdpmx = next(
        r
        for r in hodges
        if r.ticker == "HDPMX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hdpmx.amount == Decimal("5.82")

    tocqueville = parse_distribution_html(
        (ROOT / "tocqueville" / "2025_final_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://tocqueville",
        fund_family="Tocqueville",
    )
    tocqx = next(
        r
        for r in tocqueville
        if r.ticker == "TOCQX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tocqx.amount == Decimal("3.578")


def test_wave_aj_leftover_paid_fixtures() -> None:
    value_line = parse_distribution_html(
        (ROOT / "value_line" / "leftover_paid_history_wave_aj.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://value_line-wave-aj",
        fund_family="Value Line",
    )
    vleox = next(
        r
        for r in value_line
        if r.ticker == "VLEOX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2021-12-14"
    )
    assert vleox.amount == Decimal("3.27482")
    assert vleox.publication_stage == PublicationStage.final
    vlaax_2022 = next(
        r
        for r in value_line
        if r.ticker == "VLAAX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.ex_date
        and str(r.ex_date) == "2022-12-14"
    )
    assert vlaax_2022.amount == Decimal("0.32727")

    permanent = parse_distribution_html(
        (ROOT / "permanent_portfolio" / "leftover_paid_history_wave_aj.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://permanent_portfolio-wave-aj",
        fund_family="Permanent Portfolio",
    )
    prpfx = next(
        r
        for r in permanent
        if r.ticker == "PRPFX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2021-12-08"
    )
    assert prpfx.amount == Decimal("0.82485")

    kopernik = parse_distribution_html(
        (ROOT / "kopernik" / "leftover_paid_history_wave_aj.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://kopernik-wave-aj",
        fund_family="Kopernik",
    )
    kggix_oi = next(
        r
        for r in kopernik
        if r.ticker == "KGGIX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.ex_date
        and str(r.ex_date) == "2021-12-30"
    )
    assert kggix_oi.amount == Decimal("0.7679")

    tocqueville = parse_distribution_html(
        (ROOT / "tocqueville" / "leftover_paid_history_wave_aj.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://tocqueville-wave-aj",
        fund_family="Tocqueville",
    )
    tocqx = next(
        r
        for r in tocqueville
        if r.ticker == "TOCQX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and str(r.ex_date) == "2024-12-06"
    )
    assert tocqx.amount == Decimal("3.813")
    assert tocqx.publication_stage == PublicationStage.final


def test_dws_xtrackers_fixtures() -> None:
    dws_ici = parse_ici_primary(
        (ROOT / "dws" / "ici_primary_2025.csv").read_text(encoding="utf-8"),
        source_url="fixture://dws-ici-2025",
        fund_family="DWS / Xtrackers",
        default_as_of=date(2025, 12, 31),
    )
    dbef_jun = next(
        r
        for r in dws_ici
        if r.ticker == "DBEF"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2025-06-20"
    )
    assert dbef_jun.amount == Decimal("1.419000000")
    dbef_dec = next(
        r
        for r in dws_ici
        if r.ticker == "DBEF"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2025-12-19"
    )
    assert dbef_dec.amount == Decimal("1.250620000")
    hylb_feb = next(
        r
        for r in dws_ici
        if r.ticker == "HYLB"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2025-02-03"
    )
    assert hylb_feb.amount == Decimal("0.197230000")
    hdef_jun = next(
        r
        for r in dws_ici
        if r.ticker == "HDEF"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2025-06-20"
    )
    assert hdef_jun.amount == Decimal("0.630650000")
    ashr_dec = next(
        r
        for r in dws_ici
        if r.ticker == "ASHR" and r.estimate_type == EstimateType.ordinary_income
    )
    assert ashr_dec.amount == Decimal("0.758110000")
    pswd_st = next(
        r
        for r in dws_ici
        if r.ticker == "PSWD"
        and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert pswd_st.amount == Decimal("0.157780000")
    assert len({r.ticker for r in dws_ici if r.ticker}) >= 40
    assert not any(r.ticker in {"ASHS", "IND"} for r in dws_ici)

    dws_est = parse_distribution_html(
        (ROOT / "dws" / "2025_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://dws-est-2025",
        fund_family="DWS / Xtrackers",
    )
    pswd_est = next(
        r
        for r in dws_est
        if r.ticker == "PSWD"
        and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert pswd_est.amount == Decimal("0.1599")

    dws_final = parse_distribution_html(
        (ROOT / "dws" / "2025_final_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://dws-final-2025",
        fund_family="DWS / Xtrackers",
    )
    pswd_final = next(
        r
        for r in dws_final
        if r.ticker == "PSWD"
        and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert pswd_final.amount == Decimal("0.1578")

    dws_mf = parse_distribution_html(
        (ROOT / "dws" / "2025_retail_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://dws-mf-2025",
        fund_family="DWS / Xtrackers",
    )
    sdgax = next(
        r
        for r in dws_mf
        if r.ticker == "SDGAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert sdgax.amount == Decimal("9.7933")
    ktcax_lt = next(
        r
        for r in dws_mf
        if r.ticker == "KTCAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert ktcax_lt.amount == Decimal("3.5700")
    suwax = next(
        r
        for r in dws_mf
        if r.ticker == "SUWAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert suwax.amount == Decimal("3.5547")
    assert len({r.ticker for r in dws_mf if r.ticker}) >= 19
    assert not any("Municipal Income Trust" in r.fund_name for r in dws_mf)
    assert not any("New Germany" in r.fund_name for r in dws_mf)

    dws_mid = parse_distribution_html(
        (ROOT / "dws" / "2026_estimated_midyear_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://dws-mf-2026-mid",
        fund_family="DWS / Xtrackers",
    )
    sxpax_mid = next(
        r
        for r in dws_mid
        if r.ticker == "SXPAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert sxpax_mid.amount == Decimal("0.6101")
    btiex_mid = next(
        r
        for r in dws_mid
        if r.ticker == "BTIEX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert btiex_mid.amount == Decimal("6.1523")

    dws_ncsr = parse_distribution_html(
        (ROOT / "dws" / "leftover_ncsr_2021_2024_wave_bg.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/862157/"
            "000008805326000209/ar123125e500.htm"
        ),
        fund_family="DWS / Xtrackers",
    )
    btiex_2024 = next(
        r
        for r in dws_ncsr
        if r.ticker == "BTIEX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert btiex_2024.amount == Decimal("1.98")
    assert btiex_2024.publication_stage == PublicationStage.final
    sxpax_2022_cg = next(
        r
        for r in dws_ncsr
        if r.ticker == "SXPAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2022-12-31"
    )
    assert sxpax_2022_cg.amount == Decimal("1.47")
    assert {r.ticker for r in dws_ncsr} == {"BTIEX", "SXPAX"}
    assert not any(
        r.ticker in {"BTIIX", "BTIRX", "SXPCX", "SCPIX", "SXPRX", "KTCAX"}
        for r in dws_ncsr
    )

    dws_ncsr_bi = parse_distribution_html(
        (ROOT / "dws" / "leftover_ncsr_2021_2024_wave_bi.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/88048/"
            "000008805325001134/ar103125dstf.htm"
        ),
        fund_family="DWS / Xtrackers",
    )
    ktcax_2024 = next(
        r
        for r in dws_ncsr_bi
        if r.ticker == "KTCAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2024-10-31"
    )
    assert ktcax_2024.amount == Decimal("3.60")
    assert ktcax_2024.publication_stage == PublicationStage.final
    ktcax_2021 = next(
        r
        for r in dws_ncsr_bi
        if r.ticker == "KTCAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert ktcax_2021.amount == Decimal("2.43")
    assert {r.ticker for r in dws_ncsr_bi} == {"KTCAX"}
    assert not any(
        r.ticker in {"KTCCX", "KTCIX", "KTCSX", "BTIEX", "SXPAX"}
        for r in dws_ncsr_bi
    )
    assert not any(
        r.ticker == "KTCAX" and r.estimate_type == EstimateType.ordinary_income
        for r in dws_ncsr_bi
    )

    dws_ncsr_bk = parse_distribution_html(
        (ROOT / "dws" / "leftover_ncsr_2021_2024_wave_bk.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/793597/"
            "000008805326000211/ar123125drgif.htm"
        ),
        fund_family="DWS / Xtrackers",
    )
    tollx_2024 = next(
        r
        for r in dws_ncsr_bk
        if r.ticker == "TOLLX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert tollx_2024.amount == Decimal("0.39")
    assert tollx_2024.publication_stage == PublicationStage.final
    tollx_2021_cg = next(
        r
        for r in dws_ncsr_bk
        if r.ticker == "TOLLX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert tollx_2021_cg.amount == Decimal("0.86")
    assert {r.ticker for r in dws_ncsr_bk} == {"TOLLX"}
    assert not any(
        r.ticker in {"TOLCX", "TOLSX", "TOLIX", "TOLZX", "BTIEX", "SXPAX", "KTCAX", "KGDAX"}
        for r in dws_ncsr_bk
    )

    dws_ncsr_bn = parse_distribution_html(
        (ROOT / "dws" / "leftover_ncsr_2021_2024_wave_bn.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/793597/"
            "000008805325001132/ar103125dgsc.htm"
        ),
        fund_family="DWS / Xtrackers",
    )
    kgdax_2024_oi = next(
        r
        for r in dws_ncsr_bn
        if r.ticker == "KGDAX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-10-31"
    )
    assert kgdax_2024_oi.amount == Decimal("0.20")
    assert kgdax_2024_oi.publication_stage == PublicationStage.final
    kgdax_2024_cg = next(
        r
        for r in dws_ncsr_bn
        if r.ticker == "KGDAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2024-10-31"
    )
    assert kgdax_2024_cg.amount == Decimal("1.26")
    kgdax_2021_cg = next(
        r
        for r in dws_ncsr_bn
        if r.ticker == "KGDAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert kgdax_2021_cg.amount == Decimal("0.13")
    assert {r.ticker for r in dws_ncsr_bn} == {"KGDAX"}
    assert not any(
        r.ticker
        in {
            "KGDCX",
            "SGSCX",
            "KGDIX",
            "KGDZX",
            "TOLLX",
            "KTCAX",
            "BTIEX",
            "SXPAX",
            "CCGIX",
            "CCGSX",
            "CCWIX",
            "CCWSX",
        }
        for r in dws_ncsr_bn
    )
    assert not any(
        r.ticker == "KGDAX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and r.as_of.year in {2021, 2023}
        for r in dws_ncsr_bn
    )
    assert not any(r.ticker == "KTRAX" for r in dws_ncsr_bn)

    dws_ncsr_bo = parse_distribution_html(
        (ROOT / "dws" / "leftover_ncsr_2021_2024_wave_bo.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/95603/"
            "000008805325001130/ar103125dgib.htm"
        ),
        fund_family="DWS / Xtrackers",
    )
    ktrax_2024_oi = next(
        r
        for r in dws_ncsr_bo
        if r.ticker == "KTRAX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-10-31"
    )
    assert ktrax_2024_oi.amount == Decimal("0.34")
    assert ktrax_2024_oi.publication_stage == PublicationStage.final
    ktrax_2022_cg = next(
        r
        for r in dws_ncsr_bo
        if r.ticker == "KTRAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2022-10-31"
    )
    assert ktrax_2022_cg.amount == Decimal("0.80")
    ktrax_2021_oi = next(
        r
        for r in dws_ncsr_bo
        if r.ticker == "KTRAX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-10-31"
    )
    assert ktrax_2021_oi.amount == Decimal("0.22")
    assert {r.ticker for r in dws_ncsr_bo} == {"KTRAX"}
    assert not any(
        r.ticker
        in {
            "KTRCX",
            "KTRSX",
            "KTRIX",
            "KTRZX",
            "KGDAX",
            "TOLLX",
            "KTCAX",
            "BTIEX",
            "SXPAX",
            "CCGIX",
            "CCGSX",
            "CCWIX",
            "CCWSX",
        }
        for r in dws_ncsr_bo
    )
    assert not any(
        r.ticker == "KTRAX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and r.as_of.year in {2021, 2023, 2024}
        for r in dws_ncsr_bo
    )

    baird_ncsr_bm = parse_distribution_html(
        (ROOT / "baird" / "leftover_ncsr_2021_2024_wave_bm.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1282693/"
            "000113322826002879/bf-efp22201_ncsr.htm"
        ),
        fund_family="Baird",
    )
    ccgix_2021 = next(
        r
        for r in baird_ncsr_bm
        if r.ticker == "CCGIX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2021-12-31"
    )
    assert ccgix_2021.amount == Decimal("0.08")
    assert ccgix_2021.publication_stage == PublicationStage.final
    ccgsx_2023 = next(
        r
        for r in baird_ncsr_bm
        if r.ticker == "CCGSX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2023-12-31"
    )
    assert ccgsx_2023.amount == Decimal("0.04")
    ccwix_2024 = next(
        r
        for r in baird_ncsr_bm
        if r.ticker == "CCWIX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert ccwix_2024.amount == Decimal("0.12")
    ccwsx_2024 = next(
        r
        for r in baird_ncsr_bm
        if r.ticker == "CCWSX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert ccwsx_2024.amount == Decimal("0.08")
    assert {r.ticker for r in baird_ncsr_bm} == {"CCGIX", "CCGSX", "CCWIX", "CCWSX"}
    assert not any(
        r.ticker in {"BSVIX", "BSVSX", "BMDIX", "BMDSX", "BCOIX", "BSGIX", "TMAIX"}
        for r in baird_ncsr_bm
    )
    assert not any(
        r.estimate_type == EstimateType.total_capital_gains for r in baird_ncsr_bm
    )


def test_catalyst_annual_distribution_fixtures() -> None:
    catalyst = parse_distribution_html(
        (ROOT / "catalyst" / "2025_annual_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://catalyst-2025",
        fund_family="Catalyst Funds",
    )
    cpeax = next(
        r
        for r in catalyst
        if r.ticker == "CPEAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cpeax.amount == Decimal("3.4499")
    cltax = next(
        r
        for r in catalyst
        if r.ticker == "CLTAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cltax.amount == Decimal("1.5946")
    caxix_inc = next(
        r
        for r in catalyst
        if r.ticker == "CAXIX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert caxix_inc.amount == Decimal("0.2482")
    caxix_lt = next(
        r
        for r in catalyst
        if r.ticker == "CAXIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert caxix_lt.amount == Decimal("1.0636")
    shiix = next(
        r
        for r in catalyst
        if r.ticker == "SHIIX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert shiix.amount == Decimal("0.3285")
    casix = next(
        r
        for r in catalyst
        if r.ticker == "CASIX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert casix.amount == Decimal("0.2419")
    mbxax_lt = next(
        r
        for r in catalyst
        if r.ticker == "MBXAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mbxax_lt.amount == Decimal("0.00")
    eixax_lt = next(
        r
        for r in catalyst
        if r.ticker == "EIXAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert eixax_lt.amount == Decimal("0.00")
    atrax_lt = next(
        r
        for r in catalyst
        if r.ticker == "ATRAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert atrax_lt.amount == Decimal("0.00")
    cweax_lt = next(
        r
        for r in catalyst
        if r.ticker == "CWEAX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert cweax_lt.amount == Decimal("0.00")
    shiex = next(
        r
        for r in catalyst
        if r.ticker == "SHIEX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert shiex.amount == Decimal("0.3004")
    cwxax = next(
        r
        for r in catalyst
        if r.ticker == "CWXAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert cwxax.amount == Decimal("0.2115")
    tickers = {r.ticker for r in catalyst if r.ticker}
    assert len(tickers) == 54
    assert {
        "CPEAX",
        "CPEIX",
        "CPECX",
        "CLTAX",
        "CLTIX",
        "CLTCX",
        "CAXAX",
        "CAXIX",
        "CAXCX",
        "MBXAX",
        "MBXCX",
        "MBXIX",
        "EIXAX",
        "EIXCX",
        "EIXIX",
        "ATRAX",
        "CWEAX",
        "SHIEX",
        "CASAX",
        "CWXAX",
        "CLPAX",
        "INSAX",
        "IIXAX",
        "CFRAX",
        "TRXAX",
        "HIIFX",
        "TRIFX",
    } <= tickers
    assert not any(r.ticker in {"CSIOX", "MBXFX", "CFRFX"} for r in catalyst)
    assert not any(
        r.ticker == "MBXAX" and r.estimate_type == EstimateType.ordinary_income for r in catalyst
    )


def test_parallel_s_leftover_paid_fixtures() -> None:
    ariel = parse_distribution_html(
        (ROOT / "ariel" / "leftover_paid_history_parallel_s.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://ariel-leftover-s",
        fund_family="Ariel",
    )
    argfx_2024_lt = next(
        r
        for r in ariel
        if r.ticker == "ARGFX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.payable_date) == "2024-12-18"
    )
    assert argfx_2024_lt.amount == Decimal("3.868892")
    assert argfx_2024_lt.publication_stage == PublicationStage.final
    assert {r.ticker for r in ariel} == {"ARGFX", "ARAIX"}

    primecap = parse_distribution_html(
        (ROOT / "primecap" / "leftover_paid_finals_parallel_s.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://primecap-leftover-s",
        fund_family="PRIMECAP Odyssey",
    )
    poskx_2025_lt = next(
        r
        for r in primecap
        if r.ticker == "POSKX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-12-15"
    )
    assert poskx_2025_lt.amount == Decimal("8.59624")
    assert poskx_2025_lt.publication_stage == PublicationStage.final

    hotchkis = parse_distribution_html(
        (ROOT / "hotchkis" / "leftover_paid_year_end_parallel_s.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://hotchkis-leftover-s",
        fund_family="Hotchkis & Wiley",
    )
    hwlix_2024_lt = next(
        r
        for r in hotchkis
        if r.ticker == "HWLIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2024-12-05"
    )
    assert hwlix_2024_lt.amount == Decimal("3.90044000")
    assert {r.ticker for r in hotchkis} == {"HWLIX", "HWAIX", "HWNIX"}

    baird = parse_distribution_html(
        (ROOT / "baird" / "leftover_paid_capital_gains_parallel_s.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://baird-leftover-s",
        fund_family="Baird",
    )
    bmdix_2021_lt = next(
        r
        for r in baird
        if r.ticker == "BMDIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2021-12-16"
    )
    assert bmdix_2021_lt.amount == Decimal("4.39824")
    assert not any(r.ticker in {"BCOIX", "BSGIX"} for r in baird)

    champlain = parse_distribution_html(
        (ROOT / "champlain" / "leftover_paid_year_end_parallel_s.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://champlain-leftover-s",
        fund_family="Champlain",
    )
    cipix_2021_lt = next(
        r
        for r in champlain
        if r.ticker == "CIPIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2021-12-14"
    )
    assert cipix_2021_lt.amount == Decimal("1.6369")
    assert not any(r.ticker in {"CIPMX", "CIPSX"} for r in champlain)
    assert not any(
        r.ticker == "CIPTX" and r.ex_date and r.ex_date.year in {2021, 2022} for r in champlain
    )

    davis = parse_distribution_html(
        (ROOT / "davis" / "leftover_paid_year_end_parallel_s.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://davis-leftover-s",
        fund_family="Davis Funds",
    )
    nyvtx_2024_lt = next(
        r
        for r in davis
        if r.ticker == "NYVTX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2024-12-13"
    )
    assert nyvtx_2024_lt.amount == Decimal("3.00")
    assert {r.ticker for r in davis} == {"NYVTX", "DGFAX", "RPEAX"}
    assert not any(
        r.ticker == "DGFAX" and r.ex_date and r.ex_date.year == 2022 for r in davis
    )


def test_parallel_v_leftover_paid_fixtures() -> None:
    heartland = parse_distribution_html(
        (ROOT / "heartland" / "leftover_paid_history_parallel_v.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://heartland-leftover-v",
        fund_family="Heartland",
    )
    hrtvx_2024_lt = next(
        r
        for r in heartland
        if r.ticker == "HRTVX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2024-12-20"
    )
    assert hrtvx_2024_lt.amount == Decimal("3.86958")
    assert hrtvx_2024_lt.publication_stage == PublicationStage.final
    assert {r.ticker for r in heartland} == {
        "HRMDX",
        "HNMDX",
        "HRVIX",
        "HNVIX",
        "HRTVX",
        "HNTVX",
    }

    fmi = parse_distribution_html(
        (ROOT / "fmi" / "leftover_paid_history_parallel_v.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://fmi-leftover-v",
        fund_family="FMI",
    )
    fmiux_2021_lt = next(
        r
        for r in fmi
        if r.ticker == "FMIUX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2021-12-17"
    )
    assert fmiux_2021_lt.amount == Decimal("3.86103")
    assert fmiux_2021_lt.publication_stage == PublicationStage.final
    assert {r.ticker for r in fmi} == {"FMIUX", "FMIMX"}
    assert not any(r.ticker == "FMIHX" for r in fmi)

    brandes = parse_distribution_html(
        (ROOT / "brandes" / "leftover_paid_history_parallel_v.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://brandes-leftover-v",
        fund_family="Brandes",
    )
    bgvix_2025_lt = next(
        r
        for r in brandes
        if r.ticker == "BGVIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-12-10"
    )
    assert bgvix_2025_lt.amount == Decimal("3.624675")
    assert bgvix_2025_lt.publication_stage == PublicationStage.final
    assert {r.ticker for r in brandes} == {"BGVIX", "BIIEX", "BSCMX", "BEMIX", "BISMX"}

    baillie = parse_distribution_html(
        (ROOT / "baillie_gifford" / "leftover_paid_history_parallel_v.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://baillie-leftover-v",
        fund_family="Baillie Gifford",
    )
    bgakx_2025_lt = next(
        r
        for r in baillie
        if r.ticker == "BGAKX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-12-29"
    )
    assert bgakx_2025_lt.amount == Decimal("5.18723")
    assert bgakx_2025_lt.publication_stage == PublicationStage.final
    assert {r.ticker for r in baillie} == {"BGAKX", "BINSX", "BGESX", "BSGPX"}
    assert not any(r.ticker == "BGCSX" for r in baillie)

    baillie_ncsr = parse_distribution_html(
        (ROOT / "baillie_gifford" / "leftover_ncsr_2021_2024_wave_bf.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.sec.gov/Archives/edgar/data/1120543/"
            "000110465925020192/tm251686d1_ncsr.htm"
        ),
        fund_family="Baillie Gifford",
    )
    bgakx_2024 = next(
        r
        for r in baillie_ncsr
        if r.ticker == "BGAKX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.as_of
        and str(r.as_of) == "2024-12-31"
    )
    assert bgakx_2024.amount == Decimal("0.26")
    assert bgakx_2024.publication_stage == PublicationStage.final
    bsgpx_2022_cg = next(
        r
        for r in baillie_ncsr
        if r.ticker == "BSGPX"
        and r.estimate_type == EstimateType.total_capital_gains
        and r.as_of
        and str(r.as_of) == "2022-12-31"
    )
    assert bsgpx_2022_cg.amount == Decimal("0.11")
    assert {r.ticker for r in baillie_ncsr} == {"BGAKX", "BINSX", "BGESX", "BSGPX"}
    assert not any(r.ticker == "BGCSX" for r in baillie_ncsr)
    assert not any(
        r.ticker in {"BGIKX", "BGEKX", "BGPKX"} for r in baillie_ncsr
    )


def test_wave_ag_victory_leftover_paid_fixtures() -> None:
    ncsr = parse_distribution_html(
        (ROOT / "victory" / "leftover_ncsr_rs_2021.html").read_text(encoding="utf-8"),
        source_url="fixture://victory-leftover-ag-ncsr",
        fund_family="Victory Capital",
    )
    rsgrx_2021_oi = next(
        r
        for r in ncsr
        if r.ticker == "RSGRX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert rsgrx_2021_oi.amount == Decimal("0.02")
    assert str(rsgrx_2021_oi.as_of) == "2021-12-31"
    assert rsgrx_2021_oi.publication_stage == PublicationStage.final
    rsgrx_2021_cg = next(
        r
        for r in ncsr
        if r.ticker == "RSGRX" and r.estimate_type == EstimateType.total_capital_gains
    )
    assert rsgrx_2021_cg.amount == Decimal("2.35")
    rspfx_oi = [
        r
        for r in ncsr
        if r.ticker == "RSPFX" and r.estimate_type == EstimateType.ordinary_income
    ]
    assert rspfx_oi == []

    leftover_2024 = parse_distribution_html(
        (ROOT / "victory" / "leftover_2024_r_member_r6.html").read_text(encoding="utf-8"),
        source_url="fixture://victory-leftover-ag-2024",
        fund_family="Victory Capital",
    )
    getgx_2024 = next(
        r
        for r in leftover_2024
        if r.ticker == "GETGX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert getgx_2024.amount == Decimal("0.130481")
    assert str(getgx_2024.ex_date) == "2024-12-13"
    assert getgx_2024.publication_stage == PublicationStage.final
    assert {r.ticker for r in leftover_2024} >= {
        "GETGX",
        "GOGFX",
        "GRINX",
        "MGOSX",
        "MUXRX",
        "MMMMX",
    }


def test_wave_aq_victory_leftover_oct31_ncsr() -> None:
    ncsr = parse_distribution_html(
        (ROOT / "victory" / "leftover_ncsr_sycamore_diversified_2021_wave_aq.html").read_text(
            encoding="utf-8"
        ),
        source_url="fixture://victory-leftover-aq-ncsr",
        fund_family="Victory Capital",
    )
    vetax_2021_oi = next(
        r
        for r in ncsr
        if r.ticker == "VETAX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vetax_2021_oi.amount == Decimal("0.52")
    assert str(vetax_2021_oi.as_of) == "2021-10-31"
    assert vetax_2021_oi.publication_stage == PublicationStage.final
    vetax_2021_cg = next(
        r
        for r in ncsr
        if r.ticker == "VETAX" and r.estimate_type == EstimateType.total_capital_gains
    )
    assert vetax_2021_cg.amount == Decimal("1.67")
    vevix_2021_oi = next(
        r
        for r in ncsr
        if r.ticker == "VEVIX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert vevix_2021_oi.amount == Decimal("0.65")
    getgx_2021_oi = next(
        r
        for r in ncsr
        if r.ticker == "GETGX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert getgx_2021_oi.amount == Decimal("0.43")
    grinx_oi = [
        r
        for r in ncsr
        if r.ticker == "GRINX" and r.estimate_type == EstimateType.ordinary_income
    ]
    assert grinx_oi == []
    assert {r.ticker for r in ncsr} == {
        "VETAX",
        "VEVCX",
        "VEVIX",
        "GETGX",
        "VEVRX",
        "VEVYX",
        "SSGSX",
        "VSOIX",
        "GOGFX",
        "VSORX",
        "VSOYX",
        "SRVEX",
        "VDSCX",
        "VDSIX",
        "GRINX",
        "VDSRX",
        "VDSYX",
    }
