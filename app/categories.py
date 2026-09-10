"""Fund category (Morningstar-style) on fund identity.

Category is identity-level metadata — not a distribution amount and not copied
onto every estimate row. Unknown stays ``None``. Never invent a wrong category.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

# Advisor-tool Morningstar US Category names. Filters match these strings
# (case / hyphen / space insensitive via ``canonical_category``).
CANONICAL_CATEGORIES: frozenset[str] = frozenset(
    {
        "Large Growth",
        "Large Value",
        "Large Blend",
        "Mid-Cap Growth",
        "Mid-Cap Value",
        "Mid-Cap Blend",
        "Small Growth",
        "Small Value",
        "Small Blend",
        "Foreign Large Growth",
        "Foreign Large Value",
        "Foreign Large Blend",
        "Foreign Small/Mid Growth",
        "Foreign Small/Mid Value",
        "Foreign Small/Mid Blend",
        "Diversified Emerging Markets",
        "Diversified Pacific/Asia",
        "Europe Stock",
        "Japan Stock",
        "China Region",
        "India Equity",
        "Latin America Stock",
        "Pacific/Asia ex-Japan Stk",
        "World Large-Stock Growth",
        "World Large-Stock Value",
        "World Large-Stock Blend",
        "Global Large-Stock Growth",
        "Global Large-Stock Value",
        "Global Large-Stock Blend",
        "World Small/Mid Stock",
        "Global Small/Mid Stock",
        "Communications",
        "Consumer Cyclical",
        "Consumer Defensive",
        "Equity Energy",
        "Equity Precious Metals",
        "Financial",
        "Health",
        "Industrials",
        "Natural Resources",
        "Real Estate",
        "Global Real Estate",
        "Technology",
        "Utilities",
        "Infrastructure",
        "Convertibles",
        "Preferred Stock",
        "Long-Short Equity",
        "Market Neutral",
        "Options Trading",
        "Derivative Income",
        "Conservative Allocation",
        "Moderately Conservative Allocation",
        "Moderate Allocation",
        "Moderately Aggressive Allocation",
        "Aggressive Allocation",
        "Global Conservative Allocation",
        "Global Allocation",
        "Global Aggressive Allocation",
        "Tactical Allocation",
        "Retirement Income",
        "Target-Date 2000-2010",
        "Target-Date 2015",
        "Target-Date 2020",
        "Target-Date 2025",
        "Target-Date 2030",
        "Target-Date 2035",
        "Target-Date 2040",
        "Target-Date 2045",
        "Target-Date 2050",
        "Target-Date 2055",
        "Target-Date 2060",
        "Target-Date 2065",
        "Target-Date 2070+",
        "Intermediate Core Bond",
        "Intermediate Core-Plus Bond",
        "Short-Term Bond",
        "Ultrashort Bond",
        "Long-Term Bond",
        "Short Government",
        "Intermediate Government",
        "Long Government",
        "Inflation-Protected Bond",
        "Corporate Bond",
        "High Yield Bond",
        "Bank Loan",
        "Multisector Bond",
        "Nontraditional Bond",
        "Emerging Markets Bond",
        "World Bond",
        "World Bond-USD Hedged",
        "Muni National Short",
        "Muni National Interm",
        "Muni National Long",
        "High Yield Muni",
        "Muni California Intermediate",
        "Muni California Long",
        "Muni New York Intermediate",
        "Muni New York Long",
        "Money Market-Taxable",
        "Money Market-Tax-Free",
        "Defined Outcome",
        "Multistrategy",
        "Systematic Trend",
        "Equity Digital Assets",
        "Commodities Broad Basket",
        "Commodities Focused",
        "Trading--Leveraged Equity",
        "Trading--Inverse Equity",
        "Event Driven",
        "Miscellaneous Region",
        "Miscellaneous Sector",
    }
)

# Extra Yahoo / issuer spellings → canonical Morningstar-style name.
_CATEGORY_ALIASES: dict[str, str] = {
    "global large-stock growth": "World Large-Stock Growth",
    "global large stock growth": "World Large-Stock Growth",
    "global large-stock value": "World Large-Stock Value",
    "global large stock value": "World Large-Stock Value",
    "global large-stock blend": "World Large-Stock Blend",
    "global large stock blend": "World Large-Stock Blend",
    "global small/mid stock": "World Small/Mid Stock",
    "global small mid stock": "World Small/Mid Stock",
    "world stock": "World Large-Stock Blend",
    "foreign large-cap growth": "Foreign Large Growth",
    "foreign large-cap value": "Foreign Large Value",
    "foreign large-cap blend": "Foreign Large Blend",
    "large-cap growth": "Large Growth",
    "large cap growth": "Large Growth",
    "large-cap value": "Large Value",
    "large cap value": "Large Value",
    "large-cap blend": "Large Blend",
    "large cap blend": "Large Blend",
    "mid cap growth": "Mid-Cap Growth",
    "midcap growth": "Mid-Cap Growth",
    "mid cap value": "Mid-Cap Value",
    "midcap value": "Mid-Cap Value",
    "mid cap blend": "Mid-Cap Blend",
    "midcap blend": "Mid-Cap Blend",
    "small cap growth": "Small Growth",
    "small-cap growth": "Small Growth",
    "small cap value": "Small Value",
    "small-cap value": "Small Value",
    "small cap blend": "Small Blend",
    "small-cap blend": "Small Blend",
    "high-yield bond": "High Yield Bond",
    "high yield municipal": "High Yield Muni",
    "high-yield muni": "High Yield Muni",
    "muni national intermediate": "Muni National Interm",
    "municipal national intermediate": "Muni National Interm",
    "municipal national short": "Muni National Short",
    "municipal national long": "Muni National Long",
    "inflation protected bond": "Inflation-Protected Bond",
    "tips": "Inflation-Protected Bond",
    "money market - taxable": "Money Market-Taxable",
    "money market taxable": "Money Market-Taxable",
    "prime money market": "Money Market-Taxable",
    "money market - tax-free": "Money Market-Tax-Free",
    "tax-free money market": "Money Market-Tax-Free",
    "target date 2070": "Target-Date 2070+",
    "target-date 2070": "Target-Date 2070+",
    "target date 2000-2010": "Target-Date 2000-2010",
    "pacific/asia ex-japan stock": "Pacific/Asia ex-Japan Stk",
    "greater china region": "China Region",
    "greater china": "China Region",
    "digital assets": "Equity Digital Assets",
    "equity digital assets": "Equity Digital Assets",
    "defined outcome": "Defined Outcome",
    "multistrategy": "Multistrategy",
    "multi-strategy": "Multistrategy",
    "systematic trend": "Systematic Trend",
    "commodities broad basket": "Commodities Broad Basket",
    "commodities focused": "Commodities Focused",
    "trading--leveraged equity": "Trading--Leveraged Equity",
    "trading leveraged equity": "Trading--Leveraged Equity",
    "trading--inverse equity": "Trading--Inverse Equity",
    "trading inverse equity": "Trading--Inverse Equity",
    "event driven": "Event Driven",
    "intermediate-term bond": "Intermediate Core Bond",
    "intermediate term bond": "Intermediate Core Bond",
    "diversified emerging mkts": "Diversified Emerging Markets",
    # Yahoo fundProfile / Morningstar US Category spellings.
    "allocation 15% to 30% equity": "Conservative Allocation",
    "allocation 30% to 50% equity": "Moderately Conservative Allocation",
    "allocation 50% to 70% equity": "Moderate Allocation",
    "allocation 70% to 85% equity": "Moderately Aggressive Allocation",
    "allocation 85%+ equity": "Aggressive Allocation",
    "target date retirement": "Retirement Income",
    "target-date retirement": "Retirement Income",
    "target date 2060+": "Target-Date 2060",
    "target-date 2060+": "Target-Date 2060",
    "target date 2065+": "Target-Date 2065",
    "target-date 2065+": "Target-Date 2065",
    "equity market neutral": "Market Neutral",
    "world allocation": "Global Allocation",
    "global moderate allocation": "Global Allocation",
    "global moderately conservative allocation": "Global Conservative Allocation",
    "global bond usd hedged": "World Bond-USD Hedged",
    "emerging markets local currency bond": "Emerging Markets Bond",
    "emerging-markets local-currency bond": "Emerging Markets Bond",
    "government mortgage backed bond": "Intermediate Government",
    "short term inflation protected bond": "Inflation-Protected Bond",
    "focused region": "Miscellaneous Region",
}

_SPACE_RE = re.compile(r"[\s_\-/]+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")

# Well-known issuer / SEC-stable identities. Public Morningstar US Category
# as published on issuer fact sheets — not guessed from a vague name.
_CURATED_TICKERS: dict[str, str] = {
    "AGTHX": "Large Growth",
    "AMCPX": "Large Growth",
    "ABALX": "Moderate Allocation",
    "AIVSX": "Large Blend",
    "ANCFX": "Large Blend",
    "AWSHX": "Large Value",
    "AMRMX": "Large Value",
    "ANEFX": "Large Growth",
    "ANWPX": "World Large-Stock Growth",
    "AEPGX": "Foreign Large Growth",
    "SMCWX": "Global Small/Mid Stock",
    "NEWFX": "Diversified Emerging Markets",
    "IGAAX": "Foreign Large Blend",
    "CWGIX": "World Large-Stock Blend",
    "CAIBX": "Global Allocation",
    "AMECX": "Moderate Allocation",
    "ABNDX": "Intermediate Core Bond",
    "AIBAX": "Intermediate Core Bond",
    "ASBAX": "Short-Term Bond",
    "AHITX": "High Yield Bond",
    "AMHIX": "High Yield Muni",
    "LTEBX": "Muni National Interm",
    "ASTEX": "Muni National Short",
    "CWBFX": "World Bond",
    "DBEF": "Foreign Large Blend",
    "HYLB": "High Yield Bond",
    "ASHR": "China Region",
    "HDEF": "Foreign Large Value",
    "PSWD": "Technology",
    "SDGAX": "Large Growth",
    "SUWAX": "Large Blend",
    "KTCAX": "Technology",
    "SXPAX": "Large Blend",
    "AMUSX": "Intermediate Government",
    "BFIAX": "Inflation-Protected Bond",
    "BFCAX": "Corporate Bond",
    "AFCPX": "Intermediate Core-Plus Bond",
    "MFAAX": "Intermediate Government",
    "MIAQX": "Multisector Bond",
    "ANBAX": "Nontraditional Bond",
    "EBNAX": "Emerging Markets Bond",
    "DWGAX": "Diversified Emerging Markets",
    "EMRGX": "Diversified Emerging Markets",
    "GBLAX": "Global Allocation",
    "AGVFX": "World Large-Stock Blend",
    "AIVBX": "Foreign Large Growth",
    "AFAXX": "Money Market-Taxable",
    "INPAX": "Moderately Conservative Allocation",
    "GAIOX": "Moderate Allocation",
    "GWPAX": "Aggressive Allocation",
    "BLPAX": "Moderate Allocation",
    "PPVAX": "Conservative Allocation",
    "NAARX": "Retirement Income",
    "NBARX": "Retirement Income",
    "NDARX": "Retirement Income",
    "PGGAX": "World Large-Stock Growth",
    "TAIAX": "Conservative Allocation",
    "SMDEX": "Mid-Cap Blend",
    "FBGRX": "Large Growth",
    "FCNTX": "Large Growth",
    "FXAIX": "Large Blend",
    "FSKAX": "Large Blend",
    "FTBFX": "Intermediate Core Bond",
    "VFIAX": "Large Blend",
    "VFINX": "Large Blend",
    "VOO": "Large Blend",
    "VTI": "Large Blend",
    "VTSAX": "Large Blend",
    "VTSMX": "Large Blend",
    "VIGAX": "Large Growth",
    "VIGRX": "Large Growth",
    "VUG": "Large Growth",
    "VVIAX": "Large Value",
    "VIVAX": "Large Value",
    "VTV": "Large Value",
    "VIMAX": "Mid-Cap Blend",
    "VSMAX": "Small Blend",
    "VBIAX": "Moderate Allocation",
    "VBINX": "Moderate Allocation",
    "VGSTX": "Moderate Allocation",
    "VASIX": "Conservative Allocation",
    "VSCGX": "Moderately Conservative Allocation",
    "VSMGX": "Moderate Allocation",
    "VASGX": "Aggressive Allocation",
    "VGYAX": "Global Conservative Allocation",
    "VGWIX": "Global Conservative Allocation",
    "VGWAX": "Global Allocation",
    "VGWLX": "Global Allocation",
    "FASIX": "Conservative Allocation",
    "FTANX": "Conservative Allocation",
    "FFANX": "Moderately Conservative Allocation",
    "FASMX": "Moderate Allocation",
    "FSANX": "Moderate Allocation",
    "FASGX": "Moderately Aggressive Allocation",
    "FAMRX": "Aggressive Allocation",
    "VBTLX": "Intermediate Core Bond",
    "BND": "Intermediate Core Bond",
    "VTIAX": "Foreign Large Blend",
    "VGTSX": "Foreign Large Blend",
    "VXUS": "Foreign Large Blend",
    "VEMAX": "Diversified Emerging Markets",
    "VWEAX": "High Yield Bond",
    "DODIX": "Intermediate Core Bond",
    "DODGX": "Large Value",
    "DODFX": "Foreign Large Blend",
    "DODBX": "Moderate Allocation",
    "TRBCX": "Large Growth",
    "PRGFX": "Large Growth",
    "PRFDX": "Large Value",
    "SWTSX": "Large Blend",
    "SWPPX": "Large Blend",
    "SWANX": "Large Blend",
    "NOSIX": "Large Blend",
    "MDDVX": "Large Value",
    "JDCAX": "Large Growth",
    "SPY": "Large Blend",
    "IVV": "Large Blend",
    "SPYM": "Large Blend",
    "SPLG": "Large Blend",
    "AGG": "Intermediate Core Bond",
    "IWB": "Large Blend",
    "IWM": "Small Blend",
    "IWF": "Large Growth",
    "IWD": "Large Value",
    "IJH": "Mid-Cap Blend",
    "IJR": "Small Blend",
    "EFA": "Foreign Large Blend",
    "IEFA": "Foreign Large Blend",
    "EEM": "Diversified Emerging Markets",
    "IEMG": "Diversified Emerging Markets",
    "LQD": "Corporate Bond",
    "HYG": "High Yield Bond",
    "TIP": "Inflation-Protected Bond",
    "SHY": "Short Government",
    "IEF": "Intermediate Government",
    "TLT": "Long Government",
    "VNQ": "Real Estate",
    "QQQ": "Large Growth",
    "JEPI": "Derivative Income",
    "SCHD": "Large Value",
    "SCHX": "Large Blend",
    "SCHB": "Large Blend",
    "SCHF": "Foreign Large Blend",
    "SCHG": "Large Growth",
    "ARKK": "Mid-Cap Growth",
    "GLD": "Commodities Focused",
    "BNDX": "World Bond-USD Hedged",
    "ACWX": "Foreign Large Blend",
    "ITOT": "Large Blend",
    "SGENX": "Global Allocation",
    "SGOVX": "Foreign Large Blend",
    "FEVAX": "Large Blend",
    "FEFAX": "Large Blend",
    "GDX": "Equity Precious Metals",
    "SMH": "Technology",
    "HACAX": "Large Growth",
    "HAVLX": "Large Value",
    "VETAX": "Mid-Cap Value",
    "YACKX": "Large Blend",
    "NLCAX": "Large Growth",
    "OAKMX": "Large Blend",
    "OAKLX": "Large Value",
    "OAKBX": "Moderate Allocation",
    "OAKEX": "Foreign Large Blend",
    "TBGVX": "Foreign Large Value",
    "GABGX": "Large Growth",
    "RYTRX": "Small Blend",
    "BAFFX": "Large Blend",
    "BGFIX": "Large Growth",
    "AQGIX": "World Large-Stock Blend",
    "CIVIX": "Foreign Large Value",
    "HLMNX": "Foreign Large Growth",
    "MAPTX": "Diversified Pacific/Asia",
    "JENSX": "Large Growth",
    "AADEX": "Large Value",
    "LZIEX": "Foreign Large Blend",
    "GQEIX": "Large Blend",
    "LSVEX": "Large Value",
    "HFCSX": "Mid-Cap Growth",
    "WWNPX": "Mid-Cap Growth",
    "MERDX": "Mid-Cap Growth",
    "MFOCX": "Large Growth",
    "SEEGX": "Large Growth",
    "JLGMX": "Large Growth",
    "TWCGX": "Large Growth",
    "MIGHX": "Large Growth",
    "MITTX": "Large Blend",
    "MEIAX": "Large Value",
    "DGAGX": "Large Growth",
    "PEOPX": "Large Blend",
    "DISVX": "Foreign Small/Mid Value",
    "ALLW": "Tactical Allocation",
    "GTR": "Options Trading",
    "WTPI": "Derivative Income",
    "FVD": "Large Value",
    "MOAT": "Large Blend",
    "INIVX": "Equity Precious Metals",
    "MWMIX": "Large Blend",
    "NWHOX": "Technology",
}

_CURATED_IDENTIFIERS: dict[str, str] = {
    "amcap-fund": "Large Growth",
    "the-growth-fund-of-america": "Large Growth",
    "american-balanced-fund": "Moderate Allocation",
    "the-investment-company-of-america": "Large Blend",
    "fundamental-investors": "Large Blend",
    "washington-mutual-investors-fund": "Large Value",
    "american-mutual-fund": "Large Value",
    "the-new-economy-fund": "Large Growth",
    "new-perspective-fund": "World Large-Stock Growth",
    "eupac-fund": "Foreign Large Growth",
    "smallcap-world-fund": "Global Small/Mid Stock",
    "new-world-fund": "Diversified Emerging Markets",
    "international-growth-and-income-fund": "Foreign Large Blend",
    "capital-world-growth-and-income-fund": "World Large-Stock Blend",
    "capital-income-builder": "Global Allocation",
    "the-income-fund-of-america": "Moderate Allocation",
    "the-bond-fund-of-america": "Intermediate Core Bond",
    "intermediate-bond-fund-of-america": "Intermediate Core Bond",
    "short-term-bond-fund-of-america": "Short-Term Bond",
    "american-high-income-trust": "High Yield Bond",
    "american-high-income-municipal-bond-fund": "High Yield Muni",
    "limited-term-tax-exempt-bond-fund-of-america": "Muni National Interm",
    "american-funds-short-term-tax-exempt-bond-fund": "Muni National Short",
    "capital-world-bond-fund": "World Bond",
    "u-s-government-securities-fund": "Intermediate Government",
    "american-funds-inflation-linked-bond-fund": "Inflation-Protected Bond",
    "american-funds-corporate-bond-fund": "Corporate Bond",
    "american-funds-core-plus-bond-fund": "Intermediate Core-Plus Bond",
    "american-funds-mortgage-fund": "Intermediate Government",
    "american-funds-multi-sector-income-fund": "Multisector Bond",
    "american-funds-strategic-bond-fund": "Nontraditional Bond",
    "american-funds-emerging-markets-bond-fund": "Emerging Markets Bond",
    "american-funds-developing-world-growth-and-income-fund": "Diversified Emerging Markets",
    "emerging-markets-equities-fund": "Diversified Emerging Markets",
    "american-funds-global-balanced-fund": "Global Allocation",
    "american-funds-global-insight-fund": "World Large-Stock Blend",
    "american-funds-international-vantage-fund": "Foreign Large Growth",
    "american-funds-u-s-government-money-market-fund": "Money Market-Taxable",
    "american-funds-conservative-growth-and-income-portfolio": "Moderately Conservative Allocation",
    "american-funds-growth-and-income-portfolio": "Moderate Allocation",
    "american-funds-growth-portfolio": "Aggressive Allocation",
    "american-funds-moderate-growth-and-income-portfolio": "Moderate Allocation",
    "american-funds-preservation-portfolio": "Conservative Allocation",
    "american-funds-global-growth-portfolio": "World Large-Stock Growth",
    "american-funds-tax-aware-conservative-growth-and-income-portfolio": "Conservative Allocation",
    "american-funds-u-s-small-and-mid-cap-equity-fund": "Mid-Cap Blend",
    "american-funds-retirement-income-portfolio-conservative": "Retirement Income",
    "american-funds-retirement-income-portfolio-moderate": "Retirement Income",
    "american-funds-retirement-income-portfolio-enhanced": "Retirement Income",
}

_TARGET_YEAR_RE = re.compile(
    r"\b(?:target(?:[-\s]?date)?|target(?:[-\s]?retirement)|retirement(?:[-\s]?income)?)"
    r".*?\b(20[0-7]\d)\b|\b(20[0-7]\d)\b.*?\b(?:target(?:[-\s]?(?:date|retirement))?)\b",
    re.I,
)
_YEAR_ONLY_RE = re.compile(r"\b(20(?:0[0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9]|6[0-9]|7[0-9]))\b")
# Issuer vintage series that ARE target-date (Morningstar Target-Date *), not
# maturity-year bonds. Year in the name is the glide-path vintage.
_ISSUER_TARGET_SERIES = (
    "lifepath",
    "life path",
    "one choice",
    "freedom",
    "lifetime",
    "smartretirement",
    "smart retirement",
    "target date",
    "target-date",
    "target retirement",
    "targetdate",
)
_TROWE_RETIREMENT_YEAR_RE = re.compile(
    r"\bretirement(?:\s+blend|\s+i)?\s+(20[0-7]\d)\b",
    re.I,
)
# Fidelity Asset Manager publishes the equity mix in the name (same bands as
# Yahoo Allocation--X% to Y% Equity). Not a 60/40 guess.
_ASSET_MANAGER_PCT_RE = re.compile(r"\basset\s+manager\s+(\d+)\s*%", re.I)


def _norm_key(value: str) -> str:
    return _SPACE_RE.sub(" ", value.strip().lower()).strip()


def canonical_category(value: str | None) -> str | None:
    """Map a filter / source string onto a canonical category, or None."""
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None
    if raw in CANONICAL_CATEGORIES:
        return raw
    key = _norm_key(raw)
    if key in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[key]
    for name in CANONICAL_CATEGORIES:
        if _norm_key(name) == key:
            return name
    return None


def _catalog_path() -> Path:
    return Path(__file__).resolve().parent / "fund_categories.json"


@lru_cache(maxsize=1)
def _load_catalog() -> tuple[dict[str, str], dict[str, str]]:
    path = _catalog_path()
    if not path.is_file():
        return {}, {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, {}
    tickers: dict[str, str] = {}
    identifiers: dict[str, str] = {}
    for key, value in (payload.get("tickers") or {}).items():
        category = canonical_category(str(value))
        if category and isinstance(key, str) and key.strip():
            tickers[key.strip().upper()] = category
    for key, value in (payload.get("identifiers") or {}).items():
        category = canonical_category(str(value))
        if category and isinstance(key, str) and key.strip():
            identifiers[key.strip().lower()] = category
    return tickers, identifiers


def reload_catalog() -> None:
    """Test helper: drop the on-disk catalog cache."""
    _load_catalog.cache_clear()


def _year_to_target_date(year: int) -> str | None:
    if year <= 2010:
        return "Target-Date 2000-2010"
    if year == 2015:
        return "Target-Date 2015"
    if year == 2020:
        return "Target-Date 2020"
    if year == 2025:
        return "Target-Date 2025"
    if year == 2030:
        return "Target-Date 2030"
    if year == 2035:
        return "Target-Date 2035"
    if year == 2040:
        return "Target-Date 2040"
    if year == 2045:
        return "Target-Date 2045"
    if year == 2050:
        return "Target-Date 2050"
    if year == 2055:
        return "Target-Date 2055"
    if year == 2060:
        return "Target-Date 2060"
    if year == 2065:
        return "Target-Date 2065"
    if year >= 2070:
        return "Target-Date 2070+"
    return None


def _target_date_category(name: str) -> str | None:
    blob = name.lower()
    # Maturity-year bonds (e.g. Zero Coupon 2025) are not target-date.
    if "zero coupon" in blob or "zero-coupon" in blob:
        return None
    if "target allocation" in blob or "target payout" in blob:
        return None
    series = any(token in blob for token in _ISSUER_TARGET_SERIES)
    lifepath = "lifepath" in blob or "life path" in blob
    targetish = series or (
        "target" in blob and _YEAR_ONLY_RE.search(name) and "allocation" not in blob
    )
    trowe = _TROWE_RETIREMENT_YEAR_RE.search(name)
    if not targetish and not lifepath and not trowe:
        if re.search(r"retirement income", blob) and not _YEAR_ONLY_RE.search(name):
            return "Retirement Income"
        return None
    match = _TARGET_YEAR_RE.search(name)
    year_s = None
    if match:
        year_s = match.group(1) or match.group(2)
    if year_s is None and trowe:
        year_s = trowe.group(1)
    if year_s is None and (targetish or lifepath):
        years = _YEAR_ONLY_RE.findall(name)
        if len(years) == 1:
            year_s = years[0]
    if year_s is None:
        if (lifepath or series) and re.search(
            r"\b(?:in retirement|retirement)\b", blob
        ):
            return "Retirement Income"
        if re.search(r"retirement income", blob) and not _YEAR_ONLY_RE.search(name):
            return "Retirement Income"
        return None
    return _year_to_target_date(int(year_s))


def _has_any(blob: str, *needles: str) -> bool:
    return any(n in blob for n in needles)


def _name_category(fund_name: str | None) -> str | None:
    """High-confidence name → Morningstar category. None when ambiguous."""
    if not fund_name:
        return None
    name = fund_name.strip()
    if not name:
        return None
    blob = _NON_ALNUM_RE.sub(" ", name.lower())
    blob = re.sub(r"\s+", " ", blob).strip()
    if not blob:
        return None

    target = _target_date_category(name)
    if target:
        return target

    is_bond = _has_any(
        blob,
        "bond",
        "fixed income",
        "fixed-income",
        "treasury",
        "treasuries",
        "aggregate",
        "muni",
        "municipal",
        "tax exempt",
        "tax-exempt",
        "tips",
        "inflation linked",
        "inflation protected",
        "inflation protection",
        "income trust",
        "credit",
        "loan",
        "note",
        "debt",
        "high yield",
        "high income",
        "ginnie mae",
        "gnma",
        "mortgage",
    )
    is_money = _has_any(
        blob,
        "money market",
        "government money",
        "treasury money",
        "money fund",
        "prime money",
        "tax free money",
        "tax-free money",
    ) or (_has_any(blob, "cash reserve") and _has_any(blob, "government", "treasury"))
    is_reit = _has_any(blob, "real estate", "reit", "realty")
    is_alloc = _has_any(
        blob,
        "balanced",
        "allocation",
        "lifestyle",
        "target risk",
        "target-risk",
        "multi asset",
        "multi-asset",
        "asset allocation",
    )

    if is_money:
        if _has_any(blob, "muni", "municipal", "tax exempt", "tax-exempt", "tax free", "tax-free"):
            return "Money Market-Tax-Free"
        return "Money Market-Taxable"

    if _has_any(blob, "market neutral"):
        return "Market Neutral"

    asset_mgr = _ASSET_MANAGER_PCT_RE.search(name)
    if asset_mgr:
        pct = int(asset_mgr.group(1))
        if pct <= 30:
            return "Conservative Allocation"
        if pct < 50:
            return "Moderately Conservative Allocation"
        if pct < 70:
            return "Moderate Allocation"
        if pct < 85:
            return "Moderately Aggressive Allocation"
        return "Aggressive Allocation"

    # Issuer-published target-risk / balanced series (not a generic "growth fund").
    if _has_any(blob, "lifestrategy", "life strategy"):
        if "conservative growth" in blob:
            return "Moderately Conservative Allocation"
        if "moderate growth" in blob:
            return "Moderate Allocation"
        if "income" in blob:
            return "Conservative Allocation"
        if "growth" in blob:
            return "Aggressive Allocation"
    if "markettrack" in blob or "market track" in blob:
        if _has_any(blob, "all equity", "growth"):
            return "Aggressive Allocation"
        if "balanced" in blob or "conservative" in blob:
            return "Moderate Allocation" if "balanced" in blob else "Conservative Allocation"
    if "global wellesley" in blob:
        return "Global Conservative Allocation"
    if "global wellington" in blob:
        return "Global Allocation"
    if re.search(r"\bvanguard star\b", blob) or blob.endswith(" star fund"):
        return "Moderate Allocation"
    if "massachusetts investors growth stock" in blob:
        return "Large Growth"
    if "blended research core equity" in blob or re.search(r"\bmfs core equity\b", blob):
        return "Large Blend"
    if re.search(r"\bmfs global equity\b", blob):
        return "World Large-Stock Blend"
    if re.search(r"\bmfs growth allocation\b", blob):
        return "Aggressive Allocation"
    if re.search(r"\bmfs global total return\b", blob):
        return "Global Allocation"

    # American Century One Choice target-risk (not vintage) portfolios.
    if "one choice" in blob and "portfolio" in blob and not _YEAR_ONLY_RE.search(name):
        if "in retirement" in blob:
            return "Retirement Income"
        if "very conservative" in blob:
            return "Conservative Allocation"
        if "conservative" in blob and "aggressive" not in blob:
            return "Conservative Allocation"
        if "aggressive" in blob:
            return "Aggressive Allocation"
        if "moderate" in blob:
            return "Moderate Allocation"

    if _has_any(blob, "preferred"):
        return "Preferred Stock"
    if _has_any(blob, "convertible"):
        return "Convertibles"
    if _has_any(blob, "bank loan", "senior loan", "floating rate loan"):
        return "Bank Loan"

    if is_reit:
        if _has_any(blob, "global", "international", "world", "ex us", "ex-us"):
            return "Global Real Estate"
        return "Real Estate"

    if _has_any(blob, "semiconductor", "technology", "tech select", "nasdaq 100"):
        if not is_bond:
            if "nasdaq 100" in blob or "nasdaq composite" in blob:
                return "Large Growth"
            if "semiconductor" in blob or "technology" in blob or "tech select" in blob:
                return "Technology"
    if _has_any(blob, "health care", "healthcare", "health sciences", "biotech"):
        if not is_bond:
            return "Health"
    if _has_any(blob, "utility", "utilities"):
        if not is_bond:
            return "Utilities"
    if _has_any(blob, "precious metal", "gold miners", "silver miners"):
        if not is_bond:
            return "Equity Precious Metals"
    if _has_any(blob, "natural resource", "energy", "oil") and not is_bond:
        if _has_any(blob, "mlp", "limited partnership"):
            return None
        if "energy" in blob or "natural resource" in blob:
            return "Natural Resources" if "natural resource" in blob else "Equity Energy"
    if _has_any(blob, "financial service", "financials", "bank") and not is_bond and "loan" not in blob:
        return "Financial"
    if _has_any(blob, "industrial") and not is_bond:
        return "Industrials"
    if _has_any(blob, "communication", "telecom") and not is_bond:
        return "Communications"
    if _has_any(blob, "infrastructure") and not is_bond:
        return "Infrastructure"
    if _has_any(blob, "consumer staples", "consumer defensive") and not is_bond:
        return "Consumer Defensive"
    if _has_any(blob, "consumer discretionary", "consumer cyclical") and not is_bond:
        return "Consumer Cyclical"
    if _has_any(blob, "buffer", "defined outcome", "defined-outcome", "laddered"):
        return "Defined Outcome"
    if _has_any(blob, "blockchain", "digital asset", "bitcoin", "crypto"):
        if not is_bond:
            return "Equity Digital Assets"
    if _has_any(
        blob,
        "managed futures",
        "systematica trend",
        "trend enhanced",
        "trend total return",
    ):
        return "Systematic Trend"
    if _has_any(blob, "ultra short income", "ultrashort income", "ultra-short income"):
        return "Ultrashort Bond"

    if is_bond:
        if _has_any(blob, "high yield", "high-yield", "high income municipal", "high income muni"):
            if _has_any(blob, "muni", "municipal", "tax exempt"):
                return "High Yield Muni"
            if _has_any(blob, "emerging"):
                return "Emerging Markets Bond"
            return "High Yield Bond"
        if _has_any(blob, "emerging") and _has_any(blob, "bond", "debt", "local currency"):
            return "Emerging Markets Bond"
        if _has_any(
            blob,
            "tips",
            "inflation linked",
            "inflation protected",
            "inflation protection",
            "inflation-linked",
            "inflation-protected",
        ):
            return "Inflation-Protected Bond"
        if _has_any(blob, "low duration", "limited duration"):
            return "Short-Term Bond"
        if _has_any(blob, "california") and _has_any(blob, "muni", "municipal", "tax exempt"):
            return "Muni California Long" if _has_any(blob, "long") else "Muni California Intermediate"
        if _has_any(blob, "new york") and _has_any(blob, "muni", "municipal", "tax exempt"):
            return "Muni New York Long" if _has_any(blob, "long") else "Muni New York Intermediate"
        if _has_any(blob, "muni", "municipal", "tax exempt", "tax-exempt"):
            if _has_any(blob, "high yield", "high-yield"):
                return "High Yield Muni"
            if _has_any(blob, "short", "limited term", "limited-term", "ultra"):
                return "Muni National Short"
            if _has_any(blob, "long"):
                return "Muni National Long"
            return "Muni National Interm"
        if _has_any(blob, "multi sector", "multisector", "multi-sector", "strategic income"):
            return "Multisector Bond"
        if _has_any(blob, "core plus", "core-plus"):
            return "Intermediate Core-Plus Bond"
        if _has_any(blob, "corporate"):
            return "Corporate Bond"
        if _has_any(blob, "ultra short", "ultrashort", "ultra-short"):
            return "Ultrashort Bond"
        if _has_any(blob, "world bond", "global bond", "international bond"):
            return "World Bond"
        gov = _has_any(blob, "government", "treasury", "gnma", "ginnie mae", "mortgage")
        if _has_any(blob, "short"):
            return "Short Government" if gov and "mortgage" not in blob else "Short-Term Bond"
        if _has_any(blob, "long"):
            return "Long Government" if gov and "mortgage" not in blob else "Long-Term Bond"
        if gov and not _has_any(blob, "aggregate", "total bond", "core"):
            if "mortgage" in blob or "gnma" in blob or "ginnie mae" in blob:
                return "Intermediate Government"
            return "Intermediate Government"
        if _has_any(
            blob,
            "aggregate",
            "total bond",
            "core bond",
            "intermediate",
            "bond index",
            "bond market",
        ):
            return "Intermediate Core Bond"
        # "Something Bond Fund" without tenor/style is too easy to mis-bin.
        return None

    if is_alloc:
        if _has_any(blob, "global", "world", "international"):
            if _has_any(blob, "conservative"):
                return "Global Conservative Allocation"
            if _has_any(blob, "aggressive"):
                return "Global Aggressive Allocation"
            return "Global Allocation"
        if _has_any(blob, "conservative"):
            return "Conservative Allocation"
        if _has_any(blob, "aggressive"):
            return "Aggressive Allocation"
        if _has_any(blob, "moderately conservative"):
            return "Moderately Conservative Allocation"
        if _has_any(blob, "tactical"):
            return "Tactical Allocation"
        # Balanced / allocation / lifestyle without a risk word → Moderate.
        if _has_any(blob, "balanced", "moderate", "growth and income portfolio"):
            return "Moderate Allocation"
        return None

    china = _has_any(blob, "china", "csi 300", "ftse china")
    india = _has_any(blob, "india")
    japan = _has_any(blob, "japan", "nikkei", "topix")
    europe = _has_any(blob, "europe", "eurozone", "euro stoxx", "ftse 100", "stoxx europe")
    latam = _has_any(blob, "latin america", "latam", "brazil")
    pacific = _has_any(blob, "pacific", "asia ex", "asia-pacific", "asia pacific")
    emerging = _has_any(blob, "emerging market", "em equity", "em stock", "frontier")
    foreign = _has_any(
        blob,
        "international",
        "foreign",
        "eafe",
        "ex us",
        "ex-us",
        "exusa",
        "developed market",
        "overseas",
        "acwi ex",
    )
    world = _has_any(blob, "global", "world", "acwi") and not foreign

    small_mid_foreign = _has_any(blob, "small", "mid", "smid") and (foreign or world)

    style = None
    if _has_any(blob, "growth") and not _has_any(blob, "growth and income", "growth & income"):
        style = "Growth"
    elif _has_any(blob, "value"):
        style = "Value"
    elif _has_any(
        blob,
        "blend",
        "s p 500",
        "sp 500",
        "500 index",
        "total stock",
        "total market",
        "russell 1000",
        "russell 3000",
        "wilshire 5000",
        "crsp us total",
        "equity index",
        "stock index",
        "core equity",
    ):
        style = "Blend"

    if china and not is_bond:
        return "China Region"
    if india and not is_bond:
        return "India Equity"
    if japan and not is_bond:
        return "Japan Stock"
    if europe and not foreign and not world and not is_bond:
        return "Europe Stock"
    if latam and not is_bond:
        return "Latin America Stock"
    if pacific and not japan and not is_bond:
        return "Pacific/Asia ex-Japan Stk" if _has_any(blob, "ex japan", "ex-japan") else "Diversified Pacific/Asia"
    if emerging and not is_bond:
        return "Diversified Emerging Markets"

    if foreign and not is_bond:
        if small_mid_foreign:
            if style == "Growth":
                return "Foreign Small/Mid Growth"
            if style == "Value":
                return "Foreign Small/Mid Value"
            if style == "Blend" or _has_any(blob, "index", "small cap", "small-cap", "mid cap"):
                return "Foreign Small/Mid Blend"
            return None
        if style == "Growth":
            return "Foreign Large Growth"
        if style == "Value":
            return "Foreign Large Value"
        if style == "Blend" or _has_any(blob, "index", "total international", "eafe", "developed"):
            return "Foreign Large Blend"
        return None

    if world and not is_bond:
        if _has_any(blob, "small", "mid"):
            return "World Small/Mid Stock"
        if style == "Growth":
            return "World Large-Stock Growth"
        if style == "Value":
            return "World Large-Stock Value"
        if style == "Blend" or _has_any(blob, "index", "acwi"):
            return "World Large-Stock Blend"
        return None

    size = None
    if _has_any(blob, "micro"):
        size = "Small"
    elif _has_any(blob, "small") and not _has_any(blob, "small and mid", "small & mid", "smid"):
        size = "Small"
    elif _has_any(blob, "mid cap", "midcap", "s p mid", "russell mid"):
        size = "Mid"
    elif _has_any(blob, "large", "mega", "s p 500", "sp 500", "500 index", "nasdaq 100", "russell 1000"):
        size = "Large"
    elif _has_any(blob, "total stock", "total market", "russell 3000", "wilshire 5000", "crsp us total"):
        size = "Large"
        style = style or "Blend"
    elif _has_any(blob, "s p 400", "midcap 400"):
        size = "Mid"
        style = style or "Blend"
    elif _has_any(blob, "s p 600", "smallcap 600", "russell 2000"):
        size = "Small"
        style = style or "Blend"

    if size and not style and _has_any(blob, "index"):
        style = "Blend"
    if size and style:
        if size == "Large":
            return f"Large {style}"
        if size == "Mid":
            return f"Mid-Cap {style}"
        return f"Small {style}"

    # Index products with no size word still map when the benchmark is explicit.
    if _has_any(blob, "s p 500", "500 index") and not _has_any(blob, "equal weight"):
        return "Large Blend" if style != "Growth" and style != "Value" else f"Large {style}"
    if _has_any(blob, "russell 2000"):
        return "Small Growth" if style == "Growth" else "Small Value" if style == "Value" else "Small Blend"
    if _has_any(blob, "russell 1000"):
        return "Large Growth" if style == "Growth" else "Large Value" if style == "Value" else "Large Blend"

    return None


def resolve_category(
    *,
    ticker: str | None = None,
    fund_identifier: str | None = None,
    fund_name: str | None = None,
    fund_family: str | None = None,
) -> str | None:
    """Return a Morningstar-style category or None. Never invents.

    Lookup order: curated ticker / identifier, on-disk catalog, conservative
    name rules. ``fund_family`` is accepted for call-site symmetry and unused
    beyond that — family alone is not a category.
    """
    _ = fund_family
    catalog_tickers, catalog_idents = _load_catalog()

    if ticker:
        key = ticker.strip().upper()
        if key in _CURATED_TICKERS:
            return _CURATED_TICKERS[key]
        if key in catalog_tickers:
            return catalog_tickers[key]

    if fund_identifier:
        ident = fund_identifier.strip().lower()
        if ident in _CURATED_IDENTIFIERS:
            return _CURATED_IDENTIFIERS[ident]
        if ident in catalog_idents:
            return catalog_idents[ident]
        ident_upper = fund_identifier.strip().upper()
        if ident_upper in _CURATED_TICKERS:
            return _CURATED_TICKERS[ident_upper]
        if ident_upper in catalog_tickers:
            return catalog_tickers[ident_upper]

    return _name_category(fund_name)


def category_for_row(row: Any) -> str | None:
    """Resolve category from a distribution / summary object."""
    return resolve_category(
        ticker=getattr(row, "ticker", None),
        fund_identifier=getattr(row, "fund_identifier", None),
        fund_name=getattr(row, "fund_name", None),
        fund_family=getattr(row, "fund_family", None),
    )


def coverage_stats(
    funds: list[tuple[str | None, str | None, str | None, str | None]],
) -> dict[str, Any]:
    """``funds`` is (ticker, fund_identifier, fund_name, fund_family)."""
    categorized = 0
    by_category: dict[str, int] = {}
    for ticker, ident, name, family in funds:
        category = resolve_category(
            ticker=ticker, fund_identifier=ident, fund_name=name, fund_family=family
        )
        if category:
            categorized += 1
            by_category[category] = by_category.get(category, 0) + 1
    total = len(funds)
    return {
        "total_funds": total,
        "categorized": categorized,
        "uncategorized": total - categorized,
        "coverage_pct": round(100.0 * categorized / total, 1) if total else 0.0,
        "by_category": dict(sorted(by_category.items(), key=lambda kv: (-kv[1], kv[0]))),
    }
