"""Calamos Class A ticker aliases for name-keyed estimate PDFs.

The 2025 estimate PDF is fund-level Class A NAV (Growth CVGRX already parsed).
Remaining paying-fund names stay slug-keyed. Antetokounmpo Class A left
unmapped (unconfirmed). Do not attach Class I (CTSIX / CSGIX / CIGEX).

Sources: calamos.com Class A product pages (CPLSX, CAGCX, CTAGX, CVAAX,
CIGRX, CAGEX, CVLOX, CAISX, CMRAX).
"""

from __future__ import annotations

CALAMOS_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    ("CAGCX", None, ("Calamos Global Convertible Fund",), None),
    ("CAGEX", None, ("Calamos Global Equity Fund",), None),
    ("CVLOX", None, ("Calamos Global Opportunities Fund",), None),
    ("CIGRX", None, ("Calamos International Growth Fund",), None),
    ("CAISX", None, ("Calamos International Small Cap Growth Fund",), None),
    ("CMRAX", None, ("Calamos Merger Arbitrage Fund",), None),
    ("CPLSX", None, ("Calamos Phineus Long/Short Fund",), None),
    ("CVAAX", None, ("Calamos Select Fund",), None),
    ("CTAGX", None, ("Calamos Timpani SMID Growth Fund",), None),
)
