from __future__ import annotations

from app.sources.american_funds import AmericanFundsSource
from app.sources.base import FundSource
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

_ALIASES = {
    "american_funds": "american_funds",
    "american-funds": "american_funds",
    "americanfunds": "american_funds",
    "capital_group": "american_funds",
    "capital-group": "american_funds",
    "capitalgroup": "american_funds",
    "blackrock": "blackrock",
    "ishares": "blackrock",
    "i_shares": "blackrock",
    "vanguard": "vanguard",
    "fidelity": "fidelity",
    "state_street": "state_street",
    "statestreet": "state_street",
    "ssga": "state_street",
    "spdr": "state_street",
    "jpmorgan": "jpmorgan",
    "jp_morgan": "jpmorgan",
    "jpm": "jpmorgan",
    "goldman_sachs": "goldman_sachs",
    "goldman": "goldman_sachs",
    "gs": "goldman_sachs",
    "gsam": "goldman_sachs",
    "pimco": "pimco",
    "invesco": "invesco",
    "t_rowe_price": "t_rowe_price",
    "troweprice": "t_rowe_price",
    "t_rowe": "t_rowe_price",
    "trp": "t_rowe_price",
}


def _sources() -> dict[str, FundSource]:
    ordered = [
        BlackRockSource(),
        VanguardSource(),
        FidelitySource(),
        StateStreetSource(),
        JPMorganSource(),
        GoldmanSachsSource(),
        AmericanFundsSource(),
        PimcoSource(),
        InvescoSource(),
        TRowePriceSource(),
    ]
    return {source.slug: source for source in ordered}


def list_sources() -> list[FundSource]:
    return sorted(
        _sources().values(),
        key=lambda s: (s.aum_rank is None, s.aum_rank or 99, s.slug),
    )


def get_source(slug: str) -> FundSource:
    sources = _sources()
    key = _ALIASES.get(slug.strip().lower().replace(" ", "_"), slug.strip().lower().replace(" ", "_"))
    if key not in sources:
        known = ", ".join(sorted(sources))
        raise KeyError(f"Unknown fund family '{slug}'. Registered: {known}")
    return sources[key]


def resolve_slug(value: str | None) -> str | None:
    if not value:
        return None
    key = value.strip().lower().replace(" ", "_")
    if key in _ALIASES:
        return _ALIASES[key]
    sources = _sources()
    if key in sources:
        return key
    return None


def resolve_families(fund_family: str) -> list[FundSource]:
    if fund_family.strip().lower() in {"all", "*"}:
        return [s for s in list_sources() if s.implemented]
    return [get_source(fund_family)]
