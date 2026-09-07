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

HERO_FAMILIES = ("american_funds", "fidelity", "t_rowe_price", "vanguard")


def _seed(client: TestClient, *families: str) -> None:
    slugs = families or ("american_funds",)
    for slug in slugs:
        fetched = client.post("/ingest/fetch", json={"fund_family": slug, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text


def test_normalize_weight_pct_is_ui_percent() -> None:
    assert normalize_weight_pct(Decimal("25")) == Decimal("0.25")
    assert normalize_weight_pct(Decimal("100")) == Decimal("1")
    assert normalize_weight_pct(Decimal("1")) == Decimal("0.01")


def test_portfolio_compare_im_field_names_and_hero_tickers(client: TestClient) -> None:
    _seed(client, *HERO_FAMILIES)
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {
                "label": "Current Allocation",
                "book_dollars": 1000000,
                "holdings": [
                    {"ticker": "AMCPX", "fund_identifier": "amcap-fund", "weight_pct": 25},
                    {"ticker": "CGHM", "weight_pct": 15},
                    {"ticker": "TRBCX", "weight_pct": 20, "nav_per_share": 100},
                    {"ticker": "VFIAX", "weight_pct": 15, "nav_per_share": 100},
                    {"ticker": "VBIAX", "weight_pct": 10, "nav_per_share": 100},
                    {"ticker": "FBGRX", "holding_dollars": 150000, "nav_per_share": 100},
                ],
            },
            "proposed": {
                "label": "Proposed Allocation",
                "book_dollars": 1000000,
                "holdings": [
                    {"ticker": "AMCPX", "weight_pct": 20, "nav_per_share": 100},
                    {"ticker": "CGHM", "holding_dollars": 100000, "nav_per_share": 25},
                    {"ticker": "TRBCX", "weight_pct": 10, "nav_per_share": 100},
                    {"ticker": "VFIAX", "weight_pct": 30, "nav_per_share": 100},
                    {"ticker": "VBIAX", "weight_pct": 20, "nav_per_share": 100},
                    {"ticker": "FBGRX", "weight_pct": 10, "nav_per_share": 100},
                ],
            },
            "tax_rates": {},
            "combine_state_with_federal": True,
            "snapshot": {},
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["current"]["label"] == "Current Allocation"
    assert body["proposed"]["label"] == "Proposed Allocation"
    assert set(body["current"].keys()) >= {
        "holdings",
        "totals",
        "coverage",
        "gaps",
        "warnings",
        "notes",
        "tax_rates",
        "label",
    }
    assert set(body["deltas"].keys()) >= {
        "estimated_tax",
        "distribution_dollars",
        "effective_tax_on_holding",
        "coverage_pct",
    }

    current_tickers = {h["ticker"] for h in body["current"]["holdings"]}
    proposed_tickers = {h["ticker"] for h in body["proposed"]["holdings"]}
    assert {"AMCPX", "CGHM", "TRBCX", "VFIAX", "VBIAX", "FBGRX"} <= current_tickers
    assert {"AMCPX", "CGHM", "TRBCX", "VFIAX", "VBIAX", "FBGRX"} <= proposed_tickers

    amcap = next(
        h
        for h in body["current"]["holdings"]
        if h["fund_identifier"] == "amcap-fund" or h["ticker"] == "AMCPX"
    )
    assert amcap["covered"] is True
    assert Decimal(amcap["holding_dollars"]) == Decimal("250000.00")
    cghm = next(h for h in body["current"]["holdings"] if h["ticker"] == "CGHM")
    assert Decimal(cghm["holding_dollars"]) == Decimal("150000.00")
    fbgrx = next(h for h in body["current"]["holdings"] if h["ticker"] == "FBGRX")
    assert Decimal(fbgrx["holding_dollars"]) == Decimal("150000.00")
    assert fbgrx["covered"] is True

    assert all(h["covered"] for h in body["current"]["holdings"])
    assert all(h["covered"] for h in body["proposed"]["holdings"])
    assert body["current"]["gaps"] == []
    assert body["proposed"]["gaps"] == []

    proposed_amcap = next(
        h
        for h in body["proposed"]["holdings"]
        if h["fund_identifier"] == "amcap-fund" or h["ticker"] == "AMCPX"
    )
    assert Decimal(proposed_amcap["holding_dollars"]) == Decimal("200000.00")

    deltas = body["deltas"]
    assert Decimal(deltas["estimated_tax"]) == (
        Decimal(body["proposed"]["totals"]["estimated_tax"])
        - Decimal(body["current"]["totals"]["estimated_tax"])
    )
    assert Decimal(deltas["distribution_dollars"]) == (
        Decimal(body["proposed"]["totals"]["distribution_dollars"])
        - Decimal(body["current"]["totals"]["distribution_dollars"])
    )
    assert Decimal(deltas["effective_tax_on_holding"]) == (
        Decimal(body["proposed"]["totals"]["effective_tax_on_holding"])
        - Decimal(body["current"]["totals"]["effective_tax_on_holding"])
    )
    assert Decimal(deltas["coverage_pct"]) == Decimal("0.000000")
    assert Decimal(body["summary"]["normalized_book_dollars"]) == Decimal("10000.00")
    assert "periods[]" in " ".join(body["notes"])


def test_portfolio_compare_current_vs_proposed_dollars(client: TestClient) -> None:
    _seed(client)
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {
                "label": "Current Allocation",
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
                "label": "Proposed Allocation",
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

    assert Decimal(body["current"]["coverage"]["dollars_uncovered"]) == Decimal("150000.00")
    assert body["current"]["gaps"][0]["ticker"] == "XYZAX"
    assert body["proposed"]["gaps"] == []
    assert Decimal(body["deltas"]["estimated_tax"]) == Decimal("1500.00")
    assert Decimal(body["deltas"]["distribution_dollars"]) == Decimal("6000.00")
    assert Decimal(body["deltas"]["coverage_pct"]) == Decimal("10.714286")
    assert Decimal(body["summary"]["normalized_book_dollars"]) == Decimal("10000.00")
    assert Decimal(body["summary"]["estimated_tax"]) == Decimal("10.71")
    assert any("Uncovered holdings" in note for note in body["notes"])


def test_portfolio_compare_side_book_dollars_weight_pct(client: TestClient) -> None:
    _seed(client)
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {
                "label": "Current Allocation",
                "book_dollars": 1000000,
                "holdings": [
                    {"fund_identifier": "amcap-fund", "weight_pct": 80},
                    {"ticker": "CGHM", "weight_pct": 20},
                ],
            },
            "proposed": {
                "label": "Proposed Allocation",
                "book_dollars": 1000000,
                "holdings": [
                    {"fund_identifier": "amcap-fund", "weight_pct": 50},
                    {"ticker": "CGHM", "holding_dollars": 500000},
                ],
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


def test_portfolio_compare_validation(client: TestClient) -> None:
    missing_side = client.post(
        "/illustrate/portfolio/compare",
        json={"current": {"holdings": [{"ticker": "CGHM", "holding_dollars": 1000}]}},
    )
    assert missing_side.status_code == 422

    no_dollars = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {"holdings": [{"ticker": "CGHM"}]},
            "proposed": {"holdings": [{"ticker": "CGHM", "holding_dollars": 1000}]},
        },
    )
    assert no_dollars.status_code == 422

    both = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {
                "book_dollars": 1000000,
                "holdings": [{"ticker": "CGHM", "holding_dollars": 250000, "weight_pct": 25}],
            },
            "proposed": {"holdings": [{"ticker": "CGHM", "holding_dollars": 1000}]},
        },
    )
    assert both.status_code == 422

    weight_without_book = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {"holdings": [{"ticker": "CGHM", "weight_pct": 50}]},
            "proposed": {"holdings": [{"ticker": "CGHM", "holding_dollars": 1000}]},
        },
    )
    assert weight_without_book.status_code == 422
