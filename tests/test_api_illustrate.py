from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient


def _ingest_amcap_pair(client: TestClient) -> None:
    response = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "American Funds",
                    "fund_name": "AMCAP Fund",
                    "estimate_type": "total_capital_gains",
                    "amount": "4",
                    "amount_min": "3",
                    "amount_max": "5",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2025-09-19",
                    "ex_date": "2025-12-12",
                    "publication_stage": "preliminary_estimate",
                    "source_url": "https://example.invalid/amcap-estimate",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "AMCAP Fund",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "3.5365",
                    "amount_unit": "per_share",
                    "as_of": "2026-07-08",
                    "ex_date": "2026-06-16",
                    "publication_stage": "paid",
                    "source_url": "https://www.capitalgroup.com/individual/service-and-support/tax-center/midyear-cap-gains.html",
                },
            ]
        },
    )
    assert response.status_code == 200, response.text


def test_illustrate_requires_ids_or_selectors(client: TestClient) -> None:
    response = client.post("/illustrate", json={"holding_dollars": 1000000})
    assert response.status_code == 422


def test_illustrate_percent_of_nav_via_selectors(client: TestClient) -> None:
    _ingest_amcap_pair(client)
    response = client.post(
        "/illustrate",
        json={
            "holding_dollars": 1000000,
            "selectors": {
                "fund_family": "American Funds",
                "fund_identifier": "amcap-fund",
                "as_of": "2025-09-19",
            },
            "tax_rates": {
                "ordinary_income": 0.35,
                "long_term_capital_gains": 0.15,
                "short_term_capital_gains": 0.35,
                "qualified_dividend": 0.15,
                "state": 0.093,
            },
            "combine_state_with_federal": True,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["components"]) == 1
    component = body["components"][0]
    assert component["category"] == "Large Growth"
    assert component["amount_unit"] == "percent_of_nav"
    assert Decimal(component["distribution_dollars"]) == Decimal("40000.00")
    assert Decimal(component["distribution_dollars_min"]) == Decimal("30000.00")
    assert Decimal(component["distribution_dollars_max"]) == Decimal("50000.00")
    assert Decimal(component["applied_rate"]) == Decimal("0.243000")
    assert Decimal(component["estimated_tax"]) == Decimal("9720.00")
    assert Decimal(body["totals"]["estimated_tax"]) == Decimal("9720.00")
    assert Decimal(body["tax_rates"]["long_term_capital_gains"]) == Decimal("0.15")
    assert Decimal(body["tax_rates"]["state"]) == Decimal("0.093")


def test_illustrate_per_share_requires_nav(client: TestClient) -> None:
    _ingest_amcap_pair(client)
    found = client.get("/distributions", params={"estimate_type": "long_term_capital_gains"})
    dist_id = found.json()["items"][0]["id"]

    missing = client.post(
        "/illustrate",
        json={"holding_dollars": 1000000, "distribution_ids": [dist_id]},
    )
    assert missing.status_code == 422
    body = missing.json()
    assert body["code"] == "needs_nav_or_shares"
    assert "nav_per_share" in body["detail"]
    assert "shares" in body["detail"]
    assert missing.headers.get("x-error-code") == "needs_nav_or_shares"

    ok = client.post(
        "/illustrate",
        json={
            "holding_dollars": 1000000,
            "distribution_ids": [dist_id],
            "nav_per_share": "80",
            "tax_rates": {"long_term_capital_gains": 0.20, "state": 0.05},
        },
    )
    assert ok.status_code == 200, ok.text
    body = ok.json()
    assert Decimal(body["shares"]) == Decimal("12500.00")
    component = body["components"][0]
    assert Decimal(component["distribution_dollars"]) == Decimal("44206.25")
    assert Decimal(component["estimated_tax"]) == Decimal("11051.56")


def test_illustrate_skips_qdi_percent_and_unknown_id(client: TestClient, session) -> None:
    _ingest_amcap_pair(client)
    from datetime import date

    from app.models import AmountUnit, DistributionEstimate, EstimateType
    from app.schemas import make_upsert_key

    leftover = DistributionEstimate(
        upsert_key=make_upsert_key(
            fund_family="American Funds",
            fund_identifier_value="amcap-fund",
            share_class=None,
            estimate_type=EstimateType.qualified_dividend.value,
            as_of=date(2026, 1, 22),
            ex_date=None,
        ),
        fund_family="American Funds",
        fund_name="AMCAP Fund",
        fund_identifier="amcap-fund",
        estimate_type=EstimateType.qualified_dividend.value,
        amount=Decimal("100"),
        amount_unit=AmountUnit.percent.value,
        as_of=date(2026, 1, 22),
        source_url="https://example.invalid/qdi",
    )
    session.add(leftover)
    session.commit()
    qdi = client.get("/distributions", params={"estimate_type": "qualified_dividend"}).json()["items"][0]
    response = client.post(
        "/illustrate",
        json={"holding_dollars": 1000000, "distribution_ids": [qdi["id"]]},
    )
    assert response.status_code == 200
    component = response.json()["components"][0]
    assert component["included_in_totals"] is False
    assert component["estimated_tax"] is None
    assert Decimal(response.json()["totals"]["estimated_tax"]) == Decimal("0.00")

    missing = client.post(
        "/illustrate",
        json={"holding_dollars": 1, "distribution_ids": ["00000000-0000-0000-0000-000000000000"]},
    )
    assert missing.status_code == 404
