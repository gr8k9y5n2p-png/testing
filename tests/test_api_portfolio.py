from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient


def test_portfolio_illustrate_coverage_and_gaps(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200

    response = client.post(
        "/illustrate/portfolio",
        json={
            "holdings": [
                {"ticker": "CGHM", "holding_dollars": 250000},
                {
                    "fund_identifier": "amcap-fund",
                    "fund_family": "American Funds",
                    "holding_dollars": 1000000,
                },
                {"ticker": "XYZAX", "fund_family": "dimensional", "holding_dollars": 150000},
            ],
            "tax_rates": {
                "ordinary_income": 0.37,
                "long_term_capital_gains": 0.20,
                "short_term_capital_gains": 0.37,
                "qualified_dividend": 0.20,
                "state": 0.05,
            },
            "combine_state_with_federal": True,
            "snapshot": {
                "prefer_publication_stages": [
                    "preliminary_estimate",
                    "updated_estimate",
                    "final",
                    "paid",
                ]
            },
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert Decimal(body["coverage"]["dollars_total"]) == Decimal("1400000.00")
    assert Decimal(body["coverage"]["dollars_covered"]) == Decimal("1250000.00")
    assert Decimal(body["coverage"]["dollars_uncovered"]) == Decimal("150000.00")
    assert Decimal(body["coverage"]["coverage_pct"]) == Decimal("89.285714")
    assert body["coverage"]["holdings_covered"] == 2
    assert body["coverage"]["holdings_uncovered"] == 1

    gaps = body["gaps"]
    assert len(gaps) == 1
    assert gaps[0]["ticker"] == "XYZAX"
    assert "No matching" in gaps[0]["reason"]

    amcap = next(h for h in body["holdings"] if h["fund_identifier"] == "amcap-fund")
    assert amcap["covered"] is True
    assert amcap["publication_stage_used"] == "preliminary_estimate"
    # Latest prelim is 2025 3–5% NAV on $1M → $40,000 mid, 25% tax → $10,000
    assert Decimal(amcap["illustration"]["totals"]["distribution_dollars"]) == Decimal("40000.00")
    assert Decimal(amcap["illustration"]["totals"]["estimated_tax"]) == Decimal("10000.00")

    cghm = next(h for h in body["holdings"] if h["ticker"] == "CGHM")
    assert cghm["covered"] is True
    assert any("nav_per_share" in w for w in cghm["warnings"])
    assert Decimal(cghm["illustration"]["totals"]["distribution_dollars"]) == Decimal("0.00")

    assert Decimal(body["totals"]["distribution_dollars"]) == Decimal("40000.00")
    assert Decimal(body["totals"]["estimated_tax"]) == Decimal("10000.00")


def test_portfolio_per_share_with_nav(client: TestClient) -> None:
    client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    response = client.post(
        "/illustrate/portfolio",
        json={
            "holdings": [
                {"ticker": "CGHM", "holding_dollars": 250000, "nav_per_share": 25},
            ],
            "snapshot": {"prefer_publication_stages": ["paid", "final"]},
        },
    )
    assert response.status_code == 200, response.text
    holding = response.json()["holdings"][0]
    assert holding["covered"] is True
    assert Decimal(holding["illustration"]["totals"]["distribution_dollars"]) > 0
    assert holding["publication_stage_used"] == "paid"


def test_portfolio_holding_requires_lookup(client: TestClient) -> None:
    response = client.post(
        "/illustrate/portfolio",
        json={"holdings": [{"holding_dollars": 1000}]},
    )
    assert response.status_code == 422


def test_portfolio_weight_pct_with_book_dollars(client: TestClient) -> None:
    client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    response = client.post(
        "/illustrate/portfolio",
        json={
            "holdings": [
                {
                    "fund_identifier": "amcap-fund",
                    "weight_pct": 0.80,
                    "book_dollars": 1000000,
                }
            ],
            "snapshot": {"prefer_publication_stages": ["preliminary_estimate"]},
        },
    )
    assert response.status_code == 200, response.text
    holding = response.json()["holdings"][0]
    assert Decimal(holding["holding_dollars"]) == Decimal("800000.00")
    assert Decimal(response.json()["totals"]["distribution_dollars"]) == Decimal("32000.00")
