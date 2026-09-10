from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from app.models import EstimateType
from app.sources.next_tier import FranklinTempletonSource, NuveenSource
from app.sources.parser import parse_distribution_html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "fixtures"

HEROES = ("TIIRX", "NSBAX", "TINRX", "FFEIX", "EMO", "WDI", "PIM")


def test_wave9_tickers_are_exact_fund_hits(client: TestClient) -> None:
    for family in ("nuveen", "franklin_templeton"):
        fetched = client.post("/ingest/fetch", json={"fund_family": family, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in HEROES:
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    tiirx = client.get("/distributions", params={"q": "TIIRX", "page_size": 50}).json()
    amounts = [Decimal(row["amount"]) for row in tiirx["items"] if row.get("ticker") == "TIIRX"]
    assert Decimal("1.97") in amounts
    emo = client.get("/distributions", params={"q": "EMO", "page_size": 50}).json()
    emo_amounts = [Decimal(row["amount"]) for row in emo["items"] if row.get("ticker") == "EMO"]
    assert Decimal("3.504") in emo_amounts


def test_wave9_official_books_have_no_invented_managed_accounts() -> None:
    nuveen = parse_distribution_html(
        (ROOT / "nuveen" / "2025_estimated_taxable_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://nuveen",
        fund_family="Nuveen / TIAA",
    )
    assert {r.ticker for r in nuveen if r.ticker} >= {"TIIRX", "NSBAX", "TINRX"}
    assert len({r.ticker for r in nuveen if r.ticker}) >= 500
    assert not any("Managed Account" in (r.fund_name or "") for r in nuveen)
    tiirx_lt = next(
        r
        for r in nuveen
        if r.ticker == "TIIRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert tiirx_lt.amount == Decimal("1.97")

    fetched = NuveenSource().fetch(mode="fixture")
    assert len({r.ticker for r in fetched.records if r.ticker}) >= 500

    ft = FranklinTempletonSource().fetch(mode="fixture")
    ft_tickers = {r.ticker for r in ft.records if r.ticker}
    assert {"FT", "EMO", "WDI", "PIM"} <= ft_tickers
    assert "RMT" not in ft_tickers
