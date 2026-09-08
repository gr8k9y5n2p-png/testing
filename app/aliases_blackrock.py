"""BlackRock / iShares open-end Investor A (or fixture share-class) ticker aliases.

Official open-end tax HTML is name + share class with no ticker. Rows stay
name-slug keyed (``blackrock-equity-dividend-fund``). Investor A is the
display ticker when the book listed Investor A; Institutional / Composite
tickers are used only when that is the class already in the fixtures.

iShares ETFs already publish tickers on the capital-gains HTML — do not
override those. CUSIPs are included only when confirmed on a BlackRock
product page or fact sheet.

Sources: BlackRock product pages / Investor A fact sheets (e.g. MDDVX, LIRAX,
BMSAX, BACAX, MDGCX, BARDX) and the LifePath Funds III 497 / product pages
(LPRAX / LPYAX / LELAX / LEVAX / LEWAX / LEYAX). LifePath Index 2025 Investor A
LILAX is the pre-merger Class A symbol (Form 8937, Oct 2024).

Left unmapped on purpose: Institutional/K-only books (China A Opportunities
CHILX/CHKLX; Enhanced Roll Yield BERYX), HPS Credit Strategies interval
(CREDX), Composite / GA / Defensive / Sustainable / Impact series without a
confirmed Investor A page, and iShares FTSE NAREIT / U.S. Securitized Bond
index classes that are not Investor A on the public product page.
"""

from __future__ import annotations

# (ticker, fund_identifier or None, names, cusip or None)
# None identifier → slugify(names[0]) so upsert keys stay name-keyed.
BLACKROCK_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    # LifePath Index Investor A — blackrock.com product pages / fact sheets
    ("LIRAX", None, ("BlackRock LifePath Index Retirement Fund",), "066923608"),
    ("LILAX", None, ("BlackRock LifePath Index 2025 Fund",), "066923855"),
    ("LINAX", None, ("BlackRock LifePath Index 2030 Fund",), "066923822"),
    ("LIJAX", None, ("BlackRock LifePath Index 2035 Fund",), "066923780"),
    ("LIKAX", None, ("BlackRock LifePath Index 2040 Fund",), "066923756"),
    ("LIHAX", None, ("BlackRock LifePath Index 2045 Fund",), "066923723"),
    ("LIPAX", None, ("BlackRock LifePath Index 2050 Fund",), "066923681"),
    ("LIVAX", None, ("BlackRock LifePath Index 2055 Fund",), "066923657"),
    ("LIZAX", None, ("BlackRock LifePath Index 2060 Fund",), "066923475"),
    ("LIWAX", None, ("BlackRock LifePath Index 2065 Fund",), "066923186"),
    ("LIYAX", None, ("BlackRock LifePath Index 2070 Fund",), "09260W493"),
    # LifePath Dynamic Investor A — Dynamic Investor prospectus + product pages
    ("LPRAX", None, ("BlackRock LifePath Dynamic Retirement Fund",), "066922709"),
    ("LPBAX", None, ("BlackRock LifePath Dynamic 2025 Fund",), None),
    ("LPRDX", None, ("BlackRock LifePath Dynamic 2030 Fund",), None),
    ("LPJAX", None, ("BlackRock LifePath Dynamic 2035 Fund",), "066922295"),
    ("LPREX", None, ("BlackRock LifePath Dynamic 2040 Fund",), "066922824"),
    ("LPHAX", None, ("BlackRock LifePath Dynamic 2045 Fund",), None),
    ("LPRFX", None, ("BlackRock LifePath Dynamic 2050 Fund",), None),
    ("LPVAX", None, ("BlackRock LifePath Dynamic 2055 Fund",), None),
    ("LPDAX", None, ("BlackRock LifePath Dynamic 2060 Fund",), None),
    ("LPWAX", None, ("BlackRock LifePath Dynamic 2065 Fund",), None),
    ("LPYAX", None, ("BlackRock LifePath Dynamic 2070 Fund",), "09260W550"),
    # LifePath ESG Index Investor A — blackrock.com product pages / Funds III 497
    ("LERAX", None, ("BlackRock LifePath ESG Index Retirement Fund",), "09260W600"),
    ("LELAX", None, ("BlackRock LifePath ESG Index 2025 Fund",), None),
    ("LENAX", None, ("BlackRock LifePath ESG Index 2030 Fund",), None),
    ("LEJAX", None, ("BlackRock LifePath ESG Index 2035 Fund",), "09260W824"),
    ("LEKAX", None, ("BlackRock LifePath ESG Index 2040 Fund",), "09260W782"),
    ("LEHAX", None, ("BlackRock LifePath ESG Index 2045 Fund",), "09260W758"),
    ("LEBAX", None, ("BlackRock LifePath ESG Index 2050 Fund",), None),
    ("LEVAX", None, ("BlackRock LifePath ESG Index 2055 Fund",), "09260W683"),
    ("LEZAX", None, ("BlackRock LifePath ESG Index 2060 Fund",), "09260W659"),
    ("LEWAX", None, ("BlackRock LifePath ESG Index 2065 Fund",), "09260W626"),
    ("LEYAX", None, ("BlackRock LifePath ESG Index 2070 Fund",), "09260W451"),
    # Target Allocation Investor A
    ("BACPX", None, ("BlackRock 20/80 Target Allocation Fund",), "091937177"),
    ("BAMPX", None, ("BlackRock 40/60 Target Allocation Fund",), "091937151"),
    ("BAGPX", None, ("BlackRock 60/40 Target Allocation Fund",), "091937136"),
    ("BAAPX", None, ("BlackRock 80/20 Target Allocation Fund",), None),
    # Flagship open-end Investor A
    ("MDDVX", None, ("BlackRock Equity Dividend Fund",), "09251M108"),
    ("MDLOX", None, ("BlackRock Global Allocation Fund", "BlackRock Global Allocation Fund, Inc."), "09251T103"),
    (
        "MDCDX",
        None,
        ("BlackRock Balanced Fund", "BlackRock Balanced Capital Fund"),
        None,
    ),
    ("BCBAX", None, ("BlackRock Core Bond Portfolio",), "09260B101"),
    ("BHYAX", None, ("BlackRock High Yield Portfolio", "BlackRock High Yield Bond Portfolio", "BlackRock High Yield Bond Fund"), None),
    ("BMSAX", None, ("BlackRock Income Fund", "BlackRock Income"), "09260B705"),
    ("BCRAX", None, ("BlackRock Advantage CoreAlpha Bond Fund",), "09260T102"),
    ("BASIX", None, ("BlackRock Strategic Income Opportunities Portfolio",), None),
    ("BAICX", None, ("BlackRock Multi-Asset Income Portfolio", "BlackRock Multi-Asset Income Fund"), None),
    ("BDHAX", None, ("BlackRock Dynamic High Income Portfolio",), None),
    ("BLDAX", None, ("BlackRock Low Duration Bond Portfolio", "BlackRock Low Duration Fund"), None),
    ("BFRAX", None, ("BlackRock Floating Rate Income Portfolio",), None),
    ("BPRAX", None, ("BlackRock Inflation Protected Bond Portfolio",), None),
    ("STSEX", None, ("BlackRock Exchange Portfolio",), None),
    ("BAMBX", None, ("BlackRock Systematic Multi-Strategy Fund",), None),
    ("MDGRX", None, ("BlackRock Natural Resources Trust",), None),
    ("BDMAX", None, ("BlackRock Global Equity Market Neutral Fund",), None),
    ("BABDX", None, ("BlackRock Global Dividend Portfolio", "BlackRock Global Dividend Fund"), None),
    ("MDFGX", None, ("BlackRock Capital Appreciation Fund",), None),
    ("SHSAX", None, ("BlackRock Health Sciences Opportunities Portfolio",), None),
    ("BGSAX", None, ("BlackRock Technology Opportunities Fund",), None),
    ("BMGAX", None, ("BlackRock Mid-Cap Growth Equity Portfolio",), None),
    ("MCFOX", None, ("BlackRock Large Cap Focus Growth Fund",), None),
    ("MDLVX", None, ("BlackRock Large Cap Focus Value Fund",), None),
    ("MALRX", None, ("BlackRock Advantage Large Cap Core Fund",), None),
    ("MALVX", None, ("BlackRock Advantage Large Cap Value Fund",), None),
    ("CMLAX", None, ("BlackRock Advantage Large Cap Growth Fund",), None),
    ("BDSAX", None, ("BlackRock Advantage Small Cap Core Fund",), None),
    ("CSGEX", None, ("BlackRock Advantage Small Cap Growth Fund",), "091928309"),
    ("MDSPX", None, ("BlackRock Advantage SMID Cap Fund",), None),
    ("BROAX", None, ("BlackRock Advantage International Fund",), None),
    ("BLSAX", None, ("BlackRock Advantage Emerging Markets Fund", "BlackRock Advantage Emerging Market Fund"), None),
    (
        "MDGCX",
        None,
        (
            "BlackRock Advantage Global Fund",
            "BlackRock Advantage Global Fund, Inc.",
            "BlackRock Advantage Global",
        ),
        "09252A103",
    ),
    ("MDILX", None, ("BlackRock International Fund",), None),
    (
        "MDDCX",
        None,
        ("BlackRock Emerging Markets Fund", "BlackRock Emerging Markets Fund, Inc."),
        None,
    ),
    ("MDEFX", None, ("BlackRock EuroFund",), None),
    ("BALPX", None, ("BlackRock Event Driven Equity Fund",), None),
    ("BACAX", None, ("BlackRock Energy Opportunities Fund",), "091937334"),
    ("BAREX", None, ("BlackRock Real Estate Securities Fund",), None),
    ("MDHQX", None, ("BlackRock Total Return Fund",), None),
    (
        "BGPAX",
        None,
        (
            "BlackRock GNMA Portfolio",
            # 2025 tax HTML rename of the same Investor A class (later ETF conversion).
            "BlackRock Mortgage-Backed Securities Fund",
        ),
        None,
    ),
    ("MDNLX", None, ("BlackRock National Municipal Fund",), None),
    ("MDHYX", None, ("BlackRock High Yield Municipal Fund",), None),
    ("MDLTX", None, ("BlackRock Latin America Fund, Inc.",), None),
    ("MDEHX", None, ("BlackRock Long-Horizon Equity Fund",), None),
    ("PCBAX", None, ("BlackRock Tactical Opportunities Fund",), None),
    ("BSTAX", None, ("BlackRock Total Factor Fund",), None),
    ("MDRFX", None, ("BlackRock Mid Cap Value Fund",), "09255V104"),
    ("BMPAX", None, ("BlackRock U.S. Mortgage Portfolio",), None),
    (
        "BGCAX",
        None,
        (
            "BlackRock Global Long/Short Credit Fund",
            # Same Investor A class after the Credit Relative Value rename.
            "BlackRock Credit Relative Value Fund",
        ),
        "09260C406",
    ),
    ("BICSX", None, ("BlackRock Commodity Strategies Fund",), None),
    ("BIRAX", None, ("BlackRock Sustainable Advantage Large Cap Core Fund", "BlackRock Sustainable Aware Advantage Large Cap Core Fund"), None),
    # iShares index mutual funds (not iShares ETFs)
    ("BSPAX", None, ("iShares S&P 500 Index Fund",), "066923566"),
    ("MDIIX", None, ("iShares MSCI EAFE International Index Fund",), None),
    ("BDOAX", None, ("iShares MSCI Total International Index Fund",), None),
    ("BRGAX", None, ("iShares Russell 1000 Large-Cap Index Fund",), None),
    ("MDSKX", None, ("iShares Russell 2000 Small-Cap Index Fund",), None),
    ("BRMAX", None, ("iShares Russell Mid-Cap Index Fund",), "09258N307"),
    ("BSMAX", None, ("iShares Russell Small/Mid-Cap Index Fund",), None),
    (
        "BASMX",
        None,
        ("iShares Total U.S. Stock Market Index Fund", "iShares Total US Stock Market Index Fund"),
        "091936179",
    ),
    ("BARDX", None, ("iShares Developed Real Estate Index Fund",), "091936211"),
    ("BMAAX", None, ("iShares Municipal Bond Index Fund",), None),
    ("BATAX", None, ("iShares Short-Term TIPS Bond Index Fund",), None),
    (
        "BMOAX",
        None,
        ("iShares U.S. Aggregate Bond Index Fund", "iShares US Aggregate Bond Index Fund"),
        None,
    ),
)
