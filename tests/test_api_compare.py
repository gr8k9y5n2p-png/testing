from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

RATES = {
    "ordinary_income": 0.35,
    "long_term_capital_gains": 0.15,
    "short_term_capital_gains": 0.35,
    "qualified_dividend": 0.15,
    "state": 0.093,
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
                    "amount_min": "3",
                    "amount_max": "5",
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


def test_compare_fund_vs_fund_chart_contract(client: TestClient) -> None:
    _ingest_compare_book(client)
    response = client.post(
        "/illustrate/compare",
        json={
            "mode": "fund_vs_fund",
            "holding_dollars": 1000000,
            "tax_rates": RATES,
            "combine_state_with_federal": True,
            "left": {"label": "Fund A", "selectors": {"fund_identifier": "amcap-fund"}},
            "right": {"label": "Fund B", "selectors": {"ticker": "CGHM"}},
            "periods": [
                {"year": 2024, "as_of": "2024-12-15"},
                {"year": 2025, "as_of": "2025-09-19"},
            ],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "fund_vs_fund"
    assert len(body["periods"]) == 2
    assert any("right − left" in note or "right - left" in note for note in body["notes"])

    y2024 = body["periods"][0]
    assert y2024["year"] == 2024
    assert y2024["as_of"] == "2024-12-15"
    assert y2024["left"]["label"] == "Fund A"
    assert y2024["right"]["label"] == "Fund B"
    assert y2024["left"]["matched"] is True
    assert y2024["right"]["matched"] is True
    assert Decimal(y2024["left"]["totals"]["distribution_dollars"]) == Decimal("20000.00")
    assert Decimal(y2024["right"]["totals"]["distribution_dollars"]) == Decimal("10000.00")
    assert Decimal(y2024["deltas"]["distribution_dollars"]) == Decimal("-10000.00")
    assert Decimal(y2024["deltas"]["estimated_tax"]) == Decimal("-2430.00")
    assert Decimal(y2024["deltas"]["federal_tax"]) == Decimal("-1500.00")
    assert Decimal(y2024["deltas"]["state_tax"]) == Decimal("-930.00")
    assert Decimal(y2024["deltas"]["effective_tax_on_holding"]) == Decimal("-0.002430")

    y2025 = body["periods"][1]
    assert y2025["year"] == 2025
    assert y2025["as_of"] == "2025-09-19"
    assert Decimal(y2025["left"]["totals"]["distribution_dollars"]) == Decimal("40000.00")
    assert Decimal(y2025["right"]["totals"]["distribution_dollars"]) == Decimal("60000.00")
    assert Decimal(y2025["deltas"]["distribution_dollars"]) == Decimal("20000.00")
    assert Decimal(y2025["deltas"]["estimated_tax"]) == Decimal("4860.00")
    assert Decimal(y2025["deltas"]["effective_tax_on_holding"]) == Decimal("0.004860")
    assert Decimal(y2025["deltas"]["distribution_dollars_min"]) == Decimal("30000.00")
    assert Decimal(y2025["deltas"]["distribution_dollars_max"]) == Decimal("10000.00")


def test_compare_yoy_same_fund_periods(client: TestClient) -> None:
    _ingest_compare_book(client)
    response = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 1000000,
            "tax_rates": RATES,
            "combine_state_with_federal": True,
            "selectors": {"fund_identifier": "amcap-fund"},
            "periods": [
                {"year": 2024, "as_of": "2024-12-15"},
                {"year": 2025, "as_of": "2025-09-19"},
            ],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "yoy"
    assert len(body["periods"]) == 1
    period = body["periods"][0]
    assert period["year"] == 2025
    assert period["as_of"] == "2025-09-19"
    assert period["left"]["label"] == "2024"
    assert period["right"]["label"] == "2025"
    assert Decimal(period["left"]["totals"]["distribution_dollars"]) == Decimal("20000.00")
    assert Decimal(period["right"]["totals"]["distribution_dollars"]) == Decimal("40000.00")
    assert Decimal(period["deltas"]["distribution_dollars"]) == Decimal("20000.00")
    assert Decimal(period["deltas"]["estimated_tax"]) == Decimal("4860.00")
    assert Decimal(period["deltas"]["effective_tax_on_holding"]) == Decimal("0.004860")


def test_compare_yoy_left_right_as_of(client: TestClient) -> None:
    _ingest_compare_book(client)
    response = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 1000000,
            "tax_rates": RATES,
            "left": {
                "label": "2024 vintage",
                "selectors": {"fund_identifier": "amcap-fund", "as_of": "2024-12-15"},
            },
            "right": {
                "label": "2025 vintage",
                "selectors": {"fund_identifier": "amcap-fund", "as_of": "2025-09-19"},
            },
        },
    )
    assert response.status_code == 200, response.text
    period = response.json()["periods"][0]
    assert period["left"]["label"] == "2024 vintage"
    assert period["right"]["label"] == "2025 vintage"
    assert Decimal(period["deltas"]["effective_tax_on_holding"]) == Decimal("0.004860")


def test_compare_empty_tax_rates_and_missing_side(client: TestClient) -> None:
    _ingest_compare_book(client)
    response = client.post(
        "/illustrate/compare",
        json={
            "mode": "fund_vs_fund",
            "holding_dollars": 1000000,
            "tax_rates": {},
            "left": {"label": "Fund A", "selectors": {"fund_identifier": "amcap-fund"}},
            "right": {"label": "Missing", "selectors": {"ticker": "ZZNOPE"}},
            "periods": [{"year": 2025, "as_of": "2025-09-19"}],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    period = body["periods"][0]
    assert period["left"]["matched"] is True
    assert period["right"]["matched"] is False
    assert Decimal(period["right"]["totals"]["estimated_tax"]) == Decimal("0.00")
    assert Decimal(period["deltas"]["distribution_dollars"]) == Decimal("-40000.00")
    assert any("ZZNOPE" in note or "No distribution" in note for note in body["notes"])
    assert Decimal(period["left"]["tax_rates"]["long_term_capital_gains"]) == Decimal("0.20")


def test_compare_validation(client: TestClient) -> None:
    missing_right = client.post(
        "/illustrate/compare",
        json={
            "mode": "fund_vs_fund",
            "holding_dollars": 1000000,
            "left": {"selectors": {"fund_identifier": "amcap-fund"}},
        },
    )
    assert missing_right.status_code == 422

    yoy_one_period = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 1000000,
            "selectors": {"fund_identifier": "amcap-fund"},
            "periods": [{"year": 2025, "as_of": "2025-09-19"}],
        },
    )
    assert yoy_one_period.status_code == 422
