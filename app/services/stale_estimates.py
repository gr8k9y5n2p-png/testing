"""Scrub stale preliminary estimates once paid finals exist. Never invents amounts."""

from __future__ import annotations

from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import Any, Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.aliases import enrich_class_a_fields
from app.models import DistributionEstimate, PublicationStage
from app.schemas import DistributionIn, fund_identifier

ESTIMATE_STAGES = frozenset(
    {
        PublicationStage.preliminary_estimate.value,
        PublicationStage.updated_estimate.value,
    }
)
PAID_STAGES = frozenset(
    {
        PublicationStage.final.value,
        PublicationStage.paid.value,
    }
)


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _stage_value(row: Any) -> str | None:
    stage = getattr(row, "publication_stage", None)
    if stage is None:
        return None
    return stage.value if hasattr(stage, "value") else str(stage)


def season_year(row: Any) -> int | None:
    """Calendar year for matching prelims to finals. Prefer ex_date year."""
    ex_date = getattr(row, "ex_date", None)
    if ex_date is not None:
        return ex_date.year
    payable_date = getattr(row, "payable_date", None)
    if payable_date is not None:
        return payable_date.year
    as_of = getattr(row, "as_of", None)
    if as_of is not None:
        return as_of.year
    return None


def window_date(row: Any) -> date | None:
    """Published ex/payable used to decide past vs still-upcoming. Never invented."""
    return getattr(row, "ex_date", None) or getattr(row, "payable_date", None)


def is_past_window(row: Any, today: date) -> bool:
    event = window_date(row)
    return event is not None and event <= today


def is_future_window(row: Any, today: date) -> bool:
    event = window_date(row)
    return event is not None and today < event


def fund_match_keys(row: Any) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    ticker = getattr(row, "ticker", None)
    if ticker and str(ticker).strip():
        keys.add(("t", str(ticker).strip().upper()))
    ident = getattr(row, "fund_identifier", None)
    if ident and str(ident).strip():
        keys.add(("i", str(ident).strip().lower()))
    return keys


def incoming_identity(record: DistributionIn) -> SimpleNamespace:
    """Same ticker / fund_identifier upsert will persist. Never invents amounts."""
    ident = fund_identifier(record.ticker, record.fund_name, record.fund_family)
    ticker, _cusip = enrich_class_a_fields(
        ticker=record.ticker,
        cusip=record.cusip,
        fund_name=record.fund_name,
        fund_family=record.fund_family,
    )
    return SimpleNamespace(
        ticker=ticker,
        fund_identifier=ident,
        ex_date=record.ex_date,
        payable_date=record.payable_date,
        as_of=record.as_of,
        publication_stage=record.publication_stage,
    )


def build_paid_season_index(rows: Iterable[Any]) -> dict[int, set[tuple[str, str]]]:
    index: dict[int, set[tuple[str, str]]] = {}
    for row in rows:
        if _stage_value(row) not in PAID_STAGES:
            continue
        year = season_year(row)
        if year is None:
            continue
        index.setdefault(year, set()).update(fund_match_keys(row))
    return index


def _intersects_paid(row: Any, paid_index: dict[int, set[tuple[str, str]]]) -> bool:
    year = season_year(row)
    if year is None:
        return False
    return bool(fund_match_keys(row) & paid_index.get(year, set()))


def is_stale_superseded_preliminary(
    row: Any, today: date, paid_index: dict[int, set[tuple[str, str]]]
) -> bool:
    """Past prelim with a matching final/paid for the same fund + calendar year."""
    if _stage_value(row) != PublicationStage.preliminary_estimate.value:
        return False
    if not is_past_window(row, today):
        return False
    return _intersects_paid(row, paid_index)


def is_live_unpaid_estimate(
    row: Any, today: date, paid_index: dict[int, set[tuple[str, str]]]
) -> bool:
    """Unpaid prelim/updated with a future ex/payable. Past-season rows never qualify."""
    if _stage_value(row) not in ESTIMATE_STAGES:
        return False
    if not is_future_window(row, today):
        return False
    return not _intersects_paid(row, paid_index)


def live_estimate_fund_identifiers(session: Session, today: date | None = None) -> set[str]:
    today = today or utc_today()
    rows = list(
        session.scalars(
            select(DistributionEstimate).where(
                DistributionEstimate.publication_stage.in_([*ESTIMATE_STAGES, *PAID_STAGES])
            )
        )
    )
    paid_index = build_paid_season_index(rows)
    return {
        row.fund_identifier
        for row in rows
        if is_live_unpaid_estimate(row, today, paid_index)
    }


def load_paid_rows(session: Session) -> list[DistributionEstimate]:
    return list(
        session.scalars(
            select(DistributionEstimate).where(DistributionEstimate.publication_stage.in_(list(PAID_STAGES)))
        )
    )


def filter_stale_incoming_prelims(
    session: Session,
    records: list[DistributionIn],
    *,
    today: date | None = None,
) -> tuple[list[DistributionIn], int]:
    """Drop incoming past prelims already superseded by a stored or batch final/paid."""
    today = today or utc_today()
    incoming = [incoming_identity(record) for record in records]
    paid_index = build_paid_season_index([*load_paid_rows(session), *incoming])
    kept: list[DistributionIn] = []
    skipped = 0
    for record, view in zip(records, incoming, strict=True):
        if is_stale_superseded_preliminary(view, today, paid_index):
            skipped += 1
            continue
        kept.append(record)
    return kept, skipped


def scrub_stale_preliminary_estimates(session: Session, today: date | None = None) -> int:
    """Delete stored past prelims superseded by final/paid for the same fund + year.

    Past prelims with no matching final/paid are kept (never invent a final) and
    do not set ``has_estimate``. Render's SQLite disk survives redeploy, so seed
    and boot must delete leftovers or they stay in Search after the skip lands.
    """
    today = today or utc_today()
    rows = list(
        session.scalars(
            select(DistributionEstimate).where(
                DistributionEstimate.publication_stage.in_(
                    [PublicationStage.preliminary_estimate.value, *PAID_STAGES]
                )
            )
        )
    )
    paid_index = build_paid_season_index(rows)
    ids = [row.id for row in rows if is_stale_superseded_preliminary(row, today, paid_index)]
    if not ids:
        return 0
    result = session.execute(delete(DistributionEstimate).where(DistributionEstimate.id.in_(ids)))
    session.flush()
    return int(result.rowcount or 0)
