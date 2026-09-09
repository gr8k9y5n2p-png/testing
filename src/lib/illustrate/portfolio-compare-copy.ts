import { formatPct, formatUsd } from "../format.ts";
import { TAX_DRAG_NA_LABEL } from "./tax-drag-map.ts";

/**
 * Advisor-facing PortfolioCompare copy. Empty upcoming must not look like $0.
 * Do not invent dates or dollars.
 */

export const UPCOMING_UNAVAILABLE_HEADLINE = "Not available / undisclosed";
/** Short cell label so Dist $ / % of NAV stay scannable. Never $0. */
export const UPCOMING_AMOUNT_UNAVAILABLE = "Undisclosed";
export const UPCOMING_UNAVAILABLE_DETAIL =
  "No unpaid announced estimates for these holdings.";
export const UPCOMING_MODULE_HEADING = "Upcoming / announced";
export const UPCOMING_MODULE_DETAIL =
  "sell before record · unpaid announced · all funds · never invent";
/** Scannable Upcoming columns — Dist $, % of NAV, $ impact. */
export const DIST_AMOUNT_COLUMN = "Dist $";
export const PCT_OF_NAV_COLUMN = "% of NAV";
export const DOLLAR_IMPACT_COLUMN = "$ impact";
export const ANNOUNCED_COLUMN = "Announced";
export const RECORD_COLUMN = "Record";
export const EX_COLUMN = "Ex";
export const EST_DISTRIBUTION_LINE_LABEL = "Est. Distribution";
export const ESTIMATED_TAX_LINE_LABEL = "Estimated Tax";
export const PCT_OF_NAV_LINE_LABEL = "% of NAV";

/** $ / share from Dist $ ÷ (holding ÷ NAV). Null when NAV is missing — never invent. */
export function upcomingPerShareAmount(row: {
  available: boolean;
  distributionDollars: number | null;
  holdingDollars: number | null;
  navPerShare: number | null;
}): string | null {
  if (!row.available || row.distributionDollars == null) return null;
  if (
    row.navPerShare == null ||
    !(row.navPerShare > 0) ||
    row.holdingDollars == null ||
    !(row.holdingDollars > 0)
  ) {
    return null;
  }
  const shares = row.holdingDollars / row.navPerShare;
  if (!(shares > 0)) return null;
  return `${formatUsd(row.distributionDollars / shares, 4)} / sh`;
}

/** Dist $ cell. Empty upcoming is undisclosed, never $0. */
export function upcomingDistributionAmount(row: {
  available: boolean;
  distributionDollars: number | null;
}): string {
  if (!row.available || row.distributionDollars == null) {
    return UPCOMING_AMOUNT_UNAVAILABLE;
  }
  return formatUsd(row.distributionDollars, 0);
}

/** % of NAV cell. Missing Dist $ or holding $ stays undisclosed — never invent. */
export function upcomingPctOfNavAmount(row: {
  available: boolean;
  pctOfNav: number | null;
}): string {
  if (!row.available || row.pctOfNav == null) {
    return UPCOMING_AMOUNT_UNAVAILABLE;
  }
  return formatPct(row.pctOfNav);
}

/** Dollar impact to holder (estimated tax). Empty / uncovered is N/A, never $0. */
export function upcomingDollarImpactAmount(row: {
  available: boolean;
  covered: boolean;
  estimatedTax: number | null;
}): string {
  if (!row.available || !row.covered || row.estimatedTax == null) {
    return TAX_DRAG_NA_LABEL;
  }
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
