from __future__ import annotations

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.crud import get_by_ids, list_matching
from app.models import AmountUnit, DistributionEstimate, EstimateType
from app.schemas import (
    IllustrationComponent,
    IllustrationSnapshot,
    IllustrationTotals,
    IllustrateRequest,
    IllustrateResponse,
    PortfolioCoverage,
    PortfolioHoldingGap,
    PortfolioHoldingIn,
    PortfolioHoldingOut,
    PortfolioIllustrateRequest,
    PortfolioIllustrateResponse,
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
            skip_reason="nav_per_share or shares is required when illustrating per_share distributions",
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
        raise HTTPException(
            status_code=422,
            detail="nav_per_share or shares is required when illustrating per_share distributions",
            headers={"X-Error-Code": "nav_required"},
        )
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
    if snapshot.as_of:
        rows = [row for row in rows if row.as_of == snapshot.as_of]

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
        rows, warnings, stage_used = _select_holding_rows(session, holding, body.snapshot)
        if not rows:
            reason = "No matching distribution estimates for this holding."
            dollars_uncovered += holding.holding_dollars
            uncovered_n += 1
            gaps.append(
                PortfolioHoldingGap(
                    holding_index=index,
                    ticker=holding.ticker,
                    fund_identifier=holding.fund_identifier,
                    fund_family=holding.fund_family,
                    fund_name=holding.fund_name,
                    holding_dollars=_money(holding.holding_dollars),
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
                    holding_dollars=_money(holding.holding_dollars),
                    covered=False,
                    warnings=warnings,
                    gap_reason=reason,
                )
            )
            continue

        illustration = illustrate_from_rows(
            rows,
            holding=holding.holding_dollars,
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
        dollars_covered += holding.holding_dollars
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
                holding_dollars=_money(holding.holding_dollars),
                covered=True,
                publication_stage_used=stage_used,
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
