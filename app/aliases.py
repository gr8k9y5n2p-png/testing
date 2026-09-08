"""Shared Class A ticker ↔ stored fund_identifier aliases.

American Funds (and similar) official books are name-keyed: rows store
``ticker=null`` and ``fund_identifier`` like ``amcap-fund``. Illustrate already
resolves AGTHX / AMCPX / AMCAP through this map. List/search must use the
same map so UI ticker filters are not empty.

Display ticker is the official Class A symbol (AMCPX, not the AMCAP nickname).
"""

from __future__ import annotations

# Class A ticker (or nickname) → stored identity when the HTML book has no ticker column.
TICKER_LOOKUP_ALIASES: dict[str, dict[str, str]] = {
    "AMCPX": {"fund_identifier": "amcap-fund"},
    "AMCAP": {"fund_identifier": "amcap-fund"},
    "AGTHX": {"fund_identifier": "the-growth-fund-of-america"},
}

# Preferred UI ticker for a stored slug (Class A).
IDENTIFIER_DISPLAY_TICKER: dict[str, str] = {
    "amcap-fund": "AMCPX",
    "the-growth-fund-of-america": "AGTHX",
}


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
