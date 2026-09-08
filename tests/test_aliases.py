from __future__ import annotations

from pathlib import Path

from app.aliases import (
    CLASS_A_FUNDS,
    class_a_for_name,
    class_a_identifier_for_name,
    display_cusip,
    display_ticker,
    enrich_class_a_fields,
)
from app.schemas import fund_identifier
from app.sources.parser import parse_capital_group_html

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "american_funds"


def test_abalx_class_a_identity() -> None:
    identity = class_a_for_name("American Balanced Fund®")
    assert identity is not None
    assert identity.ticker == "ABALX"
    assert identity.cusip == "024071102"
    assert identity.fund_identifier == "american-balanced-fund"
    assert class_a_identifier_for_name("American Balanced Fund") == "american-balanced-fund"
    ticker, cusip = enrich_class_a_fields(
        ticker=None,
        cusip=None,
        fund_name="American Balanced Fund",
        fund_family="American Funds",
    )
    assert ticker == "ABALX"
    assert cusip == "024071102"
    assert {fund.ticker for fund in CLASS_A_FUNDS} >= {"ABALX", "AMCPX", "AGTHX", "ANCFX"}


def test_class_a_attach_keeps_name_slug_identifier() -> None:
    ident = fund_identifier("ABALX", "American Balanced Fund", "American Funds")
    assert ident == "american-balanced-fund"
    ident = fund_identifier(None, "AMCAP Fund", "American Funds")
    assert ident == "amcap-fund"
    # Non-AF ticker-keyed books still use the ticker.
    ident = fund_identifier("VFIAX", "Vanguard 500 Index Fund", "Vanguard")
    assert ident == "VFIAX"


def test_display_backfill_from_slug() -> None:
    assert display_ticker(None, "american-balanced-fund") == "ABALX"
    assert display_cusip(None, "american-balanced-fund") == "024071102"
    assert display_ticker("CGHM", "capital-group-municipal-high-income-etf") == "CGHM"


def test_year_end_fixture_name_keyed_rows_have_class_a_tickers() -> None:
    html = (FIXTURES / "year_end_2025_distributions.html").read_text(encoding="utf-8")
    records = parse_capital_group_html(
        html,
        source_url="https://www.capitalgroup.com/individual/service-and-support/tax-center/2025-year-end-distributions.html",
    )
    unmapped = sorted(
        {
            r.fund_name
            for r in records
            if r.ticker is None and class_a_for_name(r.fund_name) is None
        }
    )
    assert unmapped == [], unmapped
