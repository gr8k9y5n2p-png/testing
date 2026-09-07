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
    coverage_tier: str = "stub"
    aum_rank: int | None = None
    priority: int | None = None
    notes: str | None = None
    source_urls: list[str] = Field(default_factory=list)
    last_ingest_at: datetime | None = None
    last_ingest_status: str | None = None
    last_ingest_mode: str | None = None
    last_ingest_created: int | None = None
    last_ingest_updated: int | None = None
    last_error: str | None = None


class CoverageOut(BaseModel):
    top_n: int
    implemented_count: int
    stub_count: int
    implemented_pct: float
    logged_gap_count: int
    families: list[FundFamilyOut]


class CoverageGapIn(BaseModel):
    ticker: str | None = Field(default=None, max_length=32)
    fund_name: str | None = Field(default=None, max_length=512)
    fund_family: str | None = Field(default=None, max_length=128)
    holding_dollars: Decimal | None = Field(default=None, ge=0)

    @field_validator("ticker", "fund_name", "fund_family", mode="before")
    @classmethod
    def blank_gap_fields(cls, value: Any) -> Any:
        return _empty_to_none(value)

    @field_validator("ticker", mode="after")
    @classmethod
    def gap_ticker_upper(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("holding_dollars", mode="before")
    @classmethod
    def gap_dollars(cls, value: Any) -> Any:
        if isinstance(value, float):
            return Decimal(str(value))
        return value

    @model_validator(mode="after")
    def require_ticker_or_name(self) -> CoverageGapIn:
        if not self.ticker and not self.fund_name:
            raise ValueError("ticker or fund_name is required")
        return self


class CoverageGapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ticker: str | None
    fund_name: str | None
    fund_family: str | None
    holding_dollars: Decimal | None
    adapter_slug: str | None
    adapter_exists: bool
    adapter_implemented: bool
    suggested_next_step: str
    detail: str | None
    created_at: datetime


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


class TaxRates(BaseModel):
    """Marginal rates as decimals (0.20 = 20%). All fields optional; omitted keys use defaults.

    Defaults are *illustrative* top federal brackets plus a sample state rate, not tax advice.
    """

    ordinary_income: Decimal = Field(default=Decimal("0.37"), ge=0, le=1)
    long_term_capital_gains: Decimal = Field(default=Decimal("0.20"), ge=0, le=1)
    short_term_capital_gains: Decimal = Field(
        default=Decimal("0.37"),
        ge=0,
        le=1,
        description="STCG is taxed as ordinary income; defaults to the ordinary rate but can be overridden independently.",
    )
    qualified_dividend: Decimal = Field(default=Decimal("0.20"), ge=0, le=1)
    return_of_capital: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=1,
        description="ROC is generally not currently taxable (basis reduction). Default 0.",
    )
    state: Decimal = Field(default=Decimal("0.05"), ge=0, le=1)

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "ordinary_income",
        "long_term_capital_gains",
        "short_term_capital_gains",
        "qualified_dividend",
        "return_of_capital",
        "state",
        mode="before",
    )
    @classmethod
    def decimal_from_json_float(cls, value: Any) -> Any:
        if isinstance(value, float):
            return Decimal(str(value))
        return value


class IllustrateSelectors(BaseModel):
    fund_family: str | None = None
    fund_identifier: str | None = None
    fund_name: str | None = None
    ticker: str | None = None
    estimate_type: str | None = None
    as_of: date | None = Field(default=None, description="Pin to one publication snapshot.")
    publication_stage: str | None = None

    def has_any(self) -> bool:
        return any(
            [
                self.fund_family,
                self.fund_identifier,
                self.fund_name,
                self.ticker,
                self.estimate_type,
                self.as_of,
                self.publication_stage,
            ]
        )


class IllustrateRequest(BaseModel):
    holding_dollars: Decimal = Field(..., gt=0, description="Market value of the holding to illustrate.")
    distribution_ids: list[str] | None = Field(
        default=None,
        description="Explicit estimate row IDs. If set, selectors are ignored.",
    )
    selectors: IllustrateSelectors | None = Field(
        default=None,
        description="Find estimates by family/fund/as_of when IDs are not provided.",
    )
    nav_per_share: Decimal | None = Field(
        default=None,
        gt=0,
        description="Required (unless shares is set) when any selected row uses amount_unit=per_share.",
    )
    shares: Decimal | None = Field(
        default=None,
        gt=0,
        description="Share units. If omitted, computed as holding_dollars / nav_per_share.",
    )
    tax_rates: TaxRates = Field(default_factory=TaxRates)
    combine_state_with_federal: bool = True
    latest_as_of_only: bool = Field(
        default=True,
        description="When using selectors, keep only the newest as_of per fund so snapshots are not double-counted.",
    )

    @field_validator("holding_dollars", "nav_per_share", "shares", mode="before")
    @classmethod
    def money_from_json_float(cls, value: Any) -> Any:
        if isinstance(value, float):
            return Decimal(str(value))
        return value

    @model_validator(mode="after")
    def require_source(self) -> IllustrateRequest:
        has_ids = bool(self.distribution_ids)
        has_selectors = bool(self.selectors and self.selectors.has_any())
        if has_ids and has_selectors:
            raise ValueError("provide distribution_ids or selectors, not both")
        if not has_ids and not has_selectors:
            raise ValueError("provide distribution_ids or selectors")
        return self


class IllustrationComponent(BaseModel):
    distribution_id: str
    fund_family: str
    fund_name: str
    fund_identifier: str
    ticker: str | None
    estimate_type: str
    amount_unit: str
    amount: Decimal | None
    amount_min: Decimal | None
    amount_max: Decimal | None
    as_of: date | None
    ex_date: date | None
    federal_rate_key: str | None
    federal_rate: Decimal | None
    state_rate: Decimal | None
    applied_rate: Decimal | None
    distribution_dollars: Decimal | None
    distribution_dollars_min: Decimal | None
    distribution_dollars_max: Decimal | None
    estimated_tax: Decimal | None
    estimated_tax_min: Decimal | None
    estimated_tax_max: Decimal | None
    federal_tax: Decimal | None
    state_tax: Decimal | None
    included_in_totals: bool
    skip_reason: str | None = None


class IllustrationTotals(BaseModel):
    distribution_dollars: Decimal
    distribution_dollars_min: Decimal | None
    distribution_dollars_max: Decimal | None
    estimated_tax: Decimal
    estimated_tax_min: Decimal | None
    estimated_tax_max: Decimal | None
    federal_tax: Decimal
    state_tax: Decimal
    effective_tax_on_holding: Decimal


class IllustrateResponse(BaseModel):
    holding_dollars: Decimal
    shares: Decimal | None
    nav_per_share: Decimal | None
    tax_rates: TaxRates
    combine_state_with_federal: bool
    rate_mapping: dict[str, str]
    components: list[IllustrationComponent]
    totals: IllustrationTotals
    notes: list[str]
