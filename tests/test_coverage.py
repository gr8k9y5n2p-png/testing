from __future__ import annotations

from fastapi.testclient import TestClient


def test_coverage_endpoint_lists_top_20(client: TestClient) -> None:
    response = client.get("/coverage")
    assert response.status_code == 200
    body = response.json()
    assert body["top_n"] == 20
    assert body["implemented_count"] == 20
    assert body["stub_count"] == 0
    assert body["implemented_pct"] == 100.0
    slugs = [row["slug"] for row in body["families"]]
    assert slugs == [
        "blackrock",
        "vanguard",
        "fidelity",
        "state_street",
        "jpmorgan",
        "goldman_sachs",
        "american_funds",
        "pimco",
        "invesco",
        "t_rowe_price",
        "ubs",
        "franklin_templeton",
        "bny_mellon",
        "nuveen",
        "northern_trust",
        "morgan_stanley",
        "schwab",
        "dimensional",
        "columbia_threadneedle",
        "amundi",
    ]
    assert all(row["coverage_tier"] == "implemented" for row in body["families"])
    assert body["families"][0]["priority"] == 1
    assert body["families"][10]["aum_rank"] == 11
    assert body["families"][19]["slug"] == "amundi"


def test_coverage_gap_implemented_family(client: TestClient) -> None:
    response = client.post(
        "/coverage/gaps",
        json={"ticker": "FBGRX", "fund_family": "fidelity", "holding_dollars": 250000},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["adapter_exists"] is True
    assert body["adapter_implemented"] is True
    assert body["adapter_slug"] == "fidelity"
    assert body["suggested_next_step"] == "fetch_adapter"
    assert body["ticker"] == "FBGRX"
    assert float(body["holding_dollars"]) == 250000

    listed = client.get("/coverage/gaps")
    assert listed.status_code == 200
    assert any(item["id"] == body["id"] for item in listed.json())

    snap = client.get("/coverage")
    assert snap.json()["logged_gap_count"] >= 1


def test_coverage_gap_unknown_family_manual_ingest(client: TestClient) -> None:
    response = client.post(
        "/coverage/gaps",
        json={"fund_name": "Obscure Small-Cap Trust", "fund_family": "not-a-family"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["adapter_exists"] is False
    assert body["suggested_next_step"] == "manual_ingest"


def test_coverage_gap_alias_ishares(client: TestClient) -> None:
    response = client.post("/coverage/gaps", json={"ticker": "BDVL", "fund_family": "ishares"})
    assert response.status_code == 200
    assert response.json()["adapter_slug"] == "blackrock"


def test_coverage_gap_alias_pioneer_and_dfa(client: TestClient) -> None:
    pioneer = client.post("/coverage/gaps", json={"ticker": "PIODX", "fund_family": "pioneer"})
    assert pioneer.status_code == 200
    assert pioneer.json()["adapter_slug"] == "amundi"
    dfa = client.post("/coverage/gaps", json={"ticker": "DFQTX", "fund_family": "dfa"})
    assert dfa.status_code == 200
    assert dfa.json()["adapter_slug"] == "dimensional"


def test_coverage_gap_requires_ticker_or_name(client: TestClient) -> None:
    response = client.post("/coverage/gaps", json={"holding_dollars": 1000})
    assert response.status_code == 422


def test_fetch_alias_capital_group_still_works(client: TestClient) -> None:
    response = client.post("/ingest/fetch", json={"fund_family": "capital_group", "mode": "fixture"})
    assert response.status_code == 200
    assert response.json()["created"] > 0


def test_partner_ingest_still_escape_hatch(client: TestClient) -> None:
    response = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "Dimensional",
                    "fund_name": "DFA US Core Equity 2",
                    "ticker": "DFQTX",
                    "estimate_type": "total_capital_gains",
                    "amount": "1.10",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2025-11-01",
                }
            ]
        },
    )
    assert response.status_code == 200
    found = client.get("/distributions", params={"ticker": "DFQTX"})
    assert found.json()["total"] == 1