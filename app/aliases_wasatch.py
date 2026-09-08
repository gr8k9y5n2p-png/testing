"""Wasatch Investor-class ticker aliases for name-keyed estimate PDFs.

Existing rows already use Investor tickers (WGROX / WAIGX / WMCVX). Remaining
names stay slug-keyed on the same Investor class. Institutional (WIINX, …)
is not mapped.

Sources: Wasatch Funds Trust SEC 497 / Investor product pages (WAINX, WAEMX,
WAGOX, FMIEX, WAIOX, WAIVX, WAMVX, WAAEX, WHOSX, WAUSX).
"""

from __future__ import annotations

WASATCH_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    ("WAINX", None, ("Wasatch Emerging India Fund",), None),
    ("WAEMX", None, ("Wasatch Emerging Markets Small Cap Fund",), None),
    ("WAGOX", None, ("Wasatch Global Opportunities Fund",), None),
    ("FMIEX", None, ("Wasatch Global Value Fund",), None),
    ("WAIOX", None, ("Wasatch International Opportunities Fund",), None),
    ("WAIVX", None, ("Wasatch International Value Fund",), None),
    ("WAMVX", None, ("Wasatch Micro Cap Value Fund",), None),
    ("WAAEX", None, ("Wasatch Small Cap Growth Fund",), None),
    ("WAUSX", None, ("Wasatch U.S. Select Fund",), None),
    ("WHOSX", None, ("Wasatch-Hoisington U.S. Treasury Fund",), None),
)
