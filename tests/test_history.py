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


def test_american_funds_paid_history_2021_2025() -> None:
    html = (AF / "paid_history_2021_2025.html").read_text(encoding="utf-8")
    records = parse_capital_group_html(
        html,
        source_url="https://www.capitalgroup.com/individual/investments/mutual-funds/details/amcap-a",
    )
    amcap_lt = {
        str(r.as_of): r
        for r in records
        if r.fund_name == "AMCAP Fund" and r.estimate_type == EstimateType.long_term_capital_gains
    }
    assert amcap_lt["2021-12-15"].amount == Decimal("1.1710")
    assert amcap_lt["2021-12-15"].publication_stage == PublicationStage.final
    assert amcap_lt["2022-06-15"].amount == Decimal("2.2668")
    assert amcap_lt["2022-06-15"].publication_stage == PublicationStage.paid
    assert amcap_lt["2023-12-13"].amount == Decimal("1.0270")
    assert amcap_lt["2024-12-17"].amount == Decimal("2.5220")
    assert amcap_lt["2025-12-12"].amount == Decimal("2.1509")
    gfa_lt = {
        str(r.as_of): r
        for r in records
        if r.fund_name == "The Growth Fund of America"
        and r.estimate_type == EstimateType.long_term_capital_gains
    }
    assert gfa_lt["2021-12-17"].amount == Decimal("6.0140")
    assert gfa_lt["2022-12-16"].amount == Decimal("1.8410")
    assert gfa_lt["2023-12-15"].amount == Decimal("4.3010")
    assert gfa_lt["2024-12-18"].amount == Decimal("6.3810")
    assert gfa_lt["2025-12-17"].amount == Decimal("8.3640")
    abalx_oi = {
        str(r.as_of): r
        for r in records
        if r.ticker == "ABALX" and r.estimate_type == EstimateType.ordinary_income
    }
    assert abalx_oi["2021-12-14"].amount == Decimal("0.1000")
    assert abalx_oi["2022-12-13"].amount == Decimal("0.1000")
    assert abalx_oi["2023-12-12"].amount == Decimal("0.1000")
    assert abalx_oi["2024-12-16"].amount == Decimal("0.1100")
    assert abalx_oi["2025-12-15"].amount == Decimal("0.1100")
    abalx_lt = {
        str(r.as_of): r
        for r in records
        if r.ticker == "ABALX" and r.estimate_type == EstimateType.long_term_capital_gains
    }
    assert abalx_lt["2021-12-14"].amount == Decimal("0.8600")
    assert "2022-12-13" not in abalx_lt
    assert "2023-12-12" not in abalx_lt
    assert abalx_lt["2022-06-13"].amount == Decimal("0.1775")
    assert abalx_lt["2024-12-16"].amount == Decimal("1.7485")
    assert abalx_lt["2025-12-15"].amount == Decimal("2.1250")
    abalx_sp = {
        str(r.as_of): r
        for r in records
        if r.ticker == "ABALX" and r.estimate_type == EstimateType.special_dividend
    }
    assert abalx_sp["2022-12-13"].amount == Decimal("0.0850")
    assert abalx_sp["2023-12-12"].amount == Decimal("0.3550")
    ica_lt = next(
        r
        for r in records
        if r.ticker == "AIVSX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.as_of) == "2022-12-14"
    )
    assert ica_lt.amount == Decimal("1.3330")
    eupac_22 = [
        r
        for r in records
        if r.ticker == "AEPGX"
        and str(r.as_of) == "2022-12-15"
        and r.estimate_type == EstimateType.long_term_capital_gains
    ]
    assert eupac_22 == []
    ancfx_22 = next(
        r
        for r in records
        if r.ticker == "ANCFX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.as_of) == "2022-12-16"
    )
    assert ancfx_22.amount == Decimal("0.8350")
    assert not any(
        r.ticker == "SMCWX" and r.as_of and r.as_of.year == 2022 for r in records
    )


def test_american_funds_tax_year_lookback_2021_2025() -> None:
    """Wayback / official YE books with tax-year as_of — no invented $0 or QDI %."""
    by_year: dict[int, list] = {}
    for year in (2021, 2022, 2023, 2024, 2025):
        records = parse_capital_group_html(
            (AF / f"year_end_{year}_tax_year.html").read_text(encoding="utf-8"),
            source_url=f"fixture://af-{year}-tax-year",
        )
        by_year[year] = records
        assert records
        assert all(r.amount_unit == AmountUnit.per_share for r in records)
        assert all(r.publication_stage == PublicationStage.final for r in records)
        assert all(r.as_of and r.as_of.year == year for r in records)
        assert all(r.amount is not None and r.amount != Decimal("0") for r in records)
        assert not any(r.amount_unit == AmountUnit.percent for r in records)
        assert len({r.ticker or r.fund_name for r in records}) >= 25

    amcap_21 = next(
        r
        for r in by_year[2021]
        if r.ticker == "AMCPX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert amcap_21.amount == Decimal("1.1710")
    assert str(amcap_21.as_of) == "2021-12-15"
    assert not any(
        r.ticker == "AMCPX" and r.estimate_type == EstimateType.long_term_capital_gains
        for r in by_year[2022]
    )
    amcap_24 = next(
        r
        for r in by_year[2024]
        if r.ticker == "AMCPX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert amcap_24.amount == Decimal("2.5220")
    assert str(amcap_24.as_of) == "2024-12-17"
    amcap_25 = next(
        r
        for r in by_year[2025]
        if r.ticker == "AMCPX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert amcap_25.amount == Decimal("2.1509")
    abalx_21 = next(
        r
        for r in by_year[2021]
        if r.ticker == "ABALX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert abalx_21.amount == Decimal("0.8600")
    gfa_22 = next(
        r
        for r in by_year[2022]
        if r.ticker == "AGTHX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    assert gfa_22.amount == Decimal("1.8410")


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
    y2021 = parse_distribution_html(
        (TRP / "2021_year_end_distributions.html").read_text(encoding="utf-8"),
        source_url="fixture://trp-2021",
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
    trbcx_21 = next(
        r for r in y2021 if r.ticker == "TRBCX" and r.estimate_type == EstimateType.long_term_capital_gains
    )
    trbcx_21_st = next(
        r for r in y2021 if r.ticker == "TRBCX" and r.estimate_type == EstimateType.short_term_capital_gains
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
    assert trbcx_21.amount == Decimal("16.03")
    assert trbcx_21_st.amount == Decimal("0.65")
    assert trbcx_21.publication_stage == PublicationStage.final
    assert {r.ticker for r in y2022 if r.ticker} >= {"TRBCX", "PRDGX", "PREIX", "PRGFX", "TBCIX"}
    assert len({r.ticker for r in y2022 if r.ticker}) >= 300
    assert len({r.ticker for r in y2021 if r.ticker}) >= 300
    assert trbcx_22_prelim.amount == Decimal("5.75")
    assert trbcx_22_prelim.publication_stage == PublicationStage.preliminary_estimate
    assert str(trbcx_24.as_of) == "2024-12-31"
    assert str(trbcx_23.as_of) == "2023-12-31"
    assert str(trbcx_22.as_of) == "2022-12-31"
    assert str(trbcx_21.as_of) == "2021-12-31"
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
    # 2024/2025 prelims are scrubbed once same-year finals exist.
    assert all(
        not (item.get("ex_date") or item.get("as_of") or "").startswith(("2024", "2025"))
        for item in prelim.json()["items"]
    )

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
    assert est_lt.record_date is None
    assert paid_lt.record_date is None
    # Reinvest NAV must not be parsed as a payable date or a dollar amount.
    assert paid_lt.payable_date is not None
    assert str(paid_lt.payable_date) == "2025-09-15"
    assert all(r.amount != Decimal("253.23") for r in paid if r.ticker == "FBGRX")


def test_fidelity_2024_prior_year_fbgrx() -> None:
    paid = parse_distribution_html(
        (FID / "prior_year_distributions_2024.html").read_text(encoding="utf-8"),
        source_url="https://institutional.fidelity.com/app/tabbed/products/FIIS_SP10_DPL6.html?navId=324",
        fund_family="Fidelity",
    )
    fbgrx = [r for r in paid if r.ticker == "FBGRX"]
    lt = sorted(
        (r for r in fbgrx if r.estimate_type == EstimateType.long_term_capital_gains),
        key=lambda r: r.ex_date or r.as_of,
    )
    assert [r.amount for r in lt] == [Decimal("11.08100"), Decimal("1.66900")]
    assert str(lt[0].ex_date) == "2024-09-13"
    assert str(lt[1].ex_date) == "2024-12-20"
    assert {str(r.as_of) for r in lt} == {"2024-12-31"}
    st_sep = next(
        r
        for r in fbgrx
        if r.estimate_type == EstimateType.short_term_capital_gains and str(r.ex_date) == "2024-09-13"
    )
    assert st_sep.amount == Decimal("0.00000")
    assert all(r.amount != Decimal("230.68") for r in fbgrx)
    assert all(r.amount != Decimal("204.17") for r in fbgrx)
    fcntx_lt = next(
        r
        for r in paid
        if r.ticker == "FCNTX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2024-12-06"
    )
    assert fcntx_lt.amount == Decimal("0.85500")
    assert len({r.ticker for r in paid if r.ticker}) >= 300


def test_fidelity_2021_prior_year_fcntx() -> None:
    paid = parse_distribution_html(
        (FID / "prior_year_distributions_2021.html").read_text(encoding="utf-8"),
        source_url="https://institutional.fidelity.com/app/tabbed/products/FIIS_SP10_DPL6.html?navId=324",
        fund_family="Fidelity",
    )
    fcntx = [r for r in paid if r.ticker == "FCNTX"]
    lt = sorted(
        (r for r in fcntx if r.estimate_type == EstimateType.long_term_capital_gains),
        key=lambda r: r.ex_date or r.as_of,
    )
    assert [r.amount for r in lt] == [Decimal("0.40000"), Decimal("1.62700")]
    assert str(lt[0].ex_date) == "2021-02-12"
    assert str(lt[1].ex_date) == "2021-12-10"
    assert {str(r.as_of) for r in lt} == {"2021-12-31"}
    assert all(r.publication_stage == PublicationStage.final for r in lt)
    st_dec = next(
        r
        for r in fcntx
        if r.estimate_type == EstimateType.short_term_capital_gains and str(r.ex_date) == "2021-12-10"
    )
    assert st_dec.amount == Decimal("0.00000")
    fbgrx_lt = next(
        r
        for r in paid
        if r.ticker == "FBGRX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2021-12-17"
    )
    assert fbgrx_lt.amount == Decimal("2.51300")
    assert len({r.ticker for r in paid if r.ticker}) >= 200
    # Must not be the 2024 DPL6 replay.
    assert not any(r.ex_date and r.ex_date.year == 2024 for r in paid)


def test_fidelity_2022_2023_fcntx_highlights_no_invented_stlt() -> None:
    records = parse_distribution_html(
        (FID / "financial_highlights_2022_2023.html").read_text(encoding="utf-8"),
        source_url="https://institutional.fidelity.com/app/funds-and-products/22/fidelity-contrafund-fcntx.html",
        fund_family="Fidelity",
    )
    fcntx = [r for r in records if r.ticker == "FCNTX"]
    by_year = {(str(r.as_of), r.estimate_type): r for r in fcntx}
    assert by_year[("2022-12-31", EstimateType.ordinary_income)].amount == Decimal("0.08")
    assert by_year[("2022-12-31", EstimateType.total_capital_gains)].amount == Decimal("1.36")
    assert by_year[("2023-12-31", EstimateType.ordinary_income)].amount == Decimal("0.08")
    assert by_year[("2023-12-31", EstimateType.total_capital_gains)].amount == Decimal("0.61")
    assert all(r.publication_stage == PublicationStage.final for r in fcntx)
    # Highlights do not publish ST/LT — do not invent zeros.
    assert not any(
        r.estimate_type
        in {EstimateType.short_term_capital_gains, EstimateType.long_term_capital_gains}
        for r in fcntx
    )
    assert not any(r.amount_unit.value == "percent" for r in fcntx)


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
    assert {"2021", "2024", "2025", "2026"} <= years

    fcntx = client.get("/distributions", params={"fund_identifier": "FCNTX", "page_size": 100})
    assert fcntx.status_code == 200
    fcntx_years = {item["as_of"][:4] for item in fcntx.json()["items"] if item.get("as_of")}
    assert {"2021", "2022", "2023", "2024", "2025"} <= fcntx_years
    finals = [
        item
        for item in fcntx.json()["items"]
        if item.get("publication_stage") in {"final", "paid"} and item.get("amount_unit") == "per_share"
    ]
    assert {item["as_of"][:4] for item in finals if item.get("as_of")} >= {
        "2021",
        "2022",
        "2023",
        "2024",
        "2025",
    }
    stages = {item["publication_stage"] for item in fbgrx.json()["items"]}
    assert "final" in stages

    trbcx_2022 = client.get(
        "/distributions",
        params={"fund_identifier": "TRBCX", "as_of_from": "2022-01-01", "as_of_to": "2022-12-31", "page_size": 50},
    )
    assert trbcx_2022.json()["total"] >= 1
    stages_2022 = {item["publication_stage"] for item in trbcx_2022.json()["items"]}
    assert "final" in stages_2022
    assert "preliminary_estimate" not in stages_2022
    assert any(
        Decimal(item["amount"]) == Decimal("6.039400")
        and item["publication_stage"] == "final"
        for item in trbcx_2022.json()["items"]
        if item["estimate_type"] == "long_term_capital_gains"
    )

    trbcx_years = client.get("/distributions", params={"fund_identifier": "TRBCX", "page_size": 50})
    as_ofs = {item["as_of"] for item in trbcx_years.json()["items"] if item.get("as_of")}
    assert len(as_ofs) >= 4  # 2022–2025 finals; 2022 prelim scrubbed once final exists

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
    assert {"2021", "2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in vtsax_years.json()["items"] if item.get("as_of")
    }
    vfiax_2021 = client.get(
        "/distributions",
        params={"fund_identifier": "VFIAX", "as_of_from": "2021-01-01", "as_of_to": "2021-12-31"},
    )
    assert vfiax_2021.json()["total"] >= 1

    for family in (
        "northern_trust",
        "bny_mellon",
        "schwab",
        "dimensional",
        "columbia_threadneedle",
        "morgan_stanley",
        "franklin_templeton",
        "state_street",
    ):
        fetched = client.post("/ingest/fetch", json={"fund_family": family, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text

    nosix = client.get("/distributions", params={"fund_identifier": "NOSIX", "page_size": 50})
    assert {"2021", "2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in nosix.json()["items"] if item.get("as_of")
    }
    nosix_2024 = client.get(
        "/distributions",
        params={
            "fund_identifier": "NOSIX",
            "as_of_from": "2024-01-01",
            "as_of_to": "2024-12-31",
            "page_size": 20,
        },
    )
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("0.699110")
        for item in nosix_2024.json()["items"]
    )

    dgagx = client.get("/distributions", params={"fund_identifier": "DGAGX", "page_size": 50})
    dgagx_years = {item["as_of"][:4] for item in dgagx.json()["items"] if item.get("as_of")}
    assert {"2021", "2022", "2023", "2024", "2025"} <= dgagx_years
    dgagx_stages = {item["publication_stage"] for item in dgagx.json()["items"]}
    assert "final" in dgagx_stages

    swtsx = client.get("/distributions", params={"fund_identifier": "SWTSX", "page_size": 50})
    assert {"2021", "2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in swtsx.json()["items"] if item.get("as_of")
    }
    swanx = client.get("/distributions", params={"fund_identifier": "SWANX", "page_size": 20})
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("1.5191")
        for item in swanx.json()["items"]
    )
    spy = client.get("/distributions", params={"fund_identifier": "SPY", "page_size": 50})
    assert {"2021", "2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in spy.json()["items"] if item.get("as_of")
    }
    allw = client.get("/distributions", params={"fund_identifier": "ALLW", "page_size": 20})
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("0.172577")
        for item in allw.json()["items"]
    )
    ftf = client.get("/distributions", params={"fund_identifier": "FTF", "page_size": 20})
    assert any(
        item["estimate_type"] == "ordinary_income" and Decimal(item["amount"]) == Decimal("0.0418")
        for item in ftf.json()["items"]
    )
    swtsx_2021 = client.get(
        "/distributions",
        params={
            "fund_identifier": "SWTSX",
            "as_of_from": "2021-01-01",
            "as_of_to": "2021-12-31",
            "page_size": 20,
        },
    )
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("0.2022")
        for item in swtsx_2021.json()["items"]
    )

    disvx = client.get("/distributions", params={"fund_identifier": "DISVX", "page_size": 50})
    disvx_years = {item["as_of"][:4] for item in disvx.json()["items"] if item.get("as_of")}
    assert {"2023", "2024", "2025"} <= disvx_years
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("0.025620")
        and item.get("as_of", "").startswith("2023")
        for item in disvx.json()["items"]
    )

    lbsax = client.get("/distributions", params={"fund_identifier": "LBSAX", "page_size": 20})
    lbsax_years = {item["as_of"][:4] for item in lbsax.json()["items"] if item.get("as_of")}
    assert {"2022", "2024", "2025"} <= lbsax_years
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("1.385810")
        for item in lbsax.json()["items"]
    )
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("0.561140")
        for item in lbsax.json()["items"]
    )

    dagvx = client.get("/distributions", params={"fund_identifier": "DAGVX", "page_size": 50})
    assert {"2021", "2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in dagvx.json()["items"] if item.get("as_of")
    }

    cvlc = client.get("/distributions", params={"fund_identifier": "CVLC", "page_size": 20})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in cvlc.json()["items"] if item.get("as_of")}

    ft = client.get("/distributions", params={"fund_identifier": "FT", "page_size": 20})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in ft.json()["items"] if item.get("as_of")}

    for family in (
        "allspring",
        "janus_henderson",
        "american_century",
        "dodge_cox",
        "mfs",
        "ab",
        "virtus",
    ):
        fetched = client.post("/ingest/fetch", json={"fund_family": family, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text

    wfmix = client.get("/distributions", params={"fund_identifier": "WFMIX", "page_size": 50})
    assert {"2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in wfmix.json()["items"] if item.get("as_of")
    }
    wfmix_2024 = client.get(
        "/distributions",
        params={
            "fund_identifier": "WFMIX",
            "as_of_from": "2024-01-01",
            "as_of_to": "2024-12-31",
            "page_size": 20,
        },
    )
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("2.93497")
        for item in wfmix_2024.json()["items"]
    )

    jdcax = client.get("/distributions", params={"fund_identifier": "JDCAX", "page_size": 50})
    assert {"2021", "2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in jdcax.json()["items"] if item.get("as_of")
    }
    jdcax_lt = {
        (item["as_of"][:4], item["publication_stage"]): Decimal(item["amount"])
        for item in jdcax.json()["items"]
        if item["estimate_type"] == "long_term_capital_gains"
    }
    assert jdcax_lt[("2023", "final")] == Decimal("3.888750")
    assert jdcax_lt[("2024", "final")] == Decimal("5.469390")
    assert jdcax_lt[("2025", "final")] == Decimal("6.966940")

    twcgx = client.get("/distributions", params={"fund_identifier": "TWCGX", "page_size": 20})
    twcgx_types = {item["estimate_type"] for item in twcgx.json()["items"]}
    assert "long_term_capital_gains" in twcgx_types
    assert "total_capital_gains" in twcgx_types
    assert {"2022", "2023", "2025"} <= {
        item["as_of"][:4] for item in twcgx.json()["items"] if item.get("as_of")
    }

    dodgx = client.get("/distributions", params={"fund_identifier": "DODGX", "page_size": 50})
    assert {"2021", "2022", "2023", "2024", "2025", "2026"} <= {
        item["as_of"][:4] for item in dodgx.json()["items"] if item.get("as_of")
    }

    mighx = client.get("/distributions", params={"fund_identifier": "MIGHX", "page_size": 50})
    assert {"2021", "2022", "2023", "2024", "2025", "2026"} <= {
        item["as_of"][:4] for item in mighx.json()["items"] if item.get("as_of")
    }

    agrfx = client.get("/distributions", params={"fund_identifier": "AGRFX", "page_size": 20})
    assert {"2023", "2025"} <= {item["as_of"][:4] for item in agrfx.json()["items"] if item.get("as_of")}

    stvtx = client.get("/distributions", params={"fund_identifier": "STVTX", "page_size": 20})
    assert {"2024", "2025", "2026"} <= {
        item["as_of"][:4] for item in stvtx.json()["items"] if item.get("as_of")
    }

    for family in (
        "john_hancock",
        "principal",
        "thrivent",
        "hartford",
        "macquarie",
        "first_eagle",
        "gmo",
        "artisan",
        "calamos",
        "wasatch",
        "harbor",
        "nationwide",
        "voya",
        "oakmark",
        "tweedy",
        "gabelli",
        "royce",
        "nylife",
        "touchstone",
        "victory",
        "sei",
        "brown_advisory",
        "william_blair",
        "vaneck",
        "wisdomtree",
        "first_trust",
        "dws",
        "catalyst",
        "federated_hermes",
        "jpmorgan",
        "aqr",
        "causeway",
        "alger",
        "harding_loevner",
        "matthews_asia",
        "tcw",
        "bridgeway",
        "jensen",
        "diamond_hill",
    ):
        fetched = client.post("/ingest/fetch", json={"fund_family": family, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text

    pqiax = client.get("/distributions", params={"fund_identifier": "PQIAX", "page_size": 50})
    assert {"2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in pqiax.json()["items"] if item.get("as_of")
    }

    tagrx = client.get("/distributions", params={"fund_identifier": "TAGRX", "page_size": 50})
    assert {"2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in tagrx.json()["items"] if item.get("as_of")
    }

    hfmcx = client.get("/distributions", params={"fund_identifier": "HFMCX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in hfmcx.json()["items"] if item.get("as_of")}
    hfmcx_2024 = client.get(
        "/distributions",
        params={
            "fund_identifier": "HFMCX",
            "as_of_from": "2024-01-01",
            "as_of_to": "2024-12-31",
            "page_size": 20,
        },
    )
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("1.67")
        for item in hfmcx_2024.json()["items"]
    )

    wstax = client.get("/distributions", params={"fund_identifier": "WSTAX", "page_size": 20})
    assert {"2023", "2024", "2025"} <= {item["as_of"][:4] for item in wstax.json()["items"] if item.get("as_of")}

    meiax = client.get("/distributions", params={"fund_identifier": "MEIAX", "page_size": 50})
    assert {"2021", "2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in meiax.json()["items"] if item.get("as_of")
    }

    sgenx = client.get("/distributions", params={"fund_identifier": "SGENX", "page_size": 50})
    assert {"2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in sgenx.json()["items"] if item.get("as_of")
    }

    fege = client.get("/distributions", params={"ticker": "FEGE", "page_size": 20})
    assert any(
        item["estimate_type"] == "ordinary_income" and Decimal(item["amount"]) == Decimal("0.589")
        for item in fege.json()["items"]
    )

    mwmix = client.get("/distributions", params={"fund_identifier": "MWMIX", "page_size": 50})
    assert {"2023", "2024", "2025"} <= {item["as_of"][:4] for item in mwmix.json()["items"] if item.get("as_of")}

    seegx = client.get("/distributions", params={"fund_identifier": "SEEGX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in seegx.json()["items"] if item.get("as_of")}

    tmsix = client.get("/distributions", params={"ticker": "TMSIX", "page_size": 50})
    assert tmsix.json()["total"] >= 1, tmsix.json()
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in tmsix.json()["items"] if item.get("as_of")}

    kauax = client.get("/distributions", params={"fund_identifier": "KAUAX", "page_size": 20})
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("0.638052")
        for item in kauax.json()["items"]
    )

    gdx = client.get("/distributions", params={"ticker": "GDX", "page_size": 20})
    assert {"2023", "2024", "2025"} <= {item["as_of"][:4] for item in gdx.json()["items"] if item.get("as_of")}
    assert any(
        item["estimate_type"] == "ordinary_income" and Decimal(item["amount"]) == Decimal("0.4025")
        for item in gdx.json()["items"]
    )
    assert any(
        item["estimate_type"] == "ordinary_income" and Decimal(item["amount"]) == Decimal("0.5001")
        for item in gdx.json()["items"]
    )

    fvd = client.get("/distributions", params={"ticker": "FVD", "page_size": 20})
    assert any(
        item["estimate_type"] == "ordinary_income" and Decimal(item["amount"]) == Decimal("0.2519")
        for item in fvd.json()["items"]
    )

    jensx = client.get("/distributions", params={"ticker": "JENSX", "page_size": 20})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in jensx.json()["items"] if item.get("as_of")}
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("6.77")
        for item in jensx.json()["items"]
    )

    dhlax = client.get("/distributions", params={"ticker": "DHLAX", "page_size": 20})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in dhlax.json()["items"] if item.get("as_of")}
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("2.900")
        for item in dhlax.json()["items"]
    )

    gtr = client.get("/distributions", params={"ticker": "GTR", "page_size": 20})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in gtr.json()["items"] if item.get("as_of")}

    dgrw = client.get("/distributions", params={"ticker": "DGRW", "page_size": 20})
    assert any(
        item["estimate_type"] == "ordinary_income" and Decimal(item["amount"]) == Decimal("0.23270")
        for item in dgrw.json()["items"]
    )

    bfap = client.get("/distributions", params={"ticker": "BFAP", "page_size": 20})
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("3.1933")
        for item in bfap.json()["items"]
    )

    bchi = client.get("/distributions", params={"ticker": "BCHI", "page_size": 20})
    assert any(
        item["estimate_type"] == "short_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("0.290000")
        for item in bchi.json()["items"]
    )

    cvgrx = client.get("/distributions", params={"fund_identifier": "CVGRX", "page_size": 20})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in cvgrx.json()["items"] if item.get("as_of")}

    wgrox = client.get("/distributions", params={"fund_identifier": "WGROX", "page_size": 50})
    assert {"2022", "2024", "2025"} <= {
        item["as_of"][:4] for item in wgrox.json()["items"] if item.get("as_of")
    }

    gqetx = client.get("/distributions", params={"fund_identifier": "GQETX", "page_size": 20})
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("0.7242")
        for item in gqetx.json()["items"]
    )

    artkx = client.get("/distributions", params={"fund_identifier": "ARTKX", "page_size": 20})
    assert any(
        item["estimate_type"] == "ordinary_income"
        and Decimal(item["amount"]) == Decimal("0.338342")
        for item in artkx.json()["items"]
    )

    hacax = client.get("/distributions", params={"fund_identifier": "HACAX", "page_size": 20})
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("11.89")
        for item in hacax.json()["items"]
    )

    nwhox = client.get("/distributions", params={"fund_identifier": "NWHOX", "page_size": 20})
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("3.7231")
        for item in nwhox.json()["items"]
    )

    nlcax = client.get("/distributions", params={"fund_identifier": "NLCAX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in nlcax.json()["items"] if item.get("as_of")}

    oakex = client.get("/distributions", params={"fund_identifier": "OAKEX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in oakex.json()["items"] if item.get("as_of")}

    tbgvx = client.get("/distributions", params={"fund_identifier": "TBGVX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in tbgvx.json()["items"] if item.get("as_of")}

    gabgx = client.get("/distributions", params={"fund_identifier": "GABGX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in gabgx.json()["items"] if item.get("as_of")}

    rytrx = client.get("/distributions", params={"fund_identifier": "RYTRX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in rytrx.json()["items"] if item.get("as_of")}

    mmeax = client.get("/distributions", params={"fund_identifier": "MMEAX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in mmeax.json()["items"] if item.get("as_of")}

    baffx = client.get("/distributions", params={"fund_identifier": "BAFFX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in baffx.json()["items"] if item.get("as_of")}

    bgfix = client.get("/distributions", params={"fund_identifier": "BGFIX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in bgfix.json()["items"] if item.get("as_of")}

    aqgix = client.get("/distributions", params={"fund_identifier": "AQGIX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in aqgix.json()["items"] if item.get("as_of")}
    aqgix_2024 = client.get(
        "/distributions",
        params={
            "fund_identifier": "AQGIX",
            "as_of_from": "2024-01-01",
            "as_of_to": "2024-12-31",
            "page_size": 20,
        },
    )
    assert any(
        item["estimate_type"] == "long_term_capital_gains"
        and Decimal(item["amount"]) == Decimal("0.5462")
        for item in aqgix_2024.json()["items"]
    )

    civix = client.get("/distributions", params={"fund_identifier": "CIVIX", "page_size": 50})
    assert {"2021", "2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in civix.json()["items"] if item.get("as_of")
    }

    maptx = client.get("/distributions", params={"fund_identifier": "MAPTX", "page_size": 50})
    assert {"2021", "2022", "2023", "2024", "2025"} <= {
        item["as_of"][:4] for item in maptx.json()["items"] if item.get("as_of")
    }

    bragx = client.get("/distributions", params={"fund_identifier": "BRAGX", "page_size": 50})
    assert {"2024", "2025"} <= {item["as_of"][:4] for item in bragx.json()["items"] if item.get("as_of")}


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
            "nav_per_share": 45.70,
            "tax_rates": {},
            "selectors": {"fund_identifier": "amcap-fund"},
            "periods": [
                {"year": 2024},
                {"year": 2025},
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


def _final_paid_years(items: list[dict]) -> set[str]:
    return {
        item["as_of"][:4]
        for item in items
        if item.get("as_of")
        and item.get("publication_stage") in {"final", "paid"}
        and item["as_of"][:4] in {"2021", "2022", "2023", "2024", "2025"}
    }


def test_amcpx_dodix_tax_drag_years_overlap(client: TestClient) -> None:
    """Growth-window tax-drag needs multiple shared as_of years in 2021–2025."""
    assert client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"}).status_code == 200
    assert client.post("/ingest/fetch", json={"fund_family": "dodge_cox", "mode": "fixture"}).status_code == 200

    amcap = client.get("/distributions", params={"fund_identifier": "amcap-fund", "page_size": 100})
    dodix = client.get("/distributions", params={"ticker": "DODIX", "page_size": 50})
    amcap_years = _final_paid_years(amcap.json()["items"])
    dodix_years = _final_paid_years(dodix.json()["items"])
    assert amcap_years == {"2021", "2022", "2023", "2024", "2025"}
    assert dodix_years == {"2021", "2022", "2023", "2024", "2025"}
    assert amcap_years & dodix_years == {"2021", "2022", "2023", "2024", "2025"}

    compare = client.post(
        "/illustrate/compare",
        json={
            "mode": "yoy",
            "holding_dollars": 100000,
            "nav_per_share": 100,
            "tax_rates": {},
            "left": {"selectors": {"ticker": "AMCPX"}},
            "right": {"selectors": {"ticker": "DODIX"}},
            "periods": [
                {"year": 2021},
                {"year": 2022},
                {"year": 2023},
                {"year": 2024},
                {"year": 2025},
            ],
        },
    )
    assert compare.status_code == 200, compare.text
    periods = compare.json()["periods"]
    assert len(periods) == 4
    assert all(p["left"]["matched"] and p["right"]["matched"] for p in periods)
    assert all(Decimal(p["left"]["totals"]["distribution_dollars"]) > 0 for p in periods)
    assert all(Decimal(p["right"]["totals"]["distribution_dollars"]) > 0 for p in periods)


def test_compare_yoy_without_periods_uses_real_calendar_years(client: TestClient) -> None:
    """Heroes with multi-year books must not emit year=0 when periods[] is omitted."""
    for family in ("american_funds", "dodge_cox", "fidelity"):
        fetched = client.post("/ingest/fetch", json={"fund_family": family, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text

    for ticker in ("AGTHX", "AMCPX", "DODIX", "FBGRX"):
        response = client.post(
            "/illustrate/compare",
            json={
                "mode": "yoy",
                "holding_dollars": 100000,
                "nav_per_share": 100,
                "tax_rates": {},
                "left": {"selectors": {"ticker": ticker}},
                "right": {"selectors": {"ticker": ticker}},
            },
        )
        assert response.status_code == 200, (ticker, response.text)
        years = [period["year"] for period in response.json()["periods"]]
        assert years, ticker
        assert 0 not in years, (ticker, years)
        assert all(year >= 1900 for year in years), (ticker, years)
        assert len(years) >= 2, (ticker, years)
        assert years == sorted(set(years))
        assert all(period["left"]["matched"] and period["right"]["matched"] for period in response.json()["periods"]), (
            ticker,
            years,
        )
