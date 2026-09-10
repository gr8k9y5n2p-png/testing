from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.crud import scrub_qdi_percent_characterizations, upsert_records
from app.models import AmountUnit, DistributionEstimate, EstimateType, PublicationStage
from app.schemas import DistributionIn, make_upsert_key


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


def test_upsert_skips_qdi_percent_characterization(session: Session) -> None:
    created, updated, stored = upsert_records(
        session,
        [
            _record(),
            _record(
                fund_name="The Growth Fund of America",
                ticker="AGTHX",
                estimate_type=EstimateType.qualified_dividend,
                amount=Decimal("100"),
                amount_unit=AmountUnit.percent,
                ex_date=None,
                as_of=date(2026, 1, 22),
            ),
        ],
    )
    session.commit()
    assert created == 1 and updated == 0
    assert len(stored) == 1
    assert session.scalar(select(func.count()).select_from(DistributionEstimate)) == 1
    assert not any(row.amount_unit == AmountUnit.percent.value for row in session.scalars(select(DistributionEstimate)))


def test_upsert_keeps_qualified_dividend_per_share(session: Session) -> None:
    created, _updated, stored = upsert_records(
        session,
        [
            _record(
                fund_name="The Growth Fund of America",
                ticker="AGTHX",
                estimate_type=EstimateType.qualified_dividend,
                amount=Decimal("0.1800"),
                amount_unit=AmountUnit.per_share,
                as_of=date(2025, 12, 15),
                ex_date=date(2025, 12, 15),
            )
        ],
    )
    session.commit()
    assert created == 1
    assert stored[0][1].estimate_type == EstimateType.qualified_dividend.value
    assert stored[0][1].amount == Decimal("0.1800")
    assert stored[0][1].amount_unit == AmountUnit.per_share.value


def test_scrub_deletes_qdi_percent_characterization_rows(session: Session) -> None:
    upsert_records(session, [_record()])
    leftover = DistributionEstimate(
        upsert_key=make_upsert_key(
            fund_family="American Funds",
            fund_identifier_value="the-growth-fund-of-america",
            share_class=None,
            estimate_type=EstimateType.qualified_dividend.value,
            as_of=date(2026, 1, 22),
            ex_date=None,
        ),
        fund_family="American Funds",
        fund_name="The Growth Fund of America",
        fund_identifier="the-growth-fund-of-america",
        ticker="AGTHX",
        estimate_type=EstimateType.qualified_dividend.value,
        amount=Decimal("100"),
        amount_unit=AmountUnit.percent.value,
        as_of=date(2026, 1, 22),
        publication_stage=PublicationStage.final.value,
        source_url=(
            "https://www.capitalgroup.com/individual/service-and-support/"
            "tax-center/2025-year-end-distributions.html"
        ),
    )
    session.add(leftover)
    session.commit()
    assert session.scalar(select(func.count()).select_from(DistributionEstimate)) == 2

    removed = scrub_qdi_percent_characterizations(session)
    session.commit()
    assert removed == 1
    remaining = list(session.scalars(select(DistributionEstimate)).all())
    assert len(remaining) == 1
    assert remaining[0].estimate_type == EstimateType.long_term_capital_gains.value
    assert remaining[0].amount_unit == AmountUnit.per_share.value
