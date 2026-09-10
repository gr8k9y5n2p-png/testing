"""ICI Primary Layout ingest (CSV / named-column subset).

Source preference (Eric): when a family publishes filled ICI Primary Layout
files, those are the first-choice historical + ongoing book. PDF/HTML
archives are the fallback. Blank ICI templates on ici.org are not a feed.

Official ICI columns used here (see https://www.ici.org/year-end-tax-reporting):
1 fund name, 2 CUSIP, 3 ticker, 7 record / record date / date of record, 8 ex, 9 payable,
14 income dividends, 15 short-term capital gain, 22 total capital gain (1099 Box 2a / LT).
Fidelity midyear FIIS_SP52_DPL6 and Conestoga 2026 estimate HTML are not filled ICI files.

Vanguard publishes filled Primary Layout PDFs on the advisor tax center
(`/content/dam/fas/pdfs/ICI*_Primary*` and `ICIprimary_*.pdf`). Live PDFs are
not HTML-parsed; fixtures are December year-end rows transcribed from those
files so quarterly lines are not stored on one as_of (illustration sums).
"""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal

from app.models import AmountUnit, EstimateType, PublicationStage
from app.sources.parser import (
    NormalizedRecord,
    _parse_mdy,
    is_excluded_product,
    parse_amount,
    split_fund_identity,
)

def _norm_header(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").replace("-", " ").split())


_HEADER_ALIASES: dict[str, str] = {
    _norm_header(key): role
    for key, role in {
        "fund_name": "fund",
        "security description": "fund",
        "fund": "fund",
        "cusip": "cusip",
        "ticker": "ticker",
        "ticker symbol": "ticker",
        "record_date": "record_date",
        "record date": "record_date",
        "date of record": "record_date",
        "rec date": "record_date",
        "ex_dividend_date": "ex_date",
        "ex-dividend date": "ex_date",
        "ex date": "ex_date",
        "payable_date": "payable_date",
        "payable date": "payable_date",
        "as_of": "as_of",
        "income_dividends": "income",
        "income dividends": "income",
        "short_term_capital_gain": "st",
        "short-term capital gain": "st",
        "short term capital gain": "st",
        "total_capital_gain_distribution": "lt",
        "total capital gain distribution": "lt",
        "long_term_capital_gain": "lt",
        "long-term capital gain": "lt",
        "long term capital gain": "lt",
    }.items()
}


def parse_ici_primary(
    text: str,
    *,
    source_url: str,
    fund_family: str,
    default_as_of: date | None = None,
    publication_stage: PublicationStage = PublicationStage.final,
) -> list[NormalizedRecord]:
    """Parse an ICI Primary Layout CSV (header row required)."""
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    if not reader.fieldnames:
        return []
    records: list[NormalizedRecord] = []
    for raw in reader:
        row = {_HEADER_ALIASES.get(_norm_header(k), ""): (v or "").strip() for k, v in raw.items() if k}
        fund_raw = row.get("fund") or ""
        if not fund_raw or fund_raw.upper().startswith("TOTAL"):
            continue
        fund_name, ticker, cusip, share_class = split_fund_identity(fund_raw)
        ticker = (row.get("ticker") or ticker or "").upper() or ticker
        cusip = (row.get("cusip") or cusip or "").upper() or cusip
        if not ticker:
            continue
        if is_excluded_product(fund_name, ticker):
            continue
        rec_date = _parse_mdy(row.get("record_date") or "", None)
        ex_date = _parse_mdy(row.get("ex_date") or "", rec_date.year if rec_date else None)
        payable = _parse_mdy(row.get("payable_date") or "", rec_date.year if rec_date else None)
        as_of_raw = row.get("as_of") or ""
        try:
            as_of = date.fromisoformat(as_of_raw) if as_of_raw else None
        except ValueError:
            as_of = _parse_mdy(as_of_raw, None)
        as_of = as_of or default_as_of
        amounts = (
            (row.get("income"), EstimateType.ordinary_income),
            (row.get("st"), EstimateType.short_term_capital_gains),
            (row.get("lt"), EstimateType.long_term_capital_gains),
        )
        for raw_amount, estimate_type in amounts:
            parsed = parse_amount(raw_amount or "", AmountUnit.per_share)
            if parsed is None or parsed.amount is None:
                continue
            if parsed.amount == Decimal("0"):
                continue
            records.append(
                NormalizedRecord(
                    fund_family=fund_family,
                    fund_name=fund_name,
                    ticker=ticker,
                    cusip=cusip or None,
                    share_class=share_class,
                    estimate_type=estimate_type,
                    amount=parsed.amount,
                    amount_min=parsed.amount_min,
                    amount_max=parsed.amount_max,
                    amount_unit=parsed.unit or AmountUnit.per_share,
                    record_date=rec_date,
                    ex_date=ex_date or rec_date,
                    payable_date=payable,
                    as_of=as_of,
                    publication_stage=publication_stage,
                    source_url=source_url,
                    raw_payload={
                        "layout": "ici_primary",
                        "source_url": source_url,
                        "row": raw,
                    },
                )
            )
    return records


def ici_as_of_from_name(name: str) -> date | None:
    """Year-end as_of from an ICI page/fixture name like ici_primary_2024."""
    digits = "".join(ch for ch in name if ch.isdigit())
    if len(digits) >= 4:
        try:
            year = int(digits[:4])
            if 2000 <= year <= 2099:
                return date(year, 12, 31)
        except (TypeError, ValueError):
            return None
    return None
