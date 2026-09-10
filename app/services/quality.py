"""Post-ingest data-quality flags. Never deletes or invents amounts."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.categories import category_for_row
from app.config import settings
from app.models import AmountUnit, DistributionEstimate
from app.services.nav import get_nav_map, lookup_nav

REVIEW_CATEGORY_OUTLIER = "category_outlier"


def _calendar_year(row: DistributionEstimate) -> int | None:
    for value in (row.ex_date, row.as_of, row.payable_date):
        if value is not None:
            return value.year
    return None


def _midpoint_amount(row: DistributionEstimate) -> Decimal | None:
    if row.amount is not None:
        return Decimal(str(row.amount))
    if row.amount_min is not None and row.amount_max is not None:
        return (Decimal(str(row.amount_min)) + Decimal(str(row.amount_max))) / Decimal("2")
    if row.amount_min is not None:
        return Decimal(str(row.amount_min))
    if row.amount_max is not None:
        return Decimal(str(row.amount_max))
    return None


def _median(values: list[Decimal]) -> Decimal:
    ordered = sorted(values)
    count = len(ordered)
    mid = count // 2
    if count % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / Decimal("2")


def _nav_for_row(session: Session, row: DistributionEstimate) -> Decimal | None:
    weekly = lookup_nav(session, ticker=row.ticker, fund_identifier=row.fund_identifier)
    if weekly is not None and weekly.nav_per_share is not None:
        return Decimal(str(weekly.nav_per_share))
    return None


def _comparable(row: DistributionEstimate, nav: Decimal | None) -> tuple[str, Decimal] | None:
    amount = _midpoint_amount(row)
    if amount is None or amount <= 0:
        return None
    unit = row.amount_unit
    if unit == AmountUnit.percent_of_nav.value:
        return "pct_nav", amount
    if unit != AmountUnit.per_share.value:
        return None
    if nav is not None and nav > 0:
        return "pct_nav", (amount / nav) * Decimal("100")
    return "per_share", amount


def _set_outlier_flag(row: DistributionEstimate, flagged: bool) -> bool:
    """Return True when the category_outlier flag is on after this update."""
    flags = [str(item) for item in (row.data_quality_flags or []) if item]
    has = REVIEW_CATEGORY_OUTLIER in flags
    if flagged and not has:
        flags.append(REVIEW_CATEGORY_OUTLIER)
    if not flagged and has:
        flags = [item for item in flags if item != REVIEW_CATEGORY_OUTLIER]
    row.data_quality_flags = flags or None
    if REVIEW_CATEGORY_OUTLIER in flags:
        row.needs_review = True
        row.review_reason = REVIEW_CATEGORY_OUTLIER
        return True
    if not flags:
        row.needs_review = False
        row.review_reason = None
    elif row.review_reason == REVIEW_CATEGORY_OUTLIER:
        row.review_reason = flags[0]
    return False


def flag_category_outliers(session: Session) -> int:
    """Flag per_share rows far from the category median. Does not delete.

    Default (``CATEGORY_OUTLIER_THRESHOLD_PCT=50``): more than **±50%** vs
    the median of categorized peers in the same calendar year + estimate_type
    (high = median × 1.5, low = median × 0.5). Uses % of NAV when a stored
    weekly NAV is present, else raw $/share. Requires
    ``CATEGORY_OUTLIER_MIN_PEERS`` (default 3). Uncategorized funds are never
    used as peers and are never flagged.
    """
    rows = list(session.scalars(select(DistributionEstimate)).all())
    if not rows:
        return 0

    get_nav_map(session, [row.ticker for row in rows])

    groups: dict[tuple[str, int, str, str], list[tuple[DistributionEstimate, Decimal]]] = defaultdict(
        list
    )
    for row in rows:
        category = category_for_row(row)
        year = _calendar_year(row)
        if not category or year is None:
            continue
        comparable = _comparable(row, _nav_for_row(session, row))
        if comparable is None:
            continue
        metric, value = comparable
        groups[(category, year, row.estimate_type, metric)].append((row, value))

    threshold = Decimal(str(settings.category_outlier_threshold_pct))
    if threshold <= 0:
        threshold = Decimal("50")
    band = threshold / Decimal("100")
    min_peers = max(int(settings.category_outlier_min_peers), 2)

    flagged_ids: set[str] = set()
    for members in groups.values():
        if len(members) < min_peers:
            continue
        median = _median([value for _row, value in members])
        if median <= 0:
            continue
        high = median * (Decimal("1") + band)
        low = median * (Decimal("1") - band)
        for row, value in members:
            if row.amount_unit != AmountUnit.per_share.value:
                continue
            if value > high or value < low:
                flagged_ids.add(row.id)

    flagged_count = 0
    for row in rows:
        if _set_outlier_flag(row, row.id in flagged_ids):
            flagged_count += 1
        session.add(row)
    session.flush()
    return flagged_count
