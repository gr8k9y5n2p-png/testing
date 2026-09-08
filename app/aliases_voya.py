"""Voya Class A ticker aliases for name-keyed estimate PDFs.

Existing rows already use Class A (NLCAX / NMCAX / VYCAX). Remaining
open-end names stay slug-keyed. VACS series and variable-insurance
portfolios are left unmapped. Multi-Manager Class A left unmapped when
unconfirmed.

Sources: voya.com Class A product pages (IEDAX, NAWGX, VYMQX, VWYFX).
"""

from __future__ import annotations

VOYA_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    ("NAWGX", None, ("Voya Global High Dividend Low Volatility Fund",), None),
    ("IEDAX", None, ("Voya Large Cap Value Fund",), None),
    ("VYMQX", None, ("Voya MI Dynamic SMID Cap Fund",), None),
    ("VWYFX", None, ("Voya Small Cap Growth Fund",), None),
)
