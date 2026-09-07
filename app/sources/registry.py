from __future__ import annotations

from app.sources.american_funds import AmericanFundsSource
from app.sources.base import FundSource
from app.sources.stubs import StubFundSource

_ALIASES = {
    "american_funds": "american_funds",
    "american-funds": "american_funds",
    "americanfunds": "american_funds",
    "capital_group": "american_funds",
    "capital-group": "american_funds",
    "capitalgroup": "american_funds",
}


def _sources() -> dict[str, FundSource]:
    return {
        "american_funds": AmericanFundsSource(),
        "vanguard": StubFundSource(
            slug="vanguard",
            display_name="Vanguard",
            notes=(
                "Not implemented. Typical public source: Vanguard year-end estimated "
                "capital gains (per-share / % of NAV) on investor.vanguard.com."
            ),
            urls=["https://investor.vanguard.com/"],
        ),
        "fidelity": StubFundSource(
            slug="fidelity",
            display_name="Fidelity",
            notes=(
                "Not implemented. Typical public source: Fidelity estimated capital "
                "gain distributions PDF/HTML on fidelity.com."
            ),
            urls=["https://www.fidelity.com/"],
        ),
        "t_rowe_price": StubFundSource(
            slug="t_rowe_price",
            display_name="T. Rowe Price",
            notes="Not implemented. Plug in a FundSource subclass when a parser is ready.",
            urls=["https://www.troweprice.com/"],
        ),
    }


def list_sources() -> list[FundSource]:
    return list(_sources().values())


def get_source(slug: str) -> FundSource:
    sources = _sources()
    key = _ALIASES.get(slug.strip().lower().replace(" ", "_"), slug.strip().lower())
    if key not in sources:
        known = ", ".join(sorted(sources))
        raise KeyError(f"Unknown fund family '{slug}'. Registered: {known}")
    return sources[key]


def resolve_families(fund_family: str) -> list[FundSource]:
    if fund_family.strip().lower() in {"all", "*"}:
        return [s for s in list_sources() if s.implemented]
    return [get_source(fund_family)]
