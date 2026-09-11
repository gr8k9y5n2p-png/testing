from __future__ import annotations

from pathlib import Path

from app.aliases import (
    AB_FUNDS,
    BLACKROCK_FUNDS,
    BNY_FUNDS,
    CALAMOS_FUNDS,
    CLASS_A_FUNDS,
    HARTFORD_FUNDS,
    INVESCO_FUNDS,
    JOHNHANCOCK_FUNDS,
    JPMORGAN_FUNDS,
    MFS_FUNDS,
    THRIVENT_FUNDS,
    VOYA_FUNDS,
    WASATCH_FUNDS,
    class_a_for_name,
    class_a_identifier_for_name,
    display_cusip,
    display_ticker,
    enrich_class_a_fields,
)
from app.schemas import fund_identifier
from app.sources.parser import parse_capital_group_html, parse_distribution_html

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


def test_blackrock_investor_a_identity() -> None:
    identity = class_a_for_name("BlackRock Equity Dividend Fund", fund_family="BlackRock / iShares")
    assert identity is not None
    assert identity.ticker == "MDDVX"
    assert identity.cusip == "09251M108"
    assert identity.fund_identifier == "blackrock-equity-dividend-fund"
    ticker, cusip = enrich_class_a_fields(
        ticker=None,
        cusip=None,
        fund_name="BlackRock Equity Dividend Fund",
        fund_family="BlackRock / iShares",
    )
    assert ticker == "MDDVX"
    assert cusip == "09251M108"
    assert {fund.ticker for fund in BLACKROCK_FUNDS} >= {
        "MDDVX",
        "LIRAX",
        "BSPAX",
        "BAGPX",
        "BMSAX",
        "LPYAX",
        "LEVAX",
        "MDGCX",
        "BACAX",
        "BARDX",
    }


def test_jpmorgan_class_a_identity() -> None:
    identity = class_a_for_name("JPMorgan Equity Income Fund", fund_family="J.P. Morgan Asset Management")
    assert identity is not None
    assert identity.ticker == "OIEIX"
    assert identity.fund_identifier == "jpmorgan-equity-income-fund"
    ticker, _cusip = enrich_class_a_fields(
        ticker=None,
        cusip=None,
        fund_name="Undiscovered Managers Behavioral Value Fund",
        fund_family="J.P. Morgan Asset Management",
    )
    assert ticker == "UBVAX"
    assert {fund.ticker for fund in JPMORGAN_FUNDS} >= {"OIEIX", "BBEM", "JFLI", "VCAXX", "SEEGX"}


def test_blackrock_attach_keeps_name_slug_identifier() -> None:
    ident = fund_identifier("MDDVX", "BlackRock Equity Dividend Fund", "BlackRock / iShares")
    assert ident == "blackrock-equity-dividend-fund"
    ident = fund_identifier(None, "BlackRock LifePath Index Retirement Fund", "BlackRock / iShares")
    assert ident == "blackrock-lifepath-index-retirement-fund"
    # Existing ticker-keyed Large Cap Growth rows stay ticker-keyed.
    ident = fund_identifier("SEEGX", "JPMorgan Large Cap Growth Fund", "J.P. Morgan Asset Management")
    assert ident == "SEEGX"


def test_blackrock_oef_fixture_name_keyed_rows_have_investor_a_tickers() -> None:
    html = (Path(__file__).resolve().parents[1] / "fixtures" / "blackrock" / "2025_open_end_distributions.html").read_text(
        encoding="utf-8"
    )
    records = parse_distribution_html(
        html,
        source_url="fixture://blackrock-oef",
        fund_family="BlackRock / iShares",
    )
    equity = next(r for r in records if "Equity Dividend" in r.fund_name)
    assert equity.ticker == "MDDVX"
    unmapped = sorted(
        {
            r.fund_name
            for r in records
            if r.ticker is None and class_a_for_name(r.fund_name, fund_family="BlackRock / iShares") is None
        }
    )
    # Composite / Institutional-only / interval / unverified names may remain unmapped.
    assert "BlackRock Equity Dividend Fund" not in unmapped
    assert "BlackRock LifePath Index Retirement Fund" not in unmapped
    assert "BlackRock Income Fund" not in unmapped
    assert "BlackRock Credit Relative Value Fund" not in unmapped
    assert "BlackRock HPS Credit Strategies Fund" in unmapped


def test_jpmorgan_fixture_name_keyed_rows_have_class_a_tickers() -> None:
    html = (Path(__file__).resolve().parents[1] / "fixtures" / "jpmorgan" / "section_19a_sample.html").read_text(
        encoding="utf-8"
    )
    records = parse_distribution_html(
        html,
        source_url="fixture://jpm",
        fund_family="J.P. Morgan Asset Management",
    )
    income = next(r for r in records if r.fund_name == "JPMorgan Equity Income Fund")
    assert income.ticker == "OIEIX"
    assert next(r for r in records if r.fund_name.startswith("Undiscovered Managers")).ticker == "UBVAX"
    assert next(r for r in records if "BetaBuilders Emerging" in r.fund_name).ticker == "BBEM"
    unmapped = sorted(
        {
            r.fund_name
            for r in records
            if r.ticker is None and class_a_for_name(r.fund_name, fund_family="J.P. Morgan Asset Management") is None
        }
    )
    assert unmapped == [], unmapped


def test_name_keyed_family_maps_attach_retail_tickers() -> None:
    cases = (
        ("Invesco American Franchise Fund", "Invesco", "VAFAX", INVESCO_FUNDS),
        ("MFS Core Equity Fund Class A", "MFS Investment Management", "MRGAX", MFS_FUNDS),
        ("MFS International Equity Fund All Classes", "MFS Investment Management", "MIEJX", MFS_FUNDS),
        ("John Hancock Balanced Fund", "John Hancock / Manulife", "SVBAX", JOHNHANCOCK_FUNDS),
        ("BNY Mellon Dynamic Value Fund", "BNY Mellon", "DAGVX", BNY_FUNDS),
        ("The Hartford Capital Appreciation Fund", "Hartford Funds", "ITHAX", HARTFORD_FUNDS),
        ("AB Discovery Growth Fund, Inc.", "AllianceBernstein", "CHCLX", AB_FUNDS),
        ("Thrivent Aggressive Allocation Fund", "Thrivent", "TAAIX", THRIVENT_FUNDS),
        ("Calamos Phineus Long/Short Fund", "Calamos", "CPLSX", CALAMOS_FUNDS),
        ("Wasatch Small Cap Growth Fund", "Wasatch", "WAAEX", WASATCH_FUNDS),
        ("Voya Large Cap Value Fund", "Voya", "IEDAX", VOYA_FUNDS),
    )
    for fund_name, family, ticker, catalog in cases:
        identity = class_a_for_name(fund_name, fund_family=family)
        assert identity is not None, fund_name
        assert identity.ticker == ticker
        ticker_out, _cusip = enrich_class_a_fields(
            ticker=None,
            cusip=None,
            fund_name=fund_name,
            fund_family=family,
        )
        assert ticker_out == ticker
        assert ticker in {fund.ticker for fund in catalog}

    # Class I maps to the official I ticker, not Class A MFEGX.
    growth_i = class_a_for_name("MFS Growth Fund Class I", fund_family="MFS Investment Management")
    assert growth_i is not None
    assert growth_i.ticker == "MFEIX"
    assert class_a_for_name("John Hancock Marathon Asset-Based Lending Fund", fund_family="John Hancock / Manulife") is None


def test_mfs_all_classes_keeps_name_slug_not_product_page_ticker() -> None:
    ident = fund_identifier(None, "MFS Growth Fund All Classes", "MFS Investment Management")
    assert ident == "mfs-growth-fund-all-classes"
    ident = fund_identifier("MFEGX", "MFS Growth Fund Class A", "MFS Investment Management")
    assert ident == "MFEGX"


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
