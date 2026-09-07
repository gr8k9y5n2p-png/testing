from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.models import AmountUnit, EstimateType, PublicationStage
from app.sources.parser import parse_capital_group_html, parse_distribution_html

AF = Path(__file__).resolve().parents[1] / "fixtures" / "american_funds"
TRP = Path(__file__).resolve().parents[1] / "fixtures" / "t_rowe_price"


def test_american_funds_2024_final_fixture() -> None:
    html = (AF / "year_end_2024_distributions.html").read_text(encoding="utf-8")
    records = parse_capital_group_html(html, source_url="https://www.capitalgroup.com/advisor/tax/2024-year-end-distributions.html")
    amcap = next(
        r
        for r in records
        if r.fund_name == "AMCAP Fund" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert amcap.amount == Decimal("2.5220")
    assert str(amcap.ex_date) == "2024-12-17"
    assert str(amcap.as_of) == "2025-01-22"
    assert amcap.publication_stage == PublicationStage.final


def test_american_funds_2024_preliminary_coexists() -> None:
    html = (AF / "year_end_2024_estimates_sample.html").read_text(encoding="utf-8")
    records = parse_capital_group_html(html, source_url="fixture://2024-estimates")
    amcap = next(r for r in records if r.fund_name == "AMCAP Fund")
    assert amcap.publication_stage == PublicationStage.preliminary_estimate
    assert amcap.amount_unit == AmountUnit.percent_of_nav
    assert amcap.amount_min == Decimal("4")
    assert amcap.amount_max == Decimal("6")
    assert str(amcap.as_of) == "2024-09-18"


def test_t_rowe_prior_years() -> None:
    y2024 = parse_distribution_html(
        (TRP / "2024_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://trp-2024",
        fund_family="T. Rowe Price",
    )
    y2023 = parse_distribution_html(
        (TRP / "2023_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://trp-2023",
        fund_family="T. Rowe Price",
    )
    trbcx_24 = next(
        r for r in y2024 if r.ticker == "TRBCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    trbcx_23 = next(
        r for r in y2023 if r.ticker == "TRBCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert trbcx_24.amount == Decimal("16.1515")
    assert trbcx_23.amount == Decimal("5.2095")
    assert str(trbcx_24.as_of) == "2024-12-31"
    assert str(trbcx_23.as_of) == "2023-12-31"


def test_search_history_as_of_and_stage(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200

    prelim = client.get(
        "/distributions",
        params={
            "fund_identifier": "amcap-fund",
            "publication_stage": "preliminary_estimate",
        },
    )
    assert prelim.status_code == 200
    assert prelim.json()["total"] >= 2  # 2024 + 2025 estimate snapshots
    stages = {item["publication_stage"] for item in prelim.json()["items"]}
    assert stages == {"preliminary_estimate"}

    year_2024 = client.get(
        "/distributions",
        params={
            "fund_identifier": "amcap-fund",
            "as_of_from": "2024-01-01",
            "as_of_to": "2024-12-31",
        },
    )
    assert year_2024.json()["total"] >= 1
    assert all(item["as_of"].startswith("2024") for item in year_2024.json()["items"])

    finals = client.get(
        "/distributions",
        params={"fund_identifier": "amcap-fund", "publication_stage": "final"},
    )
    assert finals.json()["total"] >= 1
    assert any(Decimal(item["amount"]) == Decimal("2.522000") for item in finals.json()["items"])

    # Same fund_identifier, different as_of + stage — not collapsed.
    all_amcap = client.get("/distributions", params={"fund_identifier": "amcap-fund", "page_size": 50})
    as_ofs = {item["as_of"] for item in all_amcap.json()["items"]}
    assert len(as_ofs) >= 3
