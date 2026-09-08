"""J.P. Morgan Class A / ETF / retail money-market ticker aliases.

The 2025 Section 19a Appendix A fixture is name-keyed except SEEGX / JLGMX
(already ticker-keyed). Class A symbols come from the public J.P. Morgan
sales-charge schedule (SCDC_Public.pdf, June 30, 2026). ETF tickers come
from J.P. Morgan product pages / SEC 497K. Money-market funds have no Class A;
Morgan is the $1,000 retail class used here.

SEEGX / JLGMX keep ticker-keyed identifiers so re-ingest does not fork those
existing rows. Every other name stays slug-keyed.
"""

from __future__ import annotations

# (ticker, fund_identifier or None, names, cusip or None)
# None identifier → slugify(names[0]).
JPMORGAN_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    # Class A — am.jpmorgan.com SCDC_Public.pdf (June 30, 2026)
    ("JFAMX", None, ("JPMorgan Emerging Markets Equity Fund",), None),
    ("OIEIX", None, ("JPMorgan Equity Income Fund",), None),
    ("OGEAX", None, ("JPMorgan Equity Index Fund",), None),
    ("VHIAX", None, ("JPMorgan Growth Advantage Fund",), None),
    ("JSEAX", None, ("JPMorgan International Equity Fund",), None),
    ("IUAEX", None, ("JPMorgan International Focus Fund",), None),
    # Existing ticker-keyed Large Cap Growth rows — do not slug-fork
    ("SEEGX", "SEEGX", ("JPMorgan Large Cap Growth Fund",), None),
    ("JLGMX", "JLGMX", ("JPMorgan Large Cap Growth Fund R6", "JPMorgan Large Cap Growth Fund R"), None),
    ("OLVAX", None, ("JPMorgan Large Cap Value Fund",), None),
    ("JCMAX", None, ("JPMorgan Mid Cap Equity Fund",), None),
    ("OSGIX", None, ("JPMorgan Mid Cap Growth Fund",), None),
    ("JAMCX", None, ("JPMorgan Mid Cap Value Fund",), None),
    ("VSCOX", None, ("JPMorgan Small Cap Blend Fund",), None),
    ("VSEAX", None, ("JPMorgan Small Cap Equity Fund",), None),
    ("PGSGX", None, ("JPMorgan Small Cap Growth Fund",), None),
    ("PSOAX", None, ("JPMorgan Small Cap Value Fund",), None),
    ("PECAX", None, ("JPMorgan SMID Cap Equity Fund",), None),
    ("JUEAX", None, ("JPMorgan U.S. Equity Fund",), None),
    ("JIGAX", None, ("JPMorgan U.S. GARP Equity Fund",), None),
    ("JLCAX", None, ("JPMorgan U.S. Large Cap Core Plus Fund",), None),
    ("JDEAX", None, ("JPMorgan U.S. Research Enhanced Equity Fund",), None),
    ("JTUAX", None, ("JPMorgan U.S. Small Company Fund",), None),
    ("JICAX", None, ("JPMorgan U.S. Sustainable Leaders Fund",), None),
    ("JVAAX", None, ("JPMorgan Value Advantage Fund",), None),
    ("VGRIX", None, ("JPMorgan U.S. Value Fund",), None),
    ("UBVAX", None, ("Undiscovered Managers Behavioral Value Fund",), None),
    # ETFs — issuer product pages / SEC 497K
    ("JBND", None, ("JPMorgan Active Bond ETF",), None),
    ("JPHY", None, ("JPMorgan Active High Yield ETF",), "46654Q633"),
    ("BBEM", None, ("JPMorgan BetaBuilders Emerging Markets Equity ETF",), "46654Q807"),
    ("JDIV", None, ("JPMorgan Dividend Leaders ETF",), "46654Q658"),
    ("JFLI", None, ("JPMorgan Flexible Income ETF",), None),
    ("LVDS", None, ("JPMorgan Fundamental Data Science Large Value ETF",), "46654Q583"),
    ("JIVE", None, ("JPMorgan International Value ETF",), None),
    ("JUSA", None, ("JPMorgan U.S. Research Enhanced Large Cap ETF",), None),
    # Money markets — Morgan ($1,000) retail class; no Class A
    ("VCAXX", None, ("JPMorgan California Municipal Money Market Fund",), "4812A0805"),
    ("MJMXX", None, ("JPMorgan Municipal Money Market Fund",), "4812C0266"),
    ("VNYXX", None, ("JPMorgan New York Municipal Money Market Fund",), "4812A0813"),
    ("VTMXX", None, ("JPMorgan Tax Free Money Market Fund",), "4812A2728"),
)
