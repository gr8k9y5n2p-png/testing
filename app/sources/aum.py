"""Curated ≥$1B AUM filter for *older* multi-year history packs.

Current-year / published-table fixtures ingest the full public book (every
listed fund except synthetic ZZ* samples). This allowlist still applies when
a PageSpec sets large_aum_only=True — typically sparse older archives.

When the same family fetch already ingested a ticker on an unfiltered page
(current estimate / full paid book), older official archives also keep that
ticker so paid/final income and capital-gains gaps fill without adding
net-new names. Flagship-only transcriptions stay filtered.

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
        "FCNTX",
        # Other rank 1–10 flagships already in fixtures
        "AGTHX",
        "SEEGX",
        "GLCGX",
        "SPY",
        "SPLG",
        "QQQ",
        "IVV",
        "IWM",
        "EFA",
        "AGG",
        "GLD",
        "JEPI",
        "JEPQ",
        "SCHD",
        "SCHX",
        "SCHB",
        "SCHF",
        "SCHG",
        "SCHA",
        "SCHM",
        "SCHE",
        "SCHV",
        "SCHP",
        "SCHZ",
        "SCHH",
        "SCHC",
        "FNDF",
        "VGT",
        "VFH",
        "VCIT",
        "VCSH",
        "VTEB",
        "VONG",
        "VONV",
        "BNDW",
        "ACWX",
        "IEMG",
        "IEFA",
        "ITOT",
        "TLT",
        "LQD",
        "HYG",
        "VNQ",
        "ARKK",
        "BNDX",
        # Ranks 11–20 historical flagships (≥$1B / family book heroes)
        "PWTAX",
        "PWTYX",
        "DGAGX",
        "DAGVX",
        "DREVX",
        "DREQX",
        "DNLDX",
        "PGROX",
        "DGLAX",
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
        "EIVIX",
        "EGOIX",
        "ESPNX",
        "EMGNX",
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
        "MRGAX",
        "MDIDX",
        "MWEFX",
        "MWOFX",
        "MIDAX",
        "MAGWX",
        "MAMAX",
        "MRSAX",
        "NDVAX",
        "BRWAX",
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


def filter_large_aum(
    records: list[NormalizedRecord],
    universe_tickers: set[str] | frozenset[str] | None = None,
) -> list[NormalizedRecord]:
    """Keep ≥$1B allowlist tickers plus tickers already in this family's book.

    ``universe_tickers`` is the current-book set from unfiltered pages in the
    same fetch (estimates + full paid books). Official ordinary-income and
    capital-gains rows for those names are kept. Names that appear only on a
    sparse older archive stay dropped — no invented universe.
    """
    universe = {ticker.strip().upper() for ticker in (universe_tickers or set()) if ticker}
    kept: list[NormalizedRecord] = []
    for row in records:
        ticker = (row.ticker or "").strip().upper()
        if is_large_aum_ticker(ticker) or ticker in universe:
            kept.append(row)
    return kept
