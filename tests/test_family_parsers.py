from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.models import AmountUnit, EstimateType, PublicationStage
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

    jpm_2024 = parse_distribution_html(
        (ROOT / "jpmorgan" / "2024_section_19a.html").read_text(encoding="utf-8"),
        source_url="fixture://jpm-2024",
        fund_family="J.P. Morgan Asset Management",
    )
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
