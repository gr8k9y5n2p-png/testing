from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from app.models import EstimateType
from app.sources.ark import ArkSource
from app.sources.parser import parse_distribution_html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "fixtures"

MEGA = ("QQQ", "IVV", "IWM", "EFA", "AGG", "GLD", "SCHD", "ACWX", "IEMG", "IEFA", "ITOT", "TLT", "LQD", "HYG", "VNQ", "ARKK", "BNDX")


def test_mega_etf_tickers_are_exact_fund_hits(client: TestClient) -> None:
    for family in ("blackrock", "vanguard", "invesco", "state_street", "schwab", "ark"):
        fetched = client.post("/ingest/fetch", json={"fund_family": family, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in MEGA:
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"
        exact = next(item for item in body["items"] if item["ticker"] == ticker)
        assert exact["ticker"] == ticker

    qqq = client.get("/funds", params={"q": "QQQ"}).json()["items"]
    assert any(item["ticker"] == "QQQ" for item in qqq)
    ivv = client.get("/distributions", params={"q": "IVV", "page_size": 50}).json()
    amounts = [Decimal(row["amount"]) for row in ivv["items"] if row.get("ticker") == "IVV"]
    assert Decimal("2.413592") in amounts


def test_ark_2021_final_pins() -> None:
    records = parse_distribution_html(
        (ROOT / "ark" / "2021_final_distributions.html").read_text(encoding="utf-8"),
        source_url=(
            "https://etfs.ark-funds.com/hubfs/1_Download_Files_ETF_Website/"
            "Distribution%20Files/ARKETFs_12021_Handout_Capital_Gains_Distribution_2021.pdf"
        ),
        fund_family="ARK Invest",
    )
    arkk_st = next(
        r
        for r in records
        if r.ticker == "ARKK" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    arkk_lt = next(
        r
        for r in records
        if r.ticker == "ARKK" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert arkk_st.amount == Decimal("0.5249")
    assert arkk_lt.amount == Decimal("0.2577")
    assert {r.ticker for r in records} == {"ARKQ", "ARKW", "ARKK", "ARKG", "PRNT", "IZRL", "CTRU"}
    assert not any(r.ticker in {"ARKF", "ARKX"} for r in records)

    fetched = ArkSource().fetch(mode="fixture")
    assert any(r.ticker == "ARKK" for r in fetched.records)
