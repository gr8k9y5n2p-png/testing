from __future__ import annotations

from app.categories import canonical_category, resolve_category


def test_curated_flagships() -> None:
    assert resolve_category(ticker="AGTHX", fund_name="The Growth Fund of America") == "Large Growth"
    assert resolve_category(fund_identifier="amcap-fund", fund_name="AMCAP Fund") == "Large Growth"
    assert resolve_category(ticker="ABALX") == "Moderate Allocation"
    assert resolve_category(ticker="VFIAX", fund_name="Vanguard 500 Index Fund") == "Large Blend"
    assert resolve_category(ticker="VBIAX", fund_name="Vanguard Balanced Index Fund") == "Moderate Allocation"
    assert resolve_category(ticker="DODIX", fund_name="Dodge & Cox Income Fund") == "Intermediate Core Bond"
    assert resolve_category(ticker="DODGX") == "Large Value"
    assert resolve_category(ticker="VTIAX") == "Foreign Large Blend"


def test_name_rules_high_confidence() -> None:
    assert (
        resolve_category(fund_name="iShares Core S&P 500 ETF") == "Large Blend"
    )
    assert (
        resolve_category(fund_name="Vanguard Total Bond Market Index Admiral")
        == "Intermediate Core Bond"
    )
    assert resolve_category(fund_name="Schwab Short-Term Bond Index") == "Short-Term Bond"
    assert resolve_category(fund_name="Fidelity Large Cap Growth") == "Large Growth"
    assert resolve_category(fund_name="T. Rowe Price Mid-Cap Value") == "Mid-Cap Value"
    assert resolve_category(fund_name="Vanguard Small-Cap Index") == "Small Blend"
    assert (
        resolve_category(fund_name="iShares MSCI EAFE ETF") == "Foreign Large Blend"
    )
    assert (
        resolve_category(fund_name="Vanguard Emerging Markets Stock Index")
        == "Diversified Emerging Markets"
    )
    assert resolve_category(fund_name="American Funds 2035 Target Date Retirement Fund") == (
        "Target-Date 2035"
    )
    assert resolve_category(fund_name="Vanguard Health Care Index") == "Health"
    assert resolve_category(fund_name="iShares Core U.S. REIT ETF") == "Real Estate"
    assert resolve_category(fund_name="Vanguard High-Yield Corporate") == "High Yield Bond"
    assert resolve_category(fund_name="Vanguard Intermediate-Term Tax-Exempt") == (
        "Muni National Interm"
    )
    assert resolve_category(fund_name="Fidelity Government Money Market") == "Money Market-Taxable"
    assert resolve_category(fund_name="BlackRock LifePath Dynamic 2060 Fund") == "Target-Date 2060"
    assert resolve_category(fund_name="BlackRock LifePath Index Retirement Fund") == "Retirement Income"
    assert (
        resolve_category(fund_name="iShares Large Cap Max Buffer Dec ETF") == "Defined Outcome"
    )


def test_ambiguous_names_stay_null() -> None:
    assert resolve_category(fund_name="Strategic Opportunities Fund") is None
    assert resolve_category(fund_name="Select Equity") is None
    assert resolve_category(fund_name="Income Fund") is None
    assert resolve_category(fund_name="Core Fund") is None
    assert resolve_category(fund_name="ZZ Parser Sample") is None
    assert resolve_category(ticker=None, fund_identifier=None, fund_name=None) is None
    # Size-less "Growth Fund" is too easy to mis-bin (large vs mid vs small).
    assert resolve_category(fund_name="Harbor Growth Fund") is None


def test_canonical_category_aliases() -> None:
    assert canonical_category("large growth") == "Large Growth"
    assert canonical_category("Large-Cap Growth") == "Large Growth"
    assert canonical_category("muni national intermediate") == "Muni National Interm"
    assert canonical_category("not-a-real-category") is None
    assert canonical_category("") is None
    assert canonical_category(None) is None
