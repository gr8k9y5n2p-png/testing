from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base, make_engine
from app.models import AmountUnit, DistributionEstimate, EstimateType, PublicationStage
from app.services.copy_db import CopyVerifyError, copy_all, estimate_checksum, verify_copy


def _session(engine) -> Session:
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    return factory()


def _seed_source(engine) -> None:
    Base.metadata.create_all(engine)
    with _session(engine) as session:
        session.add(
            DistributionEstimate(
                upsert_key="null-amount-key",
                fund_family="American Funds",
                fund_name="The Growth Fund of America",
                fund_identifier="AGTHX",
                ticker="AGTHX",
                estimate_type=EstimateType.long_term_capital_gains.value,
                amount=None,
                amount_min=None,
                amount_max=None,
                amount_unit=AmountUnit.per_share.value,
                as_of=date(2025, 12, 18),
                publication_stage=PublicationStage.preliminary_estimate.value,
            )
        )
        session.add(
            DistributionEstimate(
                upsert_key="zero-amount-key",
                fund_family="Vanguard",
                fund_name="500 Index",
                fund_identifier="VFIAX",
                ticker="VFIAX",
                estimate_type=EstimateType.ordinary_income.value,
                amount=Decimal("0"),
                amount_unit=AmountUnit.per_share.value,
                as_of=date(2025, 12, 23),
                publication_stage=PublicationStage.paid.value,
            )
        )
        session.commit()


def test_copy_preserves_null_versus_zero_and_checksum(tmp_path) -> None:
    src = make_engine(f"sqlite:///{tmp_path / 'src.db'}")
    dest = make_engine(f"sqlite:///{tmp_path / 'dest.db'}")
    try:
        _seed_source(src)
        Base.metadata.create_all(dest)
        copied = copy_all(src, dest)
        assert copied["distribution_estimates"] == 2
        report = verify_copy(src, dest)
        assert report["ok"] is True
        assert report["source_estimate_checksum"] == report["dest_estimate_checksum"]
        with _session(dest) as session:
            from sqlalchemy import select

            rows = {
                row.upsert_key: row
                for row in session.scalars(select(DistributionEstimate))
            }
            assert rows["null-amount-key"].amount is None
            assert rows["zero-amount-key"].amount == Decimal("0")
            assert rows["null-amount-key"].publication_stage == PublicationStage.preliminary_estimate.value
            assert rows["zero-amount-key"].publication_stage == PublicationStage.paid.value
            assert rows["null-amount-key"].amount_unit == AmountUnit.per_share.value
            assert rows["zero-amount-key"].amount_unit == AmountUnit.per_share.value
    finally:
        src.dispose()
        dest.dispose()


def test_copy_refuses_nonempty_dest(tmp_path) -> None:
    src = make_engine(f"sqlite:///{tmp_path / 'src2.db'}")
    dest = make_engine(f"sqlite:///{tmp_path / 'dest2.db'}")
    try:
        _seed_source(src)
        Base.metadata.create_all(dest)
        copy_all(src, dest)
        try:
            copy_all(src, dest)
            raise AssertionError("expected CopyVerifyError")
        except CopyVerifyError:
            pass
        copy_all(src, dest, truncate_dest=True)
        verify_copy(src, dest)
    finally:
        src.dispose()
        dest.dispose()


def test_checksum_changes_when_amount_changes(tmp_path) -> None:
    engine = make_engine(f"sqlite:///{tmp_path / 'chk.db'}")
    try:
        _seed_source(engine)
        with _session(engine) as session:
            first = estimate_checksum(session)
            from sqlalchemy import select

            row = session.scalars(
                select(DistributionEstimate).where(DistributionEstimate.upsert_key == "zero-amount-key")
            ).one()
            row.amount = Decimal("0.01")
            session.commit()
            second = estimate_checksum(session)
        assert first != second
    finally:
        engine.dispose()


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL not set")
def test_copy_sqlite_snapshot_to_postgres(tmp_path) -> None:
    from app.config import rewrite_database_url
    from app.services.copy_db import counts_by_table

    src = make_engine(f"sqlite:///{tmp_path / 'pg-src.db'}")
    dest = make_engine(rewrite_database_url(os.environ["TEST_DATABASE_URL"]))
    try:
        _seed_source(src)
        Base.metadata.create_all(dest)
        copy_all(src, dest, truncate_dest=True)
        report = verify_copy(src, dest)
        assert report["ok"] is True
        with _session(dest) as session:
            assert counts_by_table(session)["distribution_estimates"] == 2
    finally:
        Base.metadata.drop_all(dest)
        src.dispose()
        dest.dispose()
