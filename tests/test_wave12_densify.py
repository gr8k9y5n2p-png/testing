from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.models import EstimateType
from app.sources.fourth_tier import HartfordSource, PrincipalSource
from app.sources.parser import parse_distribution_html
from app.sources.third_tier import AllspringSource

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_principal_product_page_year_end_pins() -> None:
    paid_2025 = parse_distribution_html(
        (ROOT / "principal" / "2025_paid_distributions.html").read_text(encoding="utf-8"),
        source_url="https://www.principalam.com/us/fund/pqiax",
        fund_family="Principal",
    )
    tickers_2025 = {r.ticker for r in paid_2025 if r.ticker}
    assert {"PQIAX", "PEMGX", "PLFPX", "PBLCX", "PLGIX", "LTSTX", "PSPIX"} <= tickers_2025
    assert len(tickers_2025) >= 75
    assert not any((r.ticker or "").startswith("ZZ") for r in paid_2025)

    pqiax_lt = next(
        r
        for r in paid_2025
        if r.ticker == "PQIAX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert pqiax_lt.amount == Decimal("3.3687")
    pblcx_lt = next(
        r
        for r in paid_2025
        if r.ticker == "PBLCX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert pblcx_lt.amount == Decimal("8.3248")
    plgix_lt = next(
        r
        for r in paid_2025
        if r.ticker == "PLGIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert plgix_lt.amount == Decimal("1.9823")
    ltstx_lt = next(
        r
        for r in paid_2025
        if r.ticker == "LTSTX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert ltstx_lt.amount == Decimal("0.9348")

    paid_2024 = parse_distribution_html(
        (ROOT / "principal" / "2024_paid_distributions.html").read_text(encoding="utf-8"),
        source_url="https://www.principalam.com/us/fund/pqiax",
        fund_family="Principal",
    )
    pemgx_2024 = next(
        r
        for r in paid_2024
        if r.ticker == "PEMGX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert pemgx_2024.amount == Decimal("1.3963")
    assert {r.ticker for r in paid_2024 if r.ticker} >= {"PQIAX", "PEMGX", "PLGIX"}


def test_allspring_share_class_product_page_pins() -> None:
    paid_2025 = parse_distribution_html(
        (ROOT / "allspring" / "2025_paid_distributions.html").read_text(encoding="utf-8"),
        source_url=(
            "https://www.allspringglobal.com/investments/equity/mutual-funds/"
            "special-mid-cap-value/"
        ),
        fund_family="Allspring",
    )
    tickers_2025 = {r.ticker for r in paid_2025 if r.ticker}
    assert {"WFMIX", "WFPAX", "SGRAX", "WOFNX", "SGRNX"} <= tickers_2025
    assert len(tickers_2025) >= 30

    wfmix_lt = next(
        r
        for r in paid_2025
        if r.ticker == "WFMIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wfmix_lt.amount == Decimal("4.26857")
    wfpax_lt = next(
        r
        for r in paid_2025
        if r.ticker == "WFPAX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wfpax_lt.amount == Decimal("4.26857")
    sgrax_lt = next(
        r
        for r in paid_2025
        if r.ticker == "SGRAX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert sgrax_lt.amount == Decimal("8.85612")
    wofnx_lt = next(
        r
        for r in paid_2025
        if r.ticker == "WOFNX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wofnx_lt.amount == Decimal("4.06281")


def test_hartford_share_class_product_page_pins() -> None:
    paid_2025 = parse_distribution_html(
        (ROOT / "hartford" / "2025_share_class_product_page_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://www.hartfordfunds.com/funds/divgr.classI.html",
        fund_family="Hartford Funds",
    )
    tickers = {r.ticker for r in paid_2025 if r.ticker}
    assert {"HDGIX", "HFMIX", "HGIIX", "ITHIX"} <= tickers
    assert len(tickers) >= 200
    assert not {"IHGIX", "HAIAX", "HFMCX"} & tickers
    assert not any((r.ticker or "").startswith("ZZ") for r in paid_2025)

    hdgix_lt = next(
        r
        for r in paid_2025
        if r.ticker == "HDGIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hdgix_lt.amount == Decimal("3.9283")
    hfmix_lt = next(
        r
        for r in paid_2025
        if r.ticker == "HFMIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hfmix_lt.amount == Decimal("5.4448")
    hgiix_lt = next(
        r
        for r in paid_2025
        if r.ticker == "HGIIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert hgiix_lt.amount == Decimal("6.1237")
    ithix_st = next(
        r
        for r in paid_2025
        if r.ticker == "ITHIX"
        and r.estimate_type == EstimateType.short_term_capital_gains
    )
    assert ithix_st.amount == Decimal("0.2297")


def test_wave12_heroes_are_searchable(client: TestClient) -> None:
    for source in (PrincipalSource(), AllspringSource(), HartfordSource()):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": source.slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in (
        "PQIAX",
        "PLGIX",
        "PBLCX",
        "PEMGX",
        "LTSTX",
        "WFPAX",
        "SGRAX",
        "WOFNX",
        "HDGIX",
        "HFMIX",
        "HGIIX",
        "ITHIX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    pqiax = client.get("/distributions", params={"q": "PQIAX", "page_size": 50}).json()
    amounts = [
        Decimal(row["amount"])
        for row in pqiax["items"]
        if row.get("ticker") == "PQIAX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("3.3687") in amounts
    assert Decimal("3.6805") in amounts

    wfpax = client.get("/distributions", params={"q": "WFPAX", "page_size": 50}).json()
    wfpax_lt = [
        Decimal(row["amount"])
        for row in wfpax["items"]
        if row.get("ticker") == "WFPAX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("4.26857") in wfpax_lt

    hdgix = client.get("/distributions", params={"q": "HDGIX", "page_size": 50}).json()
    hdgix_lt = [
        Decimal(row["amount"])
        for row in hdgix["items"]
        if row.get("ticker") == "HDGIX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("3.9283") in hdgix_lt
