from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select

from app import __version__
from app.api import router
from app import db as app_db
from app.config import settings
from app.db import init_db


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
    from app.models import DistributionEstimate
    from app.services.ingest import fetch_and_ingest

    if app_db.SessionLocal is None:
        return
    with app_db.SessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(DistributionEstimate)) or 0
        if count:
            return
        fetch_and_ingest(session, "american_funds", settings.fetch_mode or "fixture")
        session.commit()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _ensure_sqlite_dir()
    init_db()
    if _should_seed_on_start():
        _seed_fixture_if_empty()
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
        "GET /coverage and POST /coverage/gaps support Aftertax portfolio review."
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


@app.exception_handler(RequestValidationError)
async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = jsonable_encoder(exc.errors(), custom_encoder={Exception: str})
    return JSONResponse(
        status_code=422,
        content={"detail": "Validation failed", "errors": errors},
    )
