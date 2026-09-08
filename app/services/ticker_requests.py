"""User-requested ticker intake for Website → Data API ingest.

Records a ticker and resolves it to a registered family when possible.
Never invents distribution amounts. Amundi / Pioneer stays skipped.
Unknown tickers remain ``search_issuer`` for a later issuer-source hunt.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.aliases import alias_family_slug
from app.models import DistributionEstimate, TickerRequest
from app.schemas import TickerRequestIn, TickerRequestOut
from app.sources.registry import get_source, resolve_slug
from app.services.ingest import fetch_and_ingest

SKIPPED_SLUGS = frozenset({"amundi"})
PICKUP_STATUSES = frozenset({"queued", "search_issuer", "matched"})
WEBSITE_TICKER_RE = re.compile(r"^[A-Z][A-Z0-9]{1,7}$")

# Official-book tickers → adapter slug for weekly expand (never invents amounts).
KNOWN_TICKER_SLUGS: dict[str, str] = {
    "SGENX": "first_eagle",
    "FESGX": "first_eagle",
    "SGIIX": "first_eagle",
    "FEGRX": "first_eagle",
    "SGOVX": "first_eagle",
    "FEVAX": "first_eagle",
    "FEGE": "first_eagle",
    "FEOE": "first_eagle",
    "GDX": "vaneck",
    "SMH": "vaneck",
    "MOAT": "vaneck",
    "INIVX": "vaneck",
    "MWMIX": "vaneck",
    "IBOT": "vaneck",
    "BFAP": "first_trust",
    "BFJL": "first_trust",
    "BGLD": "first_trust",
    "IGLD": "first_trust",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _lookup_existing(session: Session, ticker: str) -> DistributionEstimate | None:
    return session.scalar(
        select(DistributionEstimate)
        .where(DistributionEstimate.ticker == ticker.upper())
        .order_by(DistributionEstimate.as_of.desc().nulls_last())
        .limit(1)
    )


def _resolve_slug(body: TickerRequestIn, existing: DistributionEstimate | None) -> str | None:
    if body.fund_family:
        slug = resolve_slug(body.fund_family)
        if slug:
            return slug
    if existing:
        slug = resolve_slug(existing.fund_family)
        if slug:
            return slug
    return alias_family_slug(body.ticker) or KNOWN_TICKER_SLUGS.get(body.ticker.upper())


def _classify(session: Session, body: TickerRequestIn) -> tuple[str, str | None, str]:
    existing = _lookup_existing(session, body.ticker)
    slug = _resolve_slug(body, existing)

    if slug in SKIPPED_SLUGS:
        return (
            "skipped",
            slug,
            "Amundi / Pioneer is skipped. Do not invent amounts or expand this book.",
        )
    if existing:
        return (
            "already_covered",
            slug or resolve_slug(existing.fund_family),
            (
                f"Ticker {body.ticker} is already in the distribution store "
                f"({existing.fund_family}). GET /distributions?ticker={body.ticker}."
            ),
        )
    if slug is None:
        return (
            "search_issuer",
            None,
            (
                f"No registered adapter matched {body.ticker}. "
                "Queued for an issuer-source search. Do not invent amounts. "
                "Website must not block illustrate on this pending request."
            ),
        )
    source = get_source(slug)
    if not source.implemented:
        return (
            "queued",
            slug,
            f"Adapter '{slug}' is registered but not implemented. Queued; do not invent amounts.",
        )
    return (
        "matched",
        slug,
        (
            f"Adapter '{slug}' is implemented. "
            f"POST /ingest/fetch for {slug} (or POST /ingest/ticker-requests) "
            f"then GET /distributions?ticker={body.ticker}. "
            "If the ticker is still missing after fetch, it is not on the public book."
        ),
    )


def submit_ticker_request(session: Session, body: TickerRequestIn) -> TickerRequestOut:
    status, slug, detail = _classify(session, body)
    now = _now()
    row = TickerRequest(
        ticker=body.ticker,
        fund_name=body.fund_name,
        fund_family=body.fund_family,
        source=body.source or "website_ui",
        status=status,
        adapter_slug=slug,
        detail=detail,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.flush()
    return TickerRequestOut.model_validate(row)


def submit_website_ticker_request(
    session: Session, body: TickerRequestIn
) -> tuple[TickerRequestOut, int]:
    """Website Submit-ticker box: 200 already_covered / 201 queued / 422 invalid.

    Unknown tickers persist as ``queued`` for weekly expand. Never invents amounts.
    """
    if not WEBSITE_TICKER_RE.fullmatch(body.ticker):
        raise ValueError("invalid ticker")
    existing = _lookup_existing(session, body.ticker)
    slug = _resolve_slug(body, existing)
    now = _now()
    if existing:
        status = "already_covered"
        detail = (
            f"Ticker {body.ticker} is already in the distribution store "
            f"({existing.fund_family}). GET /distributions?ticker={body.ticker}."
        )
        http_status = 200
        slug = slug or resolve_slug(existing.fund_family)
    elif slug in SKIPPED_SLUGS:
        status = "skipped"
        detail = "Amundi / Pioneer is skipped. Do not invent amounts or expand this book."
        http_status = 201
    else:
        status = "queued"
        if slug:
            detail = (
                f"Queued {body.ticker} for weekly expand via adapter '{slug}'. "
                "Do not invent amounts. Website must not block illustrate on this pending request."
            )
        else:
            detail = (
                f"Queued {body.ticker} for an issuer-source search. "
                "Do not invent amounts. Website must not block illustrate on this pending request."
            )
        if body.note:
            detail = f"{detail} Note: {body.note}"
        http_status = 201
    row = TickerRequest(
        ticker=body.ticker,
        fund_name=body.fund_name,
        fund_family=body.fund_family,
        source=body.source or "website_ui",
        status=status,
        adapter_slug=slug,
        detail=detail,
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.flush()
    return TickerRequestOut.model_validate(row), http_status


def list_ticker_requests(
    session: Session, *, status: str | None = None, limit: int = 100
) -> list[TickerRequest]:
    stmt = select(TickerRequest).order_by(TickerRequest.created_at.desc())
    if status:
        stmt = stmt.where(TickerRequest.status == status)
    return list(session.scalars(stmt.limit(limit)).all())


def process_ticker_requests(
    session: Session, *, mode: str | None = None, limit: int = 50
) -> list[TickerRequestOut]:
    """Pick up queued/search/matched rows. Fetch the adapter when known. Never invent amounts."""
    rows = [
        row
        for row in list_ticker_requests(session, limit=500)
        if row.status in PICKUP_STATUSES
    ][:limit]
    out: list[TickerRequestOut] = []
    fetched: set[str] = set()
    for row in rows:
        slug = (
            row.adapter_slug
            or resolve_slug(row.fund_family)
            or alias_family_slug(row.ticker)
            or KNOWN_TICKER_SLUGS.get((row.ticker or "").upper())
        )
        if slug in SKIPPED_SLUGS:
            row.status = "skipped"
            row.adapter_slug = slug
            row.detail = "Amundi / Pioneer is skipped. Do not invent amounts or expand this book."
            row.updated_at = _now()
            out.append(TickerRequestOut.model_validate(row))
            continue
        if slug and slug not in fetched:
            try:
                fetch_and_ingest(session, slug, mode)
                fetched.add(slug)
            except Exception as exc:
                row.status = "search_issuer"
                row.adapter_slug = slug
                row.detail = (
                    f"Adapter '{slug}' fetch did not complete ({exc}). "
                    "Left for issuer-source search. No amounts invented."
                )
                row.updated_at = _now()
                out.append(TickerRequestOut.model_validate(row))
                continue
        existing = _lookup_existing(session, row.ticker)
        if existing:
            row.status = "already_covered"
            row.adapter_slug = slug or resolve_slug(existing.fund_family)
            row.detail = (
                f"Ticker {row.ticker} is in the store after ingest "
                f"({existing.fund_family}). GET /distributions?ticker={row.ticker}."
            )
        elif slug:
            row.status = "matched"
            row.adapter_slug = slug
            row.detail = (
                f"Adapter '{slug}' was fetched; {row.ticker} is still not on the public book. "
                "Do not invent amounts. Leave for a later issuer-source search or partner ingest."
            )
        else:
            row.status = "search_issuer"
            row.detail = (
                f"No registered adapter matched {row.ticker}. "
                "Still queued for an issuer-source search. Do not invent amounts."
            )
        row.updated_at = _now()
        out.append(TickerRequestOut.model_validate(row))
    session.flush()
    return out
