"""Thrivent Class S ticker aliases for name-keyed paid-gains HTML.

The public tax-center table is fund-level with no ticker column. Existing rows
already use Class S (TMSIX / THLCX / IILGX). Remaining names stay slug-keyed
and attach the same Class S identifier. Class A (TAAAX, …) is not mapped.

Sources: Thrivent Class S prospectuses / SEC 497K (TAAIX, IBBFX, TWAIX,
TLVIX, TMAIX, TMAFX, TCAIX, TSCGX, TSCSX). Mid Cap Value Class S was TMCVX
on the 2025 paid book (converted to TMVE ETF 11/17/2025).
"""

from __future__ import annotations

THRIVENT_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    ("TAAIX", None, ("Thrivent Aggressive Allocation Fund",), None),
    ("IBBFX", None, ("Thrivent Dynamic Allocation Fund",), None),
    ("TWAIX", None, ("Thrivent International Equity Fund",), None),
    ("TLVIX", None, ("Thrivent Large Cap Value Fund",), None),
    ("TMCVX", None, ("Thrivent Mid Cap Value Fund",), None),
    ("TMAIX", None, ("Thrivent Moderate Allocation Fund",), None),
    ("TMAFX", None, ("Thrivent Moderately Aggressive Allocation Fund",), None),
    ("TCAIX", None, ("Thrivent Moderately Conservative Allocation Fund",), None),
    ("TSCGX", None, ("Thrivent Small Cap Growth Fund",), None),
    ("TSCSX", None, ("Thrivent Small Cap Stock Fund",), None),
)
