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
    assert amcap["upcoming"] is not None
    assert Decimal(amcap["upcoming"]["distribution_dollars"]) == Decimal(
        amcap["illustration"]["totals"]["distribution_dollars"]
    )
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
    assert body["periods"] == []
    assert body["summary"]["periods_compared"] == 0
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


def test_portfolio_compare_eric_beta_current_book(client: TestClient) -> None:
    """Locked Current AGTHX/DODIX/AMCAP/VIGAX 25% vs Proposed six heroes ~16.67%."""
    _seed(client, "american_funds", "dodge_cox", "vanguard", "t_rowe_price", "fidelity")
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {
                "label": "Current Allocation",
                "book_dollars": 1000000,
                "holdings": [
                    {"ticker": "AGTHX", "weight_pct": 25},
                    {"ticker": "DODIX", "weight_pct": 25, "nav_per_share": 100},
                    {"ticker": "AMCAP", "weight_pct": 25},
                    {"ticker": "VIGAX", "weight_pct": 25, "nav_per_share": 100},
                ],
            },
            "proposed": {
                "label": "Proposed Allocation",
                "book_dollars": 1000000,
                "holdings": [
                    {"ticker": "AMCPX", "weight_pct": 16.67},
                    {"ticker": "CGHM", "weight_pct": 16.67, "nav_per_share": 25},
                    {"ticker": "TRBCX", "weight_pct": 16.67, "nav_per_share": 100},
                    {"ticker": "VFIAX", "weight_pct": 16.67, "nav_per_share": 100},
                    {"ticker": "VBIAX", "weight_pct": 16.67, "nav_per_share": 100},
                    {"ticker": "FBGRX", "weight_pct": 16.67, "nav_per_share": 100},
                ],
            },
            "tax_rates": {},
            "combine_state_with_federal": True,
            "snapshot": {},
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["periods"] == []
    current_by_ticker = {h["ticker"]: h for h in body["current"]["holdings"]}
    assert current_by_ticker["AMCAP"]["fund_identifier"] == "amcap-fund"
    assert current_by_ticker["AGTHX"]["fund_identifier"] == "the-growth-fund-of-america"
    assert all(h["covered"] for h in body["current"]["holdings"])
    assert all(h["covered"] for h in body["proposed"]["holdings"])
    assert body["current"]["gaps"] == []
    assert body["proposed"]["gaps"] == []
    assert Decimal(body["current"]["coverage"]["coverage_pct"]) == Decimal("100.000000")
    assert Decimal(body["proposed"]["coverage"]["coverage_pct"]) == Decimal("100.000000")
    assert {h["ticker"] for h in body["proposed"]["holdings"]} == {
        "AMCPX",
        "CGHM",
        "TRBCX",
        "VFIAX",
        "VBIAX",
        "FBGRX",
    }


COMPARE_RATES = {
    "ordinary_income": 0.35,
    "long_term_capital_gains": 0.15,
    "short_term_capital_gains": 0.35,
    "qualified_dividend": 0.15,
    "state": 0.093,
}

YOY_BOOKS = {
    "current": {
        "label": "Current Allocation",
        "book_dollars": 1000000,
        "holdings": [{"fund_identifier": "amcap-fund", "weight_pct": 100}],
    },
    "proposed": {
        "label": "Proposed Allocation",
        "book_dollars": 1000000,
        "holdings": [
            {"fund_identifier": "amcap-fund", "weight_pct": 50},
            {"ticker": "CGHM", "weight_pct": 50},
        ],
    },
    "tax_rates": COMPARE_RATES,
    "combine_state_with_federal": True,
}


def _ingest_compare_book(client: TestClient) -> None:
    response = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "American Funds",
                    "fund_name": "AMCAP Fund",
                    "estimate_type": "total_capital_gains",
                    "amount": "2",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2024-12-15",
                    "publication_stage": "updated_estimate",
                    "source_url": "https://example.invalid/amcap-2024",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "AMCAP Fund",
                    "estimate_type": "total_capital_gains",
                    "amount": "4",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2025-09-19",
                    "publication_stage": "preliminary_estimate",
                    "source_url": "https://example.invalid/amcap-2025",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "Capital Group Municipal High-Income ETF",
                    "ticker": "CGHM",
                    "estimate_type": "total_capital_gains",
                    "amount": "1",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2024-12-15",
                    "publication_stage": "final",
                    "source_url": "https://example.invalid/cghm-2024",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "Capital Group Municipal High-Income ETF",
                    "ticker": "CGHM",
                    "estimate_type": "total_capital_gains",
                    "amount": "6",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2025-09-19",
                    "publication_stage": "preliminary_estimate",
                    "source_url": "https://example.invalid/cghm-2025",
                },
            ]
        },
    )
    assert response.status_code == 200, response.text


def test_portfolio_compare_yoy_periods_proposed_minus_current(client: TestClient) -> None:
    _ingest_compare_book(client)
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            **YOY_BOOKS,
            "periods": [
                {"year": 2024, "as_of": "2024-12-15"},
                {"year": 2025, "as_of": "2025-09-19"},
            ],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["periods"]) == 2
    assert any("latest period" in note for note in body["notes"])

    y2024 = body["periods"][0]
    assert y2024["year"] == 2024
    assert y2024["as_of"] == "2024-12-15"
    assert Decimal(y2024["current"]["totals"]["distribution_dollars"]) == Decimal("20000.00")
    assert Decimal(y2024["current"]["totals"]["estimated_tax"]) == Decimal("4860.00")
    assert Decimal(y2024["proposed"]["totals"]["distribution_dollars"]) == Decimal("15000.00")
    assert Decimal(y2024["proposed"]["totals"]["estimated_tax"]) == Decimal("3645.00")
    assert Decimal(y2024["deltas"]["distribution_dollars"]) == Decimal("-5000.00")
    assert Decimal(y2024["deltas"]["estimated_tax"]) == Decimal("-1215.00")
    assert Decimal(y2024["deltas"]["effective_tax_on_holding"]) == Decimal("-0.001215")
    assert Decimal(y2024["deltas"]["coverage_pct"]) == Decimal("0.000000")

    y2025 = body["periods"][1]
    assert y2025["year"] == 2025
    assert y2025["as_of"] == "2025-09-19"
    assert Decimal(y2025["current"]["totals"]["distribution_dollars"]) == Decimal("40000.00")
    assert Decimal(y2025["current"]["totals"]["estimated_tax"]) == Decimal("9720.00")
    assert Decimal(y2025["proposed"]["totals"]["distribution_dollars"]) == Decimal("50000.00")
    assert Decimal(y2025["proposed"]["totals"]["estimated_tax"]) == Decimal("12150.00")
    assert Decimal(y2025["deltas"]["distribution_dollars"]) == Decimal("10000.00")
    assert Decimal(y2025["deltas"]["estimated_tax"]) == Decimal("2430.00")
    assert Decimal(y2025["deltas"]["effective_tax_on_holding"]) == Decimal("0.002430")

    # Top-level current / proposed / deltas copy the latest period.
    assert Decimal(body["deltas"]["estimated_tax"]) == Decimal(y2025["deltas"]["estimated_tax"])
    assert Decimal(body["current"]["totals"]["distribution_dollars"]) == Decimal("40000.00")
    assert Decimal(body["proposed"]["totals"]["distribution_dollars"]) == Decimal("50000.00")

    summary = body["summary"]
    assert Decimal(summary["normalized_book_dollars"]) == Decimal("10000.00")
    assert Decimal(summary["estimated_tax"]) == Decimal("24.30")
    assert Decimal(summary["distribution_dollars"]) == Decimal("100.00")
    assert Decimal(summary["effective_tax_on_holding"]) == Decimal("0.002430")
    assert summary["periods_compared"] == 2
    assert Decimal(summary["total_tax_difference"]) == Decimal("12.15")
    assert Decimal(summary["distribution_dollars_difference"]) == Decimal("50.00")
    assert Decimal(summary["annualized_tax_drag_delta"]) == Decimal("0.000608")
    assert summary["common_inception"] == {
        "from_year": 2024,
        "to_year": 2025,
        "from_as_of": "2024-12-15",
        "to_as_of": "2025-09-19",
    }


def test_portfolio_compare_yoy_year_window_without_as_of(client: TestClient) -> None:
    _ingest_compare_book(client)
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            **YOY_BOOKS,
            "periods": [{"year": 2024}, {"year": 2025}],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["periods"]) == 2
    assert body["periods"][0]["as_of"] is None
    assert body["periods"][1]["as_of"] is None
    assert Decimal(body["periods"][0]["deltas"]["estimated_tax"]) == Decimal("-1215.00")
    assert Decimal(body["periods"][1]["deltas"]["estimated_tax"]) == Decimal("2430.00")
    assert Decimal(body["summary"]["annualized_tax_drag_delta"]) == Decimal("0.000608")


def test_portfolio_compare_yoy_fixture_smoke_af_and_trp(client: TestClient) -> None:
    _seed(client, "american_funds", "t_rowe_price")
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {
                "label": "Current Allocation",
                "book_dollars": 1000000,
                "holdings": [
                    {"fund_identifier": "amcap-fund", "weight_pct": 70},
                    {"ticker": "TRBCX", "weight_pct": 30, "nav_per_share": 100},
                ],
            },
            "proposed": {
                "label": "Proposed Allocation",
                "book_dollars": 1000000,
                "holdings": [
                    {"fund_identifier": "amcap-fund", "weight_pct": 40},
                    {"ticker": "CGHM", "weight_pct": 30},
                    {"ticker": "TRBCX", "weight_pct": 30, "nav_per_share": 100},
                ],
            },
            "tax_rates": {},
            "periods": [
                {"year": 2024, "as_of": "2024-09-18"},
                {"year": 2025, "as_of": "2025-09-19"},
            ],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["periods"]) == 2
    assert body["summary"]["periods_compared"] == 2
    y2024, y2025 = body["periods"]
    amcap_2024 = next(
        h for h in y2024["current"]["holdings"] if h["fund_identifier"] == "amcap-fund"
    )
    amcap_2025 = next(
        h for h in y2025["current"]["holdings"] if h["fund_identifier"] == "amcap-fund"
    )
    assert amcap_2024["covered"] is True
    assert amcap_2025["covered"] is True
    assert Decimal(y2024["deltas"]["estimated_tax"]) != Decimal(y2025["deltas"]["estimated_tax"])
    assert Decimal(body["deltas"]["estimated_tax"]) == Decimal(y2025["deltas"]["estimated_tax"])


def test_portfolio_compare_yoy_sparse_history_is_gap(client: TestClient) -> None:
    """A missed exact as_of pin is a gap, not $0 — even when the family has other vintages."""
    _seed(client, "vanguard", "fidelity", "dodge_cox")
    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {
                "book_dollars": 1000000,
                "holdings": [
                    {"ticker": "VFIAX", "weight_pct": 40, "nav_per_share": 100},
                    {"ticker": "FBGRX", "weight_pct": 30, "nav_per_share": 100},
                    {"ticker": "DODGX", "weight_pct": 30, "nav_per_share": 100},
                ],
            },
            "proposed": {
                "book_dollars": 1000000,
                "holdings": [
                    {"ticker": "VFIAX", "weight_pct": 50, "nav_per_share": 100},
                    {"ticker": "FBGRX", "weight_pct": 50, "nav_per_share": 100},
                ],
            },
            "tax_rates": {},
            "periods": [
                {"year": 2024, "as_of": "2024-12-15"},
                {"year": 2025, "as_of": "2025-12-24"},
            ],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    missed = body["periods"][0]
    assert missed["year"] == 2024
    assert all(not h["covered"] for h in missed["current"]["holdings"])
    assert all(not h["covered"] for h in missed["proposed"]["holdings"])
    assert len(missed["current"]["gaps"]) == 3
    assert {g["ticker"] for g in missed["current"]["gaps"]} == {"VFIAX", "FBGRX", "DODGX"}
    assert Decimal(missed["current"]["totals"]["estimated_tax"]) == Decimal("0.00")
    assert Decimal(missed["proposed"]["totals"]["estimated_tax"]) == Decimal("0.00")
    assert Decimal(missed["deltas"]["estimated_tax"]) == Decimal("0.00")
    assert Decimal(missed["current"]["coverage"]["coverage_pct"]) == Decimal("0.000000")
    assert any("Uncovered holdings" in note for note in body["notes"])

    vanguard_year = body["periods"][1]
    vfiax = next(h for h in vanguard_year["current"]["holdings"] if h["ticker"] == "VFIAX")
    fbgrx = next(h for h in vanguard_year["current"]["holdings"] if h["ticker"] == "FBGRX")
    dodgx = next(h for h in vanguard_year["current"]["holdings"] if h["ticker"] == "DODGX")
    assert vfiax["covered"] is True
    assert fbgrx["covered"] is False
    assert dodgx["covered"] is False
    assert Decimal(vanguard_year["current"]["coverage"]["coverage_pct"]) == Decimal("40.000000")


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
