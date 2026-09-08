"""MFS Class A ticker aliases for name-keyed tax PDFs.

The 2025 ``mfs_cg_fly.pdf`` book is % of NAV with fund + share-class labels and
no ticker column. Class A / All Classes rows stay name-slug keyed. Class B/C/I/R
rows are left unmapped (wrong share class). Product-page Class A rows that
already parse MIGHX / MFEGX / … keep those tickers (enrichment never overwrites).

Sources: MFS Class A performance book
https://www.mfs.com/content/dam/mfs-enterprise/mfscom/products/performance/perf_mfd.pdf
and Class A product pages (MRGAX, MWEFX, MAMAX, MAAGX, MIEJX, MFFSX, …).
"""

from __future__ import annotations

# (ticker, fund_identifier or None, names, cusip or None)
MFS_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    # Already ticker-keyed Class A product pages — All Classes % NAV rows only
    ("MFEGX", None, ("MFS Growth Fund All Classes",), None),
    ("MEIAX", None, ("MFS Value Fund All Classes",), None),
    ("MSFRX", None, ("MFS Total Return Fund All Classes",), None),
    ("MMUFX", None, ("MFS Utilities Fund All Classes",), None),
    ("MVCAX", None, ("MFS Mid Cap Value Fund All Classes",), None),
    ("MNDAX", None, ("MFS New Discovery Fund All Classes",), None),
    ("MGRAX", None, ("MFS International Growth Fund All Classes",), None),
    # Remaining Class A / All Classes names
    (
        "MRGAX",
        None,
        ("MFS Core Equity Fund Class A", "MFS Core Equity Fund"),
        None,
    ),
    (
        "MWEFX",
        None,
        ("MFS Global Equity Fund Class A", "MFS Global Equity Fund"),
        None,
    ),
    (
        "MWOFX",
        None,
        ("MFS Global Growth Fund Class A", "MFS Global Growth Fund"),
        None,
    ),
    (
        "MAMAX",
        None,
        ("MFS Moderate Allocation Fund Class A", "MFS Moderate Allocation Fund"),
        None,
    ),
    ("MUEAX", None, ("MFS Blended Research Core Equity Fund Class A", "MFS Blended Research Core Equity Fund"), None),
    ("BRKAX", None, ("MFS Blended Research Emerging Markets Equity Fund All Classes",), None),
    ("BRWAX", None, ("MFS Blended Research Growth Equity Fund All Classes",), None),
    ("BRXAX", None, ("MFS Blended Research International Equity Fund All Classes",), None),
    ("BMSFX", None, ("MFS Blended Research Mid Cap Equity Fund All Classes",), None),
    ("BRSDX", None, ("MFS Blended Research Small Cap Equity Fund All Classes",), None),
    ("BRUDX", None, ("MFS Blended Research Value Equity Fund All Classes",), None),
    ("MFALX", None, ("MFS Alabama Municipal Bond Fund All Classes",), None),
    ("MFARX", None, ("MFS Arkansas Municipal Bond Fund All Classes",), None),
    ("MCFTX", None, ("MFS California Municipal Bond Fund All Classes",), None),
    ("MMGAX", None, ("MFS Georgia Municipal Bond Fund All Classes",), None),
    ("MFSMX", None, ("MFS Maryland Municipal Bond Fund All Classes",), None),
    ("MFSSX", None, ("MFS Massachusetts Municipal Bond Fund All Classes",), None),
    ("MISSX", None, ("MFS Mississippi Municipal Bond Fund All Classes",), None),
    ("MSNYX", None, ("MFS New York Municipal Bond Fund All Classes",), None),
    ("MSNCX", None, ("MFS North Carolina Municipal Bond Fund All Classes",), None),
    ("MFPAX", None, ("MFS Pennsylvania Municipal Bond Fund All Classes",), None),
    ("MFSCX", None, ("MFS South Carolina Municipal Bond Fund All Classes",), None),
    ("MSVAX", None, ("MFS Virginia Municipal Bond Fund All Classes",), None),
    ("MFWVX", None, ("MFS West Virginia Municipal Bond Fund All Classes",), None),
    ("MCSAX", None, ("MFS Commodity Strategy Fund All Classes",), None),
    ("MACFX", None, ("MFS Conservative Allocation Fund All Classes",), None),
    ("MAGWX", None, ("MFS Growth Allocation Fund All Classes",), None),
    ("MAAGX", None, ("MFS Aggressive Growth Allocation Fund All Classes",), None),
    ("MCBEX", None, ("MFS Core Bond Fund All Classes",), None),
    ("MFBFX", None, ("MFS Corporate Bond Fund All Classes",), None),
    ("DIFAX", None, ("MFS Diversified Income Fund All Classes",), None),
    ("MEDAX", None, ("MFS Emerging Markets Debt Fund All Classes",), None),
    ("EMLAX", None, ("MFS Emerging Markets Debt Local Currency Fund All Classes",), None),
    ("MEMAX", None, ("MFS Emerging Markets Equity Fund All Classes",), None),
    ("EEMPX", None, ("MFS Emerging Markets Equity Research Fund All Classes",), None),
    ("EQNAX", None, ("MFS Equity Income Fund All Classes",), None),
    ("DVRAX", None, ("MFS Global Alternative Strategy Fund All Classes",), None),
    ("MHOAX", None, ("MFS Global High Yield Fund All Classes",), None),
    ("GLNAX", None, ("MFS Global New Discovery Fund All Classes",), None),
    ("MGBAX", None, ("MFS Global Opportunistic Bond Fund All Classes",), None),
    ("MGLAX", None, ("MFS Global Real Estate Fund All Classes",), None),
    ("MFWTX", None, ("MFS Global Total Return Fund All Classes",), None),
    ("MFGSX", None, ("MFS Government Securities Fund All Classes",), None),
    ("MHITX", None, ("MFS High Income Fund All Classes",), None),
    ("MFIOX", None, ("MFS Income Fund All Classes",), None),
    ("MIAAX", None, ("MFS Inflation-Adjusted Bond Fund All Classes",), None),
    ("MDIDX", None, ("MFS International Diversification Fund All Classes",), None),
    ("MIEJX", None, ("MFS International Equity Fund All Classes",), None),
    ("MKVBX", None, ("MFS International Large Cap Value Fund All Classes",), None),
    ("MIDAX", None, ("MFS International New Discovery Fund All Classes",), None),
    ("UIVVX", None, ("MFS Intrinsic Value Fund All Classes",), None),
    ("LTTAX", None, ("MFS Lifetime 2025 Fund All Classes",), None),
    ("MLTAX", None, ("MFS Lifetime 2030 Fund All Classes",), None),
    ("LFEAX", None, ("MFS Lifetime 2035 Fund All Classes",), None),
    ("MLFAX", None, ("MFS Lifetime 2040 Fund All Classes",), None),
    ("LTMAX", None, ("MFS Lifetime 2045 Fund All Classes",), None),
    ("MFFSX", None, ("MFS Lifetime 2050 Fund All Classes",), None),
    ("LFIAX", None, ("MFS Lifetime 2055 Fund All Classes",), None),
    ("MFJAX", None, ("MFS Lifetime 2060 Fund All Classes",), None),
    ("LFTFX", None, ("MFS Lifetime 2065 Fund All Classes",), None),
    ("MLLAX", None, ("MFS Lifetime Income Fund All Classes",), None),
    ("MQLFX", None, ("MFS Limited Maturity Fund All Classes",), None),
    ("MLVAX", None, ("MFS Low Volatility Equity Fund All Classes",), None),
    ("MVGAX", None, ("MFS Low Volatility Global Equity Fund All Classes",), None),
    ("MNWAX", None, ("MFS Managed Wealth Fund All Classes",), None),
    ("MMHYX", None, ("MFS Municipal High Income Fund All Classes",), None),
    ("MFIAX", None, ("MFS Municipal Income Fund All Classes",), None),
    ("MIUAX", None, ("MFS Municipal Intermediate Fund All Classes",), None),
    ("MTLFX", None, ("MFS Municipal Limited Maturity Fund All Classes",), None),
    ("NDVAX", None, ("MFS New Discovery Value Fund All Classes",), None),
    ("MRSAX", None, ("MFS Research International Fund All Classes",), None),
    ("MRBFX", None, ("MFS Total Return Bond Fund All Classes",), None),
)
