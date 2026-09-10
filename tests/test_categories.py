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
    assert resolve_category(ticker="DBEF", fund_name="Xtrackers MSCI EAFE Hedged Equity ETF") == (
        "Foreign Large Blend"
    )
    assert resolve_category(ticker="HYLB", fund_name="Xtrackers USD High Yield Corporate Bond ETF") == (
        "High Yield Bond"
    )
    assert resolve_category(ticker="ASHR") == "China Region"
    assert resolve_category(ticker="SDGAX", fund_name="DWS Capital Growth Fund") == "Large Growth"
    assert resolve_category(ticker="SUWAX", fund_name="DWS Core Equity Fund") == "Large Blend"
    assert resolve_category(ticker="KTCAX", fund_name="DWS Science and Technology Fund") == (
        "Technology"
    )
    assert resolve_category(ticker="SXPAX", fund_name="DWS S&P 500 Index Fund") == "Large Blend"
    assert resolve_category(ticker="FAGAX", fund_name="FA Growth Opp - A") == "Large Growth"
    assert resolve_category(ticker="FTRIX", fund_name="FA Mega Cap Stock - I") == "Large Blend"
    assert resolve_category(ticker="FNDX") == "Large Value"
    assert resolve_category(ticker="FNDE") == "Diversified Emerging Markets"
    assert resolve_category(ticker="FNDA") == "Small Blend"


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
    assert resolve_category(fund_name="American Century One Choice 2065 Portfolio Investor") == (
        "Target-Date 2065"
    )
    assert resolve_category(
        fund_name="American Century One Choice Blend+ In Retirement Port Investor"
    ) == "Retirement Income"
    assert resolve_category(fund_name="American Century One Choice Portfolio: Aggressive Investor") == (
        "Aggressive Allocation"
    )
    assert resolve_category(fund_name="Fidelity Freedom 2060") == "Target-Date 2060"
    assert resolve_category(fund_name="MFS Lifetime 2025 Fund") == "Target-Date 2025"
    assert resolve_category(fund_name="T. Rowe Price Retirement 2060") == "Target-Date 2060"
    assert resolve_category(fund_name="Vanguard GNMA Fund Admiral Shares") == "Intermediate Government"
    assert resolve_category(fund_name="AQR Equity Market Neutral Fund") == "Market Neutral"
    assert resolve_category(fund_name="Fidelity Asset Manager 20%") == "Conservative Allocation"
    assert resolve_category(fund_name="Fidelity Asset Manager 40%") == "Moderately Conservative Allocation"
    assert resolve_category(fund_name="Fidelity Asset Manager 60%") == "Moderate Allocation"
    assert resolve_category(fund_name="Fidelity Asset Manager 85%") == "Aggressive Allocation"
    assert resolve_category(fund_name="Vanguard LifeStrategy Conservative Growth Fund") == (
        "Moderately Conservative Allocation"
    )
    assert resolve_category(fund_name="Vanguard LifeStrategy Growth Fund") == "Aggressive Allocation"
    assert resolve_category(fund_name="Vanguard LifeStrategy Income Fund") == "Conservative Allocation"
    assert resolve_category(fund_name="Vanguard Global Wellesley Income Fund Admiral Shares") == (
        "Global Conservative Allocation"
    )
    assert resolve_category(fund_name="Vanguard Global Wellington Fund Investor Shares") == (
        "Global Allocation"
    )
    assert resolve_category(fund_name="Vanguard STAR Fund") == "Moderate Allocation"
    assert resolve_category(fund_name="MFS U.S. Government Cash Reserve Fund All Classes") == (
        "Money Market-Taxable"
    )
    assert resolve_category(fund_name="MFS Core Equity Fund Class I") == "Large Blend"
    assert resolve_category(fund_name="Massachusetts Investors Growth Stock Fund Class B") == (
        "Large Growth"
    )
    assert resolve_category(fund_name="AMG Systematica Trend-Enhanced Markets Fund Class I") == (
        "Systematic Trend"
    )
    assert resolve_category(fund_name="American Century Vp Inflation Protection Fund Class-I") == (
        "Inflation-Protected Bond"
    )
    assert resolve_category(fund_name="GMO Ultra-Short Income ETF") == "Ultrashort Bond"
    assert resolve_category(fund_name="Schwab Prime Advantage Money Fund—Investor Shares") == (
        "Money Market-Taxable"
    )
    assert resolve_category(fund_name="Schwab AMT Tax-Free Money Fund—Investor Shares") == (
        "Money Market-Tax-Free"
    )
    # Maturity-year bond is not a target-date vintage.
    assert resolve_category(fund_name="American Century Zero Coupon 2025 Fund Investor") is None
    # Target-risk mix without a published style word stays null (Yahoo/issuer map only).
    assert resolve_category(fund_name="BlackRock 60/40 Target Allocation Fund") is None


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
    assert canonical_category("Allocation--50% to 70% Equity") == "Moderate Allocation"
    assert canonical_category("Allocation--15% to 30% Equity") == "Conservative Allocation"
    assert canonical_category("Target-Date Retirement") == "Retirement Income"
    assert canonical_category("Equity Market Neutral") == "Market Neutral"
    assert canonical_category("World Allocation") == "Global Allocation"
    assert canonical_category("not-a-real-category") is None
    assert canonical_category("") is None
    assert canonical_category(None) is None
