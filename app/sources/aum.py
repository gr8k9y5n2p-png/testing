"""Curated >$1B AUM filter for historical multi-year packs.

Eric's locked strategy: do not license CapGainsValet/YCharts. When expanding
*within* a family, keep flagship / large-AUM share classes rather than every
micro class. This is a curated allowlist of funds identified as above $1B AUM
(or locked hero tickers), not a live AUM feed.
"""

from __future__ import annotations

from app.sources.parser import NormalizedRecord

# Identified >$1B flagship share classes (Admiral / Investor flagship / mega ETF).
# Not an exhaustive AUM file — prefer these when adding ICI/PDF history.
LARGE_AUM_TICKERS: frozenset[str] = frozenset(
    {
        # Vanguard flagships (ICI historical packs; Admiral / mega ETF >$1B)
        "VFIAX",
        "VOO",
        "VBIAX",
        "VIGAX",
        "VTSAX",
        "VTIAX",
        "VTI",
        "VXUS",
        # Locked compare heroes (in-scope even if a class is smaller)
        "AMCPX",
        "AMCAP",
        "CGHM",
        "TRBCX",
        "FBGRX",
        # Other rank 1–10 flagships already in fixtures
        "AGTHX",
        "SEEGX",
        "GLCGX",
        "SPY",
        "SPLG",
    }
)

MIN_HISTORICAL_AUM_USD = 1_000_000_000


def is_large_aum_ticker(ticker: str | None) -> bool:
    if not ticker:
        return False
    return ticker.strip().upper() in LARGE_AUM_TICKERS


def filter_large_aum(records: list[NormalizedRecord]) -> list[NormalizedRecord]:
    """Keep rows whose ticker is on the >$1B / hero allowlist."""
    return [row for row in records if is_large_aum_ticker(row.ticker)]
