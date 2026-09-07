from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.crud import latest_run, log_coverage_gap
from app.models import CoverageGap, DistributionEstimate
from app.schemas import CoverageGapIn, CoverageGapOut, FundFamilyOut
from app.sources.base import FundSource
from app.sources.registry import get_source, list_sources, resolve_slug


def family_to_out(source: FundSource, session: Session | None = None) -> FundFamilyOut:
    run = latest_run(session, source.slug) if session is not None else None
    return FundFamilyOut(
        slug=source.slug,
        display_name=source.display_name,
        implemented=source.implemented,
        coverage_tier=source.coverage_tier,
        aum_rank=source.aum_rank,
        priority=source.priority,
        notes=source.notes,
        source_urls=source.source_urls(),
        last_ingest_at=run.finished_at if run else None,
        last_ingest_status=run.status if run else None,
        last_ingest_mode=run.mode if run else None,
        last_ingest_created=run.records_created if run else None,
        last_ingest_updated=run.records_updated if run else None,
        last_error=run.error_message if run else None,
    )


def _lookup_existing(session: Session, ticker: str | None, fund_name: str | None) -> DistributionEstimate | None:
    if ticker:
        row = session.scalar(
            select(DistributionEstimate)
            .where(DistributionEstimate.ticker == ticker.upper())
            .order_by(DistributionEstimate.as_of.desc().nulls_last())
            .limit(1)
        )
        if row:
            return row
    if fund_name:
        return session.scalar(
            select(DistributionEstimate)
            .where(DistributionEstimate.fund_name.ilike(f"%{fund_name.strip()}%"))
            .order_by(DistributionEstimate.as_of.desc().nulls_last())
            .limit(1)
        )
    return None


def _match_source(family: str | None) -> FundSource | None:
    slug = resolve_slug(family)
    if not slug:
        return None
    try:
        return get_source(slug)
    except KeyError:
        return None


def record_gap(session: Session, body: CoverageGapIn) -> CoverageGapOut:
    source = _match_source(body.fund_family)
    existing = None
    if source is None:
        existing = _lookup_existing(session, body.ticker, body.fund_name)
        if existing:
            source = _match_source(existing.fund_family)

    if source is None:
        step = "manual_ingest"
        detail = (
            "No registered adapter matched this ticker/family. "
            "POST /ingest/distributions with a partner record (escape hatch), "
            "or retry with fund_family set to a registered slug."
        )
        adapter_slug = None
        exists = False
        implemented = False
    elif source.implemented:
        step = "fetch_adapter"
        detail = (
            f"Adapter '{source.slug}' is implemented. "
            f"POST /ingest/fetch for {source.slug} (fixture or live), then "
            f"GET /distributions?ticker={body.ticker or ''}. "
            "If the ticker is still missing, POST /ingest/distributions."
        )
        adapter_slug = source.slug
        exists = True
        implemented = True
    else:
        step = "queued"
        detail = (
            f"Adapter '{source.slug}' is registered but not implemented. "
            "Queued for a parser; until then POST /ingest/distributions."
        )
        adapter_slug = source.slug
        exists = True
        implemented = False

    gap = CoverageGap(
        ticker=body.ticker,
        fund_name=body.fund_name,
        fund_family=body.fund_family or (source.display_name if source else None),
        holding_dollars=body.holding_dollars,
        adapter_slug=adapter_slug,
        adapter_exists=exists,
        adapter_implemented=implemented,
        suggested_next_step=step,
        detail=detail,
        created_at=datetime.now(timezone.utc),
    )
    log_coverage_gap(session, gap)
    return CoverageGapOut.model_validate(gap)


def coverage_snapshot(session: Session) -> dict:
    families = [family_to_out(source, session) for source in list_sources()]
    implemented = sum(1 for f in families if f.coverage_tier == "implemented")
    stub = sum(1 for f in families if f.coverage_tier == "stub")
    top_n = len(families)
    from app.crud import count_coverage_gaps

    return {
        "top_n": top_n,
        "implemented_count": implemented,
        "stub_count": stub,
        "implemented_pct": round(100.0 * implemented / top_n, 1) if top_n else 0.0,
        "logged_gap_count": count_coverage_gaps(session),
        "families": families,
    }
