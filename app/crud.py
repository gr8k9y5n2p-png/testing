from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models import CoverageGap, DistributionEstimate, IngestRun
from app.schemas import DistributionIn, fund_identifier, make_upsert_key


def _midpoint(record: DistributionIn) -> Decimal | None:
    if record.amount is not None:
        return record.amount
    if record.amount_min is not None and record.amount_max is not None:
        return (record.amount_min + record.amount_max) / Decimal("2")
    return record.amount_min if record.amount_min is not None else record.amount_max


def upsert_records(
    session: Session, records: list[DistributionIn]
) -> tuple[int, int, list[tuple[str, DistributionEstimate]]]:
    created = 0
    updated = 0
    stored: list[tuple[str, DistributionEstimate]] = []
    now = datetime.now(timezone.utc)
    for record in records:
        ident = fund_identifier(record.ticker, record.fund_name)
        key = make_upsert_key(
            fund_family=record.fund_family,
            fund_identifier_value=ident,
            share_class=record.share_class,
            estimate_type=record.estimate_type.value,
            as_of=record.as_of,
            ex_date=record.ex_date,
        )
        existing = session.scalar(select(DistributionEstimate).where(DistributionEstimate.upsert_key == key))
        payload = {
            "fund_family": record.fund_family,
            "fund_name": record.fund_name,
            "fund_identifier": ident,
            "ticker": record.ticker,
            "cusip": record.cusip,
            "share_class": record.share_class,
            "estimate_type": record.estimate_type.value,
            "amount": _midpoint(record),
            "amount_min": record.amount_min,
            "amount_max": record.amount_max,
            "amount_unit": record.amount_unit.value,
            "record_date": record.record_date,
            "ex_date": record.ex_date,
            "payable_date": record.payable_date,
            "as_of": record.as_of,
            "publication_stage": record.publication_stage.value if record.publication_stage else None,
            "source_url": record.source_url,
            "raw_payload": record.raw_payload,
            "ingested_at": now,
        }
        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
            session.add(existing)
            updated += 1
            stored.append(("updated", existing))
        else:
            row = DistributionEstimate(upsert_key=key, **payload)
            session.add(row)
            created += 1
            stored.append(("created", row))
    session.flush()
    return created, updated, stored


def get_by_id(session: Session, distribution_id: str) -> DistributionEstimate | None:
    return session.get(DistributionEstimate, distribution_id)


def get_by_ids(session: Session, ids: list[str]) -> tuple[list[DistributionEstimate], list[str]]:
    if not ids:
        return [], []
    found = {
        row.id: row
        for row in session.scalars(select(DistributionEstimate).where(DistributionEstimate.id.in_(ids))).all()
    }
    missing = [item_id for item_id in ids if item_id not in found]
    ordered = [found[item_id] for item_id in ids if item_id in found]
    return ordered, missing


def _filter_stmt(
    *,
    q: str | None = None,
    fund_family: str | None = None,
    fund_identifier: str | None = None,
    ticker: str | None = None,
    fund_name: str | None = None,
    estimate_type: str | None = None,
    as_of: date | None = None,
    as_of_from: date | None = None,
    as_of_to: date | None = None,
    ex_date_from: date | None = None,
    ex_date_to: date | None = None,
    publication_stage: str | None = None,
) -> Select[tuple[DistributionEstimate]]:
    stmt: Select[tuple[DistributionEstimate]] = select(DistributionEstimate)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                DistributionEstimate.fund_name.ilike(like),
                DistributionEstimate.ticker.ilike(like),
                DistributionEstimate.fund_family.ilike(like),
                DistributionEstimate.fund_identifier.ilike(like),
            )
        )
    if fund_family:
        stmt = stmt.where(DistributionEstimate.fund_family.ilike(f"%{fund_family.strip()}%"))
    if fund_identifier:
        stmt = stmt.where(DistributionEstimate.fund_identifier.ilike(fund_identifier.strip()))
    if ticker:
        stmt = stmt.where(DistributionEstimate.ticker.ilike(ticker.strip()))
    if fund_name:
        stmt = stmt.where(DistributionEstimate.fund_name.ilike(f"%{fund_name.strip()}%"))
    if estimate_type:
        stmt = stmt.where(DistributionEstimate.estimate_type == estimate_type)
    if publication_stage:
        stmt = stmt.where(DistributionEstimate.publication_stage == publication_stage)
    if as_of:
        stmt = stmt.where(DistributionEstimate.as_of == as_of)
    if as_of_from:
        stmt = stmt.where(DistributionEstimate.as_of >= as_of_from)
    if as_of_to:
        stmt = stmt.where(DistributionEstimate.as_of <= as_of_to)
    if ex_date_from:
        stmt = stmt.where(DistributionEstimate.ex_date >= ex_date_from)
    if ex_date_to:
        stmt = stmt.where(DistributionEstimate.ex_date <= ex_date_to)
    return stmt


def search_distributions(
    session: Session,
    *,
    q: str | None = None,
    fund_family: str | None = None,
    fund_identifier: str | None = None,
    ticker: str | None = None,
    fund_name: str | None = None,
    estimate_type: str | None = None,
    as_of: date | None = None,
    as_of_from: date | None = None,
    as_of_to: date | None = None,
    ex_date_from: date | None = None,
    ex_date_to: date | None = None,
    publication_stage: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[DistributionEstimate], int]:
    stmt = _filter_stmt(
        q=q,
        fund_family=fund_family,
        fund_identifier=fund_identifier,
        ticker=ticker,
        fund_name=fund_name,
        estimate_type=estimate_type,
        as_of=as_of,
        as_of_from=as_of_from,
        as_of_to=as_of_to,
        ex_date_from=ex_date_from,
        ex_date_to=ex_date_to,
        publication_stage=publication_stage,
    )
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    rows = list(
        session.scalars(
            stmt.order_by(
                DistributionEstimate.as_of.desc().nulls_last(),
                DistributionEstimate.fund_name.asc(),
                DistributionEstimate.estimate_type.asc(),
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return rows, int(total)


def list_matching(
    session: Session,
    *,
    fund_family: str | None = None,
    fund_identifier: str | None = None,
    ticker: str | None = None,
    fund_name: str | None = None,
    estimate_type: str | None = None,
    as_of: date | None = None,
    publication_stage: str | None = None,
    limit: int = 500,
) -> list[DistributionEstimate]:
    stmt = _filter_stmt(
        fund_family=fund_family,
        fund_identifier=fund_identifier,
        ticker=ticker,
        fund_name=fund_name,
        estimate_type=estimate_type,
        as_of=as_of,
        publication_stage=publication_stage,
    )
    return list(
        session.scalars(
            stmt.order_by(
                DistributionEstimate.as_of.desc().nulls_last(),
                DistributionEstimate.fund_name.asc(),
                DistributionEstimate.estimate_type.asc(),
            ).limit(limit)
        ).all()
    )


def record_ingest_run(session: Session, run: IngestRun) -> IngestRun:
    session.add(run)
    session.flush()
    return run


def latest_run(session: Session, fund_family: str) -> IngestRun | None:
    return session.scalar(
        select(IngestRun)
        .where(IngestRun.fund_family == fund_family)
        .order_by(IngestRun.started_at.desc())
        .limit(1)
    )


def log_coverage_gap(session: Session, gap: CoverageGap) -> CoverageGap:
    session.add(gap)
    session.flush()
    return gap


def count_coverage_gaps(session: Session) -> int:
    return int(session.scalar(select(func.count()).select_from(CoverageGap)) or 0)


def list_coverage_gaps(session: Session, *, limit: int = 100) -> list[CoverageGap]:
    return list(
        session.scalars(select(CoverageGap).order_by(CoverageGap.created_at.desc()).limit(limit)).all()
    )
