"""Copy rows between two SQLAlchemy engines. Never invent amounts.

Used by scripts/copy_sqlite_to_postgres.py for the SQLite → Postgres dual-run.
Compares stored values only: null stays null, 0 stays 0, publication_stage and
amount_unit are copied as stored.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    CoverageGap,
    DistributionEstimate,
    FundNav,
    FundNavHistory,
    IngestRun,
    SeedFamilyState,
    TickerRequest,
)

COPY_MODELS: tuple[type, ...] = (
    DistributionEstimate,
    CoverageGap,
    TickerRequest,
    FundNav,
    FundNavHistory,
    SeedFamilyState,
    IngestRun,
)

DEFAULT_BATCH_SIZE = 500


def _column_keys(model: type) -> list[str]:
    return [prop.key for prop in inspect(model).column_attrs]


def row_mapping(obj: Any) -> dict[str, Any]:
    return {key: getattr(obj, key) for key in _column_keys(type(obj))}


def table_count(session: Session, model: type) -> int:
    return int(session.scalar(select(func.count()).select_from(model)) or 0)


def distinct_fund_identifier_count(session: Session) -> int:
    return int(
        session.scalar(select(func.count(func.distinct(DistributionEstimate.fund_identifier)))) or 0
    )


def amount_token(value: Decimal | None) -> str:
    """Distinguish NULL from 0. Never COALESCE amounts."""
    if value is None:
        return "NULL"
    return format(Decimal(value), "f")


def estimate_checksum(session: Session) -> str:
    """SHA-256 of frozen identity + stored amounts. Does not invent values."""
    stmt = (
        select(
            DistributionEstimate.upsert_key,
            DistributionEstimate.amount,
            DistributionEstimate.amount_min,
            DistributionEstimate.amount_max,
            DistributionEstimate.as_of,
            DistributionEstimate.publication_stage,
            DistributionEstimate.amount_unit,
        )
        .order_by(DistributionEstimate.upsert_key, DistributionEstimate.id)
    )
    digest = hashlib.sha256()
    for row in session.execute(stmt):
        parts = (
            row.upsert_key,
            amount_token(row.amount),
            amount_token(row.amount_min),
            amount_token(row.amount_max),
            row.as_of.isoformat() if row.as_of is not None else "NULL",
            row.publication_stage if row.publication_stage is not None else "NULL",
            row.amount_unit if row.amount_unit is not None else "NULL",
        )
        digest.update("|".join(parts).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def counts_by_table(session: Session, models: Sequence[type] = COPY_MODELS) -> dict[str, int]:
    return {model.__tablename__: table_count(session, model) for model in models}


class CopyVerifyError(RuntimeError):
    pass


def copy_all(
    source: Engine,
    dest: Engine,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    truncate_dest: bool = False,
) -> dict[str, int]:
    """Batch-copy every mapped table. Dest must be empty unless truncate_dest."""
    src_factory = sessionmaker(bind=source, autoflush=False, expire_on_commit=False)
    dst_factory = sessionmaker(bind=dest, autoflush=False, expire_on_commit=False)
    copied: dict[str, int] = {}
    with src_factory() as src, dst_factory() as dst:
        if truncate_dest:
            for model in reversed(COPY_MODELS):
                dst.execute(delete(model))
            dst.commit()
        dest_counts = counts_by_table(dst)
        nonempty = {name: count for name, count in dest_counts.items() if count}
        if nonempty:
            raise CopyVerifyError(
                f"destination is not empty: {nonempty}. Pass truncate_dest=True to replace."
            )
        for model in COPY_MODELS:
            rows = list(src.scalars(select(model)))
            mappings = [row_mapping(row) for row in rows]
            for start in range(0, len(mappings), batch_size):
                chunk = mappings[start : start + batch_size]
                if chunk:
                    dst.bulk_insert_mappings(model, chunk)
            dst.commit()
            copied[model.__tablename__] = len(mappings)
    return copied


def verify_copy(source: Engine, dest: Engine) -> dict[str, Any]:
    """Compare counts and the frozen estimate checksum. Never invent amounts."""
    src_factory = sessionmaker(bind=source, autoflush=False, expire_on_commit=False)
    dst_factory = sessionmaker(bind=dest, autoflush=False, expire_on_commit=False)
    with src_factory() as src, dst_factory() as dst:
        src_counts = counts_by_table(src)
        dst_counts = counts_by_table(dst)
        src_funds = distinct_fund_identifier_count(src)
        dst_funds = distinct_fund_identifier_count(dst)
        src_sum = estimate_checksum(src)
        dst_sum = estimate_checksum(dst)
    mismatches = {
        name: {"source": src_counts[name], "dest": dst_counts[name]}
        for name in src_counts
        if src_counts[name] != dst_counts[name]
    }
    report = {
        "source_counts": src_counts,
        "dest_counts": dst_counts,
        "source_distinct_fund_identifier": src_funds,
        "dest_distinct_fund_identifier": dst_funds,
        "source_estimate_checksum": src_sum,
        "dest_estimate_checksum": dst_sum,
        "ok": not mismatches and src_funds == dst_funds and src_sum == dst_sum,
        "count_mismatches": mismatches,
    }
    if not report["ok"]:
        raise CopyVerifyError(f"copy verification failed: {report}")
    return report
