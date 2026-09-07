from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud import upsert_records
from app.models import AmountUnit, DistributionEstimate, EstimateType
from app.schemas import DistributionIn


def _record(**overrides) -> DistributionIn:
    payload = dict(
        fund_family="American Funds",
        fund_name="AMCAP Fund",
        ticker=None,
        estimate_type=EstimateType.long_term_capital_gains,
        amount=Decimal("3.5365"),
        amount_unit=AmountUnit.per_share,
        ex_date=date(2026, 6, 16),
        as_of=date(2026, 7, 8),
        source_url="https://www.capitalgroup.com/individual/service-and-support/tax-center/midyear-cap-gains.html",
    )
    payload.update(overrides)
    return DistributionIn(**payload)


def test_upsert_is_idempotent(session: Session) -> None:
    created, updated, stored = upsert_records(session, [_record()])
    session.commit()
    assert created == 1 and updated == 0
    first_id = stored[0][1].id

    created, updated, stored = upsert_records(
        session, [_record(amount=Decimal("3.6000"), source_url="https://example.invalid/re-run")]
    )
    session.commit()
    assert created == 0 and updated == 1
    assert stored[0][1].id == first_id
    assert stored[0][1].amount == Decimal("3.6000")

    count = session.scalar(select(func.count()).select_from(DistributionEstimate))
    assert count == 1


def test_new_as_of_creates_new_snapshot(session: Session) -> None:
    upsert_records(session, [_record(as_of=date(2025, 9, 19))])
    upsert_records(session, [_record(as_of=date(2025, 12, 9), amount=Decimal("4.00"))])
    session.commit()
    count = session.scalar(select(func.count()).select_from(DistributionEstimate))
    assert count == 2
