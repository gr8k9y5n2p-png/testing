import { formatUsd } from "../format.ts";
import { TAX_DRAG_NA_LABEL } from "./tax-drag-map.ts";

/**
 * Advisor-facing PortfolioCompare copy. Empty upcoming must not look like $0.
 * Do not invent dates or dollars.
 */

export const UPCOMING_UNAVAILABLE_HEADLINE = "Not available / undisclosed";
export const UPCOMING_UNAVAILABLE_DETAIL =
  "No unpaid announced estimates for these holdings.";
export const UPCOMING_MODULE_HEADING = "Upcoming / announced";
export const UPCOMING_MODULE_DETAIL = "sell before record · unpaid announced";
/** Stacked under each ticker so Est. Distribution / Estimated Tax are not buried in columns. */
export const EST_DISTRIBUTION_LINE_LABEL = "Est. Distribution";
export const ESTIMATED_TAX_LINE_LABEL = "Estimated Tax";

/** Advisor-facing Est. Distribution line under the ticker. Empty upcoming is undisclosed, never $0. */
export function upcomingDistributionLine(row: {
  available: boolean;
  distributionDollars: number | null;
}): string {
  const value =
    !row.available || row.distributionDollars == null
      ? UPCOMING_UNAVAILABLE_HEADLINE
      : formatUsd(row.distributionDollars, 0);
  return `${EST_DISTRIBUTION_LINE_LABEL}: ${value}`;
}

/** Advisor-facing Estimated Tax line under the ticker. Empty / uncovered is N/A, never $0. */
export function upcomingEstimatedTaxLine(row: {
  available: boolean;
  covered: boolean;
  estimatedTax: number | null;
}): string {
  let value = TAX_DRAG_NA_LABEL;
  if (row.available && row.covered && row.estimatedTax != null) {
    value =
      Math.abs(row.estimatedTax) < 0.5
        ? formatUsd(0, 0)
        : formatUsd(row.estimatedTax, 0);
  }
  return `${ESTIMATED_TAX_LINE_LABEL}: ${value}`;
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
