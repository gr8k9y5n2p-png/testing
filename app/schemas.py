from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

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
    seed: str = "idle"


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
    """Money fields are null when the side is unmatched (N/A) — never invent $0.

    A published $0 / 0% of NAV still serializes as ``0.00`` with ``matched=true``.
    """

    distribution_dollars: Decimal | None
    distribution_dollars_min: Decimal | None
    distribution_dollars_max: Decimal | None
    estimated_tax: Decimal | None
    estimated_tax_min: Decimal | None
    estimated_tax_max: Decimal | None
    federal_tax: Decimal | None
    state_tax: Decimal | None
    effective_tax_on_holding: Decimal | None


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


def normalize_weight_pct(value: Decimal) -> Decimal:
    """Interpret ``weight_pct`` as Interactive Modules UI percent (0–100).

    ``25`` is 25% of ``book_dollars``. ``1`` is 1%, not a full book.
    """
    if value <= 0 or value > 100:
        raise ValueError("weight_pct must be in (0, 100] (UI percent)")
    return value / Decimal("100")


class PortfolioHoldingIn(BaseModel):
    holding_dollars: Decimal | None = Field(
        default=None,
        gt=0,
        description="Market value. Optional when weight_pct is set with book_dollars.",
    )
    weight_pct: Decimal | None = Field(
        default=None,
        gt=0,
        le=100,
        description=(
            "Allocation weight as Interactive Modules UI percent (0–100). "
            "25 = 25% of the side's book_dollars. Mutually exclusive with holding_dollars."
        ),
    )
    book_dollars: Decimal | None = Field(
        default=None,
        gt=0,
        description="Optional holding-level book. Compare prefers book_dollars on the side object.",
    )
    ticker: str | None = Field(default=None, max_length=32)
    fund_family: str | None = None
    fund_identifier: str | None = None
    fund_name: str | None = None
    distribution_ids: list[str] | None = None
    nav_per_share: Decimal | None = Field(default=None, gt=0)
    shares: Decimal | None = Field(default=None, gt=0)

    @field_validator("ticker", "fund_family", "fund_identifier", "fund_name", mode="before")
    @classmethod
    def blank_holding(cls, value: Any) -> Any:
        return _empty_to_none(value)

    @field_validator("ticker", mode="after")
    @classmethod
    def holding_ticker_upper(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator(
        "holding_dollars", "nav_per_share", "shares", "weight_pct", "book_dollars", mode="before"
    )
    @classmethod
    def holding_money(cls, value: Any) -> Any:
        if isinstance(value, float):
            return Decimal(str(value))
        return value

    @model_validator(mode="after")
    def require_lookup(self) -> PortfolioHoldingIn:
        if not any([self.ticker, self.fund_identifier, self.fund_name, self.distribution_ids]):
            raise ValueError("each holding needs ticker and/or fund_identifier (or fund_name / distribution_ids)")
        if self.holding_dollars is not None and self.weight_pct is not None:
            raise ValueError("each holding needs either holding_dollars or weight_pct, not both")
        if self.holding_dollars is not None:
            return self
        if self.weight_pct is None:
            raise ValueError("each holding needs holding_dollars, or weight_pct with book_dollars")
        if self.book_dollars is None:
            return self
        dollars = self.book_dollars * normalize_weight_pct(self.weight_pct)
        if dollars <= 0:
            raise ValueError("book_dollars * weight_pct must be greater than 0")
        return self.model_copy(update={"holding_dollars": dollars})


class IllustrationSnapshot(BaseModel):
    prefer_publication_stages: list[str] = Field(
        default_factory=lambda: [
            PublicationStage.preliminary_estimate.value,
            PublicationStage.updated_estimate.value,
            PublicationStage.final.value,
            PublicationStage.paid.value,
        ],
        description="Walk this order and keep the first stage that has rows for the holding.",
    )
    as_of: date | None = Field(default=None, description="Pin every holding to one publication as_of.")
    as_of_year: int | None = Field(
        default=None,
        ge=1900,
        le=2100,
        description="When as_of is omitted, keep rows whose as_of falls in this calendar year.",
    )
    latest_as_of_only: bool = True


class PortfolioIllustrateRequest(BaseModel):
    holdings: list[PortfolioHoldingIn] = Field(..., min_length=1, max_length=500)
    tax_rates: TaxRates = Field(default_factory=TaxRates)
    combine_state_with_federal: bool = True
    snapshot: IllustrationSnapshot = Field(default_factory=IllustrationSnapshot)

    @model_validator(mode="after")
    def holdings_have_dollars(self) -> PortfolioIllustrateRequest:
        for index, holding in enumerate(self.holdings):
            if holding.holding_dollars is None:
                raise ValueError(
                    f"holdings[{index}] needs holding_dollars, or weight_pct with book_dollars"
                )
        return self


class PortfolioHoldingGap(BaseModel):
    holding_index: int
    ticker: str | None
    fund_identifier: str | None
    fund_family: str | None
    fund_name: str | None
    holding_dollars: Decimal
    reason: str


class PortfolioHoldingUpcoming(BaseModel):
    """Convenience slice of the illustration chosen for this holding."""

    distribution_dollars: Decimal
    estimated_tax: Decimal
    as_of: date | None = None
    publication_stage: str | None = None


class PortfolioHoldingOut(BaseModel):
    holding_index: int
    ticker: str | None
    fund_identifier: str | None
    fund_family: str | None
    fund_name: str | None
    holding_dollars: Decimal
    covered: bool
    publication_stage_used: str | None = None
    upcoming: PortfolioHoldingUpcoming | None = Field(
        default=None,
        description="Null when uncovered/gap or the chosen illustration has no distribution dollars.",
    )
    warnings: list[str] = Field(default_factory=list)
    illustration: IllustrateResponse | None = None
    gap_reason: str | None = None


class PortfolioCoverage(BaseModel):
    dollars_total: Decimal
    dollars_covered: Decimal
    dollars_uncovered: Decimal
    coverage_pct: Decimal
    holdings_covered: int
    holdings_uncovered: int


class PortfolioIllustrateResponse(BaseModel):
    holdings: list[PortfolioHoldingOut]
    totals: IllustrationTotals
    coverage: PortfolioCoverage
    gaps: list[PortfolioHoldingGap]
    warnings: list[str]
    tax_rates: TaxRates
    combine_state_with_federal: bool
    rate_mapping: dict[str, str]
    notes: list[str]


class CompareSideIn(BaseModel):
    label: str | None = None
    selectors: IllustrateSelectors | None = None
    distribution_ids: list[str] | None = None
    holding_dollars: Decimal | None = Field(default=None, gt=0)
    nav_per_share: Decimal | None = Field(default=None, gt=0)
    shares: Decimal | None = Field(default=None, gt=0)

    @field_validator("holding_dollars", "nav_per_share", "shares", mode="before")
    @classmethod
    def side_money(cls, value: Any) -> Any:
        if isinstance(value, float):
            return Decimal(str(value))
        return value

    def has_lookup(self) -> bool:
        return bool(self.distribution_ids) or bool(self.selectors and self.selectors.has_any())


def _selector_key(selectors: IllustrateSelectors | None, attr: str) -> str:
    raw = getattr(selectors, attr, None) if selectors else None
    return (raw or "").strip().lower()


def sides_look_like_same_fund(left: CompareSideIn | None, right: CompareSideIn | None) -> bool:
    if not left or not right or not left.selectors or not right.selectors:
        return False
    for attr in ("fund_identifier", "ticker", "fund_name"):
        a, b = _selector_key(left.selectors, attr), _selector_key(right.selectors, attr)
        if a and b and a == b:
            return True
    return False


class ComparePeriodIn(BaseModel):
    year: int = Field(..., ge=1900, le=2100)
    as_of: date | None = Field(default=None, description="Pin both sides (or this YoY vintage) to one as_of.")


class CompareRequest(BaseModel):
    mode: Literal["fund_vs_fund", "yoy"] | None = Field(
        default=None,
        description="Omit to infer: same fund on left/right → yoy; otherwise fund_vs_fund.",
    )
    holding_dollars: Decimal = Field(..., gt=0)
    tax_rates: TaxRates = Field(default_factory=TaxRates)
    combine_state_with_federal: bool = True
    latest_as_of_only: bool = Field(
        default=True,
        description="When a period has no as_of, keep only the newest snapshot per fund.",
    )
    left: CompareSideIn | None = None
    right: CompareSideIn | None = None
    selectors: IllustrateSelectors | None = Field(
        default=None,
        description="YoY: one fund's selectors. periods[] supply the two (or more) vintages.",
    )
    periods: list[ComparePeriodIn] = Field(default_factory=list)
    nav_per_share: Decimal | None = Field(default=None, gt=0)
    shares: Decimal | None = Field(default=None, gt=0)

    @field_validator("holding_dollars", "nav_per_share", "shares", mode="before")
    @classmethod
    def compare_money(cls, value: Any) -> Any:
        if isinstance(value, float):
            return Decimal(str(value))
        return value

    @model_validator(mode="after")
    def validate_compare_shape(self) -> CompareRequest:
        left_ok = bool(self.left and self.left.has_lookup())
        right_ok = bool(self.right and self.right.has_lookup())
        shared = bool(self.selectors and self.selectors.has_any())
        mode = self.mode
        if mode is None:
            if left_ok and right_ok and sides_look_like_same_fund(self.left, self.right):
                mode = "yoy"
            elif left_ok and right_ok:
                mode = "fund_vs_fund"
            elif shared or left_ok:
                mode = "yoy"
            else:
                raise ValueError("provide left and right (or mode + selectors/periods)")
        if mode == "fund_vs_fund":
            if not left_ok:
                raise ValueError("fund_vs_fund requires left.selectors or left.distribution_ids")
            if not right_ok:
                raise ValueError("fund_vs_fund requires right.selectors or right.distribution_ids")
            return self.model_copy(update={"mode": mode})
        if left_ok and right_ok:
            return self.model_copy(update={"mode": mode})
        if shared or left_ok:
            if len(self.periods) < 2:
                raise ValueError("yoy with one selectors block requires at least two periods")
            return self.model_copy(update={"mode": mode})
        raise ValueError(
            "yoy requires selectors (or left.selectors) plus two periods, or left and right sides"
        )


class CompareIllustration(IllustrateResponse):
    """Single-fund illustration plus the chart series label."""

    label: str
    matched: bool = True


class CompareDeltas(BaseModel):
    """right − left (B − A). Chart Interactive Modules on effective_tax_on_holding.

    Money fields are null when either side is unmatched (N/A). Published zeros
    still produce ``0.00`` deltas when both sides matched.
    """

    distribution_dollars: Decimal | None
    distribution_dollars_min: Decimal | None = None
    distribution_dollars_max: Decimal | None = None
    estimated_tax: Decimal | None
    estimated_tax_min: Decimal | None = None
    estimated_tax_max: Decimal | None = None
    federal_tax: Decimal | None
    state_tax: Decimal | None
    effective_tax_on_holding: Decimal | None
    effective_tax_on_holding_min: Decimal | None = None
    effective_tax_on_holding_max: Decimal | None = None


class ComparePeriodOut(BaseModel):
    year: int
    as_of: date | None
    left: CompareIllustration
    right: CompareIllustration
    deltas: CompareDeltas


class CompareCommonInception(BaseModel):
    from_year: int | None = None
    to_year: int | None = None
    from_as_of: date | None = None
    to_as_of: date | None = None


class CompareUpcomingDistribution(BaseModel):
    """Current-calendar-year upcoming taxable $ on the $10k summary holding."""

    left_dollars: Decimal | None = None
    right_dollars: Decimal | None = None
    delta_dollars: Decimal | None = None
    left_as_of: date | None = None
    right_as_of: date | None = None
    left_publication_stage: str | None = None
    right_publication_stage: str | None = None


class CompareSummary(BaseModel):
    """Interactive Modules footer. Dollar fields are always normalized to $10,000."""

    normalized_holding_dollars: Decimal
    total_tax_difference: Decimal
    annualized_tax_drag_delta: Decimal
    distribution_dollars_difference: Decimal
    periods_compared: int
    common_inception: CompareCommonInception
    upcoming_taxable_distribution: CompareUpcomingDistribution | None = None


class CompareResponse(BaseModel):
    mode: Literal["fund_vs_fund", "yoy"]
    left: CompareIllustration | None = Field(
        default=None,
        description="Newest (or only) pair's left illustration — YoY AMCAP sketch shape.",
    )
    right: CompareIllustration | None = None
    deltas: CompareDeltas | None = Field(
        default=None,
        description="Newest (or only) pair's right − left deltas.",
    )
    periods: list[ComparePeriodOut]
    summary: CompareSummary
    notes: list[str]


def resolve_portfolio_holding_dollars(
    holding: PortfolioHoldingIn,
    *,
    side_book: Decimal | None = None,
) -> PortfolioHoldingIn:
    """Fill holding_dollars from weight_pct × the side's book_dollars."""
    if holding.holding_dollars is not None:
        return holding
    if holding.weight_pct is None:
        raise ValueError("each holding needs holding_dollars, or weight_pct with book_dollars")
    book = side_book or holding.book_dollars
    if book is None:
        raise ValueError("weight_pct requires book_dollars on the current/proposed side")
    dollars = book * normalize_weight_pct(holding.weight_pct)
    if dollars <= 0:
        raise ValueError("book_dollars * weight_pct must be greater than 0")
    return holding.model_copy(update={"holding_dollars": dollars, "weight_pct": None})


class PortfolioCompareSideIn(BaseModel):
    label: str | None = Field(default=None, description="Chart series label.")
    book_dollars: Decimal | None = Field(
        default=None,
        gt=0,
        description="Applies to weight_pct holdings on this side: holding_dollars = book_dollars * weight_pct / 100.",
    )
    holdings: list[PortfolioHoldingIn] = Field(..., min_length=1, max_length=500)

    @field_validator("book_dollars", mode="before")
    @classmethod
    def side_book_money(cls, value: Any) -> Any:
        if isinstance(value, float):
            return Decimal(str(value))
        return value


class PortfolioCompareRequest(BaseModel):
    """Current vs Proposed Allocation. Omit ``periods`` for one snapshot; send ``periods`` for YoY bars."""

    current: PortfolioCompareSideIn
    proposed: PortfolioCompareSideIn
    tax_rates: TaxRates = Field(default_factory=TaxRates)
    combine_state_with_federal: bool = True
    snapshot: IllustrationSnapshot = Field(default_factory=IllustrationSnapshot)
    periods: list[ComparePeriodIn] = Field(
        default_factory=list,
        description=(
            "Optional YoY vintages. Each entry pins both books via snapshot.as_of "
            "(or as_of_year when as_of is omitted). Omit for single-snapshot compare."
        ),
    )

    @model_validator(mode="after")
    def resolve_weights(self) -> PortfolioCompareRequest:
        current_holdings = [
            resolve_portfolio_holding_dollars(holding, side_book=self.current.book_dollars)
            for holding in self.current.holdings
        ]
        proposed_holdings = [
            resolve_portfolio_holding_dollars(holding, side_book=self.proposed.book_dollars)
            for holding in self.proposed.holdings
        ]
        return self.model_copy(
            update={
                "current": self.current.model_copy(update={"holdings": current_holdings}),
                "proposed": self.proposed.model_copy(update={"holdings": proposed_holdings}),
            }
        )


class PortfolioCompareAllocationOut(PortfolioIllustrateResponse):
    """One allocation book: full portfolio illustration plus the series label."""

    label: str


class PortfolioCompareDeltas(BaseModel):
    """proposed − current. Interactive Modules charts these four fields."""

    estimated_tax: Decimal
    distribution_dollars: Decimal
    effective_tax_on_holding: Decimal
    coverage_pct: Decimal
    estimated_tax_min: Decimal | None = None
    estimated_tax_max: Decimal | None = None
    distribution_dollars_min: Decimal | None = None
    distribution_dollars_max: Decimal | None = None


class PortfolioCompareSummary(BaseModel):
    """Interactive Modules footer. Dollar fields are scaled linearly to $10,000."""

    normalized_book_dollars: Decimal
    estimated_tax: Decimal
    distribution_dollars: Decimal
    effective_tax_on_holding: Decimal
    coverage_pct: Decimal
    total_tax_difference: Decimal | None = Field(
        default=None,
        description="Σ period estimated_tax Δ scaled to $10k (periods mode).",
    )
    annualized_tax_drag_delta: Decimal | None = Field(
        default=None,
        description="Mean of period effective_tax_on_holding Δ.",
    )
    distribution_dollars_difference: Decimal | None = Field(
        default=None,
        description="Σ period distribution_dollars Δ scaled to $10k (periods mode).",
    )
    periods_compared: int = 0
    common_inception: CompareCommonInception | None = None


class PortfolioComparePeriodOut(BaseModel):
    year: int
    as_of: date | None
    current: PortfolioCompareAllocationOut
    proposed: PortfolioCompareAllocationOut
    deltas: PortfolioCompareDeltas


class PortfolioCompareResponse(BaseModel):
    current: PortfolioCompareAllocationOut | None = Field(
        default=None,
        description="Single snapshot, or the latest periods[] row when YoY is requested.",
    )
    proposed: PortfolioCompareAllocationOut | None = None
    deltas: PortfolioCompareDeltas | None = Field(
        default=None,
        description="Single snapshot or latest period: proposed − current.",
    )
    periods: list[PortfolioComparePeriodOut] = Field(
        default_factory=list,
        description="Empty when periods[] was omitted (single-snapshot mode).",
    )
    summary: PortfolioCompareSummary
    notes: list[str]


AssetClassHint = Literal["equity", "fixed_income", "international"]


class PerformanceGrowthRequest(BaseModel):
    """Growth of $X chart request. Independent of tax / illustrate contracts."""

    ticker: str | None = Field(default=None, max_length=32)
    fund_identifier: str | None = Field(
        default=None,
        max_length=128,
        description="Ticker or stored slug (e.g. AGTHX or the-growth-fund-of-america).",
    )
    benchmark: str | None = Field(
        default=None,
        max_length=32,
        description="ETF/fund ticker. Omit to use the asset-class default (SPY / AGG / VXUS).",
    )
    asset_class: AssetClassHint | None = Field(
        default=None,
        description="equity | fixed_income | international. Used to pick the default ETF benchmark.",
    )
    benchmark_hint: AssetClassHint | None = Field(
        default=None,
        description="Alias of asset_class for Modules that already send a hint.",
    )
    start_dollars: Decimal = Field(default=Decimal("10000"), gt=0)
    start_date: date | None = None
    end_date: date | None = None
    mode: str | None = Field(
        default=None,
        description='fixture (offline), live (Yahoo chart), or auto (live then fixture).',
    )

    model_config = ConfigDict(extra="forbid")

    @field_validator("ticker", "fund_identifier", "benchmark", mode="before")
    @classmethod
    def blank_perf_fields(cls, value: Any) -> Any:
        return _empty_to_none(value)

    @field_validator("ticker", "benchmark", mode="after")
    @classmethod
    def perf_ticker_upper(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("start_dollars", mode="before")
    @classmethod
    def perf_dollars(cls, value: Any) -> Any:
        if isinstance(value, float):
            return Decimal(str(value))
        return value

    @field_validator("mode")
    @classmethod
    def perf_mode_ok(cls, value: str | None) -> str | None:
        if value is None:
            return value
        allowed = {"fixture", "live", "auto"}
        if value not in allowed:
            raise ValueError(f"mode must be one of {sorted(allowed)}")
        return value

    @model_validator(mode="after")
    def require_fund(self) -> PerformanceGrowthRequest:
        if not self.ticker and not self.fund_identifier:
            raise ValueError("ticker or fund_identifier is required")
        return self


class PerformancePoint(BaseModel):
    date: date
    adj_close: Decimal = Field(description="Yahoo split/dividend-adjusted close (USD per share).")
    monthly_return: Decimal | None = Field(
        default=None,
        description="Decimal total return vs prior month (0.01 = 1%). Null on the first point.",
    )
    growth_of_x: Decimal = Field(description="Cumulative dollars if start_dollars was invested at the first point.")


class PerformanceSeriesOut(BaseModel):
    ticker: str
    name: str
    currency: str = "USD"
    price_unit: str = "usd_per_share_adjusted"
    return_unit: str = "decimal"
    growth_unit: str = "usd"
    points: list[PerformancePoint]


class PerformanceResponse(BaseModel):
    fund_ticker: str
    fund_identifier: str
    fund_name: str
    asset_class: AssetClassHint
    start_dollars: Decimal
    start_date: date
    end_date: date
    as_of: date
    frequency: Literal["monthly"] = "monthly"
    mode: str
    source: str
    source_urls: list[str] = Field(default_factory=list)
    benchmark_id: str = Field(description="ETF or fund ticker actually plotted (SPY, AGG, VXUS, or an override).")
    benchmark_label: str = Field(
        description="UI label, e.g. 'Bloomberg US Aggregate (via AGG ETF total return)'.",
    )
    benchmark_tracks: str = Field(
        description="Index the ETF is commonly said to track. The series is still the ETF, not a licensed index.",
    )
    is_proxy: bool = Field(description="True when the series is a default ETF proxy (SPY, AGG, VXUS).")
    fund: PerformanceSeriesOut
    benchmark: PerformanceSeriesOut
    disclaimers: list[str] = Field(default_factory=list)
