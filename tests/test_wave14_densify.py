from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.aliases import CLASS_A_FUNDS
from app.models import EstimateType
from app.schemas import fund_identifier
from app.sources.american_funds import AmericanFundsSource
from app.sources.parser import parse_distribution_html

ROOT = Path(__file__).resolve().parents[1] / "fixtures"
CLASS_A_TICKERS = {fund.ticker for fund in CLASS_A_FUNDS}


def test_american_funds_share_class_product_page_pins() -> None:
    paid = parse_distribution_html(
        (ROOT / "american_funds" / "share_class_product_page_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://www.capitalgroup.com/individual/investments/fund/AMCFX",
        fund_family="American Funds",
    )
    tickers = {row.ticker for row in paid if row.ticker}
    assert {"AMCFX", "AMPCX", "FMACX", "RAFGX", "GFAFX", "AMBFX", "RGAFX"} <= tickers
    assert len(tickers) >= 900
    assert not tickers & CLASS_A_TICKERS
    assert not any((row.ticker or "").startswith("ZZ") for row in paid)
    assert {
        fund_identifier(row.ticker, row.fund_name, "American Funds") for row in paid
    }.isdisjoint({fund.fund_identifier for fund in CLASS_A_FUNDS})

    amcfx_2025_lt = next(
        row
        for row in paid
        if row.ticker == "AMCFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert amcfx_2025_lt.amount == Decimal("2.1509")
    amcfx_2024_oi = next(
        row
        for row in paid
        if row.ticker == "AMCFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2024
    )
    assert amcfx_2024_oi.amount == Decimal("0.2434")
    amcfx_2024_lt = next(
        row
        for row in paid
        if row.ticker == "AMCFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
    )
    assert amcfx_2024_lt.amount == Decimal("2.5220")

    gfafx_2025_lt = next(
        row
        for row in paid
        if row.ticker == "GFAFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert gfafx_2025_lt.amount == Decimal("8.3640")
    ambfx_2025_lt = next(
        row
        for row in paid
        if row.ticker == "AMBFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert ambfx_2025_lt.amount == Decimal("2.1250")
    ambfx_2025_oi = next(
        row
        for row in paid
        if row.ticker == "AMBFX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert ambfx_2025_oi.amount == Decimal("0.1310")


def test_wave14_heroes_are_searchable(client: TestClient) -> None:
    fetched = client.post(
        "/ingest/fetch", json={"fund_family": AmericanFundsSource().slug, "mode": "fixture"}
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["created"] > 0

    for ticker in ("AMCFX", "AMPCX", "FMACX", "RAFGX", "GFAFX", "AMBFX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    amcfx = client.get("/distributions", params={"q": "AMCFX", "page_size": 50}).json()
    amounts = [
        Decimal(row["amount"])
        for row in amcfx["items"]
        if row.get("ticker") == "AMCFX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("2.1509") in amounts
    assert Decimal("2.5220") in amounts

    gfafx = client.get("/distributions", params={"q": "GFAFX", "page_size": 50}).json()
    gfafx_lt = [
        Decimal(row["amount"])
        for row in gfafx["items"]
        if row.get("ticker") == "GFAFX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("8.3640") in gfafx_lt
