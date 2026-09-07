from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi.testclient import TestClient

from app.models import AmountUnit, EstimateType, PublicationStage
from app.sources.parser import parse_capital_group_html, parse_distribution_html

AF = Path(__file__).resolve().parents[1] / "fixtures" / "american_funds"
TRP = Path(__file__).resolve().parents[1] / "fixtures" / "t_rowe_price"
FID = Path(__file__).resolve().parents[1] / "fixtures" / "fidelity"
INV = Path(__file__).resolve().parents[1] / "fixtures" / "invesco"


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
    y2022 = parse_distribution_html(
        (TRP / "2022_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://trp-2022",
        fund_family="T. Rowe Price",
    )
    prelim_2022 = parse_distribution_html(
        (TRP / "2022_preliminary_estimated_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://trp-2022-prelim",
        fund_family="T. Rowe Price",
    )
    trbcx_24 = next(
        r for r in y2024 if r.ticker == "TRBCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    trbcx_23 = next(
        r for r in y2023 if r.ticker == "TRBCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    trbcx_22 = next(
        r for r in y2022 if r.ticker == "TRBCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    trbcx_22_st = next(
        r for r in y2022 if r.ticker == "TRBCX" and r.estimate_type == EstimateType.short_term_capital_gains
    )
    trbcx_22_prelim = next(
        r
        for r in prelim_2022
        if r.ticker == "TRBCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert trbcx_24.amount == Decimal("16.1515")
    assert trbcx_23.amount == Decimal("5.2095")
    assert trbcx_22.amount == Decimal("6.0394")
    assert trbcx_22_st.amount == Decimal("0.0325")
    assert trbcx_22.publication_stage == PublicationStage.final
    assert trbcx_22_prelim.amount == Decimal("5.75")
    assert trbcx_22_prelim.publication_stage == PublicationStage.preliminary_estimate
    assert str(trbcx_24.as_of) == "2024-12-31"
    assert str(trbcx_23.as_of) == "2023-12-31"
    assert str(trbcx_22.as_of) == "2022-12-31"
    assert str(trbcx_22_prelim.as_of) == "2022-10-31"


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


def test_fidelity_prior_year_and_estimate_coexist() -> None:
    paid = parse_distribution_html(
        (FID / "prior_year_distributions.html").read_text(encoding="utf-8"),
        source_url="https://institutional.fidelity.com/app/tabbed/products/FIIS_SP10_DPL6.html?navId=324",
        fund_family="Fidelity",
    )
    estimate = parse_distribution_html(
        (FID / "estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://fidelity-estimate",
        fund_family="Fidelity",
    )
    paid_lt = next(
        r for r in paid if r.ticker == "FBGRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    est_lt = next(
        r for r in estimate if r.ticker == "FBGRX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert paid_lt.amount == Decimal("5.07300")
    assert str(paid_lt.ex_date) == "2025-09-12"
    assert str(paid_lt.as_of) == "2025-12-31"
    assert paid_lt.publication_stage == PublicationStage.final
    assert est_lt.amount == Decimal("21.021")
    assert str(est_lt.as_of) == "2026-07-31"
    assert str(est_lt.ex_date) == "2026-09-11"
    # Reinvest NAV must not be parsed as a payable date or a dollar amount.
    assert paid_lt.payable_date is not None
    assert str(paid_lt.payable_date) == "2025-09-15"
    assert all(r.amount != Decimal("253.23") for r in paid if r.ticker == "FBGRX")


def test_invesco_2024_estimate_fixture() -> None:
    records = parse_distribution_html(
        (INV / "2024_estimated_capital_gains.html").read_text(encoding="utf-8"),
        source_url="fixture://invesco-2024",
        fund_family="Invesco",
    )
    franchise = next(
        r
        for r in records
        if "American Franchise" in r.fund_name and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert franchise.amount == Decimal("0.93")
    assert franchise.publication_stage == PublicationStage.preliminary_estimate
    assert str(franchise.as_of) == "2024-09-30"
    assert str(franchise.ex_date) == "2024-12-16"


def test_search_multi_year_top_families(client: TestClient) -> None:
    for family in ("fidelity", "t_rowe_price", "invesco", "american_funds"):
        fetched = client.post("/ingest/fetch", json={"fund_family": family, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text

    fbgrx = client.get("/distributions", params={"fund_identifier": "FBGRX", "page_size": 50})
    assert fbgrx.status_code == 200
    years = {item["as_of"][:4] for item in fbgrx.json()["items"] if item.get("as_of")}
    assert {"2025", "2026"} <= years
    stages = {item["publication_stage"] for item in fbgrx.json()["items"]}
    assert "final" in stages
    assert "preliminary_estimate" in stages

    trbcx_2022 = client.get(
        "/distributions",
        params={"fund_identifier": "TRBCX", "as_of_from": "2022-01-01", "as_of_to": "2022-12-31", "page_size": 50},
    )
    assert trbcx_2022.json()["total"] >= 2  # prelim + final
    stages_2022 = {item["publication_stage"] for item in trbcx_2022.json()["items"]}
    assert {"preliminary_estimate", "final"} <= stages_2022
    assert any(
        Decimal(item["amount"]) == Decimal("6.039400")
        and item["publication_stage"] == "final"
        for item in trbcx_2022.json()["items"]
        if item["estimate_type"] == "long_term_capital_gains"
    )

    trbcx_years = client.get("/distributions", params={"fund_identifier": "TRBCX", "page_size": 50})
    as_ofs = {item["as_of"] for item in trbcx_years.json()["items"] if item.get("as_of")}
    assert len(as_ofs) >= 5  # 2022 prelim + 2022–2025 finals

    franchise_2024 = client.get(
        "/distributions",
        params={"fund_identifier": "invesco-american-franchise-fund", "as_of_from": "2024-01-01", "as_of_to": "2024-12-31"},
    )
    assert franchise_2024.json()["total"] >= 1

    client.post("/ingest/fetch", json={"fund_family": "vanguard", "mode": "fixture"})
    vfiax_years = client.get("/distributions", params={"fund_identifier": "VFIAX", "page_size": 50})
    vfiax_as_ofs = {item["as_of"][:4] for item in vfiax_years.json()["items"] if item.get("as_of")}
    assert {"2022", "2023", "2024", "2025"} <= vfiax_as_ofs
    vtsax_years = client.get("/distributions", params={"fund_identifier": "VTSAX", "page_size": 50})
    assert {"2022", "2023", "2024"} <= {item["as_of"][:4] for item in vtsax_years.json()["items"] if item.get("as_of")}


def test_compare_hero_yoy_fixture_bars(client: TestClient) -> None:
    """Hero tickers get real compare periods[] bars where public multi-year data exists."""
    for family in ("american_funds", "fidelity", "t_rowe_price", "vanguard"):
        fetched = client.post("/ingest/fetch", json={"fund_family": family, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text

    trbcx = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 100000,
            "nav_per_share": 100,
            "tax_rates": {},
            "selectors": {"ticker": "TRBCX"},
            "periods": [{"year": 2022}, {"year": 2023}, {"year": 2024}, {"year": 2025}],
        },
    )
    assert trbcx.status_code == 200, trbcx.text
    trbcx_body = trbcx.json()
    # yoy periods[] are consecutive pairs (4 years → 3 bars). Contract unchanged.
    assert len(trbcx_body["periods"]) == 3
    assert all(p["left"]["matched"] and p["right"]["matched"] for p in trbcx_body["periods"])
    trbcx_dists = [Decimal(p["right"]["totals"]["distribution_dollars"]) for p in trbcx_body["periods"]]
    assert all(d > 0 for d in trbcx_dists)
    assert trbcx_dists == [
        Decimal("5209.50"),   # 2023 LT $5.2095
        Decimal("16908.90"),  # 2024 ST $0.7574 + LT $16.1515
        Decimal("11032.30"),  # 2025 ST $0.0748 + LT $10.9575
    ]
    assert Decimal(trbcx_body["periods"][0]["left"]["totals"]["distribution_dollars"]) == Decimal("6071.90")

    fbgrx = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 100000,
            "nav_per_share": 100,
            "tax_rates": {},
            "selectors": {"ticker": "FBGRX"},
            "periods": [{"year": 2025}, {"year": 2026}],
        },
    )
    assert fbgrx.status_code == 200, fbgrx.text
    fbgrx_body = fbgrx.json()
    assert len(fbgrx_body["periods"]) == 1
    pair = fbgrx_body["periods"][0]
    assert pair["left"]["matched"] is True
    assert pair["right"]["matched"] is True
    assert Decimal(pair["left"]["totals"]["distribution_dollars"]) == Decimal("5073.00")  # 2025 paid LT $5.073 * 1000
    # 2026 estimate snapshot stores % of NAV (7.08), LT $21.021, and total $21.021.
    # Illustrate sums components on that as_of (contract unchanged).
    assert Decimal(pair["right"]["totals"]["distribution_dollars"]) == Decimal("49122.00")

    amcpx = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 100000,
            "tax_rates": {},
            "selectors": {"fund_identifier": "amcap-fund"},
            "periods": [
                {"year": 2024, "as_of": "2024-09-18"},
                {"year": 2025, "as_of": "2025-09-19"},
            ],
        },
    )
    assert amcpx.status_code == 200, amcpx.text
    amcpx_body = amcpx.json()
    assert len(amcpx_body["periods"]) == 1
    assert amcpx_body["periods"][0]["left"]["matched"] is True
    assert amcpx_body["periods"][0]["right"]["matched"] is True
    assert Decimal(amcpx_body["periods"][0]["left"]["totals"]["distribution_dollars"]) > 0
    assert Decimal(amcpx_body["periods"][0]["right"]["totals"]["distribution_dollars"]) > 0

    vfiax = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 100000,
            "nav_per_share": 100,
            "tax_rates": {},
            "selectors": {"ticker": "VFIAX"},
            "periods": [{"year": 2024}, {"year": 2025}],
        },
    )
    assert vfiax.status_code == 200, vfiax.text
    vfiax_body = vfiax.json()
    assert len(vfiax_body["periods"]) == 1
    assert vfiax_body["periods"][0]["left"]["matched"] is True  # ICI 2024 December income
    assert vfiax_body["periods"][0]["right"]["matched"] is True
    assert Decimal(vfiax_body["periods"][0]["left"]["totals"]["distribution_dollars"]) == Decimal("1739.20")
    assert Decimal(vfiax_body["periods"][0]["right"]["totals"]["distribution_dollars"]) > 0

    vbiax = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 100000,
            "nav_per_share": 100,
            "tax_rates": {},
            "selectors": {"ticker": "VBIAX"},
            "periods": [{"year": 2022}, {"year": 2023}, {"year": 2024}, {"year": 2025}],
        },
    )
    assert vbiax.status_code == 200, vbiax.text
    assert len(vbiax.json()["periods"]) == 3
    assert all(p["left"]["matched"] and p["right"]["matched"] for p in vbiax.json()["periods"])
    assert len({p["right"]["totals"]["distribution_dollars"] for p in vbiax.json()["periods"]}) >= 2
