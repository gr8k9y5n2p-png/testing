from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings


FIXTURES = Path(settings.fixtures_dir) / "performance"


def _adj(ticker: str, index: int) -> Decimal:
    payload = json.loads((FIXTURES / f"{ticker}.json").read_text(encoding="utf-8"))
    return Decimal(str(payload["points"][index]["adj_close"]))


def _expected_growth(ticker: str, start_dollars: Decimal = Decimal("10000")) -> Decimal:
    first = _adj(ticker, 0)
    last = _adj(ticker, -1)
    return (start_dollars * (last / first)).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def test_get_performance_agthx_vs_spy(client: TestClient) -> None:
    response = client.get("/performance", params={"ticker": "AGTHX", "mode": "fixture"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["fund_ticker"] == "AGTHX"
    assert body["benchmark_id"] == "SPY"
    assert body["benchmark_tracks"] == "S&P 500"
    assert "SPY" in body["benchmark_label"]
    assert body["is_proxy"] is True
    assert body["asset_class"] == "equity"
    assert Decimal(body["start_dollars"]) == Decimal("10000")
    assert body["frequency"] == "monthly"
    assert body["mode"] == "fixture"
    assert body["as_of"]
    assert body["fund"]["price_unit"] == "usd_per_share_adjusted"
    assert body["fund"]["return_unit"] == "decimal"
    assert body["fund"]["growth_unit"] == "usd"

    fund_points = body["fund"]["points"]
    bench_points = body["benchmark"]["points"]
    assert len(fund_points) >= 24
    assert len(fund_points) == len(bench_points)
    assert Decimal(fund_points[0]["growth_of_x"]) == Decimal("10000.00")
    assert Decimal(bench_points[0]["growth_of_x"]) == Decimal("10000.00")
    assert fund_points[0]["monthly_return"] is None
    assert Decimal(fund_points[-1]["growth_of_x"]) == _expected_growth("AGTHX")

    joined = " ".join(body["disclaimers"]).lower()
    assert "not tax advice" in joined
    assert "illustrative" in joined
    assert any("illustrate" in note.lower() for note in body["disclaimers"])


def test_post_performance_growth_slug_and_window(client: TestClient) -> None:
    response = client.post(
        "/performance/growth",
        json={
            "fund_identifier": "the-growth-fund-of-america",
            "benchmark": "SPY",
            "start_dollars": 10000,
            "start_date": "2020-01-01",
            "end_date": "2024-12-31",
            "mode": "fixture",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["fund_ticker"] == "AGTHX"
    assert body["benchmark_id"] == "SPY"
    assert body["start_date"] >= "2020-01-01"
    assert body["end_date"] <= "2024-12-31"
    assert Decimal(body["fund"]["points"][0]["growth_of_x"]) == Decimal("10000.00")


def test_performance_default_benchmarks_by_asset_class(client: TestClient) -> None:
    dodix = client.get("/performance", params={"ticker": "DODIX", "mode": "fixture"})
    assert dodix.status_code == 200, dodix.text
    dodix_body = dodix.json()
    assert dodix_body["asset_class"] == "fixed_income"
    assert dodix_body["benchmark_id"] == "AGG"
    assert dodix_body["is_proxy"] is True
    assert "Aggregate" in dodix_body["benchmark_label"]

    vtiax = client.get("/performance", params={"ticker": "VTIAX", "mode": "fixture"})
    assert vtiax.status_code == 200, vtiax.text
    vtiax_body = vtiax.json()
    assert vtiax_body["asset_class"] == "international"
    assert vtiax_body["benchmark_id"] == "VXUS"
    assert vtiax_body["is_proxy"] is True
    assert "ACWI" in vtiax_body["benchmark_label"]


def test_performance_explicit_benchmark_override(client: TestClient) -> None:
    response = client.get(
        "/performance",
        params={"ticker": "AGTHX", "benchmark": "VFIAX", "mode": "fixture"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["benchmark_id"] == "VFIAX"
    assert body["is_proxy"] is False
    assert body["benchmark"]["ticker"] == "VFIAX"


def test_performance_benchmark_hint_overrides_default(client: TestClient) -> None:
    response = client.get(
        "/performance",
        params={"ticker": "AGTHX", "benchmark_hint": "fixed_income", "mode": "fixture"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["asset_class"] == "fixed_income"
    assert body["benchmark_id"] == "AGG"


def test_performance_unknown_ticker_404(client: TestClient) -> None:
    response = client.get("/performance", params={"ticker": "ZZZZZ", "mode": "fixture"})
    assert response.status_code == 404


def test_performance_new_top40_distribution_tickers(client: TestClient) -> None:
    for ticker, asset_class, bench in (
        ("ABALX", "equity", "SPY"),
        ("VIGAX", "equity", "SPY"),
        ("TRBCX", "equity", "SPY"),
        ("DODGX", "equity", "SPY"),
        ("SWTSX", "equity", "SPY"),
        ("NOSIX", "equity", "SPY"),
        ("ALLW", "equity", "SPY"),
        ("JDCAX", "equity", "SPY"),
        ("MDDVX", "equity", "SPY"),
        ("SGENX", "equity", "SPY"),
        ("GDX", "equity", "SPY"),
        ("GTR", "equity", "SPY"),
    ):
        response = client.get("/performance", params={"ticker": ticker, "mode": "fixture"})
        assert response.status_code == 200, f"{ticker}: {response.text}"
        body = response.json()
        assert body["fund_ticker"] == ticker
        assert body["asset_class"] == asset_class
        assert body["benchmark_id"] == bench
        assert len(body["fund"]["points"]) >= 12
        assert Decimal(body["fund"]["points"][0]["growth_of_x"]) == Decimal("10000.00")


def test_performance_requires_fund(client: TestClient) -> None:
    missing = client.get("/performance", params={"mode": "fixture"})
    assert missing.status_code == 422
    empty = client.post("/performance/growth", json={"start_dollars": 10000, "mode": "fixture"})
    assert empty.status_code == 422


def test_performance_does_not_change_illustrate_contract(client: TestClient) -> None:
    """Smoke: tax compare path is still the same URL and still 422 without a book."""
    compare = client.post(
        "/illustrate/compare",
        json={
            "mode": "fund_vs_fund",
            "holding_dollars": 10000,
            "tax_rates": {},
            "left": {"selectors": {"ticker": "AGTHX"}},
            "right": {"selectors": {"ticker": "AMCPX"}},
            "periods": [{"year": 2025}],
        },
    )
    assert compare.status_code == 200
    body = compare.json()
    assert "periods" in body
    assert "mode" in body
    assert "fund" not in body
    assert "growth_of_x" not in body
