from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.aliases import display_cusip, display_ticker
from app.categories import category_for_row
from app.crud import (
    FundSummary,
    coverage_status_for_in_book_fund,
    get_by_id,
    list_coverage_gaps,
    list_fund_category_counts,
    resolve_page_from_limit_offset,
    search_distributions,
    search_funds,
)
from app.db import get_session, ping_db, read_with_lock_retry
from app.schemas import (
    CoverageGapIn,
    CoverageGapOut,
    CoverageOut,
    DistributionIn,
    DistributionListOut,
    DistributionOut,
    FundCategoryListOut,
    FundCategoryOut,
    FundListOut,
    FundLookupMissOut,
    FundOut,
    FetchRequest,
    FundFamilyOut,
    HealthOut,
    CompareRequest,
    CompareResponse,
    IllustrateRequest,
    IllustrateResponse,
    PortfolioCompareRequest,
    PortfolioCompareResponse,
    PortfolioIllustrateRequest,
    PortfolioIllustrateResponse,
    IngestRequest,
    IngestResponse,
    PerformanceGrowthRequest,
    PerformanceResponse,
    TickerRequestIn,
    TickerRequestIngestOut,
    TickerRequestListOut,
    TickerRequestOut,
    WebsiteTickerRequestListOut,
    WebsiteTickerRequestOut,
)
from app.services.coverage import coverage_snapshot, family_to_out, record_gap
from app.services.nav import (
    apply_distribution_day_nav,
    get_nav_map,
    listed_ticker,
    nav_on_distribution_day_map,
)
from app.services.performance import growth_of_x
from app.services.ticker_requests import (
    list_ticker_requests,
    process_ticker_requests,
    submit_ticker_request,
    submit_website_ticker_request,
)
from app.services.illustrate import (
    illustrate,
    illustrate_compare,
    illustrate_portfolio,
    illustrate_portfolio_compare,
)
from app.services.ingest import fetch_and_ingest, ingest_records
from app.sources.registry import list_sources, registered_family_slugs

router = APIRouter()


def _fund_out(row: FundSummary, navs: dict) -> FundOut:
    ticker = display_ticker(row.ticker, row.fund_identifier)
    nav = navs.get(listed_ticker(row.ticker, row.fund_identifier) or "")
    has_estimate = bool(row.has_estimate)
    return FundOut(
        ticker=ticker,
        fund_name=row.fund_name,
        fund_family=row.fund_family,
        fund_identifier=row.fund_identifier,
        category=row.category,
        latest_as_of=row.latest_as_of,
        has_estimate=has_estimate,
        coverage_status=coverage_status_for_in_book_fund(has_estimate=has_estimate),
        nav_per_share=nav.nav_per_share if nav else None,
        nav_as_of=nav.nav_as_of if nav else None,
        nav_source=nav.source if nav else None,
    )


def _fund_matches_lookup_ticker(row: FundSummary, ticker: str) -> bool:
    wanted = ticker.strip().upper()
    shown = (display_ticker(row.ticker, row.fund_identifier) or "").upper()
    stored = (row.ticker or "").upper()
    ident = (row.fund_identifier or "").upper()
    return wanted in {shown, stored, ident}


@router.get("/health", response_model=HealthOut, tags=["ops"])
def health() -> HealthOut:
    """Liveness: HTTP 200 as soon as the process is listening, even mid-seed."""
    from app.main import seed_status

    return HealthOut(
        status="ok",
        db=ping_db(),
        registered_families=list(registered_family_slugs()),
        seed=seed_status(),
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
    fund_identifier: str | None = Query(
        default=None,
        description="Exact fund_identifier (ticker or name slug), e.g. amcap-fund",
    ),
    ticker: str | None = None,
    fund_name: str | None = None,
    estimate_type: str | None = None,
    publication_stage: str | None = Query(
        default=None,
        description="Filter one snapshot type: preliminary_estimate, updated_estimate, final, paid.",
    ),
    as_of_from: date | None = Query(
        default=None,
        description="Inclusive publication as_of lower bound for multi-year history.",
    ),
    as_of_to: date | None = Query(
        default=None,
        description="Inclusive publication as_of upper bound for multi-year history.",
    ),
    ex_date_from: date | None = None,
    ex_date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    limit: int | None = Query(
        default=None,
        ge=1,
        le=200,
        description="Website alias of page_size. When set, overrides page_size.",
    ),
    offset: int | None = Query(
        default=None,
        ge=0,
        description="Website alias of (page-1)*page_size. When set, overrides page.",
    ),
    include_raw: bool = False,
    needs_review: bool | None = Query(
        default=None,
        description="If true, only rows flagged for data-quality review (e.g. category_outlier).",
    ),
    session: Session = Depends(get_session),
) -> DistributionListOut:
    page, page_size = resolve_page_from_limit_offset(
        page=page, page_size=page_size, limit=limit, offset=offset
    )
    rows, total = search_distributions(
        session,
        q=q,
        fund_family=fund_family,
        fund_identifier=fund_identifier,
        ticker=ticker,
        fund_name=fund_name,
        estimate_type=estimate_type,
        as_of_from=as_of_from,
        as_of_to=as_of_to,
        ex_date_from=ex_date_from,
        ex_date_to=ex_date_to,
        publication_stage=publication_stage,
        needs_review=needs_review,
        page=page,
        page_size=page_size,
    )
    day_navs = nav_on_distribution_day_map(session, rows)
    items = []
    for row in rows:
        item = DistributionOut.model_validate(row)
        item.ticker = display_ticker(item.ticker, item.fund_identifier)
        item.cusip = display_cusip(item.cusip, item.fund_identifier)
        item.category = category_for_row(item)
        apply_distribution_day_nav(item, day_navs.get(row.id))
        if not include_raw:
            item.raw_payload = None
        items.append(item)
    return DistributionListOut(items=items, page=page, page_size=page_size, total=total)


@router.get("/funds/categories", response_model=FundCategoryListOut, tags=["search"])
def list_fund_categories(
    q: str | None = Query(default=None, description="Optional search narrowing the counted book"),
    fund_family: str | None = None,
    session: Session = Depends(get_session),
) -> FundCategoryListOut:
    """Distinct Morningstar-style categories with stored-fund counts. For Versus Category UI."""
    pairs, uncategorized, total = list_fund_category_counts(
        session, q=q, fund_family=fund_family
    )
    categorized = total - uncategorized
    coverage = round(100.0 * categorized / total, 1) if total else 0.0
    return FundCategoryListOut(
        items=[FundCategoryOut(category=name, fund_count=count) for name, count in pairs],
        uncategorized=uncategorized,
        total_funds=total,
        categorized=categorized,
        coverage_pct=coverage,
    )


@router.get(
    "/funds/lookup",
    response_model=FundOut,
    responses={404: {"model": FundLookupMissOut, "description": "Ticker is not in the coverage universe."}},
    tags=["search"],
)
def lookup_fund(
    ticker: str = Query(
        ...,
        min_length=1,
        max_length=32,
        description="Exact ticker (e.g. AGTHX). Miss → 404 not_in_universe, not Awaiting Estimate.",
    ),
    session: Session = Depends(get_session),
) -> FundOut | JSONResponse:
    """Exact ticker lookup. In-book funds return coverage_status; misses are not_in_universe."""
    wanted = ticker.strip().upper()

    def _load() -> tuple[FundSummary | None, dict]:
        rows, _total = search_funds(session, q=wanted, limit=50, offset=0)
        found = next((row for row in rows if _fund_matches_lookup_ticker(row, wanted)), None)
        if found is None:
            return None, {}
        navs_by_ticker = get_nav_map(
            session,
            [listed_ticker(found.ticker, found.fund_identifier)],
        )
        return found, navs_by_ticker

    match, navs = read_with_lock_retry(_load)
    if match is None:
        return JSONResponse(
            status_code=404,
            content=FundLookupMissOut(ticker=wanted).model_dump(),
        )
    return _fund_out(match, navs)


@router.get("/funds", response_model=FundListOut, tags=["search"])
def list_funds(
    q: str | None = Query(default=None, description="Search ticker, fund name, family, or identifier"),
    fund_family: str | None = None,
    category: str | None = Query(
        default=None,
        description=(
            "Optional Morningstar-style category filter (e.g. Large Growth). "
            "Case/hyphen insensitive. Unknown category names return an empty list."
        ),
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> FundListOut:
    """Unique funds already in the distribution store. For Website Search / Sample Estimates."""

    def _load() -> tuple[list, int, dict]:
        found, count = search_funds(
            session, q=q, fund_family=fund_family, category=category, limit=limit, offset=offset
        )
        navs_by_ticker = get_nav_map(
            session,
            [listed_ticker(row.ticker, row.fund_identifier) for row in found],
        )
        return found, count, navs_by_ticker

    rows, total, navs = read_with_lock_retry(_load)
    items = [_fund_out(row, navs) for row in rows]
    return FundListOut(items=items, limit=limit, offset=offset, total=total)


@router.get("/distributions/{distribution_id}", response_model=DistributionOut, tags=["search"])
def get_distribution(distribution_id: str, session: Session = Depends(get_session)) -> DistributionOut:
    row = get_by_id(session, distribution_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Distribution estimate not found")
    item = DistributionOut.model_validate(row)
    item.ticker = display_ticker(item.ticker, item.fund_identifier)
    item.cusip = display_cusip(item.cusip, item.fund_identifier)
    item.category = category_for_row(item)
    day_navs = nav_on_distribution_day_map(session, [row])
    apply_distribution_day_nav(item, day_navs.get(row.id))
    return item


@router.get("/fund-families", response_model=list[FundFamilyOut], tags=["search"])
def fund_families(session: Session = Depends(get_session)) -> list[FundFamilyOut]:
    return [family_to_out(source, session) for source in list_sources()]


@router.get("/coverage", response_model=CoverageOut, tags=["coverage"])
def coverage(session: Session = Depends(get_session)) -> CoverageOut:
    """Registered US-advisor family coverage for portfolio-review % covered later."""
    return CoverageOut.model_validate(coverage_snapshot(session))


@router.post("/coverage/gaps", response_model=CoverageGapOut, tags=["coverage"])
def report_coverage_gap(body: CoverageGapIn, session: Session = Depends(get_session)) -> CoverageGapOut:
    """Log an uncovered portfolio ticker/family and return the suggested next step."""
    return record_gap(session, body)


@router.get("/coverage/gaps", response_model=list[CoverageGapOut], tags=["coverage"])
def coverage_gaps(
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> list[CoverageGapOut]:
    return [CoverageGapOut.model_validate(row) for row in list_coverage_gaps(session, limit=limit)]


@router.post(
    "/requests/tickers",
    response_model=TickerRequestOut,
    status_code=202,
    tags=["requests"],
)
def create_ticker_request(
    body: TickerRequestIn, session: Session = Depends(get_session)
) -> TickerRequestOut:
    """Record a Website-submitted ticker for issuer-source ingest. Never invents amounts."""
    return submit_ticker_request(session, body)


@router.get("/requests/tickers", response_model=TickerRequestListOut, tags=["requests"])
def get_ticker_requests(
    status: str | None = Query(
        default=None,
        description="queued | search_issuer | matched | already_covered | skipped",
    ),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> TickerRequestListOut:
    rows = list_ticker_requests(session, status=status, limit=limit)
    return TickerRequestListOut(
        items=[TickerRequestOut.model_validate(row) for row in rows],
        total=len(rows),
    )


def _website_ticker_out(row: TickerRequestOut) -> WebsiteTickerRequestOut:
    return WebsiteTickerRequestOut(
        id=row.id,
        ticker=row.ticker,
        status=row.status,
        message=row.message or row.detail or "",
    )


@router.post("/request/ticker", tags=["requests"])
def website_create_ticker_request(
    body: TickerRequestIn, session: Session = Depends(get_session)
) -> JSONResponse:
    """Website Submit-ticker box. No auth for beta. 201 queued / 200 already_covered / 422 invalid."""
    try:
        out, status_code = submit_website_ticker_request(session, body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return JSONResponse(status_code=status_code, content=jsonable_encoder(_website_ticker_out(out)))


@router.get("/request/ticker", response_model=WebsiteTickerRequestListOut, tags=["requests"])
def website_list_ticker_requests(
    status: str | None = Query(
        default="queued",
        description="queued | search_issuer | matched | already_covered | skipped",
    ),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> WebsiteTickerRequestListOut:
    rows = list_ticker_requests(session, status=status, limit=limit)
    items = [_website_ticker_out(TickerRequestOut.model_validate(row)) for row in rows]
    return WebsiteTickerRequestListOut(items=items, total=len(items))


@router.post("/ingest/ticker-requests", response_model=TickerRequestIngestOut, tags=["ingest"])
def ingest_ticker_requests(
    mode: str | None = Query(default=None, description="fixture | live | omit for FETCH_MODE"),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> TickerRequestIngestOut:
    """Pick up queued ticker requests and fetch the matched family adapter when known."""
    items = process_ticker_requests(session, mode=mode, limit=limit)
    return TickerRequestIngestOut(processed=len(items), items=items)


@router.post("/illustrate", response_model=IllustrateResponse, tags=["illustrate"])
def illustrate_tax(body: IllustrateRequest, session: Session = Depends(get_session)) -> IllustrateResponse:
    """Server-side tax-impact illustration for a dollar holding against stored estimates."""
    return illustrate(session, body)


@router.post("/illustrate/portfolio", response_model=PortfolioIllustrateResponse, tags=["illustrate"])
def illustrate_portfolio_tax(
    body: PortfolioIllustrateRequest, session: Session = Depends(get_session)
) -> PortfolioIllustrateResponse:
    """Aftertax portfolio review: per-holding math, coverage by dollars, and explicit gaps."""
    return illustrate_portfolio(session, body)


@router.post(
    "/illustrate/portfolio/compare",
    response_model=PortfolioCompareResponse,
    tags=["illustrate"],
)
def illustrate_portfolio_compare_tax(
    body: PortfolioCompareRequest, session: Session = Depends(get_session)
) -> PortfolioCompareResponse:
    """Current vs Proposed Allocation. Omit periods for one snapshot; send periods[] for YoY bars."""
    return illustrate_portfolio_compare(session, body)


@router.post("/illustrate/compare", response_model=CompareResponse, tags=["illustrate"])
def illustrate_compare_tax(body: CompareRequest, session: Session = Depends(get_session)) -> CompareResponse:
    """Fund-vs-fund or year-over-year chart contract for Interactive Modules."""
    return illustrate_compare(session, body)


@router.get("/performance", response_model=PerformanceResponse, tags=["performance"])
def get_performance(
    ticker: str | None = Query(default=None),
    fund_identifier: str | None = Query(
        default=None,
        description="Ticker or stored slug (e.g. AGTHX or the-growth-fund-of-america).",
    ),
    benchmark: str | None = Query(
        default=None,
        description="ETF/fund ticker. Omit to use the asset-class default (SPY / AGG / VXUS).",
    ),
    asset_class: str | None = Query(
        default=None,
        description="equity | fixed_income | international. Picks the default ETF benchmark.",
    ),
    benchmark_hint: str | None = Query(
        default=None,
        description="Alias of asset_class for Modules that already send a hint.",
    ),
    start_dollars: float = Query(default=10_000, gt=0),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    mode: str | None = Query(
        default=None,
        description="fixture | live | auto. Omit to use FETCH_MODE (fixture in CI).",
    ),
) -> PerformanceResponse:
    """Growth of $X monthly series. Independent of tax / illustrate contracts."""
    if not ticker and not fund_identifier:
        raise HTTPException(status_code=422, detail="ticker or fund_identifier is required")
    try:
        payload = PerformanceGrowthRequest(
            ticker=ticker,
            fund_identifier=fund_identifier,
            benchmark=benchmark,
            asset_class=asset_class,  # type: ignore[arg-type]
            benchmark_hint=benchmark_hint,  # type: ignore[arg-type]
            start_dollars=start_dollars,
            start_date=start_date,
            end_date=end_date,
            mode=mode,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return PerformanceResponse.model_validate(growth_of_x(payload))


@router.post("/performance/growth", response_model=PerformanceResponse, tags=["performance"])
def post_performance_growth(payload: PerformanceGrowthRequest) -> PerformanceResponse:
    """Same Growth of $X payload as GET /performance, as a JSON body."""
    return PerformanceResponse.model_validate(growth_of_x(payload))
