from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.models import EstimateType
from app.sources.fourth_tier import CalamosSource
from app.sources.parser import parse_distribution_html
from app.sources.third_tier import DodgeCoxSource, MfsSource

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_mfs_remaining_share_class_year_end_pins() -> None:
    paid = parse_distribution_html(
        (ROOT / "mfs" / "remaining_share_class_paid_year_end.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.mfs.com/MFSServices/products/v1/product/MDIKX/"
            "10YearsDistribution/download?shareCode=R2"
        ),
        fund_family="MFS Investment Management",
    )
    tickers = {row.ticker for row in paid if row.ticker}
    assert {"MDIKX", "MEIGX", "MIGFX", "MFEBX", "NDVSX"} <= tickers
    assert len(tickers) >= 280
    assert "MIGHX" not in tickers
    assert "MFEGX" not in tickers
    assert "MEIAX" not in tickers
    assert "MGTIX" not in tickers
    assert not any((row.ticker or "").startswith("ZZ") for row in paid)

    mdikx_2025_lt = next(
        row
        for row in paid
        if row.ticker == "MDIKX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert mdikx_2025_lt.amount == Decimal("0.75145")
    mdikx_2025_oi = next(
        row
        for row in paid
        if row.ticker == "MDIKX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert mdikx_2025_oi.amount == Decimal("0.49478")
    mdikx_2024_lt = next(
        row
        for row in paid
        if row.ticker == "MDIKX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
    )
    assert mdikx_2024_lt.amount == Decimal("0.21839")

    meigx_2025_lt = next(
        row
        for row in paid
        if row.ticker == "MEIGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert meigx_2025_lt.amount == Decimal("3.86919")
    migfx_2025_lt = next(
        row
        for row in paid
        if row.ticker == "MIGFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert migfx_2025_lt.amount == Decimal("4.20618")
    mfebx_2025_lt = next(
        row
        for row in paid
        if row.ticker == "MFEBX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert mfebx_2025_lt.amount == Decimal("3.86919")


def test_dodge_remaining_share_class_pins() -> None:
    paid = parse_distribution_html(
        (ROOT / "dodge_cox" / "remaining_share_class_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://api-v1.dodgeandcox.com/api/funds-distribution",
        fund_family="Dodge & Cox",
    )
    tickers = {row.ticker for row in paid if row.ticker}
    assert {"DOXGX", "DOXIX", "DODEX", "DOXBX", "DODWX"} <= tickers
    assert "DODGX" not in tickers
    assert "DODIX" not in tickers
    assert "DODFX" not in tickers
    assert "DODBX" not in tickers

    doxgx_2025_lt = next(
        row
        for row in paid
        if row.ticker == "DOXGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert doxgx_2025_lt.amount == Decimal("1.1999")
    doxgx_2025_oi = next(
        row
        for row in paid
        if row.ticker == "DOXGX"
        and row.estimate_type == EstimateType.ordinary_income
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert doxgx_2025_oi.amount == Decimal("0.0446")
    doxgx_2024_lt = next(
        row
        for row in paid
        if row.ticker == "DOXGX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2024
    )
    assert doxgx_2024_lt.amount == Decimal("12.0360")


def test_calamos_etf_paid_pins() -> None:
    paid = parse_distribution_html(
        (ROOT / "calamos" / "2025_etf_paid_capital_gains.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.calamos.com/globalassets/media/documents/tax-center/"
            "2025-calamos-exchange-traded-funds-capital-gains.pdf"
        ),
        fund_family="Calamos",
    )
    tickers = {row.ticker for row in paid if row.ticker}
    assert {"CANQ", "CCEF"} <= tickers
    canq = next(
        row
        for row in paid
        if row.ticker == "CANQ"
        and row.estimate_type == EstimateType.short_term_capital_gains
    )
    assert canq.amount == Decimal("0.08")
    ccef = next(
        row
        for row in paid
        if row.ticker == "CCEF"
        and row.estimate_type == EstimateType.long_term_capital_gains
    )
    assert ccef.amount == Decimal("0.19")


def test_wave15_heroes_are_searchable(client: TestClient) -> None:
    for source in (MfsSource(), DodgeCoxSource(), CalamosSource()):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": source.slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("MDIKX", "MEIGX", "MIGFX", "MFEBX", "DOXGX", "DODEX", "CANQ", "CCEF"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    mdikx = client.get("/distributions", params={"q": "MDIKX", "page_size": 50}).json()
    mdikx_lt = [
        Decimal(row["amount"])
        for row in mdikx["items"]
        if row.get("ticker") == "MDIKX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("0.75145") in mdikx_lt
    assert Decimal("0.21839") in mdikx_lt

    doxgx = client.get("/distributions", params={"q": "DOXGX", "page_size": 50}).json()
    doxgx_lt = [
        Decimal(row["amount"])
        for row in doxgx["items"]
        if row.get("ticker") == "DOXGX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("1.1999") in doxgx_lt
    assert Decimal("12.0360") in doxgx_lt
