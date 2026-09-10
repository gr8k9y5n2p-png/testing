from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud import scrub_stale_preliminary_estimates, upsert_records
from app.models import AmountUnit, DistributionEstimate, EstimateType, PublicationStage
from app.schemas import DistributionIn
from app.services.stale_estimates import (
    build_paid_season_index,
    is_live_unpaid_estimate,
    is_prior_season,
    is_stale_superseded_preliminary,
    live_estimate_fund_identifiers,
    season_year,
)


TODAY = date(2026, 9, 10)
AGTHX_YE2025_LTCG = Decimal("8.3640")


def _row(**overrides) -> DistributionIn:
    payload = dict(
        fund_family="American Funds",
        fund_name="The Growth Fund of America",
        ticker="AGTHX",
        estimate_type=EstimateType.long_term_capital_gains,
        amount=AGTHX_YE2025_LTCG,
        amount_unit=AmountUnit.per_share,
        record_date=date(2025, 12, 17),
        ex_date=date(2025, 12, 17),
        payable_date=date(2025, 12, 18),
        as_of=date(2026, 1, 22),
        publication_stage=PublicationStage.final,
        source_url=(
            "https://www.capitalgroup.com/individual/service-and-support/"
            "tax-center/2025-year-end-distributions.html"
        ),
    )
    payload.update(overrides)
    return DistributionIn(**payload)


def _agthx_sep_2025_prelim() -> DistributionIn:
    return _row(
        estimate_type=EstimateType.total_capital_gains,
        amount=Decimal("10"),
        amount_min=Decimal("8"),
        amount_max=Decimal("12"),
        amount_unit=AmountUnit.percent_of_nav,
        record_date=date(2025, 12, 17),
        ex_date=date(2025, 12, 17),
        payable_date=date(2025, 12, 18),
        as_of=date(2025, 9, 19),
        publication_stage=PublicationStage.preliminary_estimate,
        source_url="fixture://american_funds/year_end_estimates_sample.html",
    )


def test_season_year_prefers_ex_date() -> None:
    row = _row(ex_date=date(2025, 12, 17), payable_date=date(2026, 1, 2), as_of=date(2026, 1, 22))
    assert season_year(row) == 2025


def test_stale_prelim_with_same_year_final_is_superseded() -> None:
    prelim = _agthx_sep_2025_prelim()
    final = _row()
    paid = build_paid_season_index([final])
    assert is_stale_superseded_preliminary(prelim, TODAY, paid) is True
    assert is_live_unpaid_estimate(prelim, TODAY, paid) is False


def test_dateless_prior_season_prelim_is_superseded_when_final_exists() -> None:
    prelim = _row(
        amount=Decimal("5.75"),
        record_date=None,
        ex_date=None,
        payable_date=None,
        as_of=date(2022, 10, 31),
        publication_stage=PublicationStage.preliminary_estimate,
    )
    final = _row(
        amount=Decimal("6.0394"),
        record_date=None,
        ex_date=date(2022, 12, 14),
        payable_date=date(2022, 12, 16),
        as_of=date(2022, 12, 31),
        publication_stage=PublicationStage.final,
    )
    paid = build_paid_season_index([final])
    assert is_stale_superseded_preliminary(prelim, TODAY, paid) is True
    assert is_live_unpaid_estimate(prelim, TODAY, paid) is False


def test_past_prelim_without_final_is_kept_and_not_live() -> None:
    prelim = _agthx_sep_2025_prelim()
    paid = build_paid_season_index([])
    assert is_stale_superseded_preliminary(prelim, TODAY, paid) is False
    assert is_live_unpaid_estimate(prelim, TODAY, paid) is False


def test_future_unpaid_prelim_is_live_estimate() -> None:
    prelim = _row(
        amount=Decimal("1.00"),
        record_date=date(2026, 12, 15),
        ex_date=date(2026, 12, 16),
        payable_date=date(2026, 12, 17),
        as_of=date(2026, 9, 1),
        publication_stage=PublicationStage.preliminary_estimate,
    )
    paid = build_paid_season_index([])
    assert is_stale_superseded_preliminary(prelim, TODAY, paid) is False
    assert is_live_unpaid_estimate(prelim, TODAY, paid) is True


def test_current_year_dateless_prelim_is_not_prior_season() -> None:
    prelim = _row(
        amount=Decimal("5"),
        record_date=None,
        ex_date=None,
        payable_date=None,
        as_of=date(2026, 9, 1),
        publication_stage=PublicationStage.preliminary_estimate,
    )
    final = _row(
        amount=Decimal("7"),
        record_date=None,
        ex_date=None,
        payable_date=None,
        as_of=date(2026, 9, 15),
        publication_stage=PublicationStage.final,
    )
    paid = build_paid_season_index([final])
    assert is_prior_season(prelim, TODAY) is False
    assert is_stale_superseded_preliminary(prelim, TODAY, paid) is False
    assert is_live_unpaid_estimate(prelim, TODAY, paid) is False


def test_future_prelim_with_same_year_final_is_not_live() -> None:
    prelim = _row(
        amount=Decimal("1.00"),
        record_date=date(2026, 12, 15),
        ex_date=date(2026, 12, 16),
        payable_date=date(2026, 12, 17),
        as_of=date(2026, 9, 1),
        publication_stage=PublicationStage.preliminary_estimate,
    )
    final = _row(
        amount=Decimal("1.10"),
        record_date=date(2026, 12, 15),
        ex_date=date(2026, 12, 16),
        payable_date=date(2026, 12, 17),
        as_of=date(2026, 12, 20),
        publication_stage=PublicationStage.final,
    )
    paid = build_paid_season_index([final])
    assert is_stale_superseded_preliminary(prelim, TODAY, paid) is False
    assert is_live_unpaid_estimate(prelim, TODAY, paid) is False


def test_upsert_scrubs_agthx_sep_2025_prelim_keeps_ye2025_final(session: Session) -> None:
    created, _updated, _stored = upsert_records(session, [_agthx_sep_2025_prelim(), _row()])
    session.commit()
    assert created == 1
    rows = list(session.scalars(select(DistributionEstimate)).all())
    assert len(rows) == 1
    remaining = rows[0]
    assert remaining.publication_stage == PublicationStage.final.value
    assert remaining.estimate_type == EstimateType.long_term_capital_gains.value
    assert remaining.amount == AGTHX_YE2025_LTCG
    assert remaining.ticker == "AGTHX"
    assert remaining.ex_date == date(2025, 12, 17)
    assert remaining.fund_identifier == "the-growth-fund-of-america"
    assert live_estimate_fund_identifiers(session, today=TODAY) == set()


def test_scrub_removes_leftover_agthx_prelim_after_final_lands(session: Session) -> None:
    upsert_records(
        session,
        [_agthx_sep_2025_prelim()],
        skip_stale_prelims=False,
        scrub_stale_prelims=False,
    )
    session.commit()
    assert session.scalar(select(func.count()).select_from(DistributionEstimate)) == 1

    upsert_records(session, [_row()], skip_stale_prelims=False, scrub_stale_prelims=False)
    session.commit()
    assert session.scalar(select(func.count()).select_from(DistributionEstimate)) == 2

    removed = scrub_stale_preliminary_estimates(session, today=TODAY)
    session.commit()
    assert removed == 1
    remaining = list(session.scalars(select(DistributionEstimate)).all())
    assert len(remaining) == 1
    assert remaining[0].publication_stage == PublicationStage.final.value
    assert remaining[0].amount == AGTHX_YE2025_LTCG


def test_past_prelim_without_final_survives_scrub(session: Session) -> None:
    upsert_records(session, [_agthx_sep_2025_prelim()])
    session.commit()
    rows = list(session.scalars(select(DistributionEstimate)).all())
    assert len(rows) == 1
    assert rows[0].publication_stage == PublicationStage.preliminary_estimate.value
    assert live_estimate_fund_identifiers(session, today=TODAY) == set()


def test_american_funds_fixture_agthx_amcpx_after_scrub(client: TestClient) -> None:
    fetched = client.post("/ingest/fetch", json={"fund_family": "american_funds", "mode": "fixture"})
    assert fetched.status_code == 200, fetched.text

    agthx = client.get("/distributions", params={"ticker": "AGTHX", "page_size": 100})
    assert agthx.status_code == 200
    agthx_items = agthx.json()["items"]
    assert agthx_items
    ye2025 = [
        item
        for item in agthx_items
        if item.get("estimate_type") == "long_term_capital_gains"
        and item.get("publication_stage") in {"final", "paid"}
        and item.get("ex_date") == "2025-12-17"
    ]
    assert ye2025, "YE2025 final LTCG must remain"
    assert any(Decimal(item["amount"]) == AGTHX_YE2025_LTCG for item in ye2025)
    assert not any(
        item["publication_stage"] == "preliminary_estimate"
        and (item.get("ex_date") or "").startswith("2025")
        for item in agthx_items
    )

    amcpx = client.get("/distributions", params={"ticker": "AMCPX", "page_size": 100})
    amcpx_items = amcpx.json()["items"]
    assert any(
        item.get("estimate_type") == "long_term_capital_gains"
        and item.get("publication_stage") in {"final", "paid"}
        and Decimal(item["amount"]) == Decimal("2.150900")
        for item in amcpx_items
    )
    assert not any(
        item["publication_stage"] == "preliminary_estimate"
        and (item.get("ex_date") or item.get("as_of") or "").startswith("2025")
        for item in amcpx_items
    )
    assert not any(
        item["publication_stage"] == "preliminary_estimate"
        and (item.get("ex_date") or item.get("as_of") or "").startswith("2024")
        for item in amcpx_items
    )

    agthx_fund = client.get("/funds", params={"q": "AGTHX"})
    amcpx_fund = client.get("/funds", params={"q": "AMCPX"})
    assert agthx_fund.json()["items"][0]["has_estimate"] is False
    assert amcpx_fund.json()["items"][0]["has_estimate"] is False


def test_funds_has_estimate_ignores_past_prelim_once_final_exists(client: TestClient) -> None:
    seeded = client.post(
        "/ingest/distributions",
        json={
            "records": [
                {
                    "fund_family": "American Funds",
                    "fund_name": "The Growth Fund of America",
                    "ticker": "AGTHX",
                    "estimate_type": "total_capital_gains",
                    "amount": "10",
                    "amount_min": "8",
                    "amount_max": "12",
                    "amount_unit": "percent_of_nav",
                    "as_of": "2025-09-19",
                    "record_date": "2025-12-17",
                    "ex_date": "2025-12-17",
                    "payable_date": "2025-12-18",
                    "publication_stage": "preliminary_estimate",
                },
                {
                    "fund_family": "American Funds",
                    "fund_name": "The Growth Fund of America",
                    "ticker": "AGTHX",
                    "estimate_type": "long_term_capital_gains",
                    "amount": "8.3640",
                    "amount_unit": "per_share",
                    "as_of": "2026-01-22",
                    "record_date": "2025-12-17",
                    "ex_date": "2025-12-17",
                    "payable_date": "2025-12-18",
                    "publication_stage": "final",
                },
            ]
        },
    )
    assert seeded.status_code == 200, seeded.text
    assert seeded.json()["created"] == 1

    funds = client.get("/funds", params={"q": "AGTHX"})
    assert funds.json()["total"] == 1
    assert funds.json()["items"][0]["ticker"] == "AGTHX"
    assert funds.json()["items"][0]["has_estimate"] is False

    remaining = client.get("/distributions", params={"ticker": "AGTHX", "page_size": 20})
    stages = {item["publication_stage"] for item in remaining.json()["items"]}
    assert stages == {"final"}
    assert Decimal(remaining.json()["items"][0]["amount"]) == AGTHX_YE2025_LTCG
