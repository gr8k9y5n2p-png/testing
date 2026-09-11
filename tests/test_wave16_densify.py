from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.models import EstimateType
from app.sources.fifth_tier import TouchstoneSource
from app.sources.next_tier import BnyMellonSource
from app.sources.parser import parse_distribution_html
from app.sources.sixth_tier import BrownAdvisorySource, WilliamBlairSource
from app.sources.third_tier import AllspringSource, VirtusSource

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_virtus_remaining_share_class_pins() -> None:
    paid = parse_distribution_html(
        (ROOT / "virtus" / "remaining_share_class_paid_year_end.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.virtus.com/assets/files/8ua/"
            "2025-mfs_distributions_calyr_detail.pdf"
        ),
        fund_family="Virtus",
    )
    tickers = {row.ticker for row in paid if row.ticker}
    assert {"MERFX", "MERIX", "AMFAX", "PGUAX"} <= tickers
    assert len(tickers) >= 220
    assert "STVTX" not in tickers
    assert "STCIX" not in tickers
    assert "UNWGX" not in tickers
    assert not any((row.ticker or "").startswith("ZZ") for row in paid)

    merfx_lt = next(
        row
        for row in paid
        if row.ticker == "MERFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert merfx_lt.amount == Decimal("0.028392")
    merfx_st = next(
        row
        for row in paid
        if row.ticker == "MERFX"
        and row.estimate_type == EstimateType.short_term_capital_gains
    )
    assert merfx_st.amount == Decimal("0.552904")
    merfx_oi = next(
        row
        for row in paid
        if row.ticker == "MERFX"
        and row.estimate_type == EstimateType.ordinary_income
    )
    assert merfx_oi.amount == Decimal("0.698093")
    pguax_lt = next(
        row
        for row in paid
        if row.ticker == "PGUAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
    )
    assert pguax_lt.amount == Decimal("0.874419")


def test_allspring_remaining_share_class_pins() -> None:
    paid = parse_distribution_html(
        (ROOT / "allspring" / "remaining_share_class_paid_year_end.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://www.allspringglobal.com/sitemap.xml",
        fund_family="Allspring",
    )
    tickers = {row.ticker for row in paid if row.ticker}
    assert {"EAAFX", "SCSRX", "MBFAX"} <= tickers
    assert len(tickers) >= 80
    assert "WFMIX" not in tickers
    assert "WFPAX" not in tickers
    assert "SGRNX" not in tickers

    eaafx_2025_lt = next(
        row
        for row in paid
        if row.ticker == "EAAFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert eaafx_2025_lt.amount == Decimal("0.4674")
    scsrx_2025_lt = next(
        row
        for row in paid
        if row.ticker == "SCSRX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert scsrx_2025_lt.amount == Decimal("0.73962")


def test_touchstone_remaining_share_class_pins() -> None:
    paid = parse_distribution_html(
        (ROOT / "touchstone" / "remaining_share_class_paid_year_end.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://www.touchstoneinvestments.com/mutual-funds/dividend-equity-fund",
        fund_family="Touchstone",
    )
    tickers = {row.ticker for row in paid if row.ticker}
    assert {"TQCAX", "SWRLX", "SENCX"} <= tickers
    assert len(tickers) >= 90
    assert "TVLAX" not in tickers
    assert "TFOAX" not in tickers
    assert "SEBLX" not in tickers

    tqcax_2025_lt = next(
        row
        for row in paid
        if row.ticker == "TQCAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert tqcax_2025_lt.amount == Decimal("0.850710")
    tqcax_2025_st = next(
        row
        for row in paid
        if row.ticker == "TQCAX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert tqcax_2025_st.amount == Decimal("0.117360")


def test_brown_remaining_share_class_pins() -> None:
    paid = parse_distribution_html(
        (ROOT / "brown_advisory" / "remaining_share_class_estimates.html").read_text(
            encoding="utf-8"
        ),
        source_url="https://www.brownadvisory.com/mf/funds/flexible-equity-fund",
        fund_family="Brown Advisory",
    )
    tickers = {row.ticker for row in paid if row.ticker}
    assert {"BIAFX", "BAFAX", "BIAWX"} <= tickers
    assert "BAFFX" not in tickers
    assert "BAFGX" not in tickers
    biafx = next(
        row
        for row in paid
        if row.ticker == "BIAFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert biafx.amount == Decimal("2.17")


def test_william_blair_remaining_share_class_pins() -> None:
    paid = parse_distribution_html(
        (
            ROOT / "william_blair" / "remaining_share_class_annual_distributions.html"
        ).read_text(encoding="utf-8"),
        source_url=(
            "https://media.im.williamblair.com/v1/media/edge/images/"
            "williamblaib9c8-wbim74f8-wbimprod42cd-8345/media/documents/"
            "resources/us/distributions/"
            "william-blair-funds---annual-distributions-2025---class-i-n-and-r6.pdf"
        ),
        fund_family="William Blair",
    )
    tickers = {row.ticker for row in paid if row.ticker}
    assert {"WSMDX", "WBSNX", "BGFRX"} <= tickers
    assert "BGFIX" not in tickers
    assert "LCGFX" not in tickers
    assert "WBSIX" not in tickers
    wsmdx_lt = next(
        row
        for row in paid
        if row.ticker == "WSMDX"
        and row.estimate_type == EstimateType.long_term_capital_gains
    )
    assert wsmdx_lt.amount == Decimal("0.52390")
    wbsnx_st = next(
        row
        for row in paid
        if row.ticker == "WBSNX"
        and row.estimate_type == EstimateType.short_term_capital_gains
    )
    assert wbsnx_st.amount == Decimal("0.64563")


def test_bny_remaining_share_class_pins() -> None:
    paid = parse_distribution_html(
        (ROOT / "bny_mellon" / "remaining_share_class_paid_year_end.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.bny.com/investments/us/en/intermediary/products/lt/"
            "fund/bny-mellon-international-equity-fund.html"
        ),
        fund_family="BNY Mellon / Dreyfus",
    )
    tickers = {row.ticker for row in paid if row.ticker}
    assert "NIEAX" in tickers
    assert "DGAGX" not in tickers
    nieax_lt = next(
        row
        for row in paid
        if row.ticker == "NIEAX"
        and row.estimate_type == EstimateType.long_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert nieax_lt.amount == Decimal("1.0947")
    nieax_st = next(
        row
        for row in paid
        if row.ticker == "NIEAX"
        and row.estimate_type == EstimateType.short_term_capital_gains
        and row.ex_date
        and row.ex_date.year == 2025
    )
    assert nieax_st.amount == Decimal("1.572")


def test_wave16_heroes_are_searchable(client: TestClient) -> None:
    for source in (
        VirtusSource(),
        AllspringSource(),
        TouchstoneSource(),
        BrownAdvisorySource(),
        WilliamBlairSource(),
        BnyMellonSource(),
    ):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": source.slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in (
        "MERFX",
        "PGUAX",
        "EAAFX",
        "SCSRX",
        "TQCAX",
        "BIAFX",
        "WSMDX",
        "NIEAX",
    ):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    merfx = client.get("/distributions", params={"q": "MERFX", "page_size": 50}).json()
    merfx_lt = [
        Decimal(row["amount"])
        for row in merfx["items"]
        if row.get("ticker") == "MERFX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("0.028392") in merfx_lt
