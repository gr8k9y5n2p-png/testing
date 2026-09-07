from __future__ import annotations

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import get_by_ids, list_matching
from app.models import AmountUnit, DistributionEstimate, EstimateType
from app.schemas import (
    IllustrationComponent,
    IllustrationTotals,
    IllustrateRequest,
    IllustrateResponse,
    TaxRates,
)

CENTS = Decimal("0.01")
RATE_PLACES = Decimal("0.000001")

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
        assert shares is not None
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
            ex_date=row.ex_date,
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
        ex_date=row.ex_date,
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


def illustrate(session: Session, body: IllustrateRequest) -> IllustrateResponse:
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
        if body.latest_as_of_only:
            rows = filter_latest_as_of(rows)
        if not rows:
            raise HTTPException(status_code=404, detail="No distribution estimates matched the selectors")

    needs_shares = any(row.amount_unit == AmountUnit.per_share.value for row in rows)
    shares = body.shares
    if needs_shares and shares is None:
        if body.nav_per_share is None:
            raise HTTPException(
                status_code=422,
                detail="nav_per_share or shares is required when illustrating per_share distributions",
                headers={"X-Error-Code": "nav_required"},
            )
        shares = body.holding_dollars / body.nav_per_share
    elif shares is None and body.nav_per_share is not None:
        shares = body.holding_dollars / body.nav_per_share

    components = [
        _illustrate_row(
            row,
            holding=body.holding_dollars,
            shares=shares,
            rates=body.tax_rates,
            combine=body.combine_state_with_federal,
        )
        for row in rows
    ]
    notes = list(ILLUSTRATION_NOTES)
    if body.latest_as_of_only and not body.distribution_ids:
        notes.append("selectors used latest_as_of_only=true (newest as_of per fund). Pass as_of or IDs to pin a snapshot.")

    return IllustrateResponse(
        holding_dollars=_money(body.holding_dollars),
        shares=_money(shares) if shares is not None else None,
        nav_per_share=body.nav_per_share,
        tax_rates=body.tax_rates,
        combine_state_with_federal=body.combine_state_with_federal,
        rate_mapping=dict(RATE_MAPPING),
        components=components,
        totals=_totals(components, body.holding_dollars),
        notes=notes,
    )
