from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.models import EstimateType
from app.sources.families import TRowePriceSource
from app.sources.parser import parse_distribution_html
from app.sources.third_tier import MfsSource

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_mfs_share_class_year_end_pins() -> None:
    paid_2025 = parse_distribution_html(
        (ROOT / "mfs" / "2025_share_class_paid_year_end.html").read_text(encoding="utf-8"),
        source_url=(
            "https://www.mfs.com/MFSServices/products/v1/product/MIGHX/"
            "10YearsDistribution/download?shareCode=I"
        ),
        fund_family="MFS Investment Management",
    )
    tickers_2025 = {r.ticker for r in paid_2025 if r.ticker}
    assert {"MGTIX", "MFEIX", "MEIIX", "MRGRX", "MINIX", "OTCIX"} <= tickers_2025
    assert len(tickers_2025) >= 220
    assert "MIGHX" not in tickers_2025
    assert "MFEGX" not in tickers_2025
    assert not any((r.ticker or "").startswith("ZZ") for r in paid_2025)

    mgtix_lt = next(
        r
        for r in paid_2025
        if r.ticker == "MGTIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mgtix_lt.amount == Decimal("4.20618")
    mgtix_inc = next(
        r
        for r in paid_2025
        if r.ticker == "MGTIX" and r.estimate_type == EstimateType.ordinary_income
    )
    assert mgtix_inc.amount == Decimal("0.30697")
    mfeix_lt = next(
        r
        for r in paid_2025
        if r.ticker == "MFEIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mfeix_lt.amount == Decimal("25.35332")

    paid_2024 = parse_distribution_html(
        (ROOT / "mfs" / "2024_share_class_paid_year_end.html").read_text(encoding="utf-8"),
        source_url=(
            "https://www.mfs.com/MFSServices/products/v1/product/MIGHX/"
            "10YearsDistribution/download?shareCode=I"
        ),
        fund_family="MFS Investment Management",
    )
    mgtix_2024 = next(
        r
        for r in paid_2024
        if r.ticker == "MGTIX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert mgtix_2024.amount == Decimal("3.30240")


def test_t_rowe_etf_year_end_pins() -> None:
    paid_2025 = parse_distribution_html(
        (ROOT / "t_rowe_price" / "2025_etf_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.troweprice.com/personal-investing/resources/planning/tax/"
            "dividend-distributions/etfs/2025-year-end-distributions.html"
        ),
        fund_family="T. Rowe Price",
    )
    tickers = {r.ticker for r in paid_2025 if r.ticker}
    assert {"TCAF", "TVAL", "THEQ", "TMSL", "TOUS", "TGRT"} <= tickers
    assert "TACN" not in tickers
    assert "TTEQ" not in tickers

    tcaf = next(
        r
        for r in paid_2025
        if r.ticker == "TCAF" and r.estimate_type == EstimateType.ordinary_income
    )
    assert tcaf.amount == Decimal("0.1916")
    theq_lt = next(
        r
        for r in paid_2025
        if r.ticker == "THEQ"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert theq_lt.amount == Decimal("0.0237")
    tval = next(
        r
        for r in paid_2025
        if r.ticker == "TVAL" and r.estimate_type == EstimateType.ordinary_income
    )
    assert tval.amount == Decimal("0.4061")

    paid_2024 = parse_distribution_html(
        (ROOT / "t_rowe_price" / "2024_etf_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.troweprice.com/personal-investing/resources/planning/tax/"
            "dividend-distributions/etfs/2024-year-end-distributions.html"
        ),
        fund_family="T. Rowe Price",
    )
    tcaf_2024 = next(
        r
        for r in paid_2024
        if r.ticker == "TCAF" and r.estimate_type == EstimateType.ordinary_income
    )
    assert tcaf_2024.amount == Decimal("0.1446")


def test_wave13_heroes_are_searchable(client: TestClient) -> None:
    for source in (MfsSource(), TRowePriceSource()):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": source.slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("MGTIX", "MFEIX", "MEIIX", "TCAF", "TVAL", "THEQ", "TMSL"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    mgtix = client.get("/distributions", params={"q": "MGTIX", "page_size": 50}).json()
    amounts = [
        Decimal(row["amount"])
        for row in mgtix["items"]
        if row.get("ticker") == "MGTIX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("4.20618") in amounts
    assert Decimal("3.30240") in amounts

    mfeix = client.get("/distributions", params={"q": "MFEIX", "page_size": 50}).json()
    mfeix_lt = [
        Decimal(row["amount"])
        for row in mfeix["items"]
        if row.get("ticker") == "MFEIX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("25.35332") in mfeix_lt

    theq = client.get("/distributions", params={"q": "THEQ", "page_size": 50}).json()
    theq_lt = [
        Decimal(row["amount"])
        for row in theq["items"]
        if row.get("ticker") == "THEQ"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("0.0237") in theq_lt
