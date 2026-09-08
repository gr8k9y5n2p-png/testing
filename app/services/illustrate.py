from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.aliases import TICKER_LOOKUP_ALIASES
from app.crud import get_by_ids, list_matching
from app.models import AmountUnit, DistributionEstimate, EstimateType, PublicationStage
from app.schemas import (
    CompareCommonInception,
    CompareDeltas,
    CompareIllustration,
    ComparePeriodIn,
    ComparePeriodOut,
    CompareRequest,
    CompareResponse,
    CompareSideIn,
    CompareSummary,
    CompareUpcomingDistribution,
    IllustrationComponent,
    IllustrationSnapshot,
    IllustrationTotals,
    IllustrateRequest,
    IllustrateResponse,
    IllustrateSelectors,
    PortfolioCompareAllocationOut,
    PortfolioCompareDeltas,
    PortfolioComparePeriodOut,
    PortfolioCompareRequest,
    PortfolioCompareResponse,
    PortfolioCompareSummary,
    PortfolioCoverage,
    PortfolioHoldingGap,
    PortfolioHoldingIn,
    PortfolioHoldingOut,
    PortfolioHoldingUpcoming,
    PortfolioIllustrateRequest,
    PortfolioIllustrateResponse,
    TaxRates,
)

CENTS = Decimal("0.01")
RATE_PLACES = Decimal("0.000001")
SUMMARY_HOLDING = Decimal("10000")

UPCOMING_ESTIMATE_STAGES = {
    PublicationStage.updated_estimate.value,
    PublicationStage.preliminary_estimate.value,
}
PAID_HISTORY_STAGES = {
    PublicationStage.final.value,
    PublicationStage.paid.value,
}

# estimate_type → TaxRates field. STCG has its own rate (defaults to ordinary).
# Unspecified combined capital-gain estimates are treated as LTCG.
# Unspecified "total" is treated as ordinary (conservative).
RATE_MAPPING: dict[str, str] = {
    EstimateType.ordinary_income.value: "ordinary_income",
    EstimateType.short_term_capital_gains.value: "short_term_capital_gains",
    EstimateType.long_term_capital_gains.value: "long_term_capital_gains",
    EstimateType.total_capital_gains.value: "long_term_capital_gains",
    EstimateType.total.value: "ordinary_income",
    EstimateType.qualified_dividend.value: "qualified_dividend",
    EstimateType.qualified_short_term_gains.value: "qualified_dividend",
    EstimateType.special_dividend.value: "ordinary_income",
    EstimateType.return_of_capital.value: "return_of_capital",
    EstimateType.other.value: "ordinary_income",
}

NEEDS_NAV_OR_SHARES = "needs_nav_or_shares"
NEEDS_NAV_OR_SHARES_MESSAGE = (
    "nav_per_share or shares is required when illustrating per_share distributions"
)


class NeedsNavOrShares(HTTPException):
    """422 when amount_unit=per_share cannot be priced without NAV or share units."""

    def __init__(self) -> None:
        super().__init__(
            status_code=422,
            detail=NEEDS_NAV_OR_SHARES_MESSAGE,
            headers={"X-Error-Code": NEEDS_NAV_OR_SHARES},
        )


PERCENT_SKIP_REASON = (
    "amount_unit=percent is a characterization of fund income (e.g. qualified dividend "
    "percentage on Form 1099-DIV), not a dollar distribution as % of NAV or $ per share. "
    "Tax cannot be illustrated from holding_dollars alone."
)

ILLUSTRATION_NOTES = [
    "Illustration only; not tax, legal, or investment advice.",
    "Federal + state rates are applied as flat marginal rates supplied in the request (or defaults).",
    "amount_unit=percent rows (QDI-style) are listed but excluded from dollar totals.",
    "return_of_capital defaults to a 0% current tax rate (typically a basis adjustment).",
    "total_capital_gains (unsplit) uses the long_term_capital_gains rate; short_term_capital_gains uses its own rate (defaulting to ordinary).",
]


def _d(value: object | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENTS, rounding=ROUND_HALF_UP)


def _rate(value: Decimal) -> Decimal:
    return value.quantize(RATE_PLACES, rounding=ROUND_HALF_UP)


def _point_amount(row: DistributionEstimate) -> Decimal | None:
    amount = _d(row.amount)
    if amount is not None:
        return amount
    low, high = _d(row.amount_min), _d(row.amount_max)
    if low is not None and high is not None:
        return (low + high) / Decimal("2")
    return low if low is not None else high


def filter_latest_as_of(rows: list[DistributionEstimate]) -> list[DistributionEstimate]:
    groups: dict[tuple[str, str], list[DistributionEstimate]] = defaultdict(list)
    for row in rows:
        groups[(row.fund_family.lower(), row.fund_identifier.lower())].append(row)
    kept: list[DistributionEstimate] = []
    for items in groups.values():
        dated = [item for item in items if item.as_of is not None]
        undated = [item for item in items if item.as_of is None]
        if dated:
            latest = max(item.as_of for item in dated if item.as_of is not None)
            kept.extend(item for item in dated if item.as_of == latest)
        kept.extend(undated)
    return kept


def _distribution_dollars(
    *,
    unit: str,
    amount: Decimal | None,
    holding: Decimal,
    shares: Decimal | None,
) -> Decimal | None:
    if amount is None:
        return None
    if unit == AmountUnit.percent_of_nav.value:
        return holding * (amount / Decimal("100"))
    if unit == AmountUnit.per_share.value:
        if shares is None:
            return None
        return shares * amount
    return None


def _illustrate_row(
    row: DistributionEstimate,
    *,
    holding: Decimal,
    shares: Decimal | None,
    rates: TaxRates,
    combine: bool,
) -> IllustrationComponent:
    unit = row.amount_unit
    point = _point_amount(row)
    low = _d(row.amount_min)
    high = _d(row.amount_max)
    rate_key = RATE_MAPPING.get(row.estimate_type, "ordinary_income")
    federal = getattr(rates, rate_key)
    state = rates.state

    if unit == AmountUnit.per_share.value and shares is None:
        return IllustrationComponent(
            distribution_id=row.id,
            fund_family=row.fund_family,
            fund_name=row.fund_name,
            fund_identifier=row.fund_identifier,
            ticker=row.ticker,
            estimate_type=row.estimate_type,
            amount_unit=unit,
            amount=point,
            amount_min=low,
            amount_max=high,
            as_of=row.as_of,
            record_date=getattr(row, "record_date", None),
            ex_date=row.ex_date,
            payable_date=getattr(row, "payable_date", None),
            federal_rate_key=rate_key,
            federal_rate=_rate(federal),
            state_rate=_rate(state),
            applied_rate=None,
            distribution_dollars=None,
            distribution_dollars_min=None,
            distribution_dollars_max=None,
            estimated_tax=None,
            estimated_tax_min=None,
            estimated_tax_max=None,
            federal_tax=None,
            state_tax=None,
            included_in_totals=False,
            skip_reason=NEEDS_NAV_OR_SHARES_MESSAGE,
        )

    if unit == AmountUnit.percent.value:
        return IllustrationComponent(
            distribution_id=row.id,
            fund_family=row.fund_family,
            fund_name=row.fund_name,
            fund_identifier=row.fund_identifier,
            ticker=row.ticker,
            estimate_type=row.estimate_type,
            amount_unit=unit,
            amount=point,
            amount_min=low,
            amount_max=high,
            as_of=row.as_of,
            record_date=getattr(row, "record_date", None),
            ex_date=row.ex_date,
            payable_date=getattr(row, "payable_date", None),
            federal_rate_key=rate_key,
            federal_rate=_rate(federal),
            state_rate=_rate(state),
            applied_rate=None,
            distribution_dollars=None,
            distribution_dollars_min=None,
            distribution_dollars_max=None,
            estimated_tax=None,
            estimated_tax_min=None,
            estimated_tax_max=None,
            federal_tax=None,
            state_tax=None,
            included_in_totals=False,
            skip_reason=PERCENT_SKIP_REASON,
        )

    applied = federal + state if combine else federal
    dist = _distribution_dollars(unit=unit, amount=point, holding=holding, shares=shares)
    dist_min = _distribution_dollars(unit=unit, amount=low, holding=holding, shares=shares)
    dist_max = _distribution_dollars(unit=unit, amount=high, holding=holding, shares=shares)

    def tax_on(dollars: Decimal | None, rate: Decimal) -> Decimal | None:
        if dollars is None:
            return None
        return _money(dollars * rate)

    dist_m = _money(dist) if dist is not None else None
    dist_min_m = _money(dist_min) if dist_min is not None else None
    dist_max_m = _money(dist_max) if dist_max is not None else None
    federal_tax = tax_on(dist_m, federal)
    state_tax = tax_on(dist_m, state)
    estimated = tax_on(dist_m, applied if combine else (federal + state))
    estimated_min = tax_on(dist_min_m, applied if combine else (federal + state))
    estimated_max = tax_on(dist_max_m, applied if combine else (federal + state))

    return IllustrationComponent(
        distribution_id=row.id,
        fund_family=row.fund_family,
        fund_name=row.fund_name,
        fund_identifier=row.fund_identifier,
        ticker=row.ticker,
        estimate_type=row.estimate_type,
        amount_unit=unit,
        amount=point,
        amount_min=low,
        amount_max=high,
        as_of=row.as_of,
        record_date=getattr(row, "record_date", None),
        ex_date=row.ex_date,
        payable_date=getattr(row, "payable_date", None),
        federal_rate_key=rate_key,
        federal_rate=_rate(federal),
        state_rate=_rate(state),
        applied_rate=_rate(applied if combine else (federal + state)),
        distribution_dollars=dist_m,
        distribution_dollars_min=dist_min_m,
        distribution_dollars_max=dist_max_m,
        estimated_tax=estimated,
        estimated_tax_min=estimated_min,
        estimated_tax_max=estimated_max,
        federal_tax=federal_tax,
        state_tax=state_tax,
        included_in_totals=dist_m is not None,
        skip_reason=None if dist_m is not None else "No numeric amount on this estimate row.",
    )


def _totals(components: list[IllustrationComponent], holding: Decimal) -> IllustrationTotals:
    included = [c for c in components if c.included_in_totals and c.distribution_dollars is not None]
    dist = sum((c.distribution_dollars or Decimal("0") for c in included), Decimal("0"))
    tax = sum((c.estimated_tax or Decimal("0") for c in included), Decimal("0"))
    federal = sum((c.federal_tax or Decimal("0") for c in included), Decimal("0"))
    state = sum((c.state_tax or Decimal("0") for c in included), Decimal("0"))
    has_range = any(c.distribution_dollars_min is not None or c.distribution_dollars_max is not None for c in included)

    def range_sum(attr_min: str, attr_point: str) -> Decimal | None:
        if not has_range:
            return None
        total = Decimal("0")
        for component in included:
            value = getattr(component, attr_min)
            if value is None:
                value = getattr(component, attr_point)
            total += value or Decimal("0")
        return _money(total)

    dist_min = range_sum("distribution_dollars_min", "distribution_dollars")
    dist_max = range_sum("distribution_dollars_max", "distribution_dollars")
    tax_min = range_sum("estimated_tax_min", "estimated_tax")
    tax_max = range_sum("estimated_tax_max", "estimated_tax")
    effective = (tax / holding) if holding else Decimal("0")
    return IllustrationTotals(
        distribution_dollars=_money(dist),
        distribution_dollars_min=dist_min,
        distribution_dollars_max=dist_max,
        estimated_tax=_money(tax),
        estimated_tax_min=tax_min,
        estimated_tax_max=tax_max,
        federal_tax=_money(federal),
        state_tax=_money(state),
        effective_tax_on_holding=_rate(effective),
    )


def illustrate(
    session: Session,
    body: IllustrateRequest,
    *,
    as_of_year: int | None = None,
) -> IllustrateResponse:
    if body.distribution_ids:
        rows, missing = get_by_ids(session, body.distribution_ids)
        if missing:
            raise HTTPException(status_code=404, detail=f"Unknown distribution_ids: {missing}")
    else:
        assert body.selectors is not None
        rows = list_matching(
            session,
            fund_family=body.selectors.fund_family,
            fund_identifier=body.selectors.fund_identifier,
            ticker=body.selectors.ticker,
            fund_name=body.selectors.fund_name,
            estimate_type=body.selectors.estimate_type,
            as_of=body.selectors.as_of,
            publication_stage=body.selectors.publication_stage,
        )
        # Internal YoY vintage filter (HTTP illustrate/compare schemas unchanged).
        if as_of_year is not None and not body.selectors.as_of:
            rows = [row for row in rows if row.as_of is not None and row.as_of.year == as_of_year]
        if body.latest_as_of_only:
            rows = filter_latest_as_of(rows)
        if not rows:
            raise HTTPException(status_code=404, detail="No distribution estimates matched the selectors")

    extra = []
    if body.latest_as_of_only and not body.distribution_ids:
        extra.append("selectors used latest_as_of_only=true (newest as_of per fund). Pass as_of or IDs to pin a snapshot.")
    return illustrate_from_rows(
        rows,
        holding=body.holding_dollars,
        nav_per_share=body.nav_per_share,
        shares=body.shares,
        rates=body.tax_rates,
        combine=body.combine_state_with_federal,
        extra_notes=extra,
        require_nav_for_per_share=True,
    )


def _response(
    *,
    holding: Decimal,
    shares: Decimal | None,
    nav_per_share: Decimal | None,
    rates: TaxRates,
    combine: bool,
    components: list[IllustrationComponent],
    notes: list[str],
) -> IllustrateResponse:
    return IllustrateResponse(
        holding_dollars=_money(holding),
        shares=_money(shares) if shares is not None else None,
        nav_per_share=nav_per_share,
        tax_rates=rates,
        combine_state_with_federal=combine,
        rate_mapping=dict(RATE_MAPPING),
        components=components,
        totals=_totals(components, holding),
        notes=notes,
    )


def illustrate_from_rows(
    rows: list[DistributionEstimate],
    *,
    holding: Decimal,
    nav_per_share: Decimal | None,
    shares: Decimal | None,
    rates: TaxRates,
    combine: bool,
    extra_notes: list[str] | None = None,
    require_nav_for_per_share: bool = True,
) -> IllustrateResponse:
    needs_shares = any(row.amount_unit == AmountUnit.per_share.value for row in rows)
    resolved = shares
    if needs_shares and resolved is None and nav_per_share is not None:
        resolved = holding / nav_per_share
    if needs_shares and resolved is None and require_nav_for_per_share:
        raise NeedsNavOrShares()
    elif resolved is None and nav_per_share is not None:
        resolved = holding / nav_per_share

    components = [
        _illustrate_row(row, holding=holding, shares=resolved, rates=rates, combine=combine)
        for row in rows
    ]
    notes = list(ILLUSTRATION_NOTES)
    if extra_notes:
        notes.extend(extra_notes)
    return _response(
        holding=holding,
        shares=resolved,
        nav_per_share=nav_per_share,
        rates=rates,
        combine=combine,
        components=components,
        notes=notes,
    )


def _select_holding_rows(
    session: Session,
    holding: PortfolioHoldingIn,
    snapshot: IllustrationSnapshot,
) -> tuple[list, list[str], str | None]:
    warnings: list[str] = []
    stage_used: str | None = None
    if holding.distribution_ids:
        rows, missing = get_by_ids(session, holding.distribution_ids)
        if missing:
            warnings.append(f"Unknown distribution_ids: {missing}")
        if not rows:
            return [], warnings, None
        return rows, warnings, rows[0].publication_stage

    rows = list_matching(
        session,
        fund_family=holding.fund_family,
        fund_identifier=holding.fund_identifier,
        ticker=holding.ticker,
        fund_name=holding.fund_name,
    )
    if not rows and holding.ticker:
        alias = TICKER_LOOKUP_ALIASES.get(holding.ticker.upper())
        if alias:
            rows = list_matching(
                session,
                fund_family=holding.fund_family or alias.get("fund_family"),
                fund_identifier=holding.fund_identifier or alias.get("fund_identifier"),
                fund_name=holding.fund_name or alias.get("fund_name"),
            )
    if snapshot.as_of:
        rows = [row for row in rows if row.as_of == snapshot.as_of]
    elif snapshot.as_of_year is not None:
        rows = [
            row
            for row in rows
            if row.as_of is not None and row.as_of.year == snapshot.as_of_year
        ]

    if snapshot.prefer_publication_stages:
        chosen: list = []
        for stage in snapshot.prefer_publication_stages:
            staged = [row for row in rows if row.publication_stage == stage]
            if staged:
                chosen = staged
                stage_used = stage
                break
        if chosen:
            rows = chosen
        elif rows:
            warnings.append(
                "No rows matched prefer_publication_stages; using all matching snapshots."
            )

    if snapshot.latest_as_of_only and not snapshot.as_of:
        rows = filter_latest_as_of(rows)

    idents = {row.fund_identifier.lower() for row in rows}
    if len(idents) > 1:
        warnings.append(
            f"Ambiguous match: {sorted(idents)} fund_identifiers for "
            f"ticker={holding.ticker or holding.fund_identifier}."
        )
    return rows, warnings, stage_used


def _known_component_date(components: list[IllustrationComponent], attr: str) -> date | None:
    """Return a published calendar date from included rows; never invent one."""
    included = [component for component in components if component.included_in_totals]
    ordered = sorted(included, key=lambda component: component.as_of or date.min, reverse=True)
    for component in ordered:
        value = getattr(component, attr, None)
        if value is not None:
            return value
    return None


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _component_record_window_date(component: IllustrationComponent) -> date | None:
    """First published date that closes the sell-before-record window. Never invented."""
    return component.record_date or component.ex_date or component.payable_date


def _holding_still_upcoming(
    illustration: IllustrateResponse, stage_used: str | None
) -> bool:
    """True when the chosen illustration is announced and not yet past the record window.

    Advisors sell before record date to avoid the distribution tax, so upcoming
    requires today (UTC date) strictly before the window date. Prefer record_date,
    else ex_date, else payable_date. Dateless prelim/updated rows keep the
    publication_stage fallback; final/paid never qualify.
    """
    if stage_used in PAID_HISTORY_STAGES:
        return False
    today = _utc_today()
    window_dates = [
        event_date
        for component in illustration.components
        if component.included_in_totals
        and (event_date := _component_record_window_date(component)) is not None
    ]
    if window_dates:
        return all(today < event_date for event_date in window_dates)
    return stage_used in UPCOMING_ESTIMATE_STAGES


def _holding_upcoming(
    illustration: IllustrateResponse | None, stage_used: str | None
) -> PortfolioHoldingUpcoming | None:
    if illustration is None:
        return None
    dist = illustration.totals.distribution_dollars
    if dist is None or dist <= 0:
        return None
    if not _holding_still_upcoming(illustration, stage_used):
        return None
    as_ofs = [
        component.as_of
        for component in illustration.components
        if component.included_in_totals and component.as_of is not None
    ]
    return PortfolioHoldingUpcoming(
        distribution_dollars=_money(dist),
        estimated_tax=_money(illustration.totals.estimated_tax),
        as_of=max(as_ofs) if as_ofs else None,
        publication_stage=stage_used,
        record_date=_known_component_date(illustration.components, "record_date"),
        ex_date=_known_component_date(illustration.components, "ex_date"),
        payable_date=_known_component_date(illustration.components, "payable_date"),
    )


def illustrate_portfolio(session: Session, body: PortfolioIllustrateRequest) -> PortfolioIllustrateResponse:
    holding_outs: list[PortfolioHoldingOut] = []
    gaps: list[PortfolioHoldingGap] = []
    portfolio_warnings: list[str] = []
    covered_components: list[IllustrationComponent] = []
    dollars_covered = Decimal("0")
    dollars_uncovered = Decimal("0")
    covered_n = 0
    uncovered_n = 0

    for index, holding in enumerate(body.holdings):
        dollars = holding.holding_dollars
        if dollars is None:
            raise HTTPException(
                status_code=422,
                detail=f"holdings[{index}] needs holding_dollars or weight_pct with book_dollars",
            )
        rows, warnings, stage_used = _select_holding_rows(session, holding, body.snapshot)
        if not rows:
            reason = "No matching distribution estimates for this holding."
            dollars_uncovered += dollars
            uncovered_n += 1
            gaps.append(
                PortfolioHoldingGap(
                    holding_index=index,
                    ticker=holding.ticker,
                    fund_identifier=holding.fund_identifier,
                    fund_family=holding.fund_family,
                    fund_name=holding.fund_name,
                    holding_dollars=_money(dollars),
                    reason=reason,
                )
            )
            holding_outs.append(
                PortfolioHoldingOut(
                    holding_index=index,
                    ticker=holding.ticker,
                    fund_identifier=holding.fund_identifier,
                    fund_family=holding.fund_family,
                    fund_name=holding.fund_name,
                    holding_dollars=_money(dollars),
                    covered=False,
                    warnings=warnings,
                    gap_reason=reason,
                )
            )
            continue

        illustration = illustrate_from_rows(
            rows,
            holding=dollars,
            nav_per_share=holding.nav_per_share,
            shares=holding.shares,
            rates=body.tax_rates,
            combine=body.combine_state_with_federal,
            extra_notes=[],
            require_nav_for_per_share=False,
        )
        if any(c.skip_reason and "nav_per_share" in (c.skip_reason or "") for c in illustration.components):
            warnings.append(
                "per_share rows skipped (nav_per_share or shares missing). "
                "Dollar totals exclude those components — not a silent understatement."
            )
        covered_components.extend(illustration.components)
        dollars_covered += dollars
        covered_n += 1
        ident = holding.fund_identifier or (rows[0].fund_identifier if rows else None)
        family = holding.fund_family or (rows[0].fund_family if rows else None)
        holding_outs.append(
            PortfolioHoldingOut(
                holding_index=index,
                ticker=holding.ticker or rows[0].ticker,
                fund_identifier=ident,
                fund_family=family,
                fund_name=holding.fund_name or rows[0].fund_name,
                holding_dollars=_money(dollars),
                covered=True,
                publication_stage_used=stage_used,
                upcoming=_holding_upcoming(illustration, stage_used),
                warnings=warnings,
                illustration=illustration,
            )
        )
        portfolio_warnings.extend(f"holding[{index}]: {w}" for w in warnings)

    dollars_total = dollars_covered + dollars_uncovered
    coverage_pct = (dollars_covered / dollars_total * Decimal("100")) if dollars_total else Decimal("0")
    notes = list(ILLUSTRATION_NOTES)
    notes.append(
        "Portfolio coverage is by holding dollars with at least one matched estimate. "
        "Unmatched holdings are listed in gaps and excluded from tax totals."
    )
    if body.snapshot.prefer_publication_stages:
        notes.append(
            "Snapshot prefers publication_stage in order: "
            + ", ".join(body.snapshot.prefer_publication_stages)
        )

    return PortfolioIllustrateResponse(
        holdings=holding_outs,
        totals=_totals(covered_components, dollars_covered if dollars_covered else Decimal("0")),
        coverage=PortfolioCoverage(
            dollars_total=_money(dollars_total),
            dollars_covered=_money(dollars_covered),
            dollars_uncovered=_money(dollars_uncovered),
            coverage_pct=_rate(coverage_pct),
            holdings_covered=covered_n,
            holdings_uncovered=uncovered_n,
        ),
        gaps=gaps,
        warnings=portfolio_warnings,
        tax_rates=body.tax_rates,
        combine_state_with_federal=body.combine_state_with_federal,
        rate_mapping=dict(RATE_MAPPING),
        notes=notes,
    )


PORTFOLIO_COMPARE_NOTES = [
    "Deltas are proposed − current. Interactive Modules charts Current vs Proposed Allocation (center-zero bars).",
    "Each side is a full POST /illustrate/portfolio result, including per-holding upcoming. Gaps and warnings stay on that side — never dropped.",
    "Omit periods[] for one shared snapshot. When periods[] is present, each year is a Proposed − Current pair; top-level current/proposed/deltas copy the latest period.",
    "summary dollar fields are scaled linearly to $10,000, same as POST /illustrate/compare.",
]


def _delta_optional(proposed: Decimal | None, current: Decimal | None) -> Decimal | None:
    if proposed is None and current is None:
        return None
    return _money((proposed or Decimal("0")) - (current or Decimal("0")))


def _scale_to_book(value: Decimal, book: Decimal, common: Decimal) -> Decimal:
    if book <= 0:
        return Decimal("0")
    return value * (common / book)


def _portfolio_pair_deltas(
    current: PortfolioIllustrateResponse, proposed: PortfolioIllustrateResponse
) -> PortfolioCompareDeltas:
    return PortfolioCompareDeltas(
        estimated_tax=_money(
            (proposed.totals.estimated_tax or Decimal("0"))
            - (current.totals.estimated_tax or Decimal("0"))
        ),
        distribution_dollars=_money(
            (proposed.totals.distribution_dollars or Decimal("0"))
            - (current.totals.distribution_dollars or Decimal("0"))
        ),
        effective_tax_on_holding=_rate(
            (proposed.totals.effective_tax_on_holding or Decimal("0"))
            - (current.totals.effective_tax_on_holding or Decimal("0"))
        ),
        coverage_pct=_rate(proposed.coverage.coverage_pct - current.coverage.coverage_pct),
        estimated_tax_min=_delta_optional(proposed.totals.estimated_tax_min, current.totals.estimated_tax_min),
        estimated_tax_max=_delta_optional(proposed.totals.estimated_tax_max, current.totals.estimated_tax_max),
        distribution_dollars_min=_delta_optional(
            proposed.totals.distribution_dollars_min, current.totals.distribution_dollars_min
        ),
        distribution_dollars_max=_delta_optional(
            proposed.totals.distribution_dollars_max, current.totals.distribution_dollars_max
        ),
    )


def _run_allocation_pair(
    session: Session,
    body: PortfolioCompareRequest,
    snapshot: IllustrationSnapshot,
) -> tuple[PortfolioCompareAllocationOut, PortfolioCompareAllocationOut, PortfolioCompareDeltas]:
    current = illustrate_portfolio(
        session,
        PortfolioIllustrateRequest(
            holdings=body.current.holdings,
            tax_rates=body.tax_rates,
            combine_state_with_federal=body.combine_state_with_federal,
            snapshot=snapshot,
        ),
    )
    proposed = illustrate_portfolio(
        session,
        PortfolioIllustrateRequest(
            holdings=body.proposed.holdings,
            tax_rates=body.tax_rates,
            combine_state_with_federal=body.combine_state_with_federal,
            snapshot=snapshot,
        ),
    )
    current_out = PortfolioCompareAllocationOut(
        label=body.current.label or "Current Allocation",
        **current.model_dump(),
    )
    proposed_out = PortfolioCompareAllocationOut(
        label=body.proposed.label or "Proposed Allocation",
        **proposed.model_dump(),
    )
    return current_out, proposed_out, _portfolio_pair_deltas(current, proposed)


def _period_snapshot(base: IllustrationSnapshot, period: ComparePeriodIn) -> IllustrationSnapshot:
    if period.as_of is not None:
        return base.model_copy(update={"as_of": period.as_of, "as_of_year": None, "latest_as_of_only": False})
    return base.model_copy(update={"as_of": None, "as_of_year": period.year, "latest_as_of_only": True})


def _book_for_scale(current: PortfolioCompareAllocationOut, proposed: PortfolioCompareAllocationOut) -> Decimal:
    return proposed.coverage.dollars_total or current.coverage.dollars_total or SUMMARY_HOLDING


def _gap_notes(current: PortfolioCompareAllocationOut, proposed: PortfolioCompareAllocationOut) -> list[str]:
    notes: list[str] = []
    if current.gaps or proposed.gaps:
        notes.append(
            f"Uncovered holdings: current={len(current.gaps)}, proposed={len(proposed.gaps)}. "
            "See current.gaps and proposed.gaps — never dropped silently."
        )
    notes.extend(f"current: {warning}" for warning in current.warnings)
    notes.extend(f"proposed: {warning}" for warning in proposed.warnings)
    return notes


def _portfolio_compare_summary(
    *,
    current: PortfolioCompareAllocationOut,
    proposed: PortfolioCompareAllocationOut,
    deltas: PortfolioCompareDeltas,
    period_outs: list[PortfolioComparePeriodOut],
) -> PortfolioCompareSummary:
    current_book = current.coverage.dollars_total
    proposed_book = proposed.coverage.dollars_total
    common = SUMMARY_HOLDING
    latest_tax = _money(
        _scale_to_book(proposed.totals.estimated_tax or Decimal("0"), proposed_book, common)
        - _scale_to_book(current.totals.estimated_tax or Decimal("0"), current_book, common)
    )
    latest_dist = _money(
        _scale_to_book(proposed.totals.distribution_dollars or Decimal("0"), proposed_book, common)
        - _scale_to_book(current.totals.distribution_dollars or Decimal("0"), current_book, common)
    )
    if period_outs:
        tax_sum = Decimal("0")
        dist_sum = Decimal("0")
        drag_sum = Decimal("0")
        for period in period_outs:
            book = _book_for_scale(period.current, period.proposed)
            tax_sum += _scale_to_book(period.deltas.estimated_tax, book, common)
            dist_sum += _scale_to_book(period.deltas.distribution_dollars, book, common)
            drag_sum += period.deltas.effective_tax_on_holding
        count = len(period_outs)
        first, last = period_outs[0], period_outs[-1]
        inception = CompareCommonInception(
            from_year=first.year,
            to_year=last.year,
            from_as_of=first.as_of,
            to_as_of=last.as_of,
        )
        return PortfolioCompareSummary(
            normalized_book_dollars=common,
            estimated_tax=latest_tax,
            distribution_dollars=latest_dist,
            effective_tax_on_holding=deltas.effective_tax_on_holding,
            coverage_pct=deltas.coverage_pct,
            total_tax_difference=_money(tax_sum),
            annualized_tax_drag_delta=_rate(drag_sum / Decimal(count)),
            distribution_dollars_difference=_money(dist_sum),
            periods_compared=count,
            common_inception=inception,
        )
    return PortfolioCompareSummary(
        normalized_book_dollars=common,
        estimated_tax=latest_tax,
        distribution_dollars=latest_dist,
        effective_tax_on_holding=deltas.effective_tax_on_holding,
        coverage_pct=deltas.coverage_pct,
        total_tax_difference=latest_tax,
        annualized_tax_drag_delta=deltas.effective_tax_on_holding,
        distribution_dollars_difference=latest_dist,
        periods_compared=0,
    )


def illustrate_portfolio_compare(
    session: Session, body: PortfolioCompareRequest
) -> PortfolioCompareResponse:
    notes = list(PORTFOLIO_COMPARE_NOTES)
    period_outs: list[PortfolioComparePeriodOut] = []
    if body.periods:
        for period in body.periods:
            snapshot = _period_snapshot(body.snapshot, period)
            current_out, proposed_out, deltas = _run_allocation_pair(session, body, snapshot)
            period_outs.append(
                PortfolioComparePeriodOut(
                    year=period.year,
                    as_of=period.as_of,
                    current=current_out,
                    proposed=proposed_out,
                    deltas=deltas,
                )
            )
            notes.extend(_gap_notes(current_out, proposed_out))
        latest = period_outs[-1]
        current_out, proposed_out, deltas = latest.current, latest.proposed, latest.deltas
        notes.append(
            f"periods[] YoY: {len(period_outs)} year(s). "
            "Top-level current / proposed / deltas are the latest period."
        )
    else:
        current_out, proposed_out, deltas = _run_allocation_pair(session, body, body.snapshot)
        notes.extend(_gap_notes(current_out, proposed_out))
        if current_out.coverage.dollars_total != proposed_out.coverage.dollars_total:
            notes.append(
                f"Books differ (${current_out.coverage.dollars_total} vs "
                f"${proposed_out.coverage.dollars_total}); "
                f"summary dollar deltas are scaled to ${SUMMARY_HOLDING}."
            )
    summary = _portfolio_compare_summary(
        current=current_out,
        proposed=proposed_out,
        deltas=deltas,
        period_outs=period_outs,
    )
    return PortfolioCompareResponse(
        current=current_out,
        proposed=proposed_out,
        deltas=deltas,
        periods=period_outs,
        summary=summary,
        notes=notes,
    )


COMPARE_NOTES = [
    "Deltas are right − left (B − A). Interactive Modules charts deltas.effective_tax_on_holding.",
    "A missing side returns matched=false with null tax/distribution totals (N/A), not $0, plus a note; the compare itself is not 404.",
    "Published $0 / 0% of NAV stays 0.00 with matched=true.",
    "summary dollar fields are scaled linearly to $10,000 (value × 10000 / holding_dollars).",
]


def _unmatched_totals() -> IllustrationTotals:
    """N/A totals: no row / can't price. Do not invent $0."""
    return IllustrationTotals(
        distribution_dollars=None,
        distribution_dollars_min=None,
        distribution_dollars_max=None,
        estimated_tax=None,
        estimated_tax_min=None,
        estimated_tax_max=None,
        federal_tax=None,
        state_tax=None,
        effective_tax_on_holding=None,
    )


def _empty_illustration(body: IllustrateRequest, *, reason: str) -> IllustrateResponse:
    return IllustrateResponse(
        holding_dollars=_money(body.holding_dollars),
        shares=_money(body.shares) if body.shares is not None else None,
        nav_per_share=body.nav_per_share,
        tax_rates=body.tax_rates,
        combine_state_with_federal=body.combine_state_with_federal,
        rate_mapping=dict(RATE_MAPPING),
        components=[],
        totals=_unmatched_totals(),
        notes=[reason],
    )


def _try_illustrate(
    session: Session,
    request: IllustrateRequest,
    *,
    as_of_year: int | None = None,
) -> tuple[IllustrateResponse, bool, str | None]:
    try:
        return illustrate(session, request, as_of_year=as_of_year), True, None
    except NeedsNavOrShares:
        raise
    except HTTPException as exc:
        if exc.status_code in {404, 422}:
            detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
            return _empty_illustration(request, reason=detail), False, detail
        raise


def _pin_selectors(selectors: IllustrateSelectors | None, as_of: date | None) -> IllustrateSelectors | None:
    if as_of is None:
        return selectors
    if selectors is None:
        return IllustrateSelectors(as_of=as_of)
    return selectors.model_copy(update={"as_of": as_of})


def _side_request(
    body: CompareRequest,
    side: CompareSideIn | None,
    *,
    selectors: IllustrateSelectors | None,
    as_of: date | None,
    pin_as_of: bool,
) -> IllustrateRequest | None:
    pinned = _pin_selectors(selectors, as_of) if pin_as_of else selectors
    ids = side.distribution_ids if side else None
    if not ids and not (pinned and pinned.has_any()):
        return None
    holding = side.holding_dollars if side and side.holding_dollars is not None else body.holding_dollars
    return IllustrateRequest(
        holding_dollars=holding,
        distribution_ids=ids if ids else None,
        selectors=None if ids else pinned,
        nav_per_share=(side.nav_per_share if side and side.nav_per_share is not None else body.nav_per_share),
        shares=side.shares if side and side.shares is not None else body.shares,
        tax_rates=body.tax_rates,
        combine_state_with_federal=body.combine_state_with_federal,
        latest_as_of_only=False if pin_as_of and as_of is not None else body.latest_as_of_only,
    )


def _label_for(
    side: CompareSideIn | None,
    illustration: IllustrateResponse,
    fallback: str,
) -> str:
    if side and side.label:
        return side.label
    if illustration.components:
        component = illustration.components[0]
        return component.ticker or component.fund_identifier or component.fund_name or fallback
    return fallback


def _compare_illustration(
    illustration: IllustrateResponse,
    *,
    label: str,
    matched: bool,
) -> CompareIllustration:
    return CompareIllustration.model_validate({**illustration.model_dump(), "label": label, "matched": matched})


def _delta_value(right: Decimal | None, left: Decimal | None, *, money: bool) -> Decimal:
    value = (right or Decimal("0")) - (left or Decimal("0"))
    return _money(value) if money else _rate(value)


def _range_delta(
    right_bound: Decimal | None,
    right_point: Decimal | None,
    left_bound: Decimal | None,
    left_point: Decimal | None,
    *,
    money: bool,
) -> Decimal | None:
    if right_point is None or left_point is None:
        return None
    if right_bound is None and left_bound is None:
        return None
    right = right_bound if right_bound is not None else right_point
    left = left_bound if left_bound is not None else left_point
    return _delta_value(right, left, money=money)


def _unmatched_deltas() -> CompareDeltas:
    return CompareDeltas(
        distribution_dollars=None,
        distribution_dollars_min=None,
        distribution_dollars_max=None,
        estimated_tax=None,
        estimated_tax_min=None,
        estimated_tax_max=None,
        federal_tax=None,
        state_tax=None,
        effective_tax_on_holding=None,
        effective_tax_on_holding_min=None,
        effective_tax_on_holding_max=None,
    )


def _effective_from_tax(tax: Decimal | None, holding: Decimal) -> Decimal | None:
    if tax is None or not holding:
        return None
    return _rate(tax / holding)


def compare_deltas(right: IllustrationTotals, left: IllustrationTotals, holding: Decimal) -> CompareDeltas:
    if (
        right.estimated_tax is None
        or left.estimated_tax is None
        or right.distribution_dollars is None
        or left.distribution_dollars is None
        or right.federal_tax is None
        or left.federal_tax is None
        or right.state_tax is None
        or left.state_tax is None
        or right.effective_tax_on_holding is None
        or left.effective_tax_on_holding is None
    ):
        return _unmatched_deltas()
    return CompareDeltas(
        distribution_dollars=_delta_value(right.distribution_dollars, left.distribution_dollars, money=True),
        distribution_dollars_min=_range_delta(
            right.distribution_dollars_min,
            right.distribution_dollars,
            left.distribution_dollars_min,
            left.distribution_dollars,
            money=True,
        ),
        distribution_dollars_max=_range_delta(
            right.distribution_dollars_max,
            right.distribution_dollars,
            left.distribution_dollars_max,
            left.distribution_dollars,
            money=True,
        ),
        estimated_tax=_delta_value(right.estimated_tax, left.estimated_tax, money=True),
        estimated_tax_min=_range_delta(
            right.estimated_tax_min,
            right.estimated_tax,
            left.estimated_tax_min,
            left.estimated_tax,
            money=True,
        ),
        estimated_tax_max=_range_delta(
            right.estimated_tax_max,
            right.estimated_tax,
            left.estimated_tax_max,
            left.estimated_tax,
            money=True,
        ),
        federal_tax=_delta_value(right.federal_tax, left.federal_tax, money=True),
        state_tax=_delta_value(right.state_tax, left.state_tax, money=True),
        effective_tax_on_holding=_delta_value(
            right.effective_tax_on_holding, left.effective_tax_on_holding, money=False
        ),
        effective_tax_on_holding_min=_range_delta(
            _effective_from_tax(right.estimated_tax_min, holding),
            right.effective_tax_on_holding,
            _effective_from_tax(left.estimated_tax_min, holding),
            left.effective_tax_on_holding,
            money=False,
        ),
        effective_tax_on_holding_max=_range_delta(
            _effective_from_tax(right.estimated_tax_max, holding),
            right.effective_tax_on_holding,
            _effective_from_tax(left.estimated_tax_max, holding),
            left.effective_tax_on_holding,
            money=False,
        ),
    )


def _run_side(
    session: Session,
    body: CompareRequest,
    side: CompareSideIn | None,
    *,
    selectors: IllustrateSelectors | None,
    as_of: date | None,
    pin_as_of: bool,
    fallback_label: str,
    as_of_year: int | None = None,
) -> tuple[CompareIllustration, str | None]:
    request = _side_request(body, side, selectors=selectors, as_of=as_of, pin_as_of=pin_as_of)
    if request is None:
        placeholder = IllustrateRequest(
            holding_dollars=body.holding_dollars,
            selectors=IllustrateSelectors(fund_identifier="__unmatched__"),
            tax_rates=body.tax_rates,
            combine_state_with_federal=body.combine_state_with_federal,
            nav_per_share=body.nav_per_share,
            shares=body.shares,
        )
        illustration = _empty_illustration(
            placeholder, reason="No selectors or distribution_ids for this side."
        )
        error = "No selectors or distribution_ids for this side."
        matched = False
    else:
        illustration, matched, error = _try_illustrate(session, request, as_of_year=as_of_year)
    label = _label_for(side, illustration, fallback_label)
    return _compare_illustration(illustration, label=label, matched=matched), error


def _append_side_note(notes: list[str], illustration: CompareIllustration, error: str | None, stamp: str) -> None:
    if error:
        notes.append(f"{illustration.label} ({stamp}): {error}")


def _period_out(
    *,
    year: int,
    as_of: date | None,
    left: CompareIllustration,
    right: CompareIllustration,
    holding: Decimal,
) -> ComparePeriodOut:
    return ComparePeriodOut(
        year=year,
        as_of=as_of,
        left=left,
        right=right,
        deltas=compare_deltas(right.totals, left.totals, holding),
    )


def _yoy_shared_selectors(body: CompareRequest) -> IllustrateSelectors | None:
    if body.selectors and body.selectors.has_any():
        return body.selectors
    if body.left and body.left.selectors and body.left.selectors.has_any():
        return body.left.selectors
    if body.right and body.right.selectors and body.right.selectors.has_any():
        return body.right.selectors
    return None


def _scale_to_summary(value: Decimal, holding: Decimal) -> Decimal:
    if not holding:
        return Decimal("0.00")
    return _money(value * (SUMMARY_HOLDING / holding))


def _unbound_selectors(selectors: IllustrateSelectors | None) -> IllustrateSelectors | None:
    if selectors is None or not selectors.has_any():
        return None
    return selectors.model_copy(update={"as_of": None, "publication_stage": None})


def _upcoming_side(
    session: Session,
    body: CompareRequest,
    side: CompareSideIn | None,
    selectors: IllustrateSelectors | None,
) -> tuple[Decimal | None, date | None, str | None]:
    unbound = _unbound_selectors(selectors)
    if unbound is None:
        return None, None, None
    rows = list_matching(
        session,
        fund_family=unbound.fund_family,
        fund_identifier=unbound.fund_identifier,
        ticker=unbound.ticker,
        fund_name=unbound.fund_name,
        estimate_type=unbound.estimate_type,
    )
    year = date.today().year
    current = [row for row in rows if row.as_of is not None and row.as_of.year == year]
    estimates = [row for row in current if row.publication_stage in UPCOMING_ESTIMATE_STAGES]
    finals = [row for row in current if row.publication_stage == PublicationStage.final.value]
    pool = estimates or finals
    if not pool:
        return None, None, None
    latest = max(row.as_of for row in pool if row.as_of is not None)
    chosen = [row for row in pool if row.as_of == latest]
    if estimates and any(row.publication_stage == PublicationStage.updated_estimate.value for row in chosen):
        chosen = [row for row in chosen if row.publication_stage == PublicationStage.updated_estimate.value]
        stage_used = PublicationStage.updated_estimate.value
    else:
        stage_used = chosen[0].publication_stage
    illustration = illustrate_from_rows(
        chosen,
        holding=body.holding_dollars,
        nav_per_share=(side.nav_per_share if side and side.nav_per_share is not None else body.nav_per_share),
        shares=side.shares if side and side.shares is not None else body.shares,
        rates=body.tax_rates,
        combine=body.combine_state_with_federal,
        extra_notes=[],
        require_nav_for_per_share=False,
    )
    return (
        _scale_to_summary(illustration.totals.distribution_dollars, body.holding_dollars),
        latest,
        stage_used,
    )


def _upcoming_distribution(
    session: Session,
    body: CompareRequest,
    notes: list[str],
) -> CompareUpcomingDistribution | None:
    left_sel = (body.left.selectors if body.left else None) or body.selectors
    right_sel = (body.right.selectors if body.right else None) or body.selectors or left_sel
    left_dollars, left_as_of, left_stage = _upcoming_side(session, body, body.left, left_sel)
    right_dollars, right_as_of, right_stage = _upcoming_side(session, body, body.right, right_sel)
    if left_dollars is None and right_dollars is None:
        notes.append(
            f"upcoming_taxable_distribution is null: no {date.today().year} "
            "preliminary/updated estimate (or final fallback) on either side."
        )
        return None
    left_amt = left_dollars or Decimal("0.00")
    right_amt = right_dollars or Decimal("0.00")
    return CompareUpcomingDistribution(
        left_dollars=left_dollars,
        right_dollars=right_dollars,
        delta_dollars=_money(right_amt - left_amt),
        left_as_of=left_as_of,
        right_as_of=right_as_of,
        left_publication_stage=left_stage,
        right_publication_stage=right_stage,
    )


def _common_inception(body: CompareRequest, period_outs: list[ComparePeriodOut]) -> CompareCommonInception:
    if body.periods:
        first, last = body.periods[0], body.periods[-1]
        return CompareCommonInception(
            from_year=first.year,
            to_year=last.year,
            from_as_of=first.as_of,
            to_as_of=last.as_of,
        )
    left_as_of = body.left.selectors.as_of if body.left and body.left.selectors else None
    right_as_of = body.right.selectors.as_of if body.right and body.right.selectors else None
    first_as_of = period_outs[0].as_of if period_outs else None
    last_as_of = period_outs[-1].as_of if period_outs else None
    start = left_as_of or first_as_of
    end = right_as_of or last_as_of
    return CompareCommonInception(
        from_year=start.year if start else (period_outs[0].year if period_outs else None),
        to_year=end.year if end else (period_outs[-1].year if period_outs else None),
        from_as_of=start,
        to_as_of=end,
    )


def build_compare_summary(
    session: Session,
    body: CompareRequest,
    period_outs: list[ComparePeriodOut],
    notes: list[str],
) -> CompareSummary:
    count = len(period_outs)
    tax_delta = sum((period.deltas.estimated_tax or Decimal("0") for period in period_outs), Decimal("0"))
    dist_delta = sum((period.deltas.distribution_dollars or Decimal("0") for period in period_outs), Decimal("0"))
    if count:
        drag = sum(
            (period.deltas.effective_tax_on_holding or Decimal("0") for period in period_outs),
            Decimal("0"),
        ) / Decimal(count)
    else:
        drag = Decimal("0")
    return CompareSummary(
        normalized_holding_dollars=SUMMARY_HOLDING,
        total_tax_difference=_scale_to_summary(tax_delta, body.holding_dollars),
        annualized_tax_drag_delta=_rate(drag),
        distribution_dollars_difference=_scale_to_summary(dist_delta, body.holding_dollars),
        periods_compared=count,
        common_inception=_common_inception(body, period_outs),
        upcoming_taxable_distribution=_upcoming_distribution(session, body, notes),
    )


def _compare_response(
    session: Session,
    body: CompareRequest,
    period_outs: list[ComparePeriodOut],
    notes: list[str],
) -> CompareResponse:
    summary = build_compare_summary(session, body, period_outs, notes)
    pair = period_outs[-1] if period_outs else None
    return CompareResponse(
        mode=body.mode or "yoy",
        left=pair.left if pair else None,
        right=pair.right if pair else None,
        deltas=pair.deltas if pair else None,
        periods=period_outs,
        summary=summary,
        notes=notes,
    )


def _calendar_years_for_selectors(
    session: Session, selectors: IllustrateSelectors | None
) -> list[int]:
    """Unique calendar years on matching rows (as_of, else ex_date)."""
    unbound = _unbound_selectors(selectors)
    if unbound is None:
        return []
    rows = list_matching(
        session,
        fund_family=unbound.fund_family,
        fund_identifier=unbound.fund_identifier,
        ticker=unbound.ticker,
        fund_name=unbound.fund_name,
        estimate_type=unbound.estimate_type,
        limit=2000,
    )
    years: set[int] = set()
    for row in rows:
        stamp = row.as_of or row.ex_date
        if stamp is not None:
            years.add(stamp.year)
    return sorted(years)


def _yoy_years_from_book(session: Session, body: CompareRequest) -> list[int]:
    """Calendar years to expand when the client omitted periods[].

    Same-fund (or overlapping history) uses the intersection so pair bars
    share a real vintage. If the sides never overlap, fall back to the union
    so a thin side still surfaces unmatched years instead of year=0.
    """
    left_sel = (body.left.selectors if body.left else None) or body.selectors
    right_sel = (body.right.selectors if body.right else None) or body.selectors
    left_years = _calendar_years_for_selectors(session, left_sel)
    right_years = _calendar_years_for_selectors(session, right_sel)
    if left_years and right_years:
        common = sorted(set(left_years) & set(right_years))
        if common:
            return common
        return sorted(set(left_years) | set(right_years))
    return left_years or right_years


def _expand_yoy_periods_from_book(session: Session, body: CompareRequest) -> CompareRequest:
    """YoY with no periods[] and no as_of pins → expand vintages from the book.

    Website / Interactive Modules send mode=yoy + left/right tickers and expect
    real calendar years. The previous fallback emitted a single period with
    year=0, which then latest_as_of_only'd both sides onto the newest snapshot.
    Explicit periods[] and left/right as_of pins are left unchanged.
    """
    if body.mode != "yoy" or body.periods:
        return body
    left_as_of = body.left.selectors.as_of if body.left and body.left.selectors else None
    right_as_of = body.right.selectors.as_of if body.right and body.right.selectors else None
    if left_as_of or right_as_of:
        return body
    years = _yoy_years_from_book(session, body)
    if not years:
        return body
    return body.model_copy(update={"periods": [ComparePeriodIn(year=year) for year in years]})


def illustrate_compare(session: Session, body: CompareRequest) -> CompareResponse:
    notes = list(COMPARE_NOTES)
    notes.append(ILLUSTRATION_NOTES[0])
    period_outs: list[ComparePeriodOut] = []
    body = _expand_yoy_periods_from_book(session, body)

    if body.mode == "yoy" and body.periods and len(body.periods) >= 2:
        shared = _yoy_shared_selectors(body)
        for older, newer in zip(body.periods, body.periods[1:]):
            left_sel = shared or (body.left.selectors if body.left else None)
            right_sel = shared or (body.right.selectors if body.right else None) or left_sel
            left_ill, left_err = _run_side(
                session,
                body,
                body.left,
                selectors=left_sel,
                as_of=older.as_of,
                pin_as_of=True,
                fallback_label=str(older.year),
                as_of_year=None if older.as_of is not None else older.year,
            )
            right_ill, right_err = _run_side(
                session,
                body,
                body.right,
                selectors=right_sel,
                as_of=newer.as_of,
                pin_as_of=True,
                fallback_label=str(newer.year),
                as_of_year=None if newer.as_of is not None else newer.year,
            )
            if not (body.left and body.left.label):
                left_ill = left_ill.model_copy(update={"label": str(older.year)})
            if not (body.right and body.right.label):
                right_ill = right_ill.model_copy(update={"label": str(newer.year)})
            _append_side_note(notes, left_ill, left_err, str(older.year))
            _append_side_note(notes, right_ill, right_err, str(newer.year))
            period_outs.append(
                _period_out(
                    year=newer.year,
                    as_of=newer.as_of,
                    left=left_ill,
                    right=right_ill,
                    holding=body.holding_dollars,
                )
            )
        return _compare_response(session, body, period_outs, notes)

    jobs: list[tuple[int, date | None, bool]] = []
    if body.periods:
        jobs.extend((period.year, period.as_of, True) for period in body.periods)
    else:
        left_as_of = body.left.selectors.as_of if body.left and body.left.selectors else None
        right_as_of = body.right.selectors.as_of if body.right and body.right.selectors else None
        stamp = right_as_of or left_as_of
        if stamp:
            jobs.append((stamp.year, None, False))
        else:
            years = _yoy_years_from_book(session, body)
            jobs.append((years[-1] if years else date.today().year, None, False))

    for year, as_of, pin in jobs:
        year_filter = year if pin and as_of is None and year else None
        left_ill, left_err = _run_side(
            session,
            body,
            body.left,
            selectors=body.left.selectors if body.left else body.selectors,
            as_of=as_of,
            pin_as_of=pin,
            fallback_label="left",
            as_of_year=year_filter,
        )
        right_ill, right_err = _run_side(
            session,
            body,
            body.right,
            selectors=body.right.selectors if body.right else body.selectors,
            as_of=as_of,
            pin_as_of=pin,
            fallback_label="right",
            as_of_year=year_filter,
        )
        _append_side_note(notes, left_ill, left_err, str(year or as_of))
        _append_side_note(notes, right_ill, right_err, str(year or as_of))
        period_outs.append(
            _period_out(
                year=year,
                as_of=as_of,
                left=left_ill,
                right=right_ill,
                holding=body.holding_dollars,
            )
        )
    return _compare_response(session, body, period_outs, notes)
