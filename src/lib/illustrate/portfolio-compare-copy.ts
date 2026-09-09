import { formatPct, formatUsd, formatUsdRange } from "../format.ts";
import type { TaxRates } from "./types.ts";

/**
 * Advisor-facing PortfolioCompare copy. Empty upcoming must not look like $0.
 * Do not invent dates or dollars.
 */

export const EMPTY_BOOK_INVITE = "No holdings yet — use + Add holding to start.";
export const SINGLE_BOOK_DELTA_DETAIL =
  "Add holdings on both sides to compare · not Upcoming";

export const UPCOMING_UNAVAILABLE_HEADLINE = "Not available / undisclosed";
/** Short cell label so Dist $ / % of NAV stay scannable. Never $0. */
export const UPCOMING_AMOUNT_UNAVAILABLE = "Undisclosed";
export const UPCOMING_UNAVAILABLE_DETAIL =
  "No unpaid announced estimates for these holdings.";
export const UPCOMING_MODULE_HEADING = "Upcoming / Announced";
export const UPCOMING_MODULE_DETAIL =
  "sell before record · unpaid announced · all funds · never invent";
/** Locked six-column Upcoming / Announced book. Years on every date. */
export const DIST_AMOUNT_COLUMN = "$ Distribution / share";
export const PCT_OF_NAV_COLUMN = "Distribution % of NAV";
export const DOLLAR_IMPACT_COLUMN = "$ tax impact";
export const ANNOUNCED_COLUMN = "Announced date";
export const RECORD_COLUMN = "Record date";
export const EX_COLUMN = "Ex-date";
/** Soft dash when NAV, rates, or unpaid estimate is missing — never $0. */
export const UPCOMING_SOFT_DASH = "—";
export const EST_DISTRIBUTION_LINE_LABEL = "Est. Distribution";
export const ESTIMATED_TAX_LINE_LABEL = "Estimated Tax";
export const PCT_OF_NAV_LINE_LABEL = "% of NAV";

export type UpcomingPerShareInputs = {
  distributionPerShare?: number | null;
  distributionDollars?: number | null;
  holdingDollars?: number | null;
  navPerShare?: number | null;
};

/** Manager unpaid prelim $/share, or Dist $ ÷ shares when NAV is known. Never invent a price. */
export function resolveUpcomingPerShare(row: UpcomingPerShareInputs): number | null {
  if (row.distributionPerShare != null && Number.isFinite(row.distributionPerShare)) {
    return row.distributionPerShare;
  }
  if (
    row.distributionDollars == null ||
    row.navPerShare == null ||
    !(row.navPerShare > 0) ||
    row.holdingDollars == null ||
    !(row.holdingDollars > 0)
  ) {
    return null;
  }
  const shares = row.holdingDollars / row.navPerShare;
  if (!(shares > 0)) return null;
  return row.distributionDollars / shares;
}

/** % of NAV = est $/share ÷ weekly NAV. Soft-null when either input is missing. */
export function upcomingPctOfNavFromPerShare(
  perShare: number | null | undefined,
  navPerShare: number | null | undefined,
): number | null {
  if (perShare == null || navPerShare == null || !(navPerShare > 0)) return null;
  return (perShare / navPerShare) * 100;
}

/** Holding Dist $ = $/share × (holding ÷ NAV). Soft-null when any input is missing. */
export function upcomingDistDollarsFromPerShare(
  perShare: number | null | undefined,
  holdingDollars: number | null | undefined,
  navPerShare: number | null | undefined,
): number | null {
  if (
    perShare == null ||
    holdingDollars == null ||
    !(holdingDollars > 0) ||
    navPerShare == null ||
    !(navPerShare > 0)
  ) {
    return null;
  }
  return perShare * (holdingDollars / navPerShare);
}

/** Dist $ × user rates. Component mix when known; else total as ordinary (RATE_MAPPING.total). */
export function upcomingHolderTaxDollars(input: {
  distDollars: number | null;
  ordinaryDollars?: number | null;
  ltcgDollars?: number | null;
  stcgDollars?: number | null;
  qdiDollars?: number | null;
  taxRates: TaxRates;
  combine: boolean;
}): number | null {
  if (input.distDollars == null || !Number.isFinite(input.distDollars)) return null;
  const state = input.combine ? input.taxRates.state : 0;
  const parts: Array<[number | null | undefined, number]> = [
    [input.ordinaryDollars, input.taxRates.ordinary_income],
    [input.ltcgDollars, input.taxRates.long_term_capital_gains],
    [input.stcgDollars, input.taxRates.short_term_capital_gains],
    [input.qdiDollars, input.taxRates.qualified_dividend],
  ];
  const hasParts = parts.some(([dollars]) => dollars != null);
  if (hasParts) {
    const taxed = parts.reduce(
      (sum, [dollars, federal]) => sum + (dollars ?? 0) * (federal + state),
      0,
    );
    const accounted = parts.reduce((sum, [dollars]) => sum + (dollars ?? 0), 0);
    const rest = input.distDollars - accounted;
    return rest > 0 ? taxed + rest * (input.taxRates.ordinary_income + state) : taxed;
  }
  return input.distDollars * (input.taxRates.ordinary_income + state);
}

export function resolveUpcomingDistDollars(row: UpcomingPerShareInputs): number | null {
  return (
    upcomingDistDollarsFromPerShare(
      resolveUpcomingPerShare(row),
      row.holdingDollars ?? null,
      row.navPerShare ?? null,
    ) ?? (row.distributionDollars != null && Number.isFinite(row.distributionDollars)
      ? row.distributionDollars
      : null)
  );
}

export function resolveUpcomingTaxImpact(
  row: UpcomingPerShareInputs & {
    ordinaryPerShare?: number | null;
    capitalGainsPerShare?: number | null;
    estimatedTax?: number | null;
  },
  rates?: { taxRates: TaxRates; combine: boolean },
): number | null {
  if (!rates) return row.estimatedTax ?? null;
  const dist = resolveUpcomingDistDollars(row);
  if (dist == null) return null;
  const shares =
    row.holdingDollars != null &&
    row.holdingDollars > 0 &&
    row.navPerShare != null &&
    row.navPerShare > 0
      ? row.holdingDollars / row.navPerShare
      : null;
  return upcomingHolderTaxDollars({
    distDollars: dist,
    ordinaryDollars:
      shares != null && row.ordinaryPerShare != null ? row.ordinaryPerShare * shares : null,
    ltcgDollars:
      shares != null && row.capitalGainsPerShare != null
        ? row.capitalGainsPerShare * shares
        : null,
    taxRates: rates.taxRates,
    combine: rates.combine,
  });
}

/** $ / share cell. Missing unpaid prelim or NAV conversion stays undisclosed. */
export function upcomingPerShareAmount(row: {
  available: boolean;
  distributionPerShare?: number | null;
  distributionDollars: number | null;
  holdingDollars: number | null;
  navPerShare: number | null;
}): string | null {
  if (!row.available) return null;
  const perShare = resolveUpcomingPerShare(row);
  return perShare == null ? null : `${formatUsd(perShare, 4)} / sh`;
}

export function upcomingDistributionPerShareAmount(row: {
  available: boolean;
  distributionPerShare?: number | null;
  distributionDollars: number | null;
  holdingDollars: number | null;
  navPerShare: number | null;
}): string {
  if (!row.available) return UPCOMING_AMOUNT_UNAVAILABLE;
  const formatted = upcomingPerShareAmount(row);
  return formatted ?? UPCOMING_SOFT_DASH;
}

/** Dist $ cell. Empty upcoming is undisclosed, never $0. */
export function upcomingDistributionAmount(row: {
  available: boolean;
  distributionDollars: number | null;
  distributionDollarsMin?: number | null;
  distributionDollarsMax?: number | null;
}): string {
  if (
    !row.available ||
    (row.distributionDollars == null &&
      row.distributionDollarsMin == null &&
      row.distributionDollarsMax == null)
  ) {
    return UPCOMING_AMOUNT_UNAVAILABLE;
  }
  if (
    row.distributionDollarsMin != null &&
    row.distributionDollarsMax != null &&
    row.distributionDollarsMin !== row.distributionDollarsMax
  ) {
    return formatUsdRange(
      row.distributionDollars,
      row.distributionDollarsMin,
      row.distributionDollarsMax,
      0,
    );
  }
  if (row.distributionDollars == null) return UPCOMING_AMOUNT_UNAVAILABLE;
  return formatUsd(row.distributionDollars, 0);
}

/** % of NAV cell. Prefer $/share ÷ weekly NAV; never invent a manager rate. */
export function upcomingPctOfNavAmount(row: {
  available: boolean;
  pctOfNav: number | null;
  distributionPerShare?: number | null;
  distributionDollars?: number | null;
  holdingDollars?: number | null;
  navPerShare?: number | null;
}): string {
  if (!row.available) return UPCOMING_AMOUNT_UNAVAILABLE;
  const computed =
    upcomingPctOfNavFromPerShare(resolveUpcomingPerShare(row), row.navPerShare ?? null) ??
    row.pctOfNav;
  if (computed == null) return UPCOMING_SOFT_DASH;
  return formatPct(computed);
}

/** $ tax impact = Dist $ × user rates when rates are given. Else API tax. */
export function upcomingDollarImpactAmount(
  row: {
    available: boolean;
    covered: boolean;
    estimatedTax: number | null;
    distributionPerShare?: number | null;
    distributionDollars?: number | null;
    holdingDollars?: number | null;
    navPerShare?: number | null;
    ordinaryPerShare?: number | null;
    capitalGainsPerShare?: number | null;
  },
  rates?: { taxRates: TaxRates; combine: boolean },
): string {
  if (!row.available) return UPCOMING_AMOUNT_UNAVAILABLE;
  if (rates) {
    const tax = resolveUpcomingTaxImpact(row, rates);
    if (tax == null) return UPCOMING_SOFT_DASH;
    return Math.abs(tax) < 0.5 ? formatUsd(0, 0) : formatUsd(tax, 0);
  }
  if (!row.covered || row.estimatedTax == null) return UPCOMING_SOFT_DASH;
  return Math.abs(row.estimatedTax) < 0.5
    ? formatUsd(0, 0)
    : formatUsd(row.estimatedTax, 0);
}

/** Advisor-facing Est. Distribution line. Empty upcoming is undisclosed, never $0. */
export function upcomingDistributionLine(row: {
  available: boolean;
  distributionDollars: number | null;
}): string {
  return `${EST_DISTRIBUTION_LINE_LABEL}: ${upcomingDistributionAmount(row)}`;
}

/** Advisor-facing Estimated Tax line. Empty / uncovered is N/A, never $0. */
export function upcomingEstimatedTaxLine(row: {
  available: boolean;
  covered: boolean;
  estimatedTax: number | null;
}): string {
  return `${ESTIMATED_TAX_LINE_LABEL}: ${upcomingDollarImpactAmount(row)}`;
}

/** Advisor-facing % of NAV line. Missing inputs stay undisclosed. */
export function upcomingPctOfNavLine(row: {
  available: boolean;
  pctOfNav: number | null;
}): string {
  return `${PCT_OF_NAV_LINE_LABEL}: ${upcomingPctOfNavAmount(row)}`;
}

export const PAID_HISTORY_HEADING = "Paid history";
export const PAID_HISTORY_DETAIL = "past · not upcoming";
export const PAID_HISTORY_EMPTY = "No paid distribution history for these holdings.";
/** Tax drag cards read compare totals, not the Upcoming table. */
export const TAX_DRAG_CARD_DETAIL = "compare totals · not Upcoming";
export const TAX_IMPACT_DELTA_DETAIL = "proposed − current · not Upcoming";
export const YEAR_TAX_HEADING = "Calendar-year tax";
export const YEAR_TAX_DETAIL =
  "historical tax $ · 2025–2021 · not Upcoming";
export const YEAR_TAX_EMPTY = "No calendar-year tax for these holdings.";
