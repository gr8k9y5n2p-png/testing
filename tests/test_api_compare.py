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

    summary = body["summary"]
    assert Decimal(summary["normalized_holding_dollars"]) == Decimal("10000")
    assert summary["periods_compared"] == 2
    assert Decimal(summary["total_tax_difference"]) == Decimal("24.30")
    assert Decimal(summary["distribution_dollars_difference"]) == Decimal("100.00")
    assert Decimal(summary["annualized_tax_drag_delta"]) == Decimal("0.001215")
    assert summary["common_inception"] == {
        "from_year": 2024,
        "to_year": 2025,
        "from_as_of": "2024-12-15",
        "to_as_of": "2025-09-19",
    }
    assert summary["upcoming_taxable_distribution"] is None
    assert any("upcoming_taxable_distribution is null" in note for note in body["notes"])
    assert "estimated_tax_min" not in summary
    assert "estimated_tax_max" not in summary
    assert "distribution_dollars_min" not in summary
    assert "distribution_dollars_max" not in summary


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
    summary = body["summary"]
    assert summary["periods_compared"] == 1
    assert Decimal(summary["total_tax_difference"]) == Decimal("48.60")
    assert Decimal(summary["distribution_dollars_difference"]) == Decimal("200.00")
    assert Decimal(summary["annualized_tax_drag_delta"]) == Decimal("0.004860")
    assert summary["common_inception"]["from_year"] == 2024
    assert summary["common_inception"]["to_year"] == 2025


def test_compare_yoy_amcap_sketch_infers_mode(client: TestClient) -> None:
    """Interactive Modules YoY sketch: no mode, left/right as_of, tax_rates {}."""
    _ingest_compare_book(client)
    response = client.post(
        "/illustrate/compare",
        json={
            "holding_dollars": 1000000,
            "nav_per_share": None,
            "tax_rates": {},
            "combine_state_with_federal": True,
            "left": {
                "label": "2024",
                "selectors": {"fund_identifier": "amcap-fund", "as_of": "2024-12-15"},
            },
            "right": {
                "label": "2025",
                "selectors": {"fund_identifier": "amcap-fund", "as_of": "2025-09-19"},
            },
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["mode"] == "yoy"
    assert body["left"]["label"] == "2024"
    assert body["right"]["label"] == "2025"
    assert body["left"]["matched"] is True
    assert body["right"]["matched"] is True
    assert Decimal(body["left"]["totals"]["distribution_dollars"]) == Decimal("20000.00")
    assert Decimal(body["right"]["totals"]["distribution_dollars"]) == Decimal("40000.00")
    assert Decimal(body["deltas"]["distribution_dollars"]) == Decimal("20000.00")
    assert Decimal(body["deltas"]["estimated_tax"]) == Decimal("5000.00")
    assert Decimal(body["deltas"]["effective_tax_on_holding"]) == Decimal("0.005000")
    assert Decimal(body["left"]["tax_rates"]["long_term_capital_gains"]) == Decimal("0.20")
    assert body["notes"]


def test_compare_per_side_holding_and_missing_rows(client: TestClient) -> None:
    _ingest_compare_book(client)
    response = client.post(
        "/illustrate/compare",
        json={
            "holding_dollars": 1000000,
            "left": {
                "label": "2024",
                "holding_dollars": 500000,
                "selectors": {"fund_identifier": "amcap-fund", "as_of": "2024-12-15"},
            },
            "right": {
                "label": "missing year",
                "selectors": {"fund_identifier": "amcap-fund", "as_of": "2019-01-01"},
            },
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["left"]["matched"] is True
    assert Decimal(body["left"]["holding_dollars"]) == Decimal("500000.00")
    assert Decimal(body["left"]["totals"]["distribution_dollars"]) == Decimal("10000.00")
    assert body["right"]["matched"] is False
    assert body["right"]["totals"]["estimated_tax"] is None
    assert body["right"]["totals"]["distribution_dollars"] is None
    assert body["right"]["totals"]["federal_tax"] is None
    assert body["right"]["totals"]["state_tax"] is None
    assert body["right"]["totals"]["effective_tax_on_holding"] is None
    assert body["deltas"]["estimated_tax"] is None
    assert body["deltas"]["distribution_dollars"] is None
    assert any("No distribution" in note for note in body["notes"])


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
    assert period["right"]["totals"]["estimated_tax"] is None
    assert period["right"]["totals"]["distribution_dollars"] is None
    assert period["right"]["totals"]["federal_tax"] is None
    assert period["right"]["totals"]["state_tax"] is None
    assert period["right"]["totals"]["effective_tax_on_holding"] is None
    assert period["deltas"]["estimated_tax"] is None
    assert period["deltas"]["distribution_dollars"] is None
    assert period["deltas"]["federal_tax"] is None
    assert period["deltas"]["state_tax"] is None
    assert period["deltas"]["effective_tax_on_holding"] is None
    assert any("ZZNOPE" in note or "No distribution" in note for note in body["notes"])
    assert Decimal(period["left"]["tax_rates"]["long_term_capital_gains"]) == Decimal("0.20")


def test_compare_upcoming_prefers_current_year_estimate(client: TestClient) -> None:
    _ingest_compare_book(client)
    seeded = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "American Funds",
                    "fund_name": "AMCAP Fund",
                    "estimate_type": "total_capital_gains",
                    "amount": "9",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-06-16",
                    "publication_stage": "paid",
                    "source_url": "https://example.invalid/amcap-2026-paid",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "AMCAP Fund",
                    "estimate_type": "total_capital_gains",
                    "amount": "8",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-06-01",
                    "publication_stage": "updated_estimate",
                    "source_url": "https://example.invalid/amcap-2026-updated-old",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "AMCAP Fund",
                    "estimate_type": "total_capital_gains",
                    "amount": "5",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-09-01",
                    "publication_stage": "preliminary_estimate",
                    "source_url": "https://example.invalid/amcap-2026-prelim",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "AMCAP Fund",
                    "estimate_type": "total_capital_gains",
                    "amount": "7",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-09-15",
                    "publication_stage": "final",
                    "source_url": "https://example.invalid/amcap-2026-final",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "Capital Group Municipal High-Income ETF",
                    "ticker": "CGHM",
                    "estimate_type": "total_capital_gains",
                    "amount": "2",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-09-01",
                    "publication_stage": "final",
                    "source_url": "https://example.invalid/cghm-2026-final",
                },
            ]
        },
    )
    assert seeded.status_code == 200, seeded.text

    response = client.post(
        "/illustrate/compare",
        json={
            "mode": "fund_vs_fund",
            "holding_dollars": 1000000,
            "tax_rates": RATES,
            "left": {"label": "Fund A", "selectors": {"fund_identifier": "amcap-fund"}},
            "right": {"label": "Fund B", "selectors": {"ticker": "CGHM"}},
            "periods": [
                {"year": 2024, "as_of": "2024-12-15"},
                {"year": 2025, "as_of": "2025-09-19"},
            ],
        },
    )
    assert response.status_code == 200, response.text
    upcoming = response.json()["summary"]["upcoming_taxable_distribution"]
    assert upcoming is not None
    # Latest estimate (Sept prelim 5%) wins over older updated (8%), paid (9%), and later final (7%).
    assert Decimal(upcoming["left_dollars"]) == Decimal("500.00")
    # CGHM has only a 2026 final → fallback.
    assert Decimal(upcoming["right_dollars"]) == Decimal("200.00")
    assert Decimal(upcoming["delta_dollars"]) == Decimal("-300.00")
    assert upcoming["left_as_of"] == "2026-09-01"
    assert upcoming["right_as_of"] == "2026-09-01"
    assert upcoming["left_publication_stage"] == "preliminary_estimate"
    assert upcoming["right_publication_stage"] == "final"


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


def test_compare_missing_year_is_null_not_zero(client: TestClient) -> None:
    """No row for that fund/year → N/A (null totals), never a invented $0 bar."""
    _ingest_compare_book(client)
    response = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 100000,
            "tax_rates": {},
            "selectors": {"fund_identifier": "amcap-fund"},
            "periods": [{"year": 2019}, {"year": 2024}],
        },
    )
    assert response.status_code == 200, response.text
    period = response.json()["periods"][0]
    assert period["left"]["matched"] is False
    assert period["right"]["matched"] is True
    totals = period["left"]["totals"]
    assert totals["estimated_tax"] is None
    assert totals["distribution_dollars"] is None
    assert totals["federal_tax"] is None
    assert totals["state_tax"] is None
    assert totals["effective_tax_on_holding"] is None
    assert period["deltas"]["estimated_tax"] is None
    assert period["deltas"]["distribution_dollars"] is None
    assert period["deltas"]["effective_tax_on_holding"] is None
    assert any("2019" in note and "No distribution" in note for note in response.json()["notes"])


def test_compare_published_zero_is_matched_zero(client: TestClient) -> None:
    """Manager-published $0 / 0% NAV is a real bar: matched=true, totals 0.00."""
    seeded = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "Test Family",
                    "fund_name": "Published Zero Fund",
                    "ticker": "ZZERO",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "0",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2024-12-31",
                    "publication_stage": "final",
                    "source_url": "https://example.invalid/zzero-2024",
                },
                {
                    "fund_family": "Test Family",
                    "fund_name": "Published Zero Fund",
                    "ticker": "ZZERO",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "0.00",
                    "amount_unit": "per_share",
                    "as_of": "2025-12-31",
                    "publication_stage": "final",
                    "source_url": "https://example.invalid/zzero-2025",
                },
            ]
        },
    )
    assert seeded.status_code == 200, seeded.text
    response = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 100000,
            "nav_per_share": 10,
            "tax_rates": {},
            "selectors": {"ticker": "ZZERO"},
            "periods": [{"year": 2024}, {"year": 2025}],
        },
    )
    assert response.status_code == 200, response.text
    period = response.json()["periods"][0]
    assert period["left"]["matched"] is True
    assert period["right"]["matched"] is True
    assert Decimal(period["left"]["totals"]["estimated_tax"]) == Decimal("0.00")
    assert Decimal(period["left"]["totals"]["distribution_dollars"]) == Decimal("0.00")
    assert Decimal(period["right"]["totals"]["estimated_tax"]) == Decimal("0.00")
    assert Decimal(period["right"]["totals"]["distribution_dollars"]) == Decimal("0.00")
    assert Decimal(period["deltas"]["estimated_tax"]) == Decimal("0.00")
    assert Decimal(period["deltas"]["distribution_dollars"]) == Decimal("0.00")


def test_compare_per_share_requires_nav_or_shares(client: TestClient) -> None:
    seeded = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "Test Family",
                    "fund_name": "Per Share Fund",
                    "ticker": "PSHRX",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "1.00",
                    "amount_unit": "per_share",
                    "as_of": "2024-12-31",
                    "publication_stage": "final",
                    "source_url": "https://example.invalid/pshrx-2024",
                },
                {
                    "fund_family": "Test Family",
                    "fund_name": "Per Share Fund",
                    "ticker": "PSHRX",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "1.25",
                    "amount_unit": "per_share",
                    "as_of": "2025-12-31",
                    "publication_stage": "final",
                    "source_url": "https://example.invalid/pshrx-2025",
                },
            ]
        },
    )
    assert seeded.status_code == 200, seeded.text
    missing = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 100000,
            "tax_rates": {},
            "selectors": {"ticker": "PSHRX"},
            "periods": [{"year": 2024}, {"year": 2025}],
        },
    )
    assert missing.status_code == 422
    body = missing.json()
    assert body["code"] == "needs_nav_or_shares"
    assert "nav_per_share" in body["detail"]
    assert missing.headers.get("x-error-code") == "needs_nav_or_shares"

    ok = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 100000,
            "nav_per_share": 25,
            "tax_rates": {},
            "selectors": {"ticker": "PSHRX"},
            "periods": [{"year": 2024}, {"year": 2025}],
        },
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["left"]["matched"] is True
