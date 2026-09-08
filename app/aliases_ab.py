"""AllianceBernstein Class A ticker aliases for name-keyed paying-fund tables.

AGRFX / APGAX / ABASX already parse. Remaining names stay slug-keyed.
Advisor-only / unconfirmed Class A pages left unmapped.

Sources: alliancebernstein.com Class A product pages
(CHCLX, CABDX, AUIAX, ADGAX, WPASX, AUUAX, SCAVX, AWAAX, CABNX).
"""

from __future__ import annotations

AB_FUND_ROWS: tuple[tuple[str, str | None, tuple[str, ...], str | None], ...] = (
    (
        "WPASX",
        None,
        ("AB Concentrated Growth Portfolio", "AB Concentrated Growth Fund"),
        None,
    ),
    (
        "ADGAX",
        None,
        ("AB Core Opportunities Fund, Inc.", "AB Core Opportunities Fund"),
        None,
    ),
    ("CHCLX", None, ("AB Discovery Growth Fund, Inc.",), None),
    (
        "AUIAX",
        None,
        ("AB Equity Income Fund, Inc.", "AB Equity Income Fund"),
        None,
    ),
    (
        "CABNX",
        None,
        ("AB Global Risk Allocation Fund, Inc.", "AB Global Risk Allocation Fund"),
        None,
    ),
    (
        "CABDX",
        None,
        ("AB Relative Value Fund, Inc.", "AB Relative Value Fund"),
        None,
    ),
    ("AUUAX", None, ("AB Select US Equity",), None),
    ("SCAVX", None, ("AB Small Cap Value Portfolio",), None),
    ("AWAAX", None, ("AB Wealth Appreciation Strategy",), None),
    ("GCEAX", None, ("AB Global Core Equity Portfolio",), None),
    ("ABVAX", None, ("AB Large Cap Value Fund",), None),
    ("ASLAX", None, ("AB Select US Long/Short Portfolio",), None),
    (
        "ALTFX",
        None,
        ("AB Sustainable Global Thematic Fund, Inc.", "AB Sustainable Global Thematic Fund"),
        None,
    ),
)
