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
    """Seed fixtures on boot without blocking HTTP.

    Empty disk: full fixture ingest (same records as POST /ingest/fetch all).
    Warm Render disk: densify only missing families or changed fixture files.
    Does not invent amounts. Commits per family.
    """
    from app.services.boot_seed import run_boot_seed

    run_boot_seed(_seed_state, _seed_lock)


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
    if _should_seed_on_start():
        # Listen immediately. Scrub + delta seed run in a background thread so
        # Render's /health probe is not blocked by fixture ingest or SQLite writes.
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
