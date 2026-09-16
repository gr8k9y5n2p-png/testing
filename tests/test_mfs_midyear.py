"""MFS mid-year paid events — official 10-year Excel, types kept."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.models import EstimateType, PublicationStage
from app.sources.mfs_excel import excel_serial_to_date, ten_year_excel_url
from app.sources.parser import parse_distribution_html
from app.sources.third_tier import MfsSource

ROOT = Path(__file__).resolve().parents[1] / "fixtures"
GROWTH_2025 = (
    "MFEGX",
    "MFEIX",
    "MFECX",
    "MFEKX",
    "MEGBX",
    "MFELX",
    "MEGRX",
    "MFEHX",
    "MFEJX",
)


def test_excel_serial_matches_issuer_midyear_dates() -> None:
    assert str(excel_serial_to_date(45869)) == "2025-07-31"
    assert str(excel_serial_to_date(45870)) == "2025-08-01"
    assert str(excel_serial_to_date(46234)) == "2026-07-31"
    assert str(excel_serial_to_date(46007)) == "2025-12-16"


def test_type_of_earnings_header_is_not_split_and_keeps_ltcg() -> None:
    html = """<!DOCTYPE html><html><head>
<title>MFS paid midyear distributions</title></head><body>
<table>
<thead><tr>
<th>Fund Name</th><th>Ticker</th><th>Type of Earnings</th>
<th>Rate Per Share</th><th>Record Date</th><th>Ex Date</th>
<th>Payable Date</th>
</tr></thead>
<tbody>
<tr>
<td>MFS Growth Fund Class A</td><td>MFEGX</td>
<td>Long Term Capital Gain</td><td>4.12961</td>
<td>07/30/2025</td><td>07/31/2025</td><td>08/01/2025</td>
</tr>
<tr>
<td>MFS Growth Fund Class A</td><td>MFEGX</td>
<td>Dividend</td><td>0.17485</td>
<td>07/30/2024</td><td>07/31/2024</td><td>08/01/2024</td>
</tr>
</tbody></table></body></html>"""
    rows = parse_distribution_html(
        html,
        source_url=ten_year_excel_url("MFEGX", "A"),
        fund_family="MFS Investment Management",
    )
    lt = next(
        row
        for row in rows
        if row.ticker == "MFEGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
    )
    assert lt.amount == Decimal("4.12961")
    assert str(lt.ex_date) == "2025-07-31"
    assert str(lt.payable_date) == "2025-08-01"
    assert lt.publication_stage == PublicationStage.paid
    income = next(
        row
        for row in rows
        if row.ticker == "MFEGX" and row.estimate_type == EstimateType.ordinary_income
    )
    assert income.amount == Decimal("0.17485")
    assert not any(row.estimate_type == EstimateType.total for row in rows)
    assert not any(row.estimate_type == EstimateType.other for row in rows)


def test_paid_midyear_fixture_fills_mfegx_and_growth_siblings() -> None:
    rows = parse_distribution_html(
        (ROOT / "mfs" / "paid_midyear.html").read_text(encoding="utf-8"),
        source_url=ten_year_excel_url("MFEGX", "A"),
        fund_family="MFS Investment Management",
    )
    assert not any((row.ticker or "").startswith("ZZ") for row in rows)
    for ticker in GROWTH_2025:
        lt = next(
            row
            for row in rows
            if row.ticker == ticker
            and row.estimate_type == EstimateType.long_term_capital_gains
            and row.ex_date
            and row.ex_date.year == 2025
        )
        assert lt.amount == Decimal("4.12961")
        assert str(lt.ex_date) == "2025-07-31"
        assert str(lt.payable_date) == "2025-08-01"
        assert str(lt.record_date) == "2025-07-30"
        assert lt.publication_stage == PublicationStage.paid


def test_mfs_source_keeps_both_2025_mfegx_ltcg_events() -> None:
    records = MfsSource().fetch(mode="fixture").records
    mfegx_2025 = [
        row
        for row in records
        if row.ticker == "MFEGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
        and row.amount is not None
    ]
    amounts = {row.amount for row in mfegx_2025}
    dates = {str(row.ex_date) for row in mfegx_2025}
    assert Decimal("4.12961") in amounts
    assert Decimal("25.35332") in amounts
    assert "2025-07-31" in dates
    assert "2025-12-16" in dates
    assert Decimal("4.12961") + Decimal("25.35332") == Decimal("29.48293")

    kept_2026 = next(
        row
        for row in records
        if row.ticker == "MFEGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and str(row.ex_date) == "2026-07-31"
    )
    assert kept_2026.amount == Decimal("1.05252")
    assert str(kept_2026.payable_date) == "2026-08-03"

    mittx_oi = next(
        row
        for row in records
        if row.ticker == "MITTX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-07-31"
    )
    mitdx_oi = next(
        row
        for row in records
        if row.ticker == "MITDX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and str(row.ex_date) == "2025-07-31"
    )
    assert mittx_oi.amount == Decimal("0.11847")
    assert mitdx_oi.amount == Decimal("0.14062")


def test_mfs_midyear_is_in_book_only() -> None:
    before_tickers = {
        "MFEGX",
        "MFEIX",
        "MFECX",
        "MFEKX",
        "MEGBX",
        "MIGHX",
        "MITTX",
        "MITDX",
        "NDVAX",
    }
    records = MfsSource().fetch(mode="fixture").records
    midyear = parse_distribution_html(
        (ROOT / "mfs" / "paid_midyear.html").read_text(encoding="utf-8"),
        source_url="fixture://mfs-paid-midyear",
        fund_family="MFS Investment Management",
    )
    book = {(row.ticker or "").upper() for row in records if row.ticker}
    filled = {(row.ticker or "").upper() for row in midyear if row.ticker}
    assert before_tickers <= filled <= book
    assert "LTTAX" not in filled


def test_mfegx_hero_smoke_lists_both_2025_rows(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": "mfs", "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    body = client.get(
        "/distributions", params={"ticker": "MFEGX", "page_size": 50}
    ).json()
    rows = [
        item
        for item in body["items"]
        if item.get("ticker") == "MFEGX"
        and item.get("estimate_type") == "long_term_capital_gains"
        and (item.get("ex_date") or "").startswith("2025")
    ]
    amounts = {Decimal(item["amount"]) for item in rows if item.get("amount")}
    dates = {item["ex_date"] for item in rows}
    assert Decimal("4.12961") in amounts
    assert Decimal("25.35332") in amounts
    assert "2025-07-31" in dates
    assert "2025-12-16" in dates
    assert all(item["estimate_type"] == "long_term_capital_gains" for item in rows)
