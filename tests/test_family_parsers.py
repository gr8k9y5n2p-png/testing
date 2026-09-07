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
    nyvtx = next(
        r
        for r in davis
        if r.ticker == "NYVTX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert nyvtx.amount == Decimal("0.89")


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
