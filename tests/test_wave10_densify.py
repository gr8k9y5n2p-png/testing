from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.models import EstimateType
from app.sources.families import FidelitySource
from app.sources.next_tier import SchwabSource
from app.sources.parser import parse_distribution_html

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_fidelity_advisor_share_class_book_pins() -> None:
    paid = parse_distribution_html(
        (ROOT / "fidelity" / "advisor_prior_year_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://institutional.fidelity.com/app/tabbed/products/"
            "FIIS_SP10_DPL2_DSC1.html?navId=320"
        ),
        fund_family="Fidelity",
    )
    tickers = {r.ticker for r in paid if r.ticker}
    assert {"FAGAX", "FAGCX", "FTRIX", "FCIGX", "FTIWX"} <= tickers
    assert len(tickers) >= 790
    assert not any((r.ticker or "").startswith("ZZ") for r in paid)

    fagax_lt = next(
        r
        for r in paid
        if r.ticker == "FAGAX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-12-26"
    )
    assert fagax_lt.amount == Decimal("8.58500")
    assert fagax_lt.cusip == "315807834"
    assert fagax_lt.record_date is None

    ftrix_lt = next(
        r
        for r in paid
        if r.ticker == "FTRIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-12-19"
    )
    assert ftrix_lt.amount == Decimal("0.27700")

    estimates = parse_distribution_html(
        (ROOT / "fidelity" / "advisor_estimated_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://institutional.fidelity.com/app/tabbed/products/"
            "FIIS_SP52_DPL2_DSC1.html?navId=320"
        ),
        fund_family="Fidelity",
    )
    fcigx_lt = next(
        r
        for r in estimates
        if r.ticker == "FCIGX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert fcigx_lt.amount == Decimal("6.922")
    assert str(fcigx_lt.as_of) == "2026-07-31"
    assert fcigx_lt.record_date is None


def test_schwab_fundamental_etf_december_pins() -> None:
    records = parse_distribution_html(
        (ROOT / "schwab" / "etf_product_page_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://www.schwabassetmanagement.com/products/fndx",
        fund_family="Charles Schwab Investment Management",
    )
    fndx = next(
        r
        for r in records
        if r.ticker == "FNDX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2025-12-10"
    )
    assert fndx.amount == Decimal("0.1222")
    assert fndx.cusip == "808524771"

    fnde = next(
        r
        for r in records
        if r.ticker == "FNDE"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2025-12-11"
    )
    assert fnde.amount == Decimal("1.2986")

    fnda = next(
        r
        for r in records
        if r.ticker == "FNDA"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2024-12-11"
    )
    assert fnda.amount == Decimal("0.1643")
    assert not any(
        r.ticker == "FNDA" and r.ex_date and r.ex_date.year == 2025 for r in records
    )


def test_wave10_heroes_are_searchable(client: TestClient) -> None:
    for source in (FidelitySource(), SchwabSource()):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": source.slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("FAGAX", "FTRIX", "FCIGX", "FNDX", "FNDE", "FNDA"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    fagax = client.get("/distributions", params={"q": "FAGAX", "page_size": 50}).json()
    amounts = [
        Decimal(row["amount"])
        for row in fagax["items"]
        if row.get("ticker") == "FAGAX" and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("8.58500") in amounts

    fndx = client.get("/distributions", params={"q": "FNDX", "page_size": 50}).json()
    fndx_income = [
        Decimal(row["amount"])
        for row in fndx["items"]
        if row.get("ticker") == "FNDX" and row.get("estimate_type") == "ordinary_income"
    ]
    assert Decimal("0.1222") in fndx_income
