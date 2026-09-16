"""Official MFS 10-year distribution Excel (per-product download).

The product-page HTML table truncates to the latest rows. The public
``/10YearsDistribution/download`` workbook is the paid event book: one row per
Type of Earnings (Dividend / Short Term / Long Term / Return of Capital) with
record / ex / payable dates. Weekly live GETs must keep every event and type —
never drop mid-year rows or collapse them into a December YE total.
"""

from __future__ import annotations

import re
import zipfile
from datetime import date, timedelta
from io import BytesIO
from xml.etree import ElementTree as ET

from app.sources.parser import parse_distribution_html

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
_PRODUCT_RE = re.compile(r"/product/([A-Za-z0-9]+)/", re.I)
_SHARE_CODE_RE = re.compile(r"shareCode=([A-Za-z0-9]+)", re.I)

SHARE_CODE_LABELS = {
    "A": "Class A",
    "B": "Class B",
    "C": "Class C",
    "I": "Class I",
    "R1": "Class R1 shares",
    "R2": "Class R2 shares",
    "R3": "Class R3 shares",
    "R4": "Class R4 shares",
    "R6": "Class R6 shares",
}


def excel_serial_to_date(value: str | float | int) -> date | None:
    """Windows Excel 1900-date serial used by the MFS 10-year workbook."""
    raw = str(value).strip()
    if not raw:
        return None
    try:
        serial = int(float(raw))
    except ValueError:
        return None
    if serial <= 0:
        return None
    return date(1899, 12, 30) + timedelta(days=serial)


def ticker_from_excel_url(source_url: str) -> str | None:
    match = _PRODUCT_RE.search(source_url or "")
    if not match:
        return None
    return match.group(1).upper()


def share_code_from_excel_url(source_url: str) -> str | None:
    match = _SHARE_CODE_RE.search(source_url or "")
    if not match:
        return None
    return match.group(1).upper()


def ten_year_excel_url(ticker: str, share_code: str) -> str:
    code = share_code.strip()
    return (
        f"https://www.mfs.com/MFSServices/products/v1/product/{ticker.upper()}/"
        "10YearsDistribution/download?"
        f"shareCode={code}&productLineCode=WEB_FAMILYFUNDS"
        "&roleCode=usinv&locationCode=us&locale=en_US"
    )


def _shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    out: list[str] = []
    for si in root.findall("m:si", _NS):
        texts = [t.text or "" for t in si.findall(".//m:t", _NS)]
        out.append("".join(texts))
    return out


def _col_row(cell_ref: str) -> tuple[int, int]:
    col = "".join(ch for ch in cell_ref if ch.isalpha())
    row = int("".join(ch for ch in cell_ref if ch.isdigit()))
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch.upper()) - 64)
    return n, row


def _sheet_rows(data: bytes) -> list[list[str]]:
    with zipfile.ZipFile(BytesIO(data)) as zf:
        strings = _shared_strings(zf)
        sheet_name = next(
            name for name in zf.namelist() if name.startswith("xl/worksheets/sheet")
        )
        root = ET.fromstring(zf.read(sheet_name))
        by_row: dict[int, dict[int, str]] = {}
        for cell in root.findall(".//m:c", _NS):
            ref = cell.get("r")
            if not ref:
                continue
            col, row = _col_row(ref)
            value_el = cell.find("m:v", _NS)
            inline = cell.find("m:is", _NS)
            val = ""
            if cell.get("t") == "s" and value_el is not None and value_el.text:
                val = strings[int(value_el.text)]
            elif cell.get("t") == "inlineStr" and inline is not None:
                val = "".join(t.text or "" for t in inline.findall(".//m:t", _NS))
            elif value_el is not None and value_el.text:
                val = value_el.text
            by_row.setdefault(row, {})[col] = val
    if not by_row:
        return []
    max_row = max(by_row)
    max_col = max((max(cols) for cols in by_row.values() if cols), default=0)
    return [
        [by_row.get(row, {}).get(col, "") for col in range(1, max_col + 1)]
        for row in range(1, max_row + 1)
    ]


def _fmt_date(value: str) -> str:
    parsed = excel_serial_to_date(value)
    if parsed is None:
        return (value or "").strip()
    return parsed.strftime("%m/%d/%Y")


def _display_fund_name(fund_name: str, share_class: str) -> str:
    name = (fund_name or "").strip()
    label = SHARE_CODE_LABELS.get((share_class or "").strip().upper(), "")
    if not name:
        return label
    if label and label.lower() not in name.lower():
        return f"{name} {label}"
    return name


def excel_bytes_to_html(data: bytes, *, source_url: str = "") -> str:
    """Flatten the official workbook to an HTML table the family parser can read.

    Keeps every Type of Earnings row (mid-year and year-end). Does not invent
    amounts, dates, or types. Glossary / empty rows are omitted.
    """
    if not data.startswith(b"PK"):
        return ""
    rows = _sheet_rows(data)
    if not rows:
        return ""
    ticker = ticker_from_excel_url(source_url) or ""
    body: list[str] = []
    for raw in rows[1:]:
        padded = list(raw) + [""] * 8
        fund, share_class, record, ex_date, payable, earnings, rate = padded[:7]
        if not (fund or "").strip() or not (earnings or "").strip():
            continue
        if not (rate or "").strip():
            continue
        try:
            if float(rate) == 0:
                continue
        except ValueError:
            if str(rate).strip() in {"", "-", "—", "–"}:
                continue
        body.append(
            "<tr>"
            f"<td>{_display_fund_name(fund, share_class)}</td>"
            f"<td>{ticker}</td>"
            f"<td>{earnings.strip()}</td>"
            f"<td>{rate.strip()}</td>"
            f"<td>{_fmt_date(record)}</td>"
            f"<td>{_fmt_date(ex_date)}</td>"
            f"<td>{_fmt_date(payable)}</td>"
            "</tr>"
        )
    if not body:
        return ""
    title = "MFS 10-year paid distribution history"
    return (
        "<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{title}</title></head><body>\n"
        f"<h1>{title}</h1>\n"
        "<p>Official per-product 10-year Excel. Every Type of Earnings row is "
        "kept (mid-year and year-end). Published $0.00 omitted.</p>\n"
        "<table>\n<thead><tr>"
        "<th>Fund Name</th><th>Ticker</th><th>Type of Earnings</th>"
        "<th>Rate Per Share</th><th>Record Date</th><th>Ex Date</th>"
        "<th>Payable Date</th></tr></thead>\n<tbody>\n"
        + "\n".join(body)
        + "\n</tbody></table>\n</body></html>\n"
    )


def parse_mfs_excel(
    data: bytes,
    *,
    source_url: str,
    fund_family: str = "MFS Investment Management",
):
    html = excel_bytes_to_html(data, source_url=source_url)
    if not html:
        return []
    return parse_distribution_html(
        html,
        source_url=source_url,
        fund_family=fund_family,
    )


def is_mfs_ten_year_excel_url(url: str) -> bool:
    blob = (url or "").lower()
    return "mfs.com" in blob and "10yearsdistribution" in blob
