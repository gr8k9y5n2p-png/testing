from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models import AmountUnit, EstimateType, PublicationStage


def _empty_to_none(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


class DistributionIn(BaseModel):
    fund_family: str = Field(..., min_length=1, max_length=128)
    fund_name: str = Field(..., min_length=1, max_length=512)
    ticker: str | None = Field(default=None, max_length=32)
    cusip: str | None = Field(default=None, max_length=16)
    share_class: str | None = Field(default=None, max_length=32)
    estimate_type: EstimateType
    amount: Decimal | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None
    amount_unit: AmountUnit
    record_date: date | None = None
    ex_date: date | None = None
    payable_date: date | None = None
    as_of: date | None = None
    publication_stage: PublicationStage | None = None
    source_url: str | None = Field(default=None, max_length=2048)
    raw_payload: dict[str, Any] | None = None

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("ticker", "cusip", "share_class", "source_url", mode="before")
    @classmethod
    def blank_to_none(cls, value: Any) -> Any:
        return _empty_to_none(value)

    @field_validator("ticker", mode="after")
    @classmethod
    def ticker_upper(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("cusip", mode="after")
    @classmethod
    def cusip_upper(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @model_validator(mode="after")
    def require_amount(self) -> DistributionIn:
        if self.amount is None and self.amount_min is None and self.amount_max is None:
            raise ValueError("at least one of amount, amount_min, amount_max is required")
        return self


class IngestRequest(BaseModel):
    records: list[DistributionIn] = Field(..., min_length=1, max_length=5000)


class FetchRequest(BaseModel):
    fund_family: str = Field(
        ...,
        description='Registered family slug (e.g. "american_funds") or "all".',
        min_length=1,
        max_length=128,
    )
    mode: str | None = Field(
        default=None,
        description='Override fetch mode: "fixture" (offline HTML) or "live" (HTTP).',
    )

    @field_validator("mode")
    @classmethod
    def mode_ok(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {"fixture", "live"}
        if value not in allowed:
            raise ValueError(f"mode must be one of {sorted(allowed)}")
        return value


class DistributionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    upsert_key: str
    fund_family: str
    fund_name: str
    fund_identifier: str
    ticker: str | None
    cusip: str | None
    share_class: str | None
    estimate_type: str
    amount: Decimal | None
    amount_min: Decimal | None
    amount_max: Decimal | None
    amount_unit: str
    record_date: date | None
    ex_date: date | None
    payable_date: date | None
    as_of: date | None
    publication_stage: str | None
    source_url: str | None
    raw_payload: dict[str, Any] | None = None
    ingested_at: datetime


class DistributionListOut(BaseModel):
    items: list[DistributionOut]
    page: int
    page_size: int
    total: int


class IngestItemOut(BaseModel):
    id: str
    action: str
    upsert_key: str
    fund_name: str
    estimate_type: str


class IngestResponse(BaseModel):
    created: int
    updated: int
    fund_family: str | None = None
    mode: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    items: list[IngestItemOut]


class ErrorBody(BaseModel):
    detail: str
    errors: list[dict[str, Any]] | None = None


class HealthOut(BaseModel):
    status: str
    db: str
    registered_families: list[str]


class FundFamilyOut(BaseModel):
    slug: str
    display_name: str
    implemented: bool
    notes: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    last_ingest_at: datetime | None = None
    last_ingest_status: str | None = None
    last_ingest_mode: str | None = None
    last_ingest_created: int | None = None
    last_ingest_updated: int | None = None
    last_error: str | None = None


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify_fund_name(name: str) -> str:
    slug = _SLUG_RE.sub("-", name.lower()).strip("-")
    return slug or "unknown-fund"


def fund_identifier(ticker: str | None, fund_name: str) -> str:
    if ticker:
        return ticker.upper()
    return slugify_fund_name(fund_name)


def make_upsert_key(
    *,
    fund_family: str,
    fund_identifier_value: str,
    share_class: str | None,
    estimate_type: str,
    as_of: date | None,
    ex_date: date | None,
) -> str:
    """Idempotency key: family + fund + class + type + publication as_of + ex-date."""
    family = fund_family.strip().lower()
    ident = fund_identifier_value.strip().lower()
    share = (share_class or "").strip().lower()
    as_of_s = as_of.isoformat() if as_of else ""
    ex_s = ex_date.isoformat() if ex_date else ""
    return f"{family}|{ident}|{share}|{estimate_type}|{as_of_s}|{ex_s}"
