"""Impax / Pax official distribution adapter.

Hero-package densify for the 22 in-book tickered shells plus the four
already-healthy identities. Live hub HTML mixes CUSIP / TA-fund-number /
IRA-copy tables with the paid book — seed must not re-upsert those as
name-only junk. Never invent amounts or NAVs. No tickers beyond the
in-book allowlist.
"""

from __future__ import annotations

import re
from dataclasses import replace

from app.sources.base import FetchResult
from app.sources.html_source import HtmlTableSource, PageSpec
from app.sources.parser import NormalizedRecord

# 4 healthy live identities + 22 tickered shells left after junk cleanup.
# High Yield (PAXHX / PXHIX / PXHAX) is printed on the issuer hub but is
# not in this in-book slice — do not add it.
IMPAX_IN_BOOK_TICKERS = frozenset(
    {
        "PAXLX",
        "PXLIX",
        "PXSCX",
        "PGINX",
        "BLDX",
        "IGSIX",
        "IGSLX",
        "PAXBX",
        "PAXDX",
        "PAXGX",
        "PAXIX",
        "PAXWX",
        "PGRNX",
        "PWGIX",
        "PXBIX",
        "PXDIX",
        "PXEAX",
        "PXGAX",
        "PXGOX",
        "PXINX",
        "PXNIX",
        "PXSAX",
        "PXSIX",
        "PXWEX",
        "PXWGX",
        "PXWIX",
    }
)

# December 2025 YE table printed CUSIP in the ticker column for Allocation.
# Same issuer page prints PAXWX / PAXIX on every other table — recover, do
# not invent a new identity.
IMPAX_CUSIP_AS_TICKER = {
    "704223106": "PAXWX",
    "704223205": "PAXIX",
}

_NUMERIC_ID_RE = re.compile(r"^\d{3,}$")
_CUSIP_AS_TICKER_RE = re.compile(r"^[0-9][0-9A-Z]{7,8}$")
_IRA_JUNK_RE = re.compile(
    r"ira(?:\s+contribution)?|contribution[\s_-]*limit|contributionlimit",
    re.I,
)


def is_impax_junk_identity(
    ticker: str | None,
    fund_name: str | None,
    fund_identifier: str | None = None,
) -> bool:
    """True for numeric ids, CUSIP-as-ticker, and IRA contribution-limit slugs."""
    blob = " ".join(part for part in (ticker, fund_name, fund_identifier) if part)
    if _IRA_JUNK_RE.search(blob):
        return True
    token = (ticker or "").strip().upper()
    if token and _NUMERIC_ID_RE.fullmatch(token):
        return True
    if token and _CUSIP_AS_TICKER_RE.fullmatch(token):
        return True
    ident = (fund_identifier or "").strip().lower()
    if ident and (_NUMERIC_ID_RE.fullmatch(ident) or _CUSIP_AS_TICKER_RE.fullmatch(ident.upper())):
        return True
    name = (fund_name or "").strip()
    if name and _NUMERIC_ID_RE.fullmatch(name):
        return True
    return False


def recover_impax_ticker(ticker: str | None, fund_name: str | None) -> str | None:
    """Map issuer-printed CUSIP / Allocation name back onto the listed ticker."""
    token = (ticker or "").strip().upper()
    if token in IMPAX_IN_BOOK_TICKERS:
        return token
    mapped = IMPAX_CUSIP_AS_TICKER.get(token)
    if mapped:
        return mapped
    name = (fund_name or "").lower()
    if "sustainable allocation" in name:
        if "institutional" in name:
            return "PAXIX"
        if "investor" in name:
            return "PAXWX"
    return None


def sanitize_impax_records(records: list[NormalizedRecord]) -> list[NormalizedRecord]:
    """Keep in-book Impax tickers only. Recover CUSIP-as-ticker; drop junk."""
    kept: list[NormalizedRecord] = []
    for record in records:
        token = (record.ticker or "").strip().upper()
        recovered = recover_impax_ticker(token or None, record.fund_name)
        if recovered is None or recovered not in IMPAX_IN_BOOK_TICKERS:
            continue
        if is_impax_junk_identity(token, record.fund_name) and recovered not in IMPAX_IN_BOOK_TICKERS:
            continue
        # Recovered from CUSIP: keep the printed CUSIP on the record.
        cusip = record.cusip
        if token and _CUSIP_AS_TICKER_RE.fullmatch(token):
            cusip = token
        if recovered != record.ticker or cusip != record.cusip:
            record = replace(record, ticker=recovered, cusip=cusip)
        kept.append(record)
    return kept


class ImpaxSource(HtmlTableSource):
    slug = "impax"
    display_name = "Impax / Pax"
    aum_rank = 80
    priority = 80
    notes = (
        "Hub: https://impaxam.com/customer-service/distributions/ "
        "Hero-package gap fill (verified 2026-09-13) transcribes the public "
        "paid book for the 22 in-book tickered shells plus the four already-"
        "healthy identities (PAXLX / PXLIX / PXSCX / PGINX). "
        "December 2025 YE: Large Cap PAXLX / PXLIX LT $3.19835; "
        "Small Cap PXSCX / PXSIX / PXSAX ST $0.18529 / LT $0.99442; "
        "GEM PGRNX / PGINX / PXEAX ST $0.00116 / LT $4.82181; "
        "Global Opportunities PAXGX / PXGOX LT $1.11926; "
        "Allocation PAXWX / PAXIX ST $0.37824 / LT $1.59892 "
        "(issuer printed CUSIP in the ticker column — recovered to PAXWX / PAXIX). "
        "June 2026 paid: BLDX OI $0.253933 (ETF rec/ex 6/22/2026, pay 6/24/2026). "
        "High Yield PAXHX / PXHIX / PXHAX omitted (not in this in-book slice). "
        "N/A Core Bond ordinary-income cells omitted (monthly book unpublished). "
        "IGSIX / IGSLX liquidated 2026-05-01 — paid 2024–2025 only."
    )
    live_limitations = (
        "Live hub is geo/investor-type gated and mixes CUSIP / TA-fund-number "
        "/ IRA-copy tables with the paid book. Weekly walk still hits the hub; "
        "empty/403/SPA pages are no-op success. Parser drops numeric ids, "
        "CUSIP-as-ticker junk, and IRA contribution-limit slugs. Fixture "
        "transcribes the official 2021–2025 paid book plus June 2026 paid."
    )

    def pages(self) -> list[PageSpec]:
        return [
            PageSpec(
                name="2025_year_end_distributions",
                url="https://impaxam.com/customer-service/distributions/",
                fixture="2025_year_end_distributions.html",
                live=True,
                role="estimate",
                empty_ok=True,
            ),
            PageSpec(
                name="leftover_paid_history_2021_2025",
                url="https://impaxam.com/customer-service/distributions/",
                fixture="leftover_paid_history_2021_2025.html",
                live=False,
                role="history",
            ),
            PageSpec(
                name="2026_june_paid",
                url="https://impaxam.com/customer-service/distributions/",
                fixture="2026_june_paid.html",
                live=False,
                role="history",
            ),
        ]

    def _parse_pages(self, pages: list[dict], extra_notes: list[str]) -> FetchResult:
        result = super()._parse_pages(pages, extra_notes)
        before = len(result.records)
        cleaned = sanitize_impax_records(result.records)
        notes = list(result.notes)
        notes.append(
            f"impax ticker gate: kept {len(cleaned)} of {before} "
            f"(in-book allowlist; CUSIP/numeric/IRA junk dropped)"
        )
        return FetchResult(
            records=cleaned,
            source_urls=result.source_urls,
            notes=notes,
        )
