"""BNY Mellon Class A / Investor / ETF ticker aliases.

The 2025 estimate PDF is the full paying-fund book with names and almost no
tickers (DGAGX / PEOPX already parsed). Class A when the issuer lists it;
Investor (MIBLX / MIMSX / MISCX) when that is the retail class. Interval /
unconfirmed names stay unmapped.

Sources: BNY product pages / Funds Trust prospectus / ETF profile sheet
(DAGVX, DNLDX, DWOAX, PESPX, BKCG, BKLC, …).
"""

from __future__ import annotations

BNY_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    ("DNLDX", None, ("BNY Mellon Active Midcap Fund",), None),
    ("MIBLX", None, ("BNY Mellon Asset Allocation Fund",), None),
    ("DBOAX", None, ("BNY Mellon Balanced Opportunity Fund",), None),
    ("DCPAX", None, ("BNY Mellon Core Plus Fund",), None),
    ("DAGVX", None, ("BNY Mellon Dynamic Value Fund",), None),
    ("DQIAX", None, ("BNY Mellon Equity Income Fund",), None),
    ("DGLAX", None, ("BNY Mellon Global Stock Fund",), None),
    ("DISAX", None, ("BNY Mellon International Stock Fund",), None),
    ("DREVX", None, ("BNY Mellon Large Cap Securities Fund, Inc.",), None),
    ("PESPX", None, ("BNY Mellon Midcap Index Fund, Inc",), None),
    ("MIMSX", None, ("BNY Mellon Mid Cap Multi-Strategy Fund",), None),
    ("DMCVX", None, ("BNY Mellon Opportunistic Midcap Value Fund",), None),
    ("DWOAX", None, ("BNY Mellon Research Growth Fund, Inc.",), None),
    ("MISCX", None, ("BNY Mellon Small Cap Multi-Strategy Fund",), None),
    ("DTGRX", None, ("BNY Mellon Technology Growth Fund",), None),
    ("PGROX", None, ("BNY Mellon Worldwide Growth Fund, Inc.",), None),
    ("DEQAX", None, ("BNY Mellon Global Equity Income Fund",), None),
    ("DIEAX", None, ("BNY Mellon International Core Equity Fund",), None),
    ("DLQAX", None, ("BNY Mellon Large Cap Equity Fund",), None),
    ("DBMAX", None, ("BNY Mellon Small/Mid Cap Growth Fund",), None),
    ("DTCAX", None, ("BNY Mellon Sustainable U.S. Equity Fund, Inc.",), None),
    ("BKCG", None, ("BNY Mellon Concentrated Growth ETF",), None),
    ("BKCI", None, ("BNY Mellon Concentrated International ETF",), None),
    ("BKAG", None, ("BNY Mellon Core Bond ETF",), None),
    ("BKDV", None, ("BNY Mellon Dynamic Value ETF",), None),
    ("BKEM", None, ("BNY Mellon Emerging Markets Equity ETF",), None),
    ("BKGI", None, ("BNY Mellon Global Infrastructure Income ETF",), None),
    ("BKHY", None, ("BNY Mellon High Yield ETF",), None),
    ("BKIE", None, ("BNY Mellon International Equity ETF",), None),
    ("BKLC", None, ("BNY Mellon US Large Cap Core Equity ETF",), None),
    ("BKMC", None, ("BNY Mellon US Mid Cap Core Equity ETF",), None),
    ("BKSE", None, ("BNY Mellon US Small Cap Core Equity ETF",), None),
    ("BKUI", None, ("BNY Mellon Ultra Short Income ETF",), None),
)
