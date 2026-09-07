from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from html import unescape
from typing import Any

from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse as parse_datetime

from app.models import AmountUnit, EstimateType, PublicationStage


EMPTY_AMOUNT = frozenset({"", "-", "—", "–", "n/a", "na", "none", "nil", "*"})
TRADEMARK_RE = re.compile(r"[®™]|<sup>.*?</sup>", re.I)
WS_RE = re.compile(r"\s+")
FOOTNOTE_RE = re.compile(r"(?:[*†‡§]|\[\d+\]|\d+)$")
YEAR_IN_TITLE_RE = re.compile(r"\b(20\d{2})\b")
TICKER_PREFIX_RE = re.compile(
    r"^(?P<ticker>[A-Z]{2,5})\s*[—–-]\s+(?P<name>.+)$"
)
TICKER_SUFFIX_RE = re.compile(
    r"^(?P<name>.+?)\s*\(\s*(?P<ticker>[A-Z]{2,6})\s*\)\s*$"
)
FIDELITY_META_RE = re.compile(
    r"^(?P<name>.+?)\s+Symbol\s+(?P<ticker>[A-Z0-9]{2,6})\s+Cusip\s+(?P<cusip>[A-Z0-9]{8,9})\b",
    re.I,
)
SHARE_CLASS_RE = re.compile(
    r"^(?P<name>.+?)(?:\s+[-–—]\s+|\s+)(?P<cls>Admiral(?:\s+Shares)?|Investor(?:\s+Shares)?|"
    r"Institutional(?:\s+Shares)?|I Class)\s*$",
    re.I,
)
DIST_TYPE_PATTERNS: list[tuple[re.Pattern[str], EstimateType]] = [
    (re.compile(r"long[\s-]*term", re.I), EstimateType.long_term_capital_gains),
    (re.compile(r"short[\s-]*term", re.I), EstimateType.short_term_capital_gains),
    (re.compile(r"return of capital|\broc\b", re.I), EstimateType.return_of_capital),
    (re.compile(r"capital gain", re.I), EstimateType.total_capital_gains),
    (re.compile(r"income|dividend|ordinary", re.I), EstimateType.ordinary_income),
]
RANGE_RE = re.compile(
    r"(?P<lt>less\s+than|<|≤)?\s*"
    r"(?P<a>\$?)(?P<low>\d+(?:\.\d+)?)\s*(?P<pct1>%?)"
    r"(?:\s*(?:–|-|—|to)\s*(?P<b>\$?)(?P<high>\d+(?:\.\d+)?)\s*(?P<pct2>%?))?",
    re.I,
)
SECTION_RE = re.compile(
    r"^(exchange[- ]traded|american funds|public[- ]private|portfolio series|"
    r"target date|retirement income)",
    re.I,
)


@dataclass
class ParsedAmount:
    amount: Decimal | None
    amount_min: Decimal | None
    amount_max: Decimal | None
    unit: AmountUnit | None


@dataclass
class ColSpec:
    role: str  # fund, ex_date, record_date, payable_date, amount
    estimate_type: EstimateType | None = None
    unit_hint: AmountUnit | None = None


@dataclass
class NormalizedRecord:
    fund_family: str
    fund_name: str
    ticker: str | None
    cusip: str | None
    share_class: str | None
    estimate_type: EstimateType
    amount: Decimal | None
    amount_min: Decimal | None
    amount_max: Decimal | None
    amount_unit: AmountUnit
    record_date: date | None
    ex_date: date | None
    payable_date: date | None
    as_of: date | None
    publication_stage: PublicationStage | None
    source_url: str | None
    raw_payload: dict[str, Any] = field(default_factory=dict)


def clean_text(value: str | None, *, strip_footnotes: bool = False) -> str:
    if not value:
        return ""
    text = unescape(value).replace("\xa0", " ").replace("\u200b", "")
    text = TRADEMARK_RE.sub("", text)
    text = re.sub(r"\b(?:TM|SM)\b", "", text, flags=re.I)
    text = WS_RE.sub(" ", text).strip()
    if strip_footnotes:
        text = FOOTNOTE_RE.sub("", text).strip()
    return text


def cell_text(el: Tag | None) -> str:
    if el is None:
        return ""
    return clean_text(el.get_text(" ", strip=True))


def split_fund_and_ticker(raw_name: str) -> tuple[str, str | None]:
    name, ticker, _cusip, _cls = split_fund_identity(raw_name)
    return name, ticker


def split_fund_identity(raw_name: str) -> tuple[str, str | None, str | None, str | None]:
    """Return (fund_name, ticker, cusip, share_class) parsed from a fund-name cell."""
    name = clean_text(raw_name, strip_footnotes=True)
    cusip: str | None = None
    ticker: str | None = None
    share_class: str | None = None

    fid = FIDELITY_META_RE.search(name)
    if fid:
        name = clean_text(fid.group("name"), strip_footnotes=True)
        ticker = fid.group("ticker").upper()
        cusip = fid.group("cusip").upper()
    else:
        match = TICKER_PREFIX_RE.match(name)
        if match:
            ticker = match.group("ticker").upper()
            name = clean_text(match.group("name"), strip_footnotes=True)
        else:
            suffix = TICKER_SUFFIX_RE.match(name)
            if suffix:
                ticker = suffix.group("ticker").upper()
                name = clean_text(suffix.group("name"), strip_footnotes=True)

    class_match = SHARE_CLASS_RE.match(name)
    if class_match:
        share_class = re.sub(r"\s+shares$", "", class_match.group("cls"), flags=re.I).strip()
        # Keep the class in the display name (Vanguard "Admiral Shares" is part of the marketed name).
    return name, ticker, cusip, share_class


def classify_distribution_type(text: str) -> EstimateType | None:
    raw = clean_text(text)
    if not raw:
        return None
    for pattern, estimate_type in DIST_TYPE_PATTERNS:
        if pattern.search(raw):
            return estimate_type
    return EstimateType.other


def parse_amount(text: str, unit_hint: AmountUnit | None = None) -> ParsedAmount | None:
    raw = clean_text(text).lower().replace(",", "")
    if raw in EMPTY_AMOUNT:
        return None
    if raw in {"none expected", "not expected", "no distribution"}:
        return None

    unit = unit_hint
    if "%" in raw or (unit_hint in {AmountUnit.percent, AmountUnit.percent_of_nav}):
        unit = unit or AmountUnit.percent_of_nav
    elif "$" in raw:
        unit = unit or AmountUnit.per_share
    else:
        unit = unit or AmountUnit.per_share

    less_than = bool(re.match(r"^(less\s+than|<|≤)", raw, re.I))
    match = RANGE_RE.search(raw.replace("less than", "<"))
    if not match:
        return None
    try:
        low = Decimal(match.group("low"))
    except (InvalidOperation, TypeError):
        return None
    high_s = match.group("high")
    high = Decimal(high_s) if high_s else None

    if less_than and high is None:
        return ParsedAmount(amount=None, amount_min=Decimal("0"), amount_max=low, unit=unit)
    if high is not None:
        mid = (low + high) / Decimal("2")
        return ParsedAmount(amount=mid, amount_min=low, amount_max=high, unit=unit)
    return ParsedAmount(amount=low, amount_min=None, amount_max=None, unit=unit)


def _parse_mdy(text: str, default_year: int | None) -> date | None:
    raw = clean_text(text)
    if not raw or raw.lower() in EMPTY_AMOUNT:
        return None
    parts = re.split(r"[/-]", raw)
    if len(parts) < 2:
        try:
            return parse_datetime(raw, yearfirst=False, dayfirst=False).date()
        except (ValueError, OverflowError, TypeError):
            return None
    try:
        month = int(parts[0])
        day = int(parts[1])
        if len(parts) >= 3 and parts[2]:
            year = int(parts[2])
            if year < 100:
                year += 2000
        elif default_year:
            year = default_year
        else:
            return None
        return date(year, month, day)
    except ValueError:
        return None


def parse_as_of(soup: BeautifulSoup) -> date | None:
    meta = soup.find("meta", attrs={"name": "date"})
    if meta and meta.get("content"):
        content = str(meta["content"]).strip()
        # Capital Group AEM uses DD-MM-YYYY HH:MM (e.g. 08-07-2026, 22-01-2026).
        for fmt in ("%d-%m-%Y %H:%M", "%d-%m-%Y", "%Y-%m-%d", "%m-%d-%Y"):
            try:
                return datetime.strptime(content[:16].strip(), fmt).date()
            except ValueError:
                continue
        try:
            return parse_datetime(content, dayfirst=True).date()
        except (ValueError, OverflowError, TypeError):
            pass
    return None


def infer_year(soup: BeautifulSoup, as_of: date | None) -> int | None:
    title = cell_text(soup.find("title")) or cell_text(soup.find("h1"))
    match = YEAR_IN_TITLE_RE.search(title)
    if match:
        return int(match.group(1))
    if as_of:
        return as_of.year
    return None


def infer_stage(soup: BeautifulSoup) -> PublicationStage | None:
    title = (cell_text(soup.find("title")) + " " + cell_text(soup.find("h1"))).lower()
    if "preliminary" in title:
        return PublicationStage.preliminary_estimate
    if "updated estimate" in title or ("estimate" in title and "updated" in title):
        return PublicationStage.updated_estimate
    if "estimate" in title:
        return PublicationStage.preliminary_estimate
    if "midyear" in title:
        return PublicationStage.paid
    if "year-end" in title or "distribution" in title:
        return PublicationStage.final
    return None


def _normalize_header(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def classify_header(text: str, table_title: str) -> ColSpec | None:
    h = _normalize_header(text)
    if not h:
        return None
    title = table_title.lower()
    if h in {"fund", "fund name", "name"}:
        return ColSpec("fund")
    if h in {"ticker", "symbol", "ticker symbol"}:
        return ColSpec("ticker")
    if h in {"cusip"}:
        return ColSpec("cusip")
    if h in {"distribution type", "type", "dist type"}:
        return ColSpec("dist_type")
    if h.startswith("as of"):
        return ColSpec("as_of")
    if "ex date" in h or "ex dividend" in h or h in {"ex", "exdividend date"}:
        return ColSpec("ex_date")
    if "record date" in h or h == "record":
        return ColSpec("record_date")
    if any(k in h for k in ("payment date", "payable", "reinvest", "pay date")):
        return ColSpec("payable_date")
    if "long term" in h:
        unit = AmountUnit.percent_of_nav if "%" in h or "percent" in h or "nav" in h else AmountUnit.per_share
        return ColSpec("amount", EstimateType.long_term_capital_gains, unit)
    if "short term" in h and "qualified" in h:
        return ColSpec("amount", EstimateType.qualified_short_term_gains, AmountUnit.percent)
    if "short term" in h:
        unit = AmountUnit.percent_of_nav if "%" in h or "percent" in h or "nav" in h else AmountUnit.per_share
        return ColSpec("amount", EstimateType.short_term_capital_gains, unit)
    if "qualified dividend" in h:
        return ColSpec("amount", EstimateType.qualified_dividend, AmountUnit.percent)
    if "special dividend" in h:
        return ColSpec("amount", EstimateType.special_dividend, AmountUnit.per_share)
    if "return of capital" in h or h in {"roc"}:
        unit = AmountUnit.percent_of_nav if "%" in h or "nav" in h else AmountUnit.per_share
        return ColSpec("amount", EstimateType.return_of_capital, unit)
    if "income" in h and ("dividend" in h or "ordinary" in h):
        unit = AmountUnit.percent_of_nav if "%" in h or "nav" in h or "percent" in h else AmountUnit.per_share
        return ColSpec("amount", EstimateType.ordinary_income, unit)
    if h == "income":
        return ColSpec("amount", EstimateType.ordinary_income, AmountUnit.per_share)
    if "of nav" in h or h in {"pct nav", "percent nav"}:
        return ColSpec("amount", EstimateType.total_capital_gains, AmountUnit.percent_of_nav)
    if h in {"nav", "nav price", "price", "nav share"}:
        return None
    if "capital gain" in h or ("nav" in h and "gain" in h):
        unit = AmountUnit.percent_of_nav if "%" in h or "nav" in h or "percent" in h else AmountUnit.per_share
        return ColSpec("amount", EstimateType.total_capital_gains, unit)
    if ("total" in h and "share" in h) or "per share" in h or h in {"amount", "distribution"}:
        if "special" in title:
            return ColSpec("amount", EstimateType.special_dividend, AmountUnit.per_share)
        if "qualified" in title:
            return ColSpec("amount", EstimateType.qualified_dividend, AmountUnit.percent)
        if "income" in title:
            return ColSpec("amount", EstimateType.ordinary_income, AmountUnit.per_share)
        return ColSpec("amount", EstimateType.total, AmountUnit.per_share)
    return None


def _row_cells(row: Tag) -> list[Tag]:
    return [c for c in row.find_all(["th", "td"], recursive=False)]


def _is_section_row(cells: list[Tag], texts: list[str]) -> bool:
    if not texts:
        return True
    nonempty = [t for t in texts if t]
    if not nonempty:
        return True
    if cells and cells[0].has_attr("colspan") and int(cells[0].get("colspan", 1)) >= 3:
        return True
    if len(nonempty) == 1 and SECTION_RE.search(nonempty[0]):
        return True
    return False


_HEADER_HINTS = (
    "ex date",
    "record",
    "payment",
    "pay date",
    "long term",
    "short term",
    "per share",
    "nav",
    "qualified",
    "capital gain",
    "amount",
    "ticker",
    "symbol",
    "as of",
    "distribution type",
)


def _is_header_row(texts: list[str]) -> bool:
    if not texts:
        return False
    first = _normalize_header(texts[0])
    rest = " ".join(_normalize_header(t) for t in texts[1:])
    if first in {"fund", "fund name", "name", "ticker", "symbol", "ticker symbol"}:
        return any(k in rest or k in first for k in _HEADER_HINTS)
    return False


def _is_split_header_start(texts: list[str]) -> bool:
    """T. Rowe style: category | Ticker Symbol | Per Share Amounts (amounts on the next row)."""
    joined = " ".join(_normalize_header(t) for t in texts)
    return "ticker" in joined and "per share" in joined and "income" not in joined and "short term" not in joined


def _is_split_header_continue(texts: list[str]) -> bool:
    joined = " ".join(_normalize_header(t) for t in texts)
    return (
        ("income" in joined or "short term" in joined or "long term" in joined)
        and "ticker" not in joined
        and "fund name" not in joined
    )


def parse_distribution_html(
    html: str,
    *,
    source_url: str,
    fund_family: str = "American Funds",
) -> list[NormalizedRecord]:
    soup = BeautifulSoup(html, "lxml")
    page_as_of = parse_as_of(soup)
    default_year = infer_year(soup, page_as_of)
    stage = infer_stage(soup)
    page_title = cell_text(soup.find("title")) or cell_text(soup.find("h1"))

    records: list[NormalizedRecord] = []
    column_map: dict[int, ColSpec] = {}
    table_title = page_title
    pending_split_header = False

    for table in soup.find_all("table"):
        caption = table.find("caption")
        heading = None
        first_row = table.find("tr")
        if first_row:
            first_texts = [cell_text(c) for c in _row_cells(first_row)]
            if first_texts and not _is_header_row(first_texts) and not _is_split_header_start(first_texts):
                heading = first_texts[0]
        if caption:
            table_title = cell_text(caption)
        elif heading:
            table_title = heading

        pending_split_header = False
        for row in table.find_all("tr"):
            cells = _row_cells(row)
            texts = [cell_text(c) for c in cells]
            if _is_split_header_start(texts):
                pending_split_header = True
                continue
            if pending_split_header and _is_split_header_continue(texts):
                local_map: dict[int, ColSpec] = {
                    0: ColSpec("fund"),
                    1: ColSpec("ticker"),
                }
                amount_idx = 2
                for text in texts:
                    spec = classify_header(text, table_title)
                    if spec and spec.role == "amount":
                        local_map[amount_idx] = spec
                        amount_idx += 1
                if local_map:
                    column_map = local_map
                pending_split_header = False
                continue
            if _is_header_row(texts):
                local_map = {}
                for idx, text in enumerate(texts):
                    spec = classify_header(text, table_title)
                    if spec:
                        local_map[idx] = spec
                if local_map:
                    column_map = local_map
                pending_split_header = False
                continue
            if not column_map:
                continue
            if _is_section_row(cells, texts):
                continue

            values: dict[str, Any] = {"amounts": []}
            for idx, spec in column_map.items():
                text = texts[idx] if idx < len(texts) else ""
                if spec.role == "fund":
                    values["fund"] = text
                elif spec.role in {"ex_date", "record_date", "payable_date", "as_of", "ticker", "cusip", "dist_type"}:
                    values[spec.role] = text
                elif spec.role == "amount":
                    values["amounts"].append((text, spec))

            raw_fund = values.get("fund") or (texts[0] if texts else "")
            fund_name, ticker, cusip, share_class = split_fund_identity(raw_fund)
            if values.get("ticker"):
                ticker = clean_text(values["ticker"]).upper() or ticker
            if values.get("cusip"):
                cusip = clean_text(values["cusip"]).upper() or cusip
            if not fund_name:
                continue

            rec_date = _parse_mdy(values.get("record_date", ""), default_year)
            ex_date = _parse_mdy(values.get("ex_date", ""), default_year)
            payable = _parse_mdy(values.get("payable_date", ""), default_year)
            row_as_of = _parse_mdy(values.get("as_of", ""), default_year) or page_as_of
            if rec_date and payable and payable < rec_date and payable.month == 1:
                payable = date(rec_date.year + 1, payable.month, payable.day)
            if rec_date and ex_date is None:
                ex_date = rec_date

            dist_type = classify_distribution_type(values["dist_type"]) if values.get("dist_type") else None

            for amount_text, spec in values["amounts"]:
                parsed = parse_amount(amount_text, spec.unit_hint)
                if parsed is None:
                    continue
                unit = parsed.unit or spec.unit_hint or AmountUnit.per_share
                estimate_type = spec.estimate_type or EstimateType.other
                if dist_type is not None:
                    estimate_type = dist_type
                if spec.estimate_type == EstimateType.qualified_dividend:
                    unit = AmountUnit.percent
                records.append(
                    NormalizedRecord(
                        fund_family=fund_family,
                        fund_name=fund_name,
                        ticker=ticker,
                        cusip=cusip,
                        share_class=share_class,
                        estimate_type=estimate_type,
                        amount=parsed.amount,
                        amount_min=parsed.amount_min,
                        amount_max=parsed.amount_max,
                        amount_unit=unit,
                        record_date=rec_date,
                        ex_date=ex_date,
                        payable_date=payable,
                        as_of=row_as_of,
                        publication_stage=stage,
                        source_url=source_url,
                        raw_payload={
                            "page_title": page_title,
                            "table_title": table_title,
                            "row_text": texts,
                            "source_url": source_url,
                        },
                    )
                )
    return records


def parse_capital_group_html(
    html: str,
    *,
    source_url: str,
    fund_family: str = "American Funds",
) -> list[NormalizedRecord]:
    return parse_distribution_html(html, source_url=source_url, fund_family=fund_family)
