from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.models import AmountUnit, EstimateType, PublicationStage
from app.sources.parser import (
    infer_stage,
    is_ingestible_distribution_amount,
    parse_amount,
    parse_capital_group_html,
    parse_distribution_html,
    split_fund_and_ticker,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "american_funds"


def test_split_ticker_em_dash() -> None:
    name, ticker = split_fund_and_ticker("CGHM — Capital Group Municipal High-Income ETF")
    assert ticker == "CGHM"
    assert "Municipal High-Income" in name


def test_parse_amount_dollar_and_range() -> None:
    single = parse_amount("$3.5365")
    assert single and single.amount == Decimal("3.5365")
    assert single.unit == AmountUnit.per_share

    rng = parse_amount("3% – 5%", AmountUnit.percent_of_nav)
    assert rng and rng.amount_min == Decimal("3") and rng.amount_max == Decimal("5")
    assert rng.amount == Decimal("4")
    assert rng.unit == AmountUnit.percent_of_nav

    lt = parse_amount("<1%", AmountUnit.percent_of_nav)
    assert lt and lt.amount_min == Decimal("0") and lt.amount_max == Decimal("1")

    assert parse_amount("—") is None
    assert parse_amount("") is None

    bare = parse_amount("100%")
    assert bare and bare.amount == Decimal("100")
    assert bare.unit == AmountUnit.percent
    assert not is_ingestible_distribution_amount(
        EstimateType.qualified_dividend, AmountUnit.percent, amount_text="100%"
    )
    assert not is_ingestible_distribution_amount(
        EstimateType.long_term_capital_gains,
        AmountUnit.percent,
        amount_text="41.94%",
        unit_hint=AmountUnit.per_share,
    )
    assert is_ingestible_distribution_amount(
        EstimateType.total_capital_gains,
        AmountUnit.percent_of_nav,
        amount_text="3% – 5%",
        unit_hint=AmountUnit.percent_of_nav,
    )
    assert is_ingestible_distribution_amount(
        EstimateType.qualified_dividend,
        AmountUnit.per_share,
        amount_text="$0.18",
    )
    assert is_ingestible_distribution_amount(
        EstimateType.ordinary_income,
        AmountUnit.per_share,
        amount_text="$0.42",
    )
    assert is_ingestible_distribution_amount(
        EstimateType.special_dividend,
        AmountUnit.per_share,
        amount_text="$0.34",
    )
    assert is_ingestible_distribution_amount(
        EstimateType.return_of_capital,
        AmountUnit.per_share,
        amount_text="$0.05",
    )


def test_midyear_fixture_normalizes_live_markup() -> None:
    html = (FIXTURES / "midyear_2026_cap_gains.html").read_text(encoding="utf-8")
    records = parse_capital_group_html(
        html,
        source_url="https://www.capitalgroup.com/individual/service-and-support/tax-center/midyear-cap-gains.html",
    )
    by_name = {(r.fund_name, r.estimate_type): r for r in records}

    amcap = by_name[("AMCAP Fund", EstimateType.long_term_capital_gains)]
    assert amcap.amount == Decimal("3.5365")
    assert amcap.amount_unit == AmountUnit.per_share
    assert amcap.publication_stage == PublicationStage.paid
    assert str(amcap.ex_date) == "2026-06-16"
    assert str(amcap.payable_date) == "2026-06-17"
    assert str(amcap.as_of) == "2026-07-08"

    cghm_lt = by_name[("Capital Group Municipal High-Income ETF", EstimateType.long_term_capital_gains)]
    assert cghm_lt.ticker == "CGHM"
    cghm_st = by_name[("Capital Group Municipal High-Income ETF", EstimateType.short_term_capital_gains)]
    assert cghm_st.amount == Decimal("0.0169")

    # Dashes must not become rows
    assert ("AMCAP Fund", EstimateType.short_term_capital_gains) not in by_name
    assert len(records) == 11


def test_year_end_fixture_dates_without_year_and_extra_tables() -> None:
    html = (FIXTURES / "year_end_2025_distributions.html").read_text(encoding="utf-8")
    records = parse_capital_group_html(
        html,
        source_url="https://www.capitalgroup.com/individual/service-and-support/tax-center/2025-year-end-distributions.html",
    )
    amcap = next(r for r in records if r.fund_name == "AMCAP Fund" and r.estimate_type == EstimateType.long_term_capital_gains)
    assert amcap.amount == Decimal("2.1509")
    assert amcap.ticker == "AMCPX"
    assert str(amcap.ex_date) == "2025-12-12"
    assert str(amcap.as_of) == "2026-01-22"

    abalx = next(
        r
        for r in records
        if r.fund_name == "American Balanced Fund" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert abalx.amount == Decimal("2.1250")
    assert abalx.ticker == "ABALX"
    assert abalx.cusip == "024071102"

    special = next(
        r for r in records if r.fund_name == "American Balanced Fund" and r.estimate_type == EstimateType.special_dividend
    )
    assert special.amount == Decimal("0.3400")

    # "% of dividends that are qualified" is 1099 character, not a distribution.
    assert not any(r.estimate_type == EstimateType.qualified_dividend for r in records)
    assert not any(r.amount_unit == AmountUnit.percent for r in records)

    # Continuation tables reuse the previous header row (no <th> Fund/Ex-date).
    portfolio = next(
        r
        for r in records
        if "Conservative Growth and Income Portfolio" in r.fund_name
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert portfolio.amount == Decimal("0.2752")
    assert str(portfolio.ex_date) == "2025-12-29"

    name, ticker = split_fund_and_ticker("CGCV — Capital Group Conservative Equity ETF")
    assert ticker == "CGCV"
    assert "Conservative Equity ETF" in name


def test_estimate_fixture_percent_of_nav_ranges() -> None:
    html = (FIXTURES / "year_end_estimates_sample.html").read_text(encoding="utf-8")
    records = parse_capital_group_html(html, source_url="fixture://estimates")
    amcap = next(r for r in records if r.fund_name == "AMCAP Fund")
    assert amcap.estimate_type == EstimateType.total_capital_gains
    assert amcap.amount_unit == AmountUnit.percent_of_nav
    assert amcap.amount_min == Decimal("3")
    assert amcap.amount_max == Decimal("5")

    insight = next(r for r in records if "Global Insight" in r.fund_name)
    assert insight.amount_max == Decimal("1")
    assert insight.amount_min == Decimal("0")

    # Bond fund row is a dash — skipped
    assert not any("Bond Fund of America" in r.fund_name for r in records)

    fund_inv = next(
        r
        for r in records
        if r.fund_name == "Fundamental Investors" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert fund_inv.amount_min == Decimal("4.80")
    assert fund_inv.amount_max == Decimal("5.50")
    assert fund_inv.ticker == "ANCFX"

    cgdv = next(r for r in records if r.ticker == "CGDV")
    assert "Dividend Value" in cgdv.fund_name


_CAP_GROUP_QDI_PERCENT_HTML = """
<html><head><meta name="date" content="2026-01-22"/></head>
<body>
<table>
<tr><th colspan="3"><h4>Funds that paid qualified dividends</h4></th></tr>
<tr>
  <th>Fund</th>
  <th>Qualified dividend income percentage*</th>
  <th>Qualified short-term capital gains percentage</th>
</tr>
<tr>
  <td>The Growth Fund of America®</td>
  <td>100.00</td>
  <td>—</td>
</tr>
<tr>
  <td>American Balanced Fund®</td>
  <td>41.94%</td>
  <td>—</td>
</tr>
</table>
</body></html>
"""


def test_cap_group_qdi_percent_is_not_a_distribution() -> None:
    """AGTHX 100% qualified is % of income — do not store a dollar/percent row."""
    records = parse_capital_group_html(
        _CAP_GROUP_QDI_PERCENT_HTML,
        source_url="https://www.capitalgroup.com/individual/service-and-support/tax-center/2025-year-end-distributions.html",
    )
    assert records == []

    html = (FIXTURES / "year_end_2025_distributions.html").read_text(encoding="utf-8")
    ye = parse_capital_group_html(
        html,
        source_url="https://www.capitalgroup.com/individual/service-and-support/tax-center/2025-year-end-distributions.html",
    )
    agthx = [r for r in ye if r.ticker == "AGTHX"]
    assert agthx, "YE fixture must still emit AGTHX dollar distributions"
    assert all(r.estimate_type != EstimateType.qualified_dividend for r in agthx)
    assert all(r.amount_unit != AmountUnit.percent for r in agthx)
    assert all(r.amount != Decimal("100") or r.amount_unit != AmountUnit.percent for r in agthx)
    gfa_qdi = [
        r
        for r in ye
        if r.fund_name == "The Growth Fund of America"
        and r.estimate_type == EstimateType.qualified_dividend
    ]
    assert gfa_qdi == []


def test_qualified_dividend_per_share_column_is_ingested() -> None:
    """Real $/share QDI (and other tax characters) are distributions — keep them."""
    html = """
    <html><head><meta name="date" content="2025-12-15"/></head>
    <body>
    <table>
      <tr>
        <th>Fund</th>
        <th>Ordinary Income</th>
        <th>Qualified Dividend</th>
        <th>Short-Term Capital Gains</th>
        <th>Long-Term Capital Gains</th>
        <th>Special Dividend</th>
        <th>Return of Capital</th>
      </tr>
      <tr>
        <td>AGTHX — The Growth Fund of America</td>
        <td>$0.4200</td>
        <td>$0.1800</td>
        <td>$0.0500</td>
        <td>$2.1500</td>
        <td>$0.3400</td>
        <td>$0.0100</td>
      </tr>
    </table>
    </body></html>
    """
    records = parse_distribution_html(html, source_url="fixture://qdi-dollars", fund_family="American Funds")
    by_type = {r.estimate_type: r for r in records if r.ticker == "AGTHX"}
    assert by_type[EstimateType.ordinary_income].amount == Decimal("0.4200")
    assert by_type[EstimateType.qualified_dividend].amount == Decimal("0.1800")
    assert by_type[EstimateType.qualified_dividend].amount_unit == AmountUnit.per_share
    assert by_type[EstimateType.short_term_capital_gains].amount == Decimal("0.0500")
    assert by_type[EstimateType.long_term_capital_gains].amount == Decimal("2.1500")
    assert by_type[EstimateType.special_dividend].amount == Decimal("0.3400")
    assert by_type[EstimateType.return_of_capital].amount == Decimal("0.0100")
    assert all(r.amount_unit == AmountUnit.per_share for r in records)


def test_bare_percent_cell_in_dollar_table_is_not_ingested() -> None:
    html = """
    <html><body>
    <table>
      <tr><th>Fund</th><th>Per Share Amount</th></tr>
      <tr><td>The Growth Fund of America®</td><td>41.94%</td></tr>
      <tr><td>AMCAP Fund</td><td>$3.5365</td></tr>
    </table>
    </body></html>
    """
    records = parse_distribution_html(html, source_url="fixture://bare-pct", fund_family="American Funds")
    assert not any("%" in (r.raw_payload or {}).get("row_text", [""])[1] and r.amount_unit == AmountUnit.percent for r in records)
    assert not any(r.amount_unit == AmountUnit.percent for r in records)
    amcap = next(r for r in records if r.fund_name == "AMCAP Fund")
    assert amcap.amount == Decimal("3.5365")
    assert amcap.amount_unit == AmountUnit.per_share
    assert not any(r.fund_name == "The Growth Fund of America" for r in records)


def test_infer_stage_midyear_paid_vs_estimate() -> None:
    assert (
        infer_stage(
            "2026 midyear capital gain distributions",
            source_url="https://www.capitalgroup.com/individual/service-and-support/tax-center/midyear-cap-gains.html",
        )
        == PublicationStage.paid
    )
    assert (
        infer_stage(
            "2025 Mid-Year Capital Gains Distributions Estimates",
            source_url=(
                "https://www.columbiathreadneedleus.com/binaries/content/assets/cti/"
                "public/2025-mid-year-cap-gain-estimates-all-funds.pdf"
            ),
        )
        == PublicationStage.preliminary_estimate
    )
    assert (
        infer_stage(
            "Capital Gains Distributions",
            "2026 mid-year ETF capital gains distributions",
            source_url="https://www.ishares.com/us/capital-gains-distributions",
        )
        == PublicationStage.paid
    )
    assert (
        infer_stage(
            "Capital Gains Distributions",
            "2025 year-end ETF capital gains distributions",
            source_url="https://www.ishares.com/us/capital-gains-distributions",
        )
        == PublicationStage.final
    )
    assert (
        infer_stage(
            "2026 Semi-Annual Distributions",
            source_url="https://davisfunds.com/funds/distributions",
        )
        == PublicationStage.paid
    )
    assert (
        infer_stage(
            "Northern Funds equity 2024 year-end paid capital gain distributions",
            source_url=(
                "https://ntam.northerntrust.com/content/dam/northerntrust/"
                "investment-management/global/en/documents/account-resources/"
                "tax-center/estimated-capital-gains-2024.pdf"
            ),
        )
        == PublicationStage.final
    )
    assert (
        infer_stage(
            "Macquarie 2025 capital gains distribution estimates as of September 30, 2025",
            source_url="https://mim.fgsfulfillment.com/download.aspx?sku=CGE-RET",
        )
        == PublicationStage.preliminary_estimate
    )
    assert (
        infer_stage(
            "Victory Portfolios 2025 Final Ordinary Income and Capital Gains",
            source_url=(
                "https://investor.vcm.com/assets/resources-mutualfunddoc/"
                "Victory-Funds-2025-Final-Ordinary-Income-and-Capital-Gains-Distributions.pdf"
            ),
        )
        == PublicationStage.final
    )
