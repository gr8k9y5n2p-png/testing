"""All-events + typed leftover densify for non-MFS in-book families."""

from __future__ import annotations

from decimal import Decimal

from fastapi.testclient import TestClient

from app.config import settings
from app.models import EstimateType, PublicationStage
from app.sources.american_funds import AmericanFundsSource
from app.sources.families import (
    BlackRockSource,
    InvescoSource,
    JPMorganSource,
    PimcoSource,
    TRowePriceSource,
    VanguardSource,
)
from app.sources.next_tier import FranklinTempletonSource
from app.sources.third_tier import MfsSource


PAID = {PublicationStage.final, PublicationStage.paid}


def _paid(records):
    return [
        r
        for r in records
        if r.publication_stage in PAID and r.amount is not None and r.ex_date
    ]


def test_seed_force_full_stays_off() -> None:
    assert settings.seed_force_full is False


def test_mfs_186_midyear_is_adopted_not_overwritten() -> None:
    """#186 paid_midyear + both 2025 MFEGX LTCGs stay after this rebase."""
    names = [page.name for page in MfsSource().pages()]
    assert "paid_midyear" in names
    assert not any("all_events" in name or "leftover_quarterly" in name for name in names)
    records = _paid(MfsSource().fetch(mode="fixture").records)
    mfegx_2025 = {
        (str(r.ex_date), r.amount)
        for r in records
        if r.ticker == "MFEGX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and r.ex_date
        and r.ex_date.year == 2025
    }
    assert ("2025-07-31", Decimal("4.12961")) in mfegx_2025
    assert ("2025-12-16", Decimal("25.35332")) in mfegx_2025


def test_american_funds_midyear_all_events_heroes() -> None:
    records = _paid(AmericanFundsSource().fetch(mode="fixture").records)
    amcpx_2021 = next(
        r
        for r in records
        if r.ticker == "AMCPX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2021-06-16"
    )
    assert amcpx_2021.amount == Decimal("1.5290")
    amcfx_2024 = next(
        r
        for r in records
        if r.ticker == "AMCFX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2024-06-12"
    )
    assert amcfx_2024.amount == Decimal("0.8110")
    amcfx_2025 = next(
        r
        for r in records
        if r.ticker == "AMCFX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-06-11"
    )
    assert amcfx_2025.amount == Decimal("1.8675")
    # Class-level income — never copied from AMCPX.
    amcpx_2023 = next(
        r
        for r in records
        if r.ticker == "AMCPX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2023-06-14"
    )
    amcfx_2023 = next(
        r
        for r in records
        if r.ticker == "AMCFX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2023-06-14"
    )
    assert amcpx_2023.amount == Decimal("0.0925")
    assert amcfx_2023.amount == Decimal("0.1677")
    abalx_lt = next(
        r
        for r in records
        if r.ticker == "ABALX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-06-09"
    )
    assert abalx_lt.amount == Decimal("0.1950")
    abalx_dates = {str(r.ex_date) for r in records if r.ticker == "ABALX" and r.ex_date.year == 2025}
    assert {"2025-03-10", "2025-06-09", "2025-09-15", "2025-12-15"} <= abalx_dates


def test_american_funds_gfa_anwpx_midyear_walls() -> None:
    records = _paid(AmericanFundsSource().fetch(mode="fixture").records)
    for ticker in ("AGTHX", "ANWPX"):
        midyear = [
            r
            for r in records
            if r.ticker == ticker
            and r.ex_date.month != 12
            and r.estimate_type
            in {EstimateType.long_term_capital_gains, EstimateType.short_term_capital_gains}
            and 2021 <= r.ex_date.year <= 2025
        ]
        assert midyear == [], ticker


def test_vanguard_quarterly_and_midyear_cg_heroes() -> None:
    records = _paid(VanguardSource().fetch(mode="fixture").records)
    vbinx_lt = next(
        r
        for r in records
        if r.ticker == "VBINX"
        and r.estimate_type == EstimateType.long_term_capital_gains
        and str(r.ex_date) == "2025-03-27"
    )
    assert vbinx_lt.amount == Decimal("0.638521")
    vbinx_st = next(
        r
        for r in records
        if r.ticker == "VBINX"
        and r.estimate_type == EstimateType.short_term_capital_gains
        and str(r.ex_date) == "2025-03-27"
    )
    assert vbinx_st.amount == Decimal("0.006602")
    vbiax_oi = next(
        r
        for r in records
        if r.ticker == "VBIAX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2025-06-30"
    )
    assert vbiax_oi.amount == Decimal("0.269200")
    vigax_dates = {
        str(r.ex_date)
        for r in records
        if r.ticker == "VIGAX"
        and r.estimate_type == EstimateType.ordinary_income
        and r.ex_date.year == 2025
    }
    assert {"2025-03-27", "2025-06-30", "2025-09-29", "2025-12-22"} <= vigax_dates


def test_t_rowe_quarterly_income_leftover() -> None:
    records = _paid(TRowePriceSource().fetch(mode="fixture").records)
    prfdx = next(
        r
        for r in records
        if r.ticker == "PRFDX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2025-06-26"
    )
    assert prfdx.amount == Decimal("0.1922")
    rpbax = next(
        r
        for r in records
        if r.ticker == "RPBAX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2024-09-26"
    )
    assert rpbax.amount == Decimal("0.1229")
    prdgx_2021 = next(
        r
        for r in records
        if r.ticker == "PRDGX"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2021-06-28"
    )
    assert prdgx_2021.amount == Decimal("0.14")


def test_ishares_quarterly_ordinary_not_qualified_character() -> None:
    records = _paid(BlackRockSource().fetch(mode="fixture").records)
    ivv_2025 = next(
        r
        for r in records
        if r.ticker == "IVV"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2025-06-16"
    )
    assert ivv_2025.amount == Decimal("1.866967")
    ivv_2024 = next(
        r
        for r in records
        if r.ticker == "IVV"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2024-06-11"
    )
    # Official ordinary column — not the qualified characterization $1.455090.
    assert ivv_2024.amount == Decimal("1.611133")
    iyr = next(
        r
        for r in records
        if r.ticker == "IYR"
        and r.estimate_type == EstimateType.ordinary_income
        and str(r.ex_date) == "2025-03-18"
    )
    assert iyr.amount == Decimal("0.358576")


def test_all_events_walls_stay_unmatched() -> None:
    invesco = _paid(InvescoSource().fetch(mode="fixture").records)
    assert not any(r.ex_date.year in {2021, 2022} for r in invesco)
    assert not any(r.ex_date and r.ex_date.month != 12 for r in invesco)

    pimco = _paid(PimcoSource().fetch(mode="fixture").records)
    assert pimco == []

    franklin = _paid(FranklinTempletonSource().fetch(mode="fixture").records)
    assert franklin == []

    jpm = _paid(JPMorganSource().fetch(mode="fixture").records)
    assert not any(r.ex_date and r.ex_date.month not in {11, 12, 1} for r in jpm)

    ishares = _paid(BlackRockSource().fetch(mode="fixture").records)
    ivv_2021_mid = [
        r
        for r in ishares
        if r.ticker == "IVV" and r.ex_date.year == 2021 and r.ex_date.month != 12
    ]
    assert ivv_2021_mid == []

    trp = _paid(TRowePriceSource().fetch(mode="fixture").records)
    trbcx_q = [
        r
        for r in trp
        if r.ticker == "TRBCX" and r.ex_date.month != 12 and 2021 <= r.ex_date.year <= 2025
    ]
    assert trbcx_q == []


def test_all_events_heroes_are_searchable(client: TestClient) -> None:
    for slug in ("american_funds", "vanguard", "t_rowe_price", "blackrock", "mfs"):
        fetched = client.post("/ingest/fetch", json={"fund_family": slug, "mode": "fixture"})
        assert fetched.status_code == 200, fetched.text
        assert fetched.json()["created"] > 0

    for ticker in ("AMCPX", "AMCFX", "ABALX", "VBINX", "VBIAX", "IVV", "PRFDX", "RPBAX", "MFEGX"):
        body = client.get("/funds", params={"q": ticker}).json()
        tickers = [item["ticker"] for item in body["items"]]
        assert ticker in tickers, f"{ticker} missing from GET /funds?q={ticker}: {tickers[:8]}"

    amcpx = client.get(
        "/distributions",
        params={"ticker": "AMCPX", "page_size": 200},
    ).json()
    june_2025 = [
        Decimal(row["amount"])
        for row in amcpx["items"]
        if row.get("ticker") == "AMCPX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-06-11")
    ]
    assert Decimal("1.8675") in june_2025
    amcpx_2025_dates = {
        str(row.get("ex_date") or "")[:10]
        for row in amcpx["items"]
        if row.get("ticker") == "AMCPX" and str(row.get("ex_date") or "").startswith("2025-")
    }
    assert {"2025-06-11", "2025-12-12"} <= amcpx_2025_dates

    ivv = client.get("/distributions", params={"ticker": "IVV", "page_size": 200}).json()
    ivv_2025 = {
        str(row.get("ex_date") or "")[:10]
        for row in ivv["items"]
        if row.get("ticker") == "IVV"
        and row.get("estimate_type") == "ordinary_income"
        and str(row.get("ex_date") or "").startswith("2025-")
    }
    assert {"2025-03-18", "2025-06-16", "2025-09-16", "2025-12-16"} <= ivv_2025

    mfegx = client.get("/distributions", params={"ticker": "MFEGX", "page_size": 200}).json()
    mfegx_2025_lt = {
        (str(row.get("ex_date") or "")[:10], Decimal(row["amount"]))
        for row in mfegx["items"]
        if row.get("ticker") == "MFEGX"
        and row.get("estimate_type") == "long_term_capital_gains"
        and str(row.get("ex_date") or "").startswith("2025-")
    }
    assert ("2025-07-31", Decimal("4.12961")) in mfegx_2025_lt
    assert ("2025-12-16", Decimal("25.35332")) in mfegx_2025_lt
