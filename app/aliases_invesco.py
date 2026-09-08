"""Invesco Class A ticker aliases for name-keyed estimate PDFs.

2025 MF capital-gains PDF lists fund names without tickers. Rows stay
name-slug keyed. SMA High Yield Bond is not in this map.

Sources: Invesco Class A fact sheets / Form 5500 Schedule C
(VAFAX, ACSTX, CHTRX, OPOCX, ODMAX, OEGAX, MSIGX, …).
"""

from __future__ import annotations

INVESCO_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    ("OAAAX", None, ("Invesco Active Allocation Fund",), None),
    ("QMGAX", None, ("Invesco Advantage International Fund",), None),
    ("VAFAX", None, ("Invesco American Franchise Fund",), None),
    ("BRCAX", None, ("Invesco Balanced-Risk Commodity Strategy Fund",), None),
    ("CHTRX", None, ("Invesco Charter Fund",), None),
    ("ACSTX", None, ("Invesco Comstock Fund",), None),
    ("CGRWX", None, ("Invesco Comstock Select Fund",), None),
    ("CNSAX", None, ("Invesco Convertible Securities Fund",), None),
    ("ODMAX", None, ("Invesco Developing Markets Fund",), None),
    ("OPOCX", None, ("Invesco Discovery Fund",), None),
    ("OEGAX", None, ("Invesco Discovery Mid Cap Growth Fund",), None),
    ("LCEAX", None, ("Invesco Diversified Dividend Fund",), None),
    ("IAUTX", None, ("Invesco Dividend Income Fund",), None),
    ("AIIEX", None, ("Invesco EQV International Equity Fund",), None),
    ("VADAX", None, ("Invesco Equally-Weighted S&P 500 Fund",), None),
    ("ACEIX", None, ("Invesco Equity and Income Fund",), None),
    ("QVGIX", None, ("Invesco Global Allocation Fund",), None),
    ("AWSAX", None, ("Invesco Global Core Equity Fund",), None),
    ("GLVAX", None, ("Invesco Global Focus Fund",), None),
    ("OPPAX", None, ("Invesco Global Fund",), None),
    ("ACGIX", None, ("Invesco Growth and Income Fund",), None),
    ("GGHCX", None, ("Invesco Health Care Fund",), None),
    ("OIDAX", None, ("Invesco International Diversified Fund",), None),
    ("OSMAX", None, ("Invesco International Small-Mid Company Fund",), None),
    ("OMSOX", None, ("Invesco Main Street All Cap Fund",), None),
    ("MSIGX", None, ("Invesco Main Street Fund",), None),
    ("OPMSX", None, ("Invesco Main Street Mid Cap Fund",), None),
    ("OSCAX", None, ("Invesco Main Street Small Cap Fund",), None),
    ("IARAX", None, ("Invesco Real Estate Fund",), None),
    ("OARDX", None, ("Invesco Rising Dividends Fund",), None),
    ("SPIAX", None, ("Invesco S&P 500 Index Fund",), None),
    ("AADAX", None, ("Invesco Select Risk: Growth Investor Fund",), None),
    ("OAAIX", None, ("Invesco Select Risk: High Growth Investor Fund",), None),
    ("OAMIX", None, ("Invesco Select Risk: Moderate Investor Fund",), None),
    ("SMEAX", None, ("Invesco Small Cap Equity Fund",), None),
    ("GTSAX", None, ("Invesco Small Cap Growth Fund",), None),
    ("VSCAX", None, ("Invesco Small Cap Value Fund",), None),
    ("ASMMX", None, ("Invesco Summit Fund",), None),
    ("ITYAX", None, ("Invesco Technology Fund",), None),
    ("VVOAX", None, ("Invesco Value Opportunities Fund",), None),
)
