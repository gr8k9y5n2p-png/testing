from __future__ import annotations

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


def _ensure_sqlite_dir() -> None:
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        return
    db_path = url.removeprefix("sqlite:///")
    if db_path.startswith(":memory:"):
        return
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _ensure_sqlite_dir()
    init_db()
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
