from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import record_ingest_run, upsert_records
from app.models import IngestRun
from app.schemas import DistributionIn, IngestItemOut, IngestResponse
from app.sources.parser import NormalizedRecord
from app.sources.registry import resolve_families


def normalized_to_in(record: NormalizedRecord) -> DistributionIn:
    return DistributionIn(
        fund_family=record.fund_family,
        fund_name=record.fund_name,
        ticker=record.ticker,
        share_class=record.share_class,
        estimate_type=record.estimate_type,
        amount=record.amount,
        amount_min=record.amount_min,
        amount_max=record.amount_max,
        amount_unit=record.amount_unit,
        record_date=record.record_date,
        ex_date=record.ex_date,
        payable_date=record.payable_date,
        as_of=record.as_of,
        publication_stage=record.publication_stage,
        source_url=record.source_url,
        raw_payload=record.raw_payload,
    )


def _items_from_stored(stored: list) -> list[IngestItemOut]:
    return [
        IngestItemOut(
            id=row.id,
            action=action,
            upsert_key=row.upsert_key,
            fund_name=row.fund_name,
            estimate_type=row.estimate_type,
        )
        for action, row in stored
    ]


def ingest_records(session: Session, records: list[DistributionIn]) -> IngestResponse:
    created, updated, stored = upsert_records(session, records)
    return IngestResponse(created=created, updated=updated, items=_items_from_stored(stored))


def fetch_and_ingest(session: Session, fund_family: str, mode: str | None) -> IngestResponse:
    fetch_mode = (mode or settings.fetch_mode).lower()
    try:
        sources = resolve_families(fund_family)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    created_total = 0
    updated_total = 0
    items: list[IngestItemOut] = []
    urls: list[str] = []
    families_run: list[str] = []

    for source in sources:
        started = datetime.now(timezone.utc)
        run = IngestRun(
            fund_family=source.slug,
            mode=fetch_mode,
            status="running",
            started_at=started,
            source_urls=source.source_urls(),
        )
        if not source.implemented:
            run.status = "skipped"
            run.finished_at = datetime.now(timezone.utc)
            run.error_message = source.notes
            record_ingest_run(session, run)
            continue
        try:
            result = source.fetch(mode=fetch_mode)
            incoming = [normalized_to_in(r) for r in result.records]
            created, updated, stored = upsert_records(session, incoming)
            run.status = "success"
            run.finished_at = datetime.now(timezone.utc)
            run.records_created = created
            run.records_updated = updated
            run.source_urls = result.source_urls
            record_ingest_run(session, run)
            created_total += created
            updated_total += updated
            items.extend(_items_from_stored(stored))
            urls.extend(result.source_urls)
            families_run.append(source.slug)
        except NotImplementedError as exc:
            run.status = "skipped"
            run.finished_at = datetime.now(timezone.utc)
            run.error_message = str(exc)
            record_ingest_run(session, run)
            raise HTTPException(status_code=501, detail=str(exc)) from exc
        except HTTPException:
            raise
        except Exception as exc:
            run.status = "error"
            run.finished_at = datetime.now(timezone.utc)
            run.error_message = str(exc)
            record_ingest_run(session, run)
            raise HTTPException(status_code=502, detail=f"Fetch failed for {source.slug}: {exc}") from exc

    if not families_run:
        raise HTTPException(
            status_code=400,
            detail="No implemented fund-family adapters matched the request.",
        )

    return IngestResponse(
        created=created_total,
        updated=updated_total,
        fund_family=families_run[0] if len(families_run) == 1 else "all",
        mode=fetch_mode,
        source_urls=urls,
        items=items,
    )
