from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.crud import get_by_id, latest_run, search_distributions
from app.db import get_session
from app.schemas import (
    DistributionIn,
    DistributionListOut,
    DistributionOut,
    FetchRequest,
    FundFamilyOut,
    HealthOut,
    IngestRequest,
    IngestResponse,
)
from app.services.ingest import fetch_and_ingest, ingest_records
from app.sources.registry import list_sources

router = APIRouter()


@router.get("/health", response_model=HealthOut, tags=["ops"])
def health(session: Session = Depends(get_session)) -> HealthOut:
    db_status = "ok"
    try:
        session.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - connection failures
        db_status = f"error: {exc}"
    return HealthOut(
        status="ok" if db_status == "ok" else "degraded",
        db=db_status,
        registered_families=[s.slug for s in list_sources()],
    )


@router.post("/ingest/distributions", response_model=IngestResponse, tags=["ingest"])
def ingest_distributions(body: IngestRequest, session: Session = Depends(get_session)) -> IngestResponse:
    return ingest_records(session, body.records)


@router.post("/ingest/distributions/one", response_model=IngestResponse, tags=["ingest"], include_in_schema=False)
def ingest_one(body: DistributionIn, session: Session = Depends(get_session)) -> IngestResponse:
    return ingest_records(session, [body])


@router.post("/ingest/fetch", response_model=IngestResponse, tags=["ingest"])
def ingest_fetch(body: FetchRequest, session: Session = Depends(get_session)) -> IngestResponse:
    return fetch_and_ingest(session, body.fund_family, body.mode)


@router.get("/distributions", response_model=DistributionListOut, tags=["search"])
def list_distributions(
    q: str | None = Query(default=None, description="Text search across family, fund name, ticker"),
    fund_family: str | None = None,
    ticker: str | None = None,
    fund_name: str | None = None,
    estimate_type: str | None = None,
    publication_stage: str | None = None,
    as_of_from: date | None = None,
    as_of_to: date | None = None,
    ex_date_from: date | None = None,
    ex_date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    include_raw: bool = False,
    session: Session = Depends(get_session),
) -> DistributionListOut:
    rows, total = search_distributions(
        session,
        q=q,
        fund_family=fund_family,
        ticker=ticker,
        fund_name=fund_name,
        estimate_type=estimate_type,
        as_of_from=as_of_from,
        as_of_to=as_of_to,
        ex_date_from=ex_date_from,
        ex_date_to=ex_date_to,
        publication_stage=publication_stage,
        page=page,
        page_size=page_size,
    )
    items = []
    for row in rows:
        item = DistributionOut.model_validate(row)
        if not include_raw:
            item.raw_payload = None
        items.append(item)
    return DistributionListOut(items=items, page=page, page_size=page_size, total=total)


@router.get("/distributions/{distribution_id}", response_model=DistributionOut, tags=["search"])
def get_distribution(distribution_id: str, session: Session = Depends(get_session)) -> DistributionOut:
    row = get_by_id(session, distribution_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Distribution estimate not found")
    return DistributionOut.model_validate(row)


@router.get("/fund-families", response_model=list[FundFamilyOut], tags=["search"])
def fund_families(session: Session = Depends(get_session)) -> list[FundFamilyOut]:
    out: list[FundFamilyOut] = []
    for source in list_sources():
        run = latest_run(session, source.slug)
        out.append(
            FundFamilyOut(
                slug=source.slug,
                display_name=source.display_name,
                implemented=source.implemented,
                notes=source.notes,
                source_urls=source.source_urls(),
                last_ingest_at=run.finished_at if run else None,
                last_ingest_status=run.status if run else None,
                last_ingest_mode=run.mode if run else None,
                last_ingest_created=run.records_created if run else None,
                last_ingest_updated=run.records_updated if run else None,
                last_error=run.error_message if run else None,
            )
        )
    return out
