"""John Hancock Class A / ETF ticker aliases for name-keyed press-release PDFs.

Estimate PDFs list paying-fund names without tickers (TAGRX / USGLX / JBGAX
already parsed). Other names stay slug-keyed. Interval (Marathon ABL) omitted.

Sources: JH SAIs (Aug / Oct / Mar fiscal) and Class A fact sheets
(SVBAX, JVLAX, JHEIX, FRBAX, GOIGX, JHHY, JHAC, …).
"""

from __future__ import annotations

JOHNHANCOCK_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    ("JAAAX", None, ("John Hancock Alternative Asset Allocation Fund",), None),
    ("SVBAX", None, ("John Hancock Balanced Fund",), None),
    ("JHNBX", None, ("John Hancock Bond Fund",), None),
    ("PZFVX", None, ("John Hancock Classic Value Fund",), None),
    ("JVLAX", None, ("John Hancock Disciplined Value Fund",), None),
    ("JEVAX", None, ("John Hancock Disciplined Value Emerging Markets Equity Fund",), None),
    ("JAKRX", None, ("John Hancock Disciplined Value Global Long/Short Fund",), None),
    ("JDIBX", None, ("John Hancock Disciplined Value International Fund",), None),
    ("JVMAX", None, ("John Hancock Disciplined Value Mid Cap Fund",), None),
    ("JDJAX", None, ("John Hancock Diversified Macro Fund",), None),
    ("JHJAX", None, ("John Hancock ESG Large Cap Core Fund",), None),
    ("JEMQX", None, ("John Hancock Emerging Markets Equity Fund",), None),
    ("JHEIX", None, ("John Hancock Equity Income Fund",), None),
    ("FIDAX", None, ("John Hancock Financial Industries Fund",), None),
    ("JFCAX", None, ("John Hancock Fundamental All Cap Core Fund",), None),
    ("JHCMX", None, ("John Hancock Fundamental Equity Income Fund",), None),
    ("JABZX", None, ("John Hancock Global Environmental Opportunities Fund",), None),
    ("JHGEX", None, ("John Hancock Global Equity Fund",), None),
    ("JGYAX", None, ("John Hancock Global Shareholder Yield Fund",), None),
    ("JEEBX", None, ("John Hancock Infrastructure Fund",), None),
    ("JIJAX", None, ("John Hancock International Dynamic Growth Fund",), None),
    ("GOIGX", None, ("John Hancock International Growth Fund",), None),
    ("TAUSX", None, ("John Hancock Investment Grade Bond Fund",), None),
    ("JACJX", None, ("John Hancock Mid Cap Growth Fund",), None),
    ("JHAAX", None, ("John Hancock Multi-Asset Absolute Return Fund",), None),
    ("JYEBX", None, ("John Hancock Real Estate Securities Fund",), None),
    ("FRBAX", None, ("John Hancock Regional Bank Fund",), None),
    ("JCCAX", None, ("John Hancock Small Cap Core Fund",), None),
    ("JSJAX", None, ("John Hancock Small Cap Dynamic Growth Fund",), None),
    ("JSGAX", None, ("John Hancock U.S. Growth Fund",), None),
    ("JLAAX", None, ("John Hancock Multimanager 2010 Lifetime Portfolio",), None),
    ("JLBAX", None, ("John Hancock Multimanager 2015 Lifetime Portfolio",), None),
    ("JLDAX", None, ("John Hancock Multimanager 2020 Lifetime Portfolio",), None),
    ("JLEAX", None, ("John Hancock Multimanager 2025 Lifetime Portfolio",), None),
    ("JLFAX", None, ("John Hancock Multimanager 2030 Lifetime Portfolio",), None),
    ("JLHAX", None, ("John Hancock Multimanager 2035 Lifetime Portfolio",), None),
    ("JLIAX", None, ("John Hancock Multimanager 2040 Lifetime Portfolio",), None),
    ("JLJAX", None, ("John Hancock Multimanager 2045 Lifetime Portfolio",), None),
    ("JLKAX", None, ("John Hancock Multimanager 2050 Lifetime Portfolio",), None),
    ("JLKLX", None, ("John Hancock Multimanager 2055 Lifetime Portfolio",), None),
    ("JJERX", None, ("John Hancock Multimanager 2060 Lifetime Portfolio",), None),
    ("JAAWX", None, ("John Hancock Multimanager 2065 Lifetime Portfolio",), None),
    ("JHOQX", None, ("John Hancock Multimanager 2070 Lifetime Portfolio",), None),
    ("JALAX", None, ("John Hancock Multimanager Lifestyle Aggressive Portfolio",), None),
    ("JALBX", None, ("John Hancock Multimanager Lifestyle Balanced Portfolio",), None),
    ("JALRX", None, ("John Hancock Multimanager Lifestyle Conservative Portfolio",), None),
    ("JALGX", None, ("John Hancock Multimanager Lifestyle Growth Portfolio",), None),
    ("JALMX", None, ("John Hancock Multimanager Lifestyle Moderate Portfolio",), None),
    ("JHAC", None, ("John Hancock Fundamental All Cap Core ETF",), None),
    ("JHHY", None, ("John Hancock High Yield ETF",), None),
)
