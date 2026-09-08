"""Top-40 Aftertax coverage readiness: estimate feeds, YE history, performance.

Status strings are for GET /coverage and the weekly scrape contract.
Do not invent estimate amounts when a wired hub is empty or seasonal.
"""

from __future__ import annotations

# prelim/updated already in fixtures or live HTML that parses estimates.
# paid_history_only: estimate hub is wired for weekly walk but current book is paid/final.
# deferred: SPA/403 still walked; no invented zeros.
# skipped: Amundi — do not expand.
ESTIMATE_STATUS: dict[str, str] = {
    "blackrock": "prelim_updated",
    "vanguard": "paid_history_only",
    "fidelity": "prelim_updated",
    "state_street": "deferred",
    "jpmorgan": "prelim_updated",
    "goldman_sachs": "deferred",
    "american_funds": "prelim_updated",
    "pimco": "deferred",
    "invesco": "prelim_updated",
    "t_rowe_price": "prelim_updated",
    "ubs": "prelim_updated",
    "franklin_templeton": "deferred",
    "bny_mellon": "prelim_updated",
    "nuveen": "prelim_updated",
    "northern_trust": "prelim_updated",
    "morgan_stanley": "paid_history_only",
    "schwab": "paid_history_only",
    "dimensional": "prelim_updated",
    "columbia_threadneedle": "prelim_updated",
    "amundi": "skipped",
    "allspring": "paid_history_only",
    "janus_henderson": "prelim_updated",
    "american_century": "prelim_updated",
    "dodge_cox": "prelim_updated",
    "mfs": "prelim_updated",
    "lord_abbett": "prelim_updated",
    "ab": "prelim_updated",
    "federated_hermes": "deferred",
    "virtus": "prelim_updated",
    "eaton_vance": "deferred",
    "john_hancock": "prelim_updated",
    "principal": "paid_history_only",
    "thrivent": "paid_history_only",
    "hartford": "prelim_updated",
    "macquarie": "prelim_updated",
    "first_eagle": "prelim_updated",
    "gmo": "prelim_updated",
    "artisan": "paid_history_only",
    "calamos": "prelim_updated",
    "wasatch": "prelim_updated",
}

# Calendar years with official YE/paid/estimate fixtures (not invented).
HISTORY_YEARS: dict[str, tuple[int, ...]] = {
    "blackrock": (2021, 2022, 2023, 2024, 2025, 2026),
    "vanguard": (2021, 2022, 2023, 2024, 2025),
    "fidelity": (2024, 2025, 2026),
    "state_street": (2021, 2022, 2023, 2024, 2025),
    "jpmorgan": (2025,),
    "goldman_sachs": (2025,),
    "american_funds": (2021, 2022, 2023, 2024, 2025, 2026),
    "pimco": (),
    "invesco": (2024, 2025),
    "t_rowe_price": (2021, 2022, 2023, 2024, 2025),
    "ubs": (2025,),
    "franklin_templeton": (2024, 2025),
    "bny_mellon": (2022, 2023, 2024, 2025),
    "nuveen": (2025,),
    "northern_trust": (2021, 2022, 2023, 2024, 2025),
    "morgan_stanley": (2024, 2025),
    "schwab": (2021, 2022, 2023, 2024, 2025),
    "dimensional": (2024, 2025),
    "columbia_threadneedle": (2024, 2025),
    "amundi": (2025,),
    "allspring": (2021, 2022, 2023, 2024, 2025),
    "janus_henderson": (2021, 2022, 2023, 2024, 2025),
    "american_century": (2022, 2023, 2025),
    "dodge_cox": (2021, 2022, 2023, 2024, 2025, 2026),
    "mfs": (2021, 2022, 2023, 2024, 2025, 2026),
    "lord_abbett": (2025,),
    "ab": (2023, 2025),
    "federated_hermes": (2025,),
    "virtus": (2024, 2025, 2026),
    "eaton_vance": (2025,),
    "john_hancock": (2022, 2023, 2024, 2025),
    "principal": (2023, 2024, 2025),
    "thrivent": (2025,),
    "hartford": (2024, 2025),
    "macquarie": (2023, 2024, 2025),
    "first_eagle": (2023, 2024, 2025),
    "gmo": (2026,),
    "artisan": (2024, 2025, 2026),
    "calamos": (2024, 2025),
    "wasatch": (2022, 2024, 2025),
}

# Tickers with Growth of $X fixtures (Yahoo monthly adj close).
PERFORMANCE_TICKERS: dict[str, tuple[str, ...]] = {
    "blackrock": ("MDDVX", "AGG"),
    "vanguard": ("VFIAX", "VTIAX", "VIGAX", "VBIAX", "VXUS"),
    "fidelity": ("FBGRX",),
    "state_street": ("SPY", "ALLW"),
    "american_funds": ("AGTHX", "AMCPX", "ABALX"),
    "t_rowe_price": ("TRBCX",),
    "schwab": ("SWTSX", "SWANX"),
    "dodge_cox": ("DODIX", "DODGX"),
    "janus_henderson": ("JDCAX",),
    "northern_trust": ("NOSIX",),
}


def estimate_feed_status(slug: str) -> str:
    return ESTIMATE_STATUS.get(slug, "unlisted")


def history_years(slug: str) -> list[int]:
    return list(HISTORY_YEARS.get(slug, ()))


def has_multi_year_history(slug: str) -> bool:
    return len(HISTORY_YEARS.get(slug, ())) >= 2


def performance_tickers(slug: str) -> list[str]:
    return list(PERFORMANCE_TICKERS.get(slug, ()))


def has_performance(slug: str) -> bool:
    return bool(PERFORMANCE_TICKERS.get(slug))
