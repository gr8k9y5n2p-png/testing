"""Curated ≥$1B AUM filter for *older* multi-year history packs.

Current-year / published-table fixtures ingest the full public book (every
listed fund except synthetic ZZ* samples). This allowlist still applies when
a PageSpec sets large_aum_only=True — typically sparse older archives.
Not a live AUM feed. Do not license CapGainsValet/YCharts.
"""

from __future__ import annotations

from app.sources.parser import NormalizedRecord

# Identified ≥$1B flagship share classes (Admiral / Investor flagship / mega ETF).
# Not an exhaustive AUM file — prefer these when adding ICI/PDF history.
LARGE_AUM_TICKERS: frozenset[str] = frozenset(
    {
        # Vanguard ICI book (Admiral + mega ETF, ≥$1B)
        "VFIAX",
        "VOO",
        "VBIAX",
        "VIGAX",
        "VTSAX",
        "VTIAX",
        "VTI",
        "VXUS",
        "VEA",
        "VWO",
        "VUG",
        "VIG",
        "VYM",
        "VV",
        "VO",
        "VB",
        "VTV",
        "VVIAX",
        "VWENX",
        "VWNAX",
        "VIMAX",
        "VSMAX",
        "VLCAX",
        "VFWAX",
        "VEMAX",
        "VPMAX",
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
        # Ranks 11–20 historical flagships (≥$1B / family book heroes)
        "PWTAX",
        "PWTYX",
        "DGAGX",
        "PEOPX",
        "TIIRX",
        "NOSIX",
        "NOLCX",
        "NOMIX",
        "NOIEX",
        "NOSGX",
        "CVLC",
        "SWTSX",
        "SWPPX",
        "SWLVX",
        "SWSSX",
        "SWISX",
        "SWLGX",
        "SWMCX",
        "SNXFX",
        "SPYM",
        "DIA",
        "DISVX",
        "DFELX",
        "DFQTX",
        "IEVAX",
        "ELGAX",
        "LBSAX",
        "PIODX",
        "PIGFX",
        # Ranks 21–30 historical flagships (≥$1B / family book heroes)
        "WFMIX",
        "SGRNX",
        "JDCAX",
        "JDMAX",
        "JCNAX",
        "TWCGX",
        "BEQGX",
        "DODGX",
        "DODBX",
        "DODFX",
        "DODIX",
        "MIGHX",
        "MITTX",
        "MEIAX",
        "MFEGX",
        "MFRFX",
        "OTCAX",
        "MVCAX",
        "MSFRX",
        "MGRAX",
        "MGIAX",
        "MNDAX",
        "MTCAX",
        "MMUFX",
        "AGRFX",
        "APGAX",
        "ABASX",
        "STVTX",
        "STCIX",
        "UNWGX",
        # Ranks 31–42 historical flagships (US books / ≥$1B / family heroes)
        "TAGRX",
        "USGLX",
        "JBGAX",
        "HFMCX",
        "HAIAX",
        "IHGIX",
        "WSTAX",
        "WLGAX",
        "DDVAX",
        "SGENX",
        "SGOVX",
        "FEVAX",
        "GQETX",
        "GMUEX",
        "ARTKX",
        "CVGRX",
        "CVTRX",
        "CCVIX",
        "WGROX",
        "HACAX",
        "NWHOX",
        "PQIAX",
        "PEMGX",
    }
)

MIN_HISTORICAL_AUM_USD = 1_000_000_000


def is_large_aum_ticker(ticker: str | None) -> bool:
    if not ticker:
        return False
    return ticker.strip().upper() in LARGE_AUM_TICKERS


def filter_large_aum(records: list[NormalizedRecord]) -> list[NormalizedRecord]:
    """Keep rows whose ticker is on the ≥$1B / hero allowlist."""
    return [row for row in records if is_large_aum_ticker(row.ticker)]
