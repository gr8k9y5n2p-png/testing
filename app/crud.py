from __future__ import annotations

import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import NamedTuple

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import ColumnElement

from app.aliases import alias_fund_identifier, enrich_class_a_fields
from app.categories import canonical_category, resolve_category
from app.models import AmountUnit, CoverageGap, DistributionEstimate, IngestRun
from app.schemas import DistributionIn, fund_identifier, make_upsert_key
from app.services.stale_estimates import (
    filter_stale_incoming_prelims,
    live_estimate_fund_identifiers,
    scrub_stale_preliminary_estimates,
)
from app.sources.parser import is_ingestible_distribution_amount

# Compact Search tokens (AGTHX, FBGRX, AMCAP). Leading-wildcard ILIKE cannot use
# ix_dist_ticker / ix_dist_fund_identifier and forces a raw_payload table scan.
_TICKER_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9./-]{0,7}$")
_FUND_SEARCH_COLUMNS = (
    DistributionEstimate.id,
    DistributionEstimate.fund_identifier,
    DistributionEstimate.fund_name,
    DistributionEstimate.fund_family,
    DistributionEstimate.ticker,
    DistributionEstimate.as_of,
    DistributionEstimate.ingested_at,
)


class FundSummary(NamedTuple):
    """One unique fund from the distribution store. Never invented."""

    fund_identifier: str
    fund_name: str
    fund_family: str
    ticker: str | None
    latest_as_of: date | None
    has_estimate: bool
    category: str | None = None
    coverage_status: str = "awaiting_estimate"


def coverage_status_for_in_book_fund(*, has_estimate: bool) -> str:
    """In-book funds only: awaiting_estimate | estimate_announced.

    Never returns ``not_in_universe`` (that is a ticker-lookup miss only).
    Never invents an estimate — ``has_estimate`` is the live unpaid-prelim flag.
    """
    return "estimate_announced" if has_estimate else "awaiting_estimate"


def looks_like_ticker_token(q: str | None) -> bool:
    """True for compact ticker / nickname tokens used by Website Search."""
    if not q or not q.strip():
        return False
    return bool(_TICKER_TOKEN_RE.fullmatch(q.strip()))


def prefer_indexed_fund_match(q: str | None) -> bool:
    """Exact ticker / nickname Search should never fall back to a table scan.

    5-character tokens, tokens with a digit, and Class A aliases (AGTHX, AMCAP)
    are index equality. Longer all-letter tokens (Balanced, Growth) still use
    contains so name Search keeps working.
    """
    if not looks_like_ticker_token(q):
        return False
    token = (q or "").strip()
    if alias_fund_identifier(token):
        return True
    if any(ch.isdigit() for ch in token):
        return True
    return len(token) <= 5


def _identity_variants(raw: str) -> list[str]:
    token = raw.strip()
    variants = {token, token.upper(), token.lower()}
    return sorted(variants)


def _indexed_fund_q_clauses(raw_q: str) -> list[ColumnElement[bool]]:
    """Indexable equality on ticker / fund_identifier / Class A alias. No leading %."""
    variants = _identity_variants(raw_q)
    clauses: list[ColumnElement[bool]] = [
        DistributionEstimate.ticker.in_(variants),
        DistributionEstimate.fund_identifier.in_(variants),
    ]
    alias_ident = alias_fund_identifier(raw_q)
    if alias_ident:
        alias_variants = _identity_variants(alias_ident)
        clauses.append(DistributionEstimate.fund_identifier.in_(alias_variants))
    return clauses


def _contains_fund_q_clauses(raw_q: str) -> list[ColumnElement[bool]]:
    like = f"%{raw_q}%"
    clauses: list[ColumnElement[bool]] = [
        DistributionEstimate.fund_name.ilike(like),
        DistributionEstimate.ticker.ilike(like),
        DistributionEstimate.fund_family.ilike(like),
        DistributionEstimate.fund_identifier.ilike(like),
    ]
    alias_ident = alias_fund_identifier(raw_q)
    if alias_ident:
        clauses.append(DistributionEstimate.fund_identifier.ilike(alias_ident))
    return clauses


def _midpoint(record: DistributionIn) -> Decimal | None:
    if record.amount is not None:
        return record.amount
    if record.amount_min is not None and record.amount_max is not None:
        return (record.amount_min + record.amount_max) / Decimal("2")
    return record.amount_min if record.amount_min is not None else record.amount_max


def upsert_records(
    session: Session,
    records: list[DistributionIn],
    *,
    skip_stale_prelims: bool = True,
    scrub_stale_prelims: bool = True,
) -> tuple[int, int, list[tuple[str, DistributionEstimate]]]:
    created = 0
    updated = 0
    stored: list[tuple[str, DistributionEstimate]] = []
    now = datetime.now(timezone.utc)
    collapsed: dict[str, DistributionIn] = {}
    order: list[str] = []
    ingestible: list[DistributionIn] = []
    for record in records:
        if not is_ingestible_distribution_amount(record.estimate_type, record.amount_unit):
            continue
        ingestible.append(record)
    records = ingestible
    if skip_stale_prelims:
        records, _skipped = filter_stale_incoming_prelims(session, records)
    for record in records:
        ident = fund_identifier(record.ticker, record.fund_name, record.fund_family)
        key = make_upsert_key(
            fund_family=record.fund_family,
            fund_identifier_value=ident,
            share_class=record.share_class,
            estimate_type=record.estimate_type.value,
            as_of=record.as_of,
            ex_date=record.ex_date,
        )
        if key not in collapsed:
            order.append(key)
        collapsed[key] = record
    for key in order:
        record = collapsed[key]
        ident = fund_identifier(record.ticker, record.fund_name, record.fund_family)
        ticker, cusip = enrich_class_a_fields(
            ticker=record.ticker,
            cusip=record.cusip,
            fund_name=record.fund_name,
            fund_family=record.fund_family,
        )
        existing = session.scalar(select(DistributionEstimate).where(DistributionEstimate.upsert_key == key))
        payload = {
            "fund_family": record.fund_family,
            "fund_name": record.fund_name,
            "fund_identifier": ident,
            "ticker": ticker,
            "cusip": cusip,
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
    if scrub_stale_prelims:
        scrub_stale_preliminary_estimates(session)
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
    needs_review: bool | None = None,
    columns: tuple | None = None,
    q_match: str = "contains",
) -> Select:
    stmt: Select = select(*columns) if columns else select(DistributionEstimate)
    if q:
        raw_q = q.strip()
        if q_match == "indexed":
            q_clauses = _indexed_fund_q_clauses(raw_q)
        else:
            q_clauses = _contains_fund_q_clauses(raw_q)
        stmt = stmt.where(or_(*q_clauses))
    if fund_family:
        stmt = stmt.where(DistributionEstimate.fund_family.ilike(f"%{fund_family.strip()}%"))
    if fund_identifier:
        raw_ident = fund_identifier.strip()
        alias_ident = alias_fund_identifier(raw_ident)
        if alias_ident:
            stmt = stmt.where(
                or_(
                    DistributionEstimate.fund_identifier.ilike(raw_ident),
                    DistributionEstimate.fund_identifier.ilike(alias_ident),
                    DistributionEstimate.ticker.ilike(raw_ident),
                )
            )
        else:
            stmt = stmt.where(DistributionEstimate.fund_identifier.ilike(raw_ident))
    if ticker:
        raw_ticker = ticker.strip()
        alias_ident = alias_fund_identifier(raw_ticker)
        if alias_ident:
            stmt = stmt.where(
                or_(
                    DistributionEstimate.ticker.ilike(raw_ticker),
                    DistributionEstimate.fund_identifier.ilike(alias_ident),
                )
            )
        else:
            stmt = stmt.where(DistributionEstimate.ticker.ilike(raw_ticker))
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
    if needs_review is not None:
        stmt = stmt.where(DistributionEstimate.needs_review.is_(needs_review))
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
    needs_review: bool | None = None,
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
        needs_review=needs_review,
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


def resolve_page_from_limit_offset(
    *,
    page: int,
    page_size: int,
    limit: int | None,
    offset: int | None,
) -> tuple[int, int]:
    """Map Website ``limit``/``offset`` onto existing ``page``/``page_size``.

    ``limit`` overrides ``page_size`` when sent. ``offset`` becomes
    ``page = floor(offset / page_size) + 1``. Existing ``page``/``page_size``
    stay valid when the aliases are omitted.
    """
    resolved_size = page_size if limit is None else limit
    resolved_size = min(max(int(resolved_size), 1), 200)
    if offset is None:
        resolved_page = max(int(page), 1)
    else:
        resolved_page = (max(int(offset), 0) // resolved_size) + 1
    return resolved_page, resolved_size


def _unique_fund_query(
    session: Session,
    *,
    q: str | None = None,
    fund_family: str | None = None,
    q_match: str = "contains",
):
    """Latest stored row per fund_identifier. Never invents funds.

    Selects identity columns only — never hydrates ``raw_payload``. Ticker Search
    uses ``q_match='indexed'`` so SQLite hits ``ix_dist_ticker`` /
    ``ix_dist_fund_identifier`` instead of scanning the JSON book.
    """
    filtered = _filter_stmt(
        q=q,
        fund_family=fund_family,
        columns=_FUND_SEARCH_COLUMNS,
        q_match=q_match,
    ).subquery()
    total = session.scalar(select(func.count(func.distinct(filtered.c.fund_identifier)))) or 0
    row_number = func.row_number().over(
        partition_by=filtered.c.fund_identifier,
        order_by=(
            filtered.c.as_of.desc().nulls_last(),
            filtered.c.ingested_at.desc(),
            filtered.c.id.desc(),
        ),
    )
    ranked = select(*filtered.c, row_number.label("rn")).subquery()
    stmt = (
        select(
            ranked.c.fund_identifier,
            ranked.c.fund_name,
            ranked.c.fund_family,
            ranked.c.ticker,
            ranked.c.as_of.label("latest_as_of"),
        )
        .where(ranked.c.rn == 1)
        .order_by(
            ranked.c.fund_name.asc(),
            func.coalesce(ranked.c.ticker, "").asc(),
            ranked.c.fund_identifier.asc(),
        )
    )
    return stmt, int(total)


def _summary_from_row(row, live_estimate_ids: set[str] | None = None) -> FundSummary:
    has_estimate = bool(live_estimate_ids and row.fund_identifier in live_estimate_ids)
    return FundSummary(
        fund_identifier=row.fund_identifier,
        fund_name=row.fund_name,
        fund_family=row.fund_family,
        ticker=row.ticker,
        latest_as_of=row.latest_as_of,
        has_estimate=has_estimate,
        category=resolve_category(
            ticker=row.ticker,
            fund_identifier=row.fund_identifier,
            fund_name=row.fund_name,
            fund_family=row.fund_family,
        ),
        coverage_status=coverage_status_for_in_book_fund(has_estimate=has_estimate),
    )


def search_funds(
    session: Session,
    *,
    q: str | None = None,
    fund_family: str | None = None,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[FundSummary], int]:
    """Unique funds already stored as distribution rows. Never invents funds."""
    limit = min(max(int(limit), 1), 200)
    offset = max(int(offset), 0)
    wanted = canonical_category(category) if category else None
    if category and category.strip() and wanted is None:
        return [], 0

    q_match = "indexed" if prefer_indexed_fund_match(q) else "contains"
    stmt, sql_total = _unique_fund_query(
        session, q=q, fund_family=fund_family, q_match=q_match
    )
    if wanted is None:
        rows = session.execute(stmt.offset(offset).limit(limit)).all()
        live_ids = live_estimate_fund_identifiers(
            session,
            fund_identifiers=[row.fund_identifier for row in rows],
            tickers=[row.ticker for row in rows],
        )
        return [_summary_from_row(row, live_ids) for row in rows], sql_total

    items = [_summary_from_row(row) for row in session.execute(stmt).all()]
    items = [item for item in items if item.category == wanted]
    page = items[offset : offset + limit]
    live_ids = live_estimate_fund_identifiers(
        session,
        fund_identifiers=[item.fund_identifier for item in page],
        tickers=[item.ticker for item in page],
    )
    return [
        item._replace(
            has_estimate=item.fund_identifier in live_ids,
            coverage_status=coverage_status_for_in_book_fund(
                has_estimate=item.fund_identifier in live_ids
            ),
        )
        for item in page
    ], len(items)


def list_fund_category_counts(
    session: Session,
    *,
    q: str | None = None,
    fund_family: str | None = None,
) -> tuple[list[tuple[str, int]], int, int]:
    """Return (category, count) pairs plus uncategorized and total unique funds."""
    q_match = "indexed" if prefer_indexed_fund_match(q) else "contains"
    stmt, total = _unique_fund_query(
        session, q=q, fund_family=fund_family, q_match=q_match
    )
    counts: dict[str, int] = {}
    uncategorized = 0
    for row in session.execute(stmt).all():
        summary = _summary_from_row(row)
        if summary.category:
            counts[summary.category] = counts.get(summary.category, 0) + 1
        else:
            uncategorized += 1
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return items, uncategorized, total


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


def scrub_qdi_percent_characterizations(session: Session) -> int:
    """Delete stored characterization-percent rows (not $/share tax characters).

    Removes leftover ``amount_unit=percent`` rows — including every
    ``qualified_dividend`` / QSTCG "% of dividends that are qualified" cell —
    from Cap Group and any other family. Does not delete ``per_share`` or
    ``percent_of_nav`` ordinary_income / ST-LT gains / QDI / special / ROC.
    Render's SQLite disk survives redeploy, so seed must delete these or they
    stay in Search / paid-history after the parser skip lands.
    """
    result = session.execute(
        delete(DistributionEstimate).where(
            DistributionEstimate.amount_unit == AmountUnit.percent.value,
        )
    )
    session.flush()
    return int(result.rowcount or 0)


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
