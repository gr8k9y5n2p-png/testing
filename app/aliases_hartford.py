"""Hartford Class A ticker aliases for name-keyed capital-gains PDFs.

HFMCX / HAIAX / IHGIX already parse from flagship rows. Remaining names stay
slug-keyed. Unconfirmed Schroders / allocation Class A pages left unmapped.

Sources: hartfordfunds.com Class A product pages
(ITHAX, HQIAX, HBLAX, HGOAX, IHOAX, HEOMX, HDBAX, …).
"""

from __future__ import annotations

HARTFORD_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    ("HEOMX", None, ("Hartford Climate Opportunities Fund",), None),
    ("HDBAX", None, ("Hartford Dynamic Bond Fund",), None),
    ("SCUVX", None, ("Hartford Schroders US Small Cap Opportunities Fund",), None),
    ("HBLAX", None, ("The Hartford Balanced Income Fund",), None),
    ("ITHAX", None, ("The Hartford Capital Appreciation Fund",), None),
    ("HCKAX", None, ("The Hartford Checks and Balances Fund",), None),
    ("HQIAX", None, ("The Hartford Equity Income Fund",), None),
    ("HGOAX", None, ("The Hartford Growth Opportunities Fund",), None),
    ("IHOAX", None, ("The Hartford International Opportunities Fund",), None),
    ("HMVAX", None, ("The Hartford MidCap Value Fund",), None),
    ("HSLAX", None, ("The Hartford Small Cap Growth Fund",), None),
    ("HERAX", None, ("Hartford Emerging Markets Equity Fund",), None),
    ("HDVAX", None, ("Hartford International Equity Fund",), None),
    ("HSMAX", None, ("Hartford Small Cap Value Fund",), None),
    ("HBAAX", None, ("Hartford Moderate Allocation Fund",), None),
    ("HGHAX", None, ("The Hartford Healthcare Fund",), None),
    ("HNCAX", None, ("The Hartford International Growth Fund",), None),
    ("HILAX", None, ("The Hartford International Value Fund",), None),
)
