from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from app.schemas import normalize_weight_pct

RATES = {
    "ordinary_income": 0.37,
    "long_term_capital_gains": 0.20,
    "short_term_capital_gains": 0.37,
    "qualified_dividend": 0.20,
    "state": 0.05,
}

SNAPSHOT = {
    "prefer_publication_stages": [
        "preliminary_estimate",
        "updated_estimate",
        "final",
        "paid",
    ]
}


def _seed(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200


def test_normalize_weight_pct() -> None:
    assert normalize_weight_pct(Decimal("40")) == Decimal("0.4")
    assert normalize_weight_pct(Decimal("0.40")) == Decimal("0.40")
    assert normalize_weight_pct(Decimal("1")) == Decimal("1")
    assert normalize_weight_pct(Decimal("0.01")) == Decimal("0.01")


def test_portfolio_compare_current_vs_proposed(client: TestClient) -> None:
    _seed(client)
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {
                "label": "Current",
                "holdings": [
                    {"ticker": "CGHM", "holding_dollars": 250000},
                    {
                        "fund_identifier": "amcap-fund",
                        "fund_family": "American Funds",
                        "holding_dollars": 1000000,
                    },
                    {"ticker": "XYZAX", "fund_family": "dimensional", "holding_dollars": 150000},
                ],
            },
            "proposed": {
                "label": "Proposed",
                "holdings": [
                    {"ticker": "CGHM", "holding_dollars": 250000},
                    {
                        "fund_identifier": "amcap-fund",
                        "fund_family": "American Funds",
                        "holding_dollars": 1150000,
                    },
                ],
            },
            "tax_rates": RATES,
            "combine_state_with_federal": True,
            "snapshot": SNAPSHOT,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["current"]["label"] == "Current"
    assert body["proposed"]["label"] == "Proposed"
    assert Decimal(body["current"]["coverage"]["dollars_total"]) == Decimal("1400000.00")
    assert Decimal(body["current"]["coverage"]["dollars_uncovered"]) == Decimal("150000.00")
    assert Decimal(body["current"]["totals"]["estimated_tax"]) == Decimal("10000.00")
    assert Decimal(body["current"]["totals"]["distribution_dollars"]) == Decimal("40000.00")
    assert len(body["current"]["gaps"]) == 1
    assert body["current"]["gaps"][0]["ticker"] == "XYZAX"

    assert Decimal(body["proposed"]["coverage"]["dollars_total"]) == Decimal("1400000.00")
    assert Decimal(body["proposed"]["coverage"]["dollars_uncovered"]) == Decimal("0.00")
    assert Decimal(body["proposed"]["coverage"]["coverage_pct"]) == Decimal("100.000000")
    assert Decimal(body["proposed"]["totals"]["distribution_dollars"]) == Decimal("46000.00")
    assert Decimal(body["proposed"]["totals"]["estimated_tax"]) == Decimal("11500.00")
    assert body["proposed"]["gaps"] == []

    deltas = body["deltas"]
    assert Decimal(deltas["estimated_tax"]) == Decimal("1500.00")
    assert Decimal(deltas["distribution_dollars"]) == Decimal("6000.00")
    assert Decimal(deltas["coverage_pct"]) == Decimal("10.714286")
    assert Decimal(deltas["dollars_covered"]) == Decimal("150000.00")
    assert Decimal(deltas["dollars_uncovered"]) == Decimal("-150000.00")
    assert deltas["holdings_uncovered"] == -1

    assert Decimal(body["summary"]["normalized_book_dollars"]) == Decimal("1400000.00")
    assert Decimal(body["summary"]["estimated_tax"]) == Decimal("1500.00")
    assert "periods[]" in " ".join(body["notes"])
    assert any("Uncovered holdings" in note for note in body["notes"])
    assert any("XYZAX" in gap["ticker"] for gap in body["current"]["gaps"])


def test_portfolio_compare_weight_pct_and_book(client: TestClient) -> None:
    _seed(client)
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            "book_dollars": 1000000,
            "current": {
                "holdings": [
                    {"fund_identifier": "amcap-fund", "weight_pct": 80},
                    {"ticker": "CGHM", "weight_pct": 20},
                ]
            },
            "proposed": {
                "holdings": [
                    {"fund_identifier": "amcap-fund", "weight_pct": 0.50},
                    {"ticker": "CGHM", "weight_pct": 0.50},
                ]
            },
            "tax_rates": RATES,
            "snapshot": SNAPSHOT,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    current_amcap = next(h for h in body["current"]["holdings"] if h["fund_identifier"] == "amcap-fund")
    proposed_amcap = next(h for h in body["proposed"]["holdings"] if h["fund_identifier"] == "amcap-fund")
    assert Decimal(current_amcap["holding_dollars"]) == Decimal("800000.00")
    assert Decimal(proposed_amcap["holding_dollars"]) == Decimal("500000.00")
    assert body["current"]["label"] == "Current Allocation"
    assert body["proposed"]["label"] == "Proposed Allocation"
    assert Decimal(body["current"]["totals"]["distribution_dollars"]) == Decimal("32000.00")
    assert Decimal(body["proposed"]["totals"]["distribution_dollars"]) == Decimal("20000.00")
    assert Decimal(body["deltas"]["distribution_dollars"]) == Decimal("-12000.00")
    assert Decimal(body["deltas"]["estimated_tax"]) == Decimal("-3000.00")


def test_portfolio_compare_preserves_gaps_on_both_sides(client: TestClient) -> None:
    _seed(client)
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {
                "holdings": [{"ticker": "XYZAX", "holding_dollars": 100000}]
            },
            "proposed": {
                "holdings": [
                    {"ticker": "XYZAX", "holding_dollars": 40000},
                    {"fund_identifier": "amcap-fund", "holding_dollars": 60000},
                ]
            },
            "tax_rates": RATES,
            "snapshot": SNAPSHOT,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["current"]["gaps"]) == 1
    assert body["current"]["holdings"][0]["covered"] is False
    assert any(gap["ticker"] == "XYZAX" for gap in body["proposed"]["gaps"])
    assert any("Uncovered holdings" in note for note in body["notes"])
    assert Decimal(body["proposed"]["totals"]["distribution_dollars"]) == Decimal("2400.00")


def test_portfolio_compare_validation(client: TestClient) -> None:
    missing_side = client.post(
        "/illustrate/portfolio/compare",
        json={"current": {"holdings": [{"ticker": "AMCAP", "holding_dollars": 1000}]}},
    )
    assert missing_side.status_code == 422

    no_dollars = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {"holdings": [{"ticker": "AMCAP"}]},
            "proposed": {"holdings": [{"ticker": "AMCAP", "holding_dollars": 1000}]},
        },
    )
    assert no_dollars.status_code == 422

    weight_without_book = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {"holdings": [{"ticker": "AMCAP", "weight_pct": 50}]},
            "proposed": {"holdings": [{"ticker": "AMCAP", "holding_dollars": 1000}]},
        },
    )
    assert weight_without_book.status_code == 422
