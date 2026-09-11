from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.models import EstimateType
from app.sources.families import VanguardSource
from app.sources.ici import parse_ici_primary
from app.sources.parser import parse_distribution_html
from app.sources.third_tier import AmericanCenturySource

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_avantis_remaining_2025_pins() -> None:
    rows = parse_distribution_html(
        (
            ROOT / "american_century" / "remaining_avantis_2025_estimated_distributions.html"
        ).read_text(encoding="utf-8"),
        source_url=(
            "https://res.avantisinvestors.com/docs/"
            "estimated-distributions-november-avantis.pdf"
        ),
        fund_family="American Century",
    )
    tickers = {row.ticker for row in rows if row.ticker}
    assert {"AVUV", "AVUVX", "AVCNX", "AVUS", "AVDE", "AVEM", "AVDV", "AVEEX"} <= tickers
    assert len(tickers) >= 40
    assert "TWCGX" not in tickers
    assert "AVIGX" not in tickers
    assert "AVBNX" not in tickers

    avuvx_oi = next(
        row
        for row in rows
        if row.ticker == "AVUVX" and row.estimate_type == EstimateType.ordinary_income
    )
    assert avuvx_oi.amount == Decimal("0.2523")
    avuvx_st = next(
        row
        for row in rows
        if row.ticker == "AVUVX"
        and row.estimate_type == EstimateType.short_term_capital_gains
    )
    assert avuvx_st.amount == Decimal("0.0753")
    avuvx_lt = next(
        row
        for row in rows
        if row.ticker == "AVUVX"
        and row.estimate_type == EstimateType.long_term_capital_gains
    )
    assert avuvx_lt.amount == Decimal("0.8562")

    avcnx_oi = next(
        row
        for row in rows
        if row.ticker == "AVCNX" and row.estimate_type == EstimateType.ordinary_income
    )
    assert avcnx_oi.amount == Decimal("0.2966")

    aveex_oi = next(
        row
        for row in rows
        if row.ticker == "AVEEX" and row.estimate_type == EstimateType.ordinary_income
    )
    assert aveex_oi.amount == Decimal("0.4256")
    aveex_st = next(
        row
        for row in rows
        if row.ticker == "AVEEX"
        and row.estimate_type == EstimateType.short_term_capital_gains
    )
    assert aveex_st.amount == Decimal("0.0090")
    aveex_lt = next(
        row
        for row in rows
        if row.ticker == "AVEEX"
        and row.estimate_type == EstimateType.long_term_capital_gains
    )
    assert aveex_lt.amount == Decimal("0.0618")

    avuv_oi = next(
        row
        for row in rows
        if row.ticker == "AVUV" and row.estimate_type == EstimateType.ordinary_income
    )
    assert avuv_oi.amount == Decimal("0.2735")
    assert not any(
        row.ticker == "AVUV"
        and row.estimate_type
        in (
            EstimateType.short_term_capital_gains,
            EstimateType.long_term_capital_gains,
        )
        for row in rows
    )

    avus_oi = next(
        row
        for row in rows
        if row.ticker == "AVUS" and row.estimate_type == EstimateType.ordinary_income
    )
    assert avus_oi.amount == Decimal("0.2475")
    avde_oi = next(
        row
        for row in rows
        if row.ticker == "AVDE" and row.estimate_type == EstimateType.ordinary_income
    )
    assert avde_oi.amount == Decimal("0.9030")
    avem_oi = next(
        row
        for row in rows
        if row.ticker == "AVEM" and row.estimate_type == EstimateType.ordinary_income
    )
    assert avem_oi.amount == Decimal("1.0414")
    avdv_oi = next(
        row
        for row in rows
        if row.ticker == "AVDV" and row.estimate_type == EstimateType.ordinary_income
    )
    assert avdv_oi.amount == Decimal("1.7896")


def test_vanguard_remaining_ici_2025_pins() -> None:
    rows = parse_ici_primary(
        (ROOT / "vanguard" / "remaining_ici_primary_2025.csv").read_text(encoding="utf-8"),
        source_url="https://advisors.vanguard.com/content/dam/fas/pdfs/ICIprimary_012026.pdf",
        fund_family="Vanguard",
    )
    tickers = {row.ticker for row in rows if row.ticker}
    assert {"VONE", "VTWO", "VTHR", "VCLT", "VEVFX"} <= tickers
    assert len(tickers) >= 60
    assert "VBINX" not in tickers
    assert "VOO" not in tickers
    assert "VONG" not in tickers
    assert "VNQ" not in tickers

    vone_oi = next(
        row
        for row in rows
        if row.ticker == "VONE" and row.estimate_type == EstimateType.ordinary_income
    )
    assert vone_oi.amount == Decimal("0.873200")
    vtwo_oi = next(
        row
        for row in rows
        if row.ticker == "VTWO" and row.estimate_type == EstimateType.ordinary_income
    )
    assert vtwo_oi.amount == Decimal("0.402800")
    vthr_oi = next(
        row
        for row in rows
        if row.ticker == "VTHR" and row.estimate_type == EstimateType.ordinary_income
    )
    assert vthr_oi.amount == Decimal("0.893000")

    vclt_income = sorted(
        (
            row.amount
            for row in rows
            if row.ticker == "VCLT" and row.estimate_type == EstimateType.ordinary_income
        )
    )
    assert vclt_income == [Decimal("0.340200"), Decimal("0.349200")]

    vevfx_oi = next(
        row
        for row in rows
        if row.ticker == "VEVFX" and row.estimate_type == EstimateType.ordinary_income
    )
    assert vevfx_oi.amount == Decimal("0.494900")
    vevfx_st = next(
        row
        for row in rows
        if row.ticker == "VEVFX"
        and row.estimate_type == EstimateType.short_term_capital_gains
    )
    assert vevfx_st.amount == Decimal("0.218968")
    vevfx_lt = next(
        row
        for row in rows
        if row.ticker == "VEVFX"
        and row.estimate_type == EstimateType.long_term_capital_gains
    )
    assert vevfx_lt.amount == Decimal("3.582907")


def test_wave17_heroes_are_searchable(client: TestClient) -> None:
    for source in (VanguardSource(), AmericanCenturySource()):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": source.slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("VONE", "VTWO", "VCLT", "VEVFX", "AVUV", "AVUVX", "AVUS", "AVEEX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    vevfx = client.get("/distributions", params={"q": "VEVFX", "page_size": 50}).json()
    vevfx_lt = [
        Decimal(row["amount"])
        for row in vevfx["items"]
        if row.get("ticker") == "VEVFX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025")
    ]
    assert Decimal("3.582907") in vevfx_lt

    avuvx = client.get("/distributions", params={"q": "AVUVX", "page_size": 50}).json()
    avuvx_lt = [
        Decimal(row["amount"])
        for row in avuvx["items"]
        if row.get("ticker") == "AVUVX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("0.8562") in avuvx_lt
