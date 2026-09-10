"""Record date is stored only when the manager publishes it.

Fidelity FIIS_SP52_DPL6 and Conestoga's 2026 estimate book omit Record.
Never invent from ex−1. See fixtures/fidelity/RECORD_DATE.md.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from app.models import EstimateType
from app.sources.parser import (
    classify_header,
    extract_page_published_dates,
    parse_distribution_html,
)

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_classify_header_accepts_record_aliases() -> None:
    for header in (
        "Record",
        "Record Date",
        "Date of Record",
        "Rec Date",
        "Dt of Record",
    ):
        spec = classify_header(header, "Estimated distributions")
        assert spec is not None
        assert spec.role == "record_date"


def test_fidelity_sep_2026_unpaid_omits_unpublished_record_date() -> None:
    records = parse_distribution_html(
        (ROOT / "fidelity" / "estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="https://institutional.fidelity.com/app/tabbed/products/FIIS_SP52_DPL6.html?navId=324",
        fund_family="Fidelity",
    )
    for ticker in ("FBGRX", "FBCVX", "FDGFX"):
        lt = next(
            r
            for r in records
            if r.ticker == ticker and r.estimate_type == EstimateType.long_term_capital_gains
        )
        assert lt.record_date is None
        assert str(lt.ex_date) == "2026-09-11"
        assert str(lt.payable_date) == "2026-09-14"
        assert str(lt.as_of) == "2026-07-31"
        # Must not invent Record as ex−1 (2026-09-10) or any other offset.
        assert lt.ex_date - timedelta(days=1) != lt.record_date


def test_conestoga_2026_estimate_omits_unpublished_dates() -> None:
    records = parse_distribution_html(
        (ROOT / "conestoga" / "2026_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://conestogacapital.com/capital-gains-information/",
        fund_family="Conestoga",
    )
    for ticker, amount in (("CCALX", "19.71"), ("CMIRX", "0.31")):
        lt = next(
            r
            for r in records
            if r.ticker == ticker and r.estimate_type == EstimateType.long_term_capital_gains
        )
        assert lt.amount == Decimal(amount)
        assert lt.record_date is None
        assert lt.ex_date is None
        assert lt.payable_date is None
        assert str(lt.as_of) == "2026-07-31"
    assert not any(r.ticker == "CCSGX" for r in records)


def test_record_column_is_parsed_when_manager_publishes_it() -> None:
    html = """
    <html><head><title>Example estimates</title><meta name="date" content="2026-07-31"></head>
    <body>
    <table>
      <tr><th>Fund Name</th><th>Ticker</th><th>Date of Record</th><th>Ex Date</th><th>Pay Date</th><th>Long-Term</th></tr>
      <tr><td>Example Growth</td><td>EXMPX</td><td>09/10/2026</td><td>09/11/2026</td><td>09/14/2026</td><td>1.25</td></tr>
    </table>
    </body></html>
    """
    records = parse_distribution_html(
        html, source_url="fixture://record-column", fund_family="Example"
    )
    lt = next(r for r in records if r.ticker == "EXMPX")
    assert str(lt.record_date) == "2026-09-10"
    assert str(lt.ex_date) == "2026-09-11"
    assert str(lt.payable_date) == "2026-09-14"


def test_record_date_not_invented_from_ex_minus_one() -> None:
    html = """
    <html><head><title>Example estimates</title><meta name="date" content="2026-07-31"></head>
    <body>
    <table>
      <tr><th>Fund Name</th><th>Ticker</th><th>Ex Date</th><th>Pay Date</th><th>Long-Term</th></tr>
      <tr><td>Example Growth</td><td>EXMPX</td><td>09/11/2026</td><td>09/14/2026</td><td>1.25</td></tr>
    </table>
    </body></html>
    """
    records = parse_distribution_html(
        html, source_url="fixture://ex-only", fund_family="Example"
    )
    lt = next(r for r in records if r.ticker == "EXMPX")
    assert str(lt.ex_date) == "2026-09-11"
    assert lt.record_date is None


def test_conestoga_final_prose_dates_are_stored_when_published() -> None:
    html = """
    <html><head><title>Conestoga Funds Final Distributions</title></head>
    <body>
    <p>
      The table below lists the year-end distributions for the Conestoga Funds.
      The distributions have a record date of Tuesday, December 2, 2025,
      and an ex-date of Wednesday, December 3, 2025. These figures have been finalized.
    </p>
    <table>
      <tr><th>Fund Name</th><th>Ticker</th><th>Short-Term</th><th>Long-Term</th></tr>
      <tr><td>Conestoga Discovery Fund Institutional</td><td>CMIRX</td><td>—</td><td>0.095275</td></tr>
    </table>
    </body></html>
    """
    records = parse_distribution_html(
        html, source_url="fixture://conestoga-final-prose", fund_family="Conestoga"
    )
    lt = next(r for r in records if r.ticker == "CMIRX")
    assert lt.amount == Decimal("0.095275")
    assert str(lt.record_date) == "2025-12-02"
    assert str(lt.ex_date) == "2025-12-03"


def test_fidelity_glossary_does_not_invent_a_record_date() -> None:
    text = (
        "Record Date: All shareholders of record at 4 p.m. Eastern time on this "
        "day are eligible to receive the distribution. This date is usually the "
        "business day prior to the ex-dividend date. The Ex-Date and Pay Date "
        "are disclosed in the table."
    )
    assert extract_page_published_dates(text) == {
        "record_date": None,
        "ex_date": None,
        "payable_date": None,
    }


def test_ici_date_of_record_alias() -> None:
    from app.sources.ici import parse_ici_primary

    csv = (
        "fund,ticker,date of record,ex date,payable date,long term capital gain\n"
        "Example Fund,EXMPX,12/15/2025,12/16/2025,12/17/2025,1.10\n"
    )
    records = parse_ici_primary(
        csv, source_url="fixture://ici-record", fund_family="Example"
    )
    assert str(records[0].record_date) == "2025-12-15"
    assert records[0].amount == Decimal("1.10")
    assert records[0].record_date == date(2025, 12, 15)
