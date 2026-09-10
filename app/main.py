from __future__ import annotations

import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api import router
from app import db as app_db
from app.config import settings
from app.db import init_db
from app.services.illustrate import NEEDS_NAV_OR_SHARES, NEEDS_NAV_OR_SHARES_MESSAGE, NeedsNavOrShares

logger = logging.getLogger(__name__)

_seed_lock = threading.Lock()
_seed_state = {"status": "idle", "created": 0, "error": None}


def seed_status() -> str:
    return str(_seed_state["status"])


def _ensure_sqlite_dir() -> None:
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        return
    db_path = url.removeprefix("sqlite:///")
    if db_path.startswith(":memory:"):
        return
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def cors_origins() -> list[str]:
    return [part.strip() for part in settings.cors_origins.split(",") if part.strip()]


def _should_seed_on_start() -> bool:
    return bool(settings.seed_on_start or os.getenv("VERCEL"))


def _seed_fixture_if_empty() -> None:
    """Ingest every registered family from fixtures (same as POST /ingest/fetch all).

    Used on SEED_ON_START / Vercel boot and by tests. Commits per family so a
    mid-book failure still leaves a thick DB. Does not invent amounts.
    """
    from app.services.ingest import fetch_and_ingest
    from app.sources.registry import list_sources

    if app_db.SessionLocal is None:
        return
    with _seed_lock:
        if _seed_state["status"] == "running":
            return
        _seed_state["status"] = "running"
        _seed_state["error"] = None
    created_total = 0
    mode = settings.fetch_mode or "fixture"
    try:
        try:
            from app.crud import scrub_qdi_percent_characterizations

            with app_db.SessionLocal() as session:
                removed = scrub_qdi_percent_characterizations(session)
                session.commit()
            if removed:
                logger.info("Scrubbed %s QDI percent characterization rows", removed)
        except Exception:
            logger.exception("QDI percent scrub failed; continuing")
        for source in list_sources():
            if not source.implemented:
                continue
            try:
                with app_db.SessionLocal() as session:
                    result = fetch_and_ingest(session, source.slug, mode, review_outliers=False)
                    session.commit()
                    created_total += int(result.created or 0)
            except Exception:
                logger.exception("Fixture seed failed for %s; continuing", source.slug)
        try:
            from app.services.nav import refresh_navs

            with app_db.SessionLocal() as session:
                nav = refresh_navs(session, mode=mode if mode in {"fixture", "live", "auto"} else "fixture")
                session.commit()
            logger.info(
                "Fixture NAV seed created=%s updated=%s unknown=%s",
                nav.created,
                nav.updated,
                nav.unknown,
            )
        except Exception:
            logger.exception("Fixture NAV seed failed; continuing with null NAV")
        try:
            from app.services.quality import flag_category_outliers

            with app_db.SessionLocal() as session:
                flagged = flag_category_outliers(session)
                session.commit()
            logger.info("Category-outlier review flagged=%s", flagged)
        except Exception:
            logger.exception("Category-outlier review failed; continuing")
        _seed_state["created"] = created_total
        _seed_state["status"] = "complete"
        logger.info("Fixture seed complete created=%s", created_total)
    except Exception as exc:
        _seed_state["status"] = "error"
        _seed_state["error"] = str(exc)
        logger.exception("Fixture seed aborted")


def _start_background_seed() -> None:
    thread = threading.Thread(
        target=_seed_fixture_if_empty,
        name="fixture-seed",
        daemon=True,
    )
    thread.start()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _ensure_sqlite_dir()
    init_db()
    # Persistent Render disk keeps mis-parsed QDI % rows across deploys.
    if app_db.SessionLocal is not None:
        try:
            from app.crud import scrub_qdi_percent_characterizations

            with app_db.SessionLocal() as session:
                removed = scrub_qdi_percent_characterizations(session)
                session.commit()
            if removed:
                logger.info("Boot-scrubbed %s QDI percent characterization rows", removed)
        except Exception:
            logger.exception("Boot QDI percent scrub failed; continuing")
    if _should_seed_on_start():
        # /health must come up before the full book finishes (~11k fixture rows).
        _start_background_seed()
    yield


app = FastAPI(
    title="Fund Distribution Estimates API",
    description=(
        "Ingest and search taxable distribution estimates published by fund managers "
        "(top-110 US-advisor families). POST /illustrate computes tax-impact math; "
        "POST /illustrate/compare is the fund chart contract; "
        "POST /illustrate/portfolio/compare is Current vs Proposed Allocation; "
        "GET /performance and POST /performance/growth are Growth of $X charts "
        "(independent of tax endpoints); "
        "GET /coverage (including lookback_5y) and POST /coverage/gaps support Aftertax portfolio review."
    ),
    version=__version__,
    lifespan=lifespan,
)

_origins = cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins if _origins != ["*"] else ["*"],
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.exception_handler(NeedsNavOrShares)
async def needs_nav_or_shares_handler(_request: Request, exc: NeedsNavOrShares) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"code": NEEDS_NAV_OR_SHARES, "detail": NEEDS_NAV_OR_SHARES_MESSAGE},
        headers={"X-Error-Code": NEEDS_NAV_OR_SHARES},
    )


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = jsonable_encoder(exc.errors(), custom_encoder={Exception: str})
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation failed", "errors": errors},
    )
