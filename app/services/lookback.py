"""5-year YE finals coverage digest.

Counts funds with official final/paid per-share amounts in each calendar
year 2021–2025. Missing years stay unmatched — never invent $0. Bare
percent QDI columns are excluded from the count.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AmountUnit, DistributionEstimate, PublicationStage

LOOKBACK_YEARS: tuple[int, ...] = (2021, 2022, 2023, 2024, 2025)
FINAL_STAGES = frozenset({PublicationStage.final.value, PublicationStage.paid.value})
# Dollar YE character only. percent is QDI-style characterization — skip.
PER_SHARE = AmountUnit.per_share.value


def _year_for_row(
    as_of: date | None,
    ex_date: date | None,
    payable_date: date | None = None,
) -> int | None:
    """Calendar year of a paid/final row.

    Prefer ex_date (else payable) so a multi-year table that stamped one page-level
    ``as_of`` still counts official prior years. Never invent a year.
    """
    stamp = ex_date or payable_date or as_of
    if stamp is None:
        return None
    if stamp.year in LOOKBACK_YEARS:
        return stamp.year
    return None


def _fund_key(ticker: str | None, fund_identifier: str | None, fund_name: str | None) -> str:
    if ticker:
        return ticker.strip().upper()
    if fund_identifier:
        return fund_identifier.strip().lower()
    return (fund_name or "").strip().lower()


def _product_sleeve(ticker: str | None, fund_name: str | None) -> str:
    """Mutual-fund vs ETF sleeve for the lookback digest.

    Eric: prioritize MFs (higher tax drag). Name containing ETF wins;
    otherwise 1–4 letter alpha tickers are treated as ETFs and the rest as MFs.
    """
    name = (fund_name or "").lower()
    symbol = (ticker or "").strip().upper()
    if "etf" in name:
        return "etf"
    if symbol and symbol.isalpha() and len(symbol) <= 4:
        return "etf"
    return "mf"


def _is_ye_final_amount(stage: str | None, unit: str | None, amount: Decimal | None) -> bool:
    if stage not in FINAL_STAGES:
        return False
    if unit != PER_SHARE:
        return False
    return amount is not None


@dataclass(frozen=True)
class LookbackDigest:
    years: tuple[int, ...]
    funds_with_finals_by_year: dict[int, int]
    funds_with_finals_by_year_mf: dict[int, int]
    funds_with_finals_by_year_etf: dict[int, int]
    book_funds: int
    book_funds_mf: int
    book_funds_etf: int
    funds_with_5y: int
    funds_with_5y_mf: int
    funds_with_5y_etf: int
    pct_book_with_5y: float
    fcntx_years: list[int]
    notes: list[str]

    def as_dict(self) -> dict:
        return {
            "years": list(self.years),
            "funds_with_finals_by_year": {
                str(year): self.funds_with_finals_by_year.get(year, 0) for year in self.years
            },
            "funds_with_finals_by_year_mf": {
                str(year): self.funds_with_finals_by_year_mf.get(year, 0) for year in self.years
            },
            "funds_with_finals_by_year_etf": {
                str(year): self.funds_with_finals_by_year_etf.get(year, 0) for year in self.years
            },
            "book_funds": self.book_funds,
            "book_funds_mf": self.book_funds_mf,
            "book_funds_etf": self.book_funds_etf,
            "funds_with_5y": self.funds_with_5y,
            "funds_with_5y_mf": self.funds_with_5y_mf,
            "funds_with_5y_etf": self.funds_with_5y_etf,
            "pct_book_with_5y": self.pct_book_with_5y,
            "fcntx_years": self.fcntx_years,
            "notes": self.notes,
        }


def lookback_digest_from_rows(
    rows: Iterable[
        tuple[
            str | None,
            str | None,
            str | None,
            date | None,
            date | None,
            str | None,
            str | None,
            Decimal | None,
            date | None,
        ]
        | tuple[str | None, str | None, str | None, date | None, date | None, str | None, str | None, Decimal | None]
    ],
) -> LookbackDigest:
    """Build the digest from (ticker, ident, name, as_of, ex_date, stage, unit, amount[, payable])."""
    years_by_fund: dict[str, set[int]] = defaultdict(set)
    sleeve_by_fund: dict[str, str] = {}
    fcntx_years: set[int] = set()
    for row in rows:
        if len(row) == 9:
            ticker, ident, name, as_of, ex_date, stage, unit, amount, payable = row
        else:
            ticker, ident, name, as_of, ex_date, stage, unit, amount = row
            payable = None
        if not _is_ye_final_amount(stage, unit, amount):
            continue
        year = _year_for_row(as_of, ex_date, payable)
        if year is None:
            continue
        key = _fund_key(ticker, ident, name)
        if not key:
            continue
        years_by_fund[key].add(year)
        sleeve = _product_sleeve(ticker, name)
        prior = sleeve_by_fund.get(key)
        if prior is None or (prior == "mf" and sleeve == "etf"):
            sleeve_by_fund[key] = sleeve
        if (ticker or "").upper() == "FCNTX":
            fcntx_years.add(year)

    by_year = {year: 0 for year in LOOKBACK_YEARS}
    by_year_mf = {year: 0 for year in LOOKBACK_YEARS}
    by_year_etf = {year: 0 for year in LOOKBACK_YEARS}
    five = 0
    five_mf = 0
    five_etf = 0
    book_mf = 0
    book_etf = 0
    for key, years in years_by_fund.items():
        sleeve = sleeve_by_fund.get(key, "mf")
        if sleeve == "etf":
            book_etf += 1
        else:
            book_mf += 1
        for year in years:
            by_year[year] += 1
            if sleeve == "etf":
                by_year_etf[year] += 1
            else:
                by_year_mf[year] += 1
        if len(years) >= 5:
            five += 1
            if sleeve == "etf":
                five_etf += 1
            else:
                five_mf += 1
    book = len(years_by_fund)
    pct = round(100.0 * five / book, 1) if book else 0.0
    notes = [
        "Calendar year is ex_date, else payable_date, else as_of.",
        "Only publication_stage final/paid with amount_unit=per_share are counted.",
        "Bare percent QDI columns are excluded.",
        "Missing years stay unmatched / Undisclosed — never invented as $0.",
        "Mutual funds are prioritized over ETFs; digest splits MF vs ETF counts.",
    ]
    if set(LOOKBACK_YEARS) <= fcntx_years:
        notes.append("FCNTX has matched YE finals for 2021–2025.")
    elif fcntx_years:
        missing = [year for year in LOOKBACK_YEARS if year not in fcntx_years]
        notes.append(
            "FCNTX matched YE years: "
            + ",".join(str(year) for year in sorted(fcntx_years))
            + f"; unmatched/Undisclosed: {','.join(str(year) for year in missing)}."
        )
    else:
        notes.append("FCNTX has no YE finals in 2021–2025.")
    return LookbackDigest(
        years=LOOKBACK_YEARS,
        funds_with_finals_by_year=by_year,
        funds_with_finals_by_year_mf=by_year_mf,
        funds_with_finals_by_year_etf=by_year_etf,
        book_funds=book,
        book_funds_mf=book_mf,
        book_funds_etf=book_etf,
        funds_with_5y=five,
        funds_with_5y_mf=five_mf,
        funds_with_5y_etf=five_etf,
        pct_book_with_5y=pct,
        fcntx_years=sorted(fcntx_years),
        notes=notes,
    )


def lookback_digest(session: Session) -> LookbackDigest:
    rows = session.execute(
        select(
            DistributionEstimate.ticker,
            DistributionEstimate.fund_identifier,
            DistributionEstimate.fund_name,
            DistributionEstimate.as_of,
            DistributionEstimate.ex_date,
            DistributionEstimate.publication_stage,
            DistributionEstimate.amount_unit,
            DistributionEstimate.amount,
            DistributionEstimate.payable_date,
        )
    ).all()
    return lookback_digest_from_rows(rows)
