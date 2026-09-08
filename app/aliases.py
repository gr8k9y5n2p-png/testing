"""Shared Class A / Investor A ticker ↔ stored fund_identifier aliases.

Official books for American Funds, BlackRock open-end, J.P. Morgan Section 19a,
and other name-keyed tax PDFs/HTML (Invesco, MFS, John Hancock, BNY, Hartford,
AllianceBernstein, Thrivent, Calamos, Wasatch, Voya) have a fund-name column
and no ticker/CUSIP. Rows store ``ticker=null`` and a name slug
(``american-balanced-fund``, ``invesco-american-franchise-fund``).

List, search, and illustrate resolve Class A / Investor A tickers (ABALX,
MDDVX, OIEIX, VAFAX, MRGAX, …) through this map. Attaching a ticker must
**not** change the name-slug identity, or re-ingest would fork upsert keys.

SEEGX / JLGMX were already ticker-keyed in the JPM fixture and keep those
identifiers. iShares ETF HTML already has tickers — this map does not
override parsed values.

CUSIPs are included only when confirmed on an official issuer or SEC source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.aliases_ab import AB_FUND_ROWS
from app.aliases_blackrock import BLACKROCK_FUND_ROWS
from app.aliases_bny import BNY_FUND_ROWS
from app.aliases_calamos import CALAMOS_FUND_ROWS
from app.aliases_hartford import HARTFORD_FUND_ROWS
from app.aliases_invesco import INVESCO_FUND_ROWS
from app.aliases_john_hancock import JOHNHANCOCK_FUND_ROWS
from app.aliases_jpmorgan import JPMORGAN_FUND_ROWS
from app.aliases_mfs import MFS_FUND_ROWS
from app.aliases_thrivent import THRIVENT_FUND_ROWS
from app.aliases_voya import VOYA_FUND_ROWS
from app.aliases_wasatch import WASATCH_FUND_ROWS

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slugify(name: str) -> str:
    slug = _SLUG_RE.sub("-", name.lower()).strip("-")
    return slug or "unknown-fund"


FAMILY_AMERICAN_FUNDS = "american_funds"
FAMILY_BLACKROCK = "blackrock"
FAMILY_JPMORGAN = "jpmorgan"
FAMILY_INVESCO = "invesco"
FAMILY_MFS = "mfs"
FAMILY_JOHNHANCOCK = "john_hancock"
FAMILY_BNY = "bny_mellon"
FAMILY_HARTFORD = "hartford"
FAMILY_AB = "ab"
FAMILY_THRIVENT = "thrivent"
FAMILY_CALAMOS = "calamos"
FAMILY_WASATCH = "wasatch"
FAMILY_VOYA = "voya"


def is_american_funds_family(fund_family: str | None) -> bool:
    return family_key(fund_family) == FAMILY_AMERICAN_FUNDS


def is_blackrock_family(fund_family: str | None) -> bool:
    return family_key(fund_family) == FAMILY_BLACKROCK


def is_jpmorgan_family(fund_family: str | None) -> bool:
    return family_key(fund_family) == FAMILY_JPMORGAN


def family_key(fund_family: str | None) -> str | None:
    blob = (fund_family or "").lower()
    if "american funds" in blob or "capital group" in blob:
        return FAMILY_AMERICAN_FUNDS
    if "blackrock" in blob or "ishares" in blob:
        return FAMILY_BLACKROCK
    if "j.p. morgan" in blob or "jpmorgan" in blob or "jp morgan" in blob:
        return FAMILY_JPMORGAN
    if "invesco" in blob:
        return FAMILY_INVESCO
    if "mfs" in blob:
        return FAMILY_MFS
    if "john hancock" in blob or "manulife" in blob:
        return FAMILY_JOHNHANCOCK
    if "bny" in blob or "dreyfus" in blob:
        return FAMILY_BNY
    if "hartford" in blob:
        return FAMILY_HARTFORD
    if "alliancebernstein" in blob or "alliance bernstein" in blob:
        return FAMILY_AB
    if "thrivent" in blob:
        return FAMILY_THRIVENT
    if "calamos" in blob:
        return FAMILY_CALAMOS
    if "wasatch" in blob:
        return FAMILY_WASATCH
    if "voya" in blob:
        return FAMILY_VOYA
    return None


@dataclass(frozen=True, slots=True)
class ClassAIdentity:
    ticker: str
    fund_identifier: str
    names: tuple[str, ...]
    cusip: str | None = None
    nicknames: tuple[str, ...] = ()


def _ca(
    ticker: str,
    fund_identifier: str,
    *names: str,
    cusip: str | None = None,
    nicknames: tuple[str, ...] = (),
) -> ClassAIdentity:
    return ClassAIdentity(
        ticker=ticker.upper(),
        fund_identifier=fund_identifier,
        names=names,
        cusip=cusip,
        nicknames=tuple(n.upper() for n in nicknames),
    )


# Official American Funds / Capital Group Class A (and listed Class M) identities.
CLASS_A_FUNDS: tuple[ClassAIdentity, ...] = (
    _ca("AMCPX", "amcap-fund", "AMCAP Fund", cusip="023375108", nicknames=("AMCAP",)),
    _ca(
        "ABALX",
        "american-balanced-fund",
        "American Balanced Fund",
        cusip="024071102",
        nicknames=("AMBAL",),
    ),
    _ca(
        "AAATX",
        "american-funds-2010-target-date-retirement-income-fund",
        "American Funds 2010 Target Date Retirement Income Fund",
        "American Funds 2010 Target Date Retirement Fund",
    ),
    _ca(
        "AABTX",
        "american-funds-2015-target-date-retirement-income-fund",
        "American Funds 2015 Target Date Retirement Income Fund",
        "American Funds 2015 Target Date Retirement Fund",
    ),
    _ca(
        "AACTX",
        "american-funds-2020-target-date-retirement-income-fund",
        "American Funds 2020 Target Date Retirement Income Fund",
        "American Funds 2020 Target Date Retirement Fund",
    ),
    _ca(
        "AADTX",
        "american-funds-2025-target-date-retirement-income-fund",
        "American Funds 2025 Target Date Retirement Income Fund",
        "American Funds 2025 Target Date Retirement Fund",
    ),
    _ca(
        "AAETX",
        "american-funds-2030-target-date-retirement-fund",
        "American Funds 2030 Target Date Retirement Fund",
    ),
    _ca(
        "AAFTX",
        "american-funds-2035-target-date-retirement-fund",
        "American Funds 2035 Target Date Retirement Fund",
    ),
    _ca(
        "AAGTX",
        "american-funds-2040-target-date-retirement-fund",
        "American Funds 2040 Target Date Retirement Fund",
    ),
    _ca(
        "AAHTX",
        "american-funds-2045-target-date-retirement-fund",
        "American Funds 2045 Target Date Retirement Fund",
    ),
    _ca(
        "AALTX",
        "american-funds-2050-target-date-retirement-fund",
        "American Funds 2050 Target Date Retirement Fund",
    ),
    _ca(
        "AAMTX",
        "american-funds-2055-target-date-retirement-fund",
        "American Funds 2055 Target Date Retirement Fund",
    ),
    _ca(
        "AANTX",
        "american-funds-2060-target-date-retirement-fund",
        "American Funds 2060 Target Date Retirement Fund",
    ),
    _ca(
        "AAOTX",
        "american-funds-2065-target-date-retirement-fund",
        "American Funds 2065 Target Date Retirement Fund",
    ),
    _ca(
        "AAFJX",
        "american-funds-2070-target-date-retirement-fund",
        "American Funds 2070 Target Date Retirement Fund",
    ),
    _ca(
        "INPAX",
        "american-funds-conservative-growth-and-income-portfolio",
        "American Funds Conservative Growth and Income Portfolio",
    ),
    _ca(
        "AFCPX",
        "american-funds-core-plus-bond-fund",
        "American Funds Core Plus Bond Fund",
    ),
    _ca(
        "BFCAX",
        "american-funds-corporate-bond-fund",
        "American Funds Corporate Bond Fund",
    ),
    _ca(
        "DWGAX",
        "american-funds-developing-world-growth-and-income-fund",
        "American Funds Developing World Growth and Income Fund",
    ),
    _ca(
        "EBNAX",
        "american-funds-emerging-markets-bond-fund",
        "American Funds Emerging Markets Bond Fund",
    ),
    _ca(
        "GBLAX",
        "american-funds-global-balanced-fund",
        "American Funds Global Balanced Fund",
    ),
    _ca(
        "PGGAX",
        "american-funds-global-growth-portfolio",
        "American Funds Global Growth Portfolio",
    ),
    _ca(
        "AGVFX",
        "american-funds-global-insight-fund",
        "American Funds Global Insight Fund",
    ),
    _ca(
        "GAIOX",
        "american-funds-growth-and-income-portfolio",
        "American Funds Growth and Income Portfolio",
    ),
    _ca(
        "GWPAX",
        "american-funds-growth-portfolio",
        "American Funds Growth Portfolio",
        cusip="02630R781",
    ),
    _ca(
        "BFIAX",
        "american-funds-inflation-linked-bond-fund",
        "American Funds Inflation Linked Bond Fund",
    ),
    _ca(
        "AIVBX",
        "american-funds-international-vantage-fund",
        "American Funds International Vantage Fund",
    ),
    _ca(
        "BLPAX",
        "american-funds-moderate-growth-and-income-portfolio",
        "American Funds Moderate Growth and Income Portfolio",
    ),
    _ca(
        "MFAAX",
        "american-funds-mortgage-fund",
        "American Funds Mortgage Fund",
    ),
    _ca(
        "MIAQX",
        "american-funds-multi-sector-income-fund",
        "American Funds Multi-Sector Income Fund",
    ),
    _ca(
        "PPVAX",
        "american-funds-preservation-portfolio",
        "American Funds Preservation Portfolio",
    ),
    _ca(
        "NAARX",
        "american-funds-retirement-income-portfolio-conservative",
        "American Funds Retirement Income Portfolio — Conservative",
        "American Funds Retirement Income Portfolio - Conservative",
        "American Funds Retirement Income Portfolio Conservative",
    ),
    _ca(
        "NDARX",
        "american-funds-retirement-income-portfolio-enhanced",
        "American Funds Retirement Income Portfolio — Enhanced",
        "American Funds Retirement Income Portfolio - Enhanced",
        "American Funds Retirement Income Portfolio Enhanced",
    ),
    _ca(
        "NBARX",
        "american-funds-retirement-income-portfolio-moderate",
        "American Funds Retirement Income Portfolio — Moderate",
        "American Funds Retirement Income Portfolio - Moderate",
        "American Funds Retirement Income Portfolio Moderate",
    ),
    _ca(
        "ASTEX",
        "american-funds-short-term-tax-exempt-bond-fund",
        "American Funds Short-Term Tax-Exempt Bond Fund",
        cusip="02630W103",
    ),
    _ca(
        "ANBAX",
        "american-funds-strategic-bond-fund",
        "American Funds Strategic Bond Fund",
    ),
    _ca(
        "TAIAX",
        "american-funds-tax-aware-conservative-growth-and-income-portfolio",
        "American Funds Tax-Aware Conservative Growth and Income Portfolio",
    ),
    _ca(
        "AFAXX",
        "american-funds-u-s-government-money-market-fund",
        "American Funds U.S. Government Money Market Fund",
    ),
    _ca(
        "SMDEX",
        "american-funds-u-s-small-and-mid-cap-equity-fund",
        "American Funds U.S. Small and Mid Cap Equity Fund",
    ),
    _ca(
        "AMHIX",
        "american-high-income-municipal-bond-fund",
        "American High-Income Municipal Bond Fund",
        cusip="026545103",
    ),
    _ca("AHITX", "american-high-income-trust", "American High-Income Trust"),
    _ca("AMRMX", "american-mutual-fund", "American Mutual Fund", cusip="027681105"),
    _ca(
        "CPPKX",
        "capital-group-kkr-core-plus",
        "Capital Group KKR Core Plus +",
        "Capital Group KKR Core Plus+",
        "Capital Group — KKR Core Plus+",
        "Capital Group KKR Core Plus",
    ),
    _ca(
        "MSPPX",
        "capital-group-kkr-multi-sector",
        "Capital Group KKR Multi-Sector +",
        "Capital Group KKR Multi-Sector+",
        "Capital Group — KKR Multi-Sector+",
        "Capital Group KKR Multi-Sector",
    ),
    _ca("CAIBX", "capital-income-builder", "Capital Income Builder"),
    _ca("CWBFX", "capital-world-bond-fund", "Capital World Bond Fund"),
    _ca(
        "CWGIX",
        "capital-world-growth-and-income-fund",
        "Capital World Growth and Income Fund",
    ),
    _ca(
        "EMRGX",
        "emerging-markets-equities-fund",
        "Emerging Markets Equities Fund",
        cusip="290886100",
    ),
    _ca(
        "AEPGX",
        "eupac-fund",
        "EUPAC Fund",
        "EuroPacific Growth Fund",
        nicknames=("EUPAC",),
    ),
    _ca("ANCFX", "fundamental-investors", "Fundamental Investors", cusip="360802102"),
    _ca(
        "AIBAX",
        "intermediate-bond-fund-of-america",
        "Intermediate Bond Fund of America",
    ),
    _ca(
        "IGAAX",
        "international-growth-and-income-fund",
        "International Growth and Income Fund",
    ),
    _ca(
        "LTEBX",
        "limited-term-tax-exempt-bond-fund-of-america",
        "Limited Term Tax-Exempt Bond Fund of America",
    ),
    _ca("ANWPX", "new-perspective-fund", "New Perspective Fund"),
    _ca("NEWFX", "new-world-fund", "New World Fund"),
    _ca("ASBAX", "short-term-bond-fund-of-america", "Short-Term Bond Fund of America"),
    _ca("SMCWX", "smallcap-world-fund", "SMALLCAP World Fund"),
    _ca("ABNDX", "the-bond-fund-of-america", "The Bond Fund of America"),
    _ca(
        "AGTHX",
        "the-growth-fund-of-america",
        "The Growth Fund of America",
        cusip="399874106",
        nicknames=("GFA",),
    ),
    _ca("AMECX", "the-income-fund-of-america", "The Income Fund of America"),
    _ca(
        "AIVSX",
        "the-investment-company-of-america",
        "The Investment Company of America",
        cusip="461308108",
        nicknames=("ICA",),
    ),
    _ca("ANEFX", "the-new-economy-fund", "The New Economy Fund"),
    _ca("AMUSX", "u-s-government-securities-fund", "U.S. Government Securities Fund"),
    _ca(
        "AWSHX",
        "washington-mutual-investors-fund",
        "Washington Mutual Investors Fund",
        nicknames=("WMIF",),
    ),
)


def _payload(identity: ClassAIdentity) -> dict[str, str]:
    data = {"fund_identifier": identity.fund_identifier, "fund_name": identity.names[0]}
    if identity.cusip:
        data["cusip"] = identity.cusip
    return data


TICKER_LOOKUP_ALIASES: dict[str, dict[str, str]] = {}
IDENTIFIER_DISPLAY_TICKER: dict[str, str] = {}
IDENTIFIER_DISPLAY_CUSIP: dict[str, str] = {}
_BY_SLUG: dict[str, ClassAIdentity] = {}
_BY_FAMILY_SLUG: dict[str, dict[str, ClassAIdentity]] = {
    FAMILY_AMERICAN_FUNDS: {},
    FAMILY_BLACKROCK: {},
    FAMILY_JPMORGAN: {},
    FAMILY_INVESCO: {},
    FAMILY_MFS: {},
    FAMILY_JOHNHANCOCK: {},
    FAMILY_BNY: {},
    FAMILY_HARTFORD: {},
    FAMILY_AB: {},
    FAMILY_THRIVENT: {},
    FAMILY_CALAMOS: {},
    FAMILY_WASATCH: {},
    FAMILY_VOYA: {},
}


def _register_identity(family: str, identity: ClassAIdentity) -> None:
    row = _payload(identity)
    TICKER_LOOKUP_ALIASES[identity.ticker] = row
    for nick in identity.nicknames:
        TICKER_LOOKUP_ALIASES[nick] = row
    IDENTIFIER_DISPLAY_TICKER[identity.fund_identifier] = identity.ticker
    if identity.cusip:
        IDENTIFIER_DISPLAY_CUSIP[identity.fund_identifier] = identity.cusip
    family_slugs = _BY_FAMILY_SLUG.setdefault(family, {})
    family_slugs[identity.fund_identifier] = identity
    _BY_SLUG[identity.fund_identifier] = identity
    for name in identity.names:
        slug = _slugify(name)
        family_slugs[slug] = identity
        _BY_SLUG[slug] = identity


def _identities_from_rows(
    rows: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...],
) -> tuple[ClassAIdentity, ...]:
    out: list[ClassAIdentity] = []
    for ticker, ident, names, cusip in rows:
        fund_identifier = ident or _slugify(names[0])
        out.append(_ca(ticker, fund_identifier, *names, cusip=cusip))
    return tuple(out)


for _identity in CLASS_A_FUNDS:
    _register_identity(FAMILY_AMERICAN_FUNDS, _identity)

BLACKROCK_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(BLACKROCK_FUND_ROWS)
JPMORGAN_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(JPMORGAN_FUND_ROWS)
INVESCO_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(INVESCO_FUND_ROWS)
MFS_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(MFS_FUND_ROWS)
JOHNHANCOCK_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(JOHNHANCOCK_FUND_ROWS)
BNY_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(BNY_FUND_ROWS)
HARTFORD_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(HARTFORD_FUND_ROWS)
AB_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(AB_FUND_ROWS)
THRIVENT_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(THRIVENT_FUND_ROWS)
CALAMOS_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(CALAMOS_FUND_ROWS)
WASATCH_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(WASATCH_FUND_ROWS)
VOYA_FUNDS: tuple[ClassAIdentity, ...] = _identities_from_rows(VOYA_FUND_ROWS)

for _family, _funds in (
    (FAMILY_BLACKROCK, BLACKROCK_FUNDS),
    (FAMILY_JPMORGAN, JPMORGAN_FUNDS),
    (FAMILY_INVESCO, INVESCO_FUNDS),
    (FAMILY_MFS, MFS_FUNDS),
    (FAMILY_JOHNHANCOCK, JOHNHANCOCK_FUNDS),
    (FAMILY_BNY, BNY_FUNDS),
    (FAMILY_HARTFORD, HARTFORD_FUNDS),
    (FAMILY_AB, AB_FUNDS),
    (FAMILY_THRIVENT, THRIVENT_FUNDS),
    (FAMILY_CALAMOS, CALAMOS_FUNDS),
    (FAMILY_WASATCH, WASATCH_FUNDS),
    (FAMILY_VOYA, VOYA_FUNDS),
):
    for _identity in _funds:
        _register_identity(_family, _identity)


def class_a_for_name(fund_name: str | None, *, fund_family: str | None = None) -> ClassAIdentity | None:
    if not fund_name:
        return None
    slug = _slugify(fund_name)
    if fund_family is not None:
        family = family_key(fund_family)
        if family is None:
            return None
        return _BY_FAMILY_SLUG.get(family, {}).get(slug)
    return _BY_SLUG.get(slug)


def class_a_identifier_for_name(fund_name: str | None, *, fund_family: str | None = None) -> str | None:
    identity = class_a_for_name(fund_name, fund_family=fund_family)
    return identity.fund_identifier if identity else None


def enrich_class_a_fields(
    *,
    ticker: str | None,
    cusip: str | None,
    fund_name: str,
    fund_family: str | None = None,
) -> tuple[str | None, str | None]:
    """Fill missing ticker/CUSIP from the Class A map. Never overwrites parsed values."""
    identity = class_a_for_name(fund_name, fund_family=fund_family)
    if identity is None and ticker:
        alias = TICKER_LOOKUP_ALIASES.get(ticker.strip().upper())
        if alias:
            identity = _BY_SLUG.get(alias["fund_identifier"])
    if identity is None:
        return ticker, cusip
    out_ticker = ticker or identity.ticker
    out_cusip = cusip or identity.cusip
    return out_ticker, out_cusip


def normalize_ticker_key(value: str | None) -> str | None:
    if not value:
        return None
    key = value.strip().upper()
    return key or None


def alias_for_ticker(value: str | None) -> dict[str, str] | None:
    key = normalize_ticker_key(value)
    if not key:
        return None
    return TICKER_LOOKUP_ALIASES.get(key)


def alias_fund_identifier(value: str | None) -> str | None:
    alias = alias_for_ticker(value)
    if not alias:
        return None
    ident = alias.get("fund_identifier")
    return ident.strip().lower() if ident else None


def display_ticker(ticker: str | None, fund_identifier: str | None) -> str | None:
    """Return a UI ticker, backfilling from aliases when the row is name-keyed."""
    if ticker and ticker.strip() and ticker.strip() not in {"—", "-", "–"}:
        return ticker.strip().upper()
    if not fund_identifier:
        return ticker
    return IDENTIFIER_DISPLAY_TICKER.get(fund_identifier.strip().lower()) or ticker


def display_cusip(cusip: str | None, fund_identifier: str | None) -> str | None:
    if cusip and cusip.strip() and cusip.strip() not in {"—", "-", "–"}:
        return cusip.strip().upper()
    if not fund_identifier:
        return cusip
    return IDENTIFIER_DISPLAY_CUSIP.get(fund_identifier.strip().lower()) or cusip
