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
