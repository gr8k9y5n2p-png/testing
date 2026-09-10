from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.models import EstimateType
from app.sources.next_tier import ColumbiaThreadneedleSource
from app.sources.parser import parse_distribution_html
from app.sources.sixth_tier import FirstTrustSource

ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def test_columbia_full_share_class_year_end_pins() -> None:
    paid_2025 = parse_distribution_html(
        (ROOT / "columbia_threadneedle" / "2025_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.columbiathreadneedleus.com/binaries/content/assets/"
            "cti/public/2025-cap-gain-distributions---mutual-funds.pdf"
        ),
        fund_family="Columbia Threadneedle",
    )
    tickers_2025 = {r.ticker for r in paid_2025 if r.ticker}
    assert {"LBSAX", "GSFTX", "CDDRX", "CBLAX", "LEGAX", "ELGAX", "LCCAX"} <= tickers_2025
    assert len(tickers_2025) >= 200
    assert not any((r.ticker or "").startswith("ZZ") for r in paid_2025)

    lbsax_lt = next(
        r
        for r in paid_2025
        if r.ticker == "LBSAX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert lbsax_lt.amount == Decimal("1.33133")
    gsftx_lt = next(
        r
        for r in paid_2025
        if r.ticker == "GSFTX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert gsftx_lt.amount == Decimal("1.33133")

    paid_2024 = parse_distribution_html(
        (ROOT / "columbia_threadneedle" / "2024_year_end_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.columbiathreadneedleus.com/binaries/content/assets/"
            "cti/public/2024-cap-gains---mutual-funds.pdf"
        ),
        fund_family="Columbia Threadneedle",
    )
    tickers_2024 = {r.ticker for r in paid_2024 if r.ticker}
    assert {"LBSAX", "GSFTX", "CDDRX", "LEGAX", "ELGAX"} <= tickers_2024
    assert len(tickers_2024) >= 180
    lbsax_2024 = next(
        r
        for r in paid_2024
        if r.ticker == "LBSAX"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert lbsax_2024.amount == Decimal("1.38581")


def test_first_trust_december_family_declaration_pins() -> None:
    dec_2025 = parse_distribution_html(
        (ROOT / "first_trust" / "2025_december_etf_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
            "ContentGUID=cf8dadde-0a3c-463c-b694-5111dbd18e39"
        ),
        fund_family="First Trust",
    )
    tickers = {r.ticker for r in dec_2025 if r.ticker}
    assert {"FVD", "FTHI", "WCME", "FTCB", "FPE"} <= tickers
    assert len(tickers) >= 150

    fvd = next(
        r
        for r in dec_2025
        if r.ticker == "FVD" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fvd.amount == Decimal("0.3186")
    fthi = next(
        r
        for r in dec_2025
        if r.ticker == "FTHI" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fthi.amount == Decimal("0.1770")
    ftcb_lt = next(
        r
        for r in dec_2025
        if r.ticker == "FTCB"
        and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert ftcb_lt.amount == Decimal("0.0473")

    dec_2024 = parse_distribution_html(
        (ROOT / "first_trust" / "2024_december_etf_distributions.html").read_text(
            encoding="utf-8"
        ),
        source_url=(
            "https://www.ftportfolios.com/Common/ContentFileLoader.aspx?"
            "ContentGUID=93a2ae96-a7c6-468c-b68b-8f516d1de5c4"
        ),
        fund_family="First Trust",
    )
    fvd_2024 = next(
        r
        for r in dec_2024
        if r.ticker == "FVD" and r.estimate_type == EstimateType.ordinary_income
    )
    assert fvd_2024.amount == Decimal("0.2752")


def test_wave11_heroes_are_searchable(client: TestClient) -> None:
    for source in (ColumbiaThreadneedleSource(), FirstTrustSource()):
        fetched = client.post(
            "/ingest/fetch", json={"fund_family": source.slug, "mode": "fixture"}
        )
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("LBSAX", "GSFTX", "CDDRX", "CBLAX", "LEGAX", "ELGAX", "FVD", "FTHI", "WCME"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    lbsax = client.get("/distributions", params={"q": "LBSAX", "page_size": 50}).json()
    amounts = [
        Decimal(row["amount"])
        for row in lbsax["items"]
        if row.get("ticker") == "LBSAX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("1.33133") in amounts
    assert Decimal("1.38581") in amounts

    gsftx = client.get("/distributions", params={"q": "GSFTX", "page_size": 50}).json()
    gsftx_lt = [
        Decimal(row["amount"])
        for row in gsftx["items"]
        if row.get("ticker") == "GSFTX"
        and row.get("estimate_type") == "long_term_capital_gains"
    ]
    assert Decimal("1.33133") in gsftx_lt

    fvd = client.get("/distributions", params={"q": "FVD", "page_size": 50}).json()
    fvd_income = [
        Decimal(row["amount"])
        for row in fvd["items"]
        if row.get("ticker") == "FVD" and row.get("estimate_type") == "ordinary_income"
    ]
    assert Decimal("0.3186") in fvd_income
    assert Decimal("0.2519") in fvd_income
