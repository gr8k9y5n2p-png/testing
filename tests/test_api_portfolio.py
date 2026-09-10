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
                    "nav_per_share": 45.70,
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
    # Sep 2025 prelim is scrubbed once the YE2025 final exists; prefer list falls through.
    assert amcap["publication_stage_used"] in {"final", "paid"}
    listed = client.get(
        "/distributions",
        params={
            "fund_identifier": "amcap-fund",
            "publication_stage": "final",
            "page_size": 50,
        },
    )
    assert listed.status_code == 200, listed.text
    ye2025 = [
        item
        for item in listed.json()["items"]
        if item.get("estimate_type") == "long_term_capital_gains"
        and item.get("ex_date") == "2025-12-12"
    ]
    assert ye2025
    assert any(Decimal(item["amount"]) == Decimal("2.150900") for item in ye2025)
    assert amcap["upcoming"] is None
    assert amcap["paid_history"]
    assert all(
        item["payable_date"] or item["ex_date"] or item["record_date"] or item["as_of"]
        for item in amcap["paid_history"]
    )

    cghm = next(h for h in body["holdings"] if h["ticker"] == "CGHM")
    assert cghm["covered"] is True
    assert any("nav_per_share" in w for w in cghm["warnings"])
    assert Decimal(cghm["illustration"]["totals"]["distribution_dollars"]) == Decimal("0.00")
    assert cghm["upcoming"] is None

    xyzax = next(h for h in body["holdings"] if h["ticker"] == "XYZAX")
    assert xyzax["covered"] is False
    assert xyzax["upcoming"] is None
    assert xyzax["paid_history"] == []

    # Per-share YE finals need NAV; this coverage case does not invent one.
    assert body["totals"]["distribution_dollars"] is not None
    assert body["totals"]["estimated_tax"] is not None


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
    assert holding["upcoming"] is None
    assert holding["paid_history"]


def test_portfolio_upcoming_copies_record_ex_payable_when_present(client: TestClient) -> None:
    ingested = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "American Funds",
                    "fund_name": "Dateful Fund",
                    "ticker": "DATES",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "4",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-09-01",
                    "record_date": "2026-12-15",
                    "ex_date": "2026-12-16",
                    "payable_date": "2026-12-17",
                    "publication_stage": "preliminary_estimate",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "Dateless Fund",
                    "ticker": "NODTE",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "2",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-09-01",
                    "publication_stage": "preliminary_estimate",
                },
            ]
        },
    )
    assert ingested.status_code == 200, ingested.text

    response = client.post(
        "/illustrate/portfolio",
        json={
            "holdings": [
                {"ticker": "DATES", "holding_dollars": 10000},
                {"ticker": "NODTE", "holding_dollars": 10000},
            ],
            "snapshot": {"prefer_publication_stages": ["preliminary_estimate"]},
        },
    )
    assert response.status_code == 200, response.text
    holdings = {item["ticker"]: item for item in response.json()["holdings"]}

    dated = holdings["DATES"]["upcoming"]
    assert dated is not None
    assert dated["record_date"] == "2026-12-15"
    assert dated["ex_date"] == "2026-12-16"
    assert dated["payable_date"] == "2026-12-17"
    assert dated["as_of"] == "2026-09-01"
    assert dated["publication_stage"] == "preliminary_estimate"
    assert holdings["DATES"]["illustration"]["components"][0]["record_date"] == "2026-12-15"
    assert holdings["DATES"]["illustration"]["components"][0]["ex_date"] == "2026-12-16"
    assert holdings["DATES"]["illustration"]["components"][0]["payable_date"] == "2026-12-17"

    dateless = holdings["NODTE"]["upcoming"]
    assert dateless is not None
    assert dateless["record_date"] is None
    assert dateless["ex_date"] is None
    assert dateless["payable_date"] is None
    assert dateless["as_of"] == "2026-09-01"


def test_portfolio_past_dated_prelim_excluded_from_upcoming(client: TestClient) -> None:
    ingested = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "American Funds",
                    "fund_name": "AMCAP Fund",
                    "ticker": "AMCPX",
                    "fund_identifier": "amcap-fund",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "4",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2025-09-19",
                    "record_date": "2025-12-12",
                    "ex_date": "2025-12-12",
                    "payable_date": "2025-12-15",
                    "publication_stage": "preliminary_estimate",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "Future Prelim Fund",
                    "ticker": "FUTR",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "3",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-09-01",
                    "record_date": "2026-12-15",
                    "ex_date": "2026-12-16",
                    "payable_date": "2026-12-17",
                    "publication_stage": "preliminary_estimate",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "Record Past Payable Future",
                    "ticker": "MIXED",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "2",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-09-01",
                    "record_date": "2025-12-12",
                    "ex_date": "2026-12-16",
                    "payable_date": "2026-12-17",
                    "publication_stage": "preliminary_estimate",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "Paid Future Record",
                    "ticker": "PAIDF",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "2",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-09-01",
                    "record_date": "2026-12-15",
                    "ex_date": "2026-12-16",
                    "payable_date": "2026-12-17",
                    "publication_stage": "paid",
                },
            ]
        },
    )
    assert ingested.status_code == 200, ingested.text

    payload = {
        "holdings": [
            {"ticker": "AMCPX", "holding_dollars": 10000},
            {"ticker": "FUTR", "holding_dollars": 10000},
            {"ticker": "MIXED", "holding_dollars": 10000},
            {"ticker": "PAIDF", "holding_dollars": 10000},
        ],
        "snapshot": {
            "prefer_publication_stages": [
                "preliminary_estimate",
                "updated_estimate",
                "final",
                "paid",
            ]
        },
    }
    response = client.post("/illustrate/portfolio", json=payload)
    assert response.status_code == 200, response.text
    holdings = {item["ticker"]: item for item in response.json()["holdings"]}

    amcpx = holdings["AMCPX"]
    assert amcpx["covered"] is True
    assert amcpx["publication_stage_used"] == "preliminary_estimate"
    assert Decimal(amcpx["illustration"]["totals"]["distribution_dollars"]) == Decimal("400.00")
    assert amcpx["illustration"]["components"][0]["record_date"] == "2025-12-12"
    assert amcpx["upcoming"] is None
    assert len(amcpx["paid_history"]) == 1
    assert amcpx["paid_history"][0]["publication_stage"] == "preliminary_estimate"
    assert amcpx["paid_history"][0]["record_date"] == "2025-12-12"
    assert amcpx["paid_history"][0]["payable_date"] == "2025-12-15"
    assert Decimal(amcpx["paid_history"][0]["distribution_dollars"]) == Decimal("400.00")

    future = holdings["FUTR"]["upcoming"]
    assert future is not None
    assert future["record_date"] == "2026-12-15"
    assert future["ex_date"] == "2026-12-16"
    assert future["payable_date"] == "2026-12-17"
    assert future["publication_stage"] == "preliminary_estimate"
    assert holdings["FUTR"]["paid_history"] == []

    assert holdings["MIXED"]["upcoming"] is None
    assert holdings["MIXED"]["paid_history"][0]["record_date"] == "2025-12-12"
    assert holdings["PAIDF"]["upcoming"] is None
    assert holdings["PAIDF"]["paid_history"][0]["publication_stage"] == "paid"

    compared = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {"holdings": [{"ticker": "AMCPX", "holding_dollars": 10000}]},
            "proposed": {"holdings": [{"ticker": "FUTR", "holding_dollars": 10000}]},
            "snapshot": payload["snapshot"],
        },
    )
    assert compared.status_code == 200, compared.text
    body = compared.json()
    assert body["current"]["holdings"][0]["upcoming"] is None
    assert body["current"]["holdings"][0]["paid_history"]
    proposed_upcoming = body["proposed"]["holdings"][0]["upcoming"]
    assert proposed_upcoming is not None
    assert proposed_upcoming["record_date"] == "2026-12-15"


def test_portfolio_compare_upcoming_includes_calendar_dates(client: TestClient) -> None:
    ingested = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "American Funds",
                    "fund_name": "Dateful Fund",
                    "ticker": "DATES",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "4",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2026-09-01",
                    "record_date": "2026-12-15",
                    "ex_date": "2026-12-16",
                    "payable_date": "2026-12-17",
                    "publication_stage": "updated_estimate",
                }
            ]
        },
    )
    assert ingested.status_code == 200, ingested.text

    response = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {
                "holdings": [{"ticker": "DATES", "holding_dollars": 25000}],
            },
            "proposed": {
                "holdings": [{"ticker": "DATES", "holding_dollars": 10000}],
            },
            "snapshot": {
                "prefer_publication_stages": ["preliminary_estimate", "updated_estimate"]
            },
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    for side in ("current", "proposed"):
        upcoming = body[side]["holdings"][0]["upcoming"]
        assert upcoming["record_date"] == "2026-12-15"
        assert upcoming["ex_date"] == "2026-12-16"
        assert upcoming["payable_date"] == "2026-12-17"


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
                    "weight_pct": 80,
                    "book_dollars": 1000000,
                }
            ],
            "snapshot": {"prefer_publication_stages": ["preliminary_estimate"]},
        },
    )
    assert response.status_code == 200, response.text
    holding = response.json()["holdings"][0]
    assert Decimal(holding["holding_dollars"]) == Decimal("800000.00")
    assert holding["covered"] is True


def _paid_history_sort_value(item: dict) -> str:
    return item["payable_date"] or item["ex_date"] or item["record_date"] or item["as_of"] or ""


def test_portfolio_paid_history_amcpx_agthx_sitrep(client: TestClient) -> None:
    """Eric Paid History: AMCPX/AGTHX past rows (not upcoming) on portfolio + compare."""
    ingested = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert ingested.status_code == 200, ingested.text

    payload = {
        "holdings": [
            {"ticker": "AMCPX", "holding_dollars": 10000, "nav_per_share": 45.70},
            {"ticker": "AGTHX", "holding_dollars": 10000, "nav_per_share": 88.69},
        ],
        "tax_rates": {
            "ordinary_income": 0.37,
            "long_term_capital_gains": 0.20,
            "short_term_capital_gains": 0.37,
            "qualified_dividend": 0.20,
            "state": 0.05,
        },
        "snapshot": {
            "prefer_publication_stages": [
                "preliminary_estimate",
                "updated_estimate",
                "final",
                "paid",
            ]
        },
    }
    response = client.post("/illustrate/portfolio", json=payload)
    assert response.status_code == 200, response.text
    holdings = {item["ticker"]: item for item in response.json()["holdings"]}

    amcpx = holdings["AMCPX"]
    agthx = holdings["AGTHX"]
    assert amcpx["covered"] is True
    assert agthx["covered"] is True
    assert amcpx["upcoming"] is None
    assert agthx["upcoming"] is None
    assert 1 <= len(amcpx["paid_history"]) <= 12
    assert 1 <= len(agthx["paid_history"]) <= 12

    for ticker, holding in (("AMCPX", amcpx), ("AGTHX", agthx)):
        history = holding["paid_history"]
        keys = [_paid_history_sort_value(item) for item in history]
        assert keys == sorted(keys, reverse=True), ticker
        for item in history:
            assert "distribution_dollars" in item
            assert Decimal(item["distribution_dollars"]) > 0
            assert item["publication_stage"] in {
                "preliminary_estimate",
                "updated_estimate",
                "final",
                "paid",
            }
            assert set(item) >= {
                "distribution_dollars",
                "estimated_tax",
                "as_of",
                "publication_stage",
                "record_date",
                "ex_date",
                "payable_date",
            }

    assert amcpx["paid_history"][0]["payable_date"] == "2026-06-17"
    assert amcpx["paid_history"][0]["publication_stage"] == "paid"
    assert any(
        item["payable_date"] == "2025-12-17" or item["ex_date"] == "2025-12-17"
        for item in agthx["paid_history"]
    )

    compared = client.post(
        "/illustrate/portfolio/compare",
        json={
            "current": {"holdings": [payload["holdings"][0]]},
            "proposed": {"holdings": [payload["holdings"][1]]},
            "tax_rates": payload["tax_rates"],
            "snapshot": payload["snapshot"],
        },
    )
    assert compared.status_code == 200, compared.text
    body = compared.json()
    assert body["current"]["holdings"][0]["ticker"] == "AMCPX"
    assert body["current"]["holdings"][0]["upcoming"] is None
    assert body["current"]["holdings"][0]["paid_history"][0]["payable_date"] == "2026-06-17"
    assert body["proposed"]["holdings"][0]["ticker"] == "AGTHX"
    assert body["proposed"]["holdings"][0]["upcoming"] is None
    assert body["proposed"]["holdings"][0]["paid_history"]
