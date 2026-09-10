/**
 * Filtered Paid History fund book. `total` is unique funds after year /
 * Family / Category — never a Data `/distributions` row count.
 *
 * Dist $/Share and Ex-div send Data `sort=amount|ex_date` + `order=`
 * so the year-window page is the top of the filtered book. Other
 * columns stay current-page `sortFunds`. Do not walk the book.
 */

import { isUpcomingFund } from "./distribution-bucket.ts";
import {
  clampPageOffset,
  clampPaidHistoryPageSize,
  type FundPageQuery,
  type FundPageResult,
} from "./pagination.ts";
import { paidHistoryViews } from "./queries.ts";
import { collectTaxYearsFromFunds } from "./tax-years.ts";
import type { FundEstimateView } from "./types.ts";
import { sortFunds, type SortDirection, type SortKey } from "../lib/format.ts";

export function paidHistorySort(
  query: FundPageQuery,
): { sort: SortKey; direction: SortDirection } {
  const sort = query.sort ?? "fundName";
  const direction =
    query.direction ??
    (query.sort === "fundName" || !query.sort ? "asc" : "desc");
  return { sort, direction };
}

/** Data GET `/distributions` additive `sort=` values. Omit = current default. */
export type PaidHistoryDataSort = "amount" | "ex_date";

/** Map Search column keys onto Data's additive `sort=` contract. */
export function paidHistoryDataSortKey(
  sort?: SortKey,
): PaidHistoryDataSort | undefined {
  if (sort === "estimatedDistributionAmount") return "amount";
  if (sort === "exDate") return "ex_date";
  return undefined;
}

/**
 * Live Data `sort=` / `order=` on GET `/distributions` (`amount` | `ex_date`).
 * Other Search columns omit these — client `sortFunds` reorders the page.
 */
export function paidHistoryDataOrderParams(query: FundPageQuery): {
  sort?: PaidHistoryDataSort;
  direction?: SortDirection;
} {
  const sort = paidHistoryDataSortKey(query.sort);
  if (!sort) return {};
  const { direction } = paidHistorySort(query);
  return { sort, direction };
}

function fundHasPaidYear(fund: FundEstimateView, year?: number): boolean {
  if (year == null) return !isUpcomingFund(fund);
  return paidHistoryViews([fund], year).length > 0;
}

export function filterPaidHistoryFunds(
  funds: FundEstimateView[],
  query: FundPageQuery,
): FundEstimateView[] {
  const family = query.family?.trim();
  const category = query.category?.trim();
  const hasCategory = funds.some(
    (fund) => fund.category && fund.category !== "—",
  );
  return funds.filter((fund) => {
    if (isUpcomingFund(fund)) return false;
    if (!fundHasPaidYear(fund, query.year)) return false;
    if (family && fund.family !== family) return false;
    if (category && hasCategory && fund.category !== category) return false;
    return true;
  });
}

/** Slice a filtered fund book. Empty page 2 of a one-page year clamps to page 1. */
export function pagePaidHistoryFunds(
  funds: FundEstimateView[],
  query: FundPageQuery = {},
): FundPageResult {
  const limit = clampPaidHistoryPageSize(query.limit);
  const filtered = filterPaidHistoryFunds(funds, query);
  const { sort, direction } = paidHistorySort(query);
  const sorted = sortFunds(filtered, sort, direction);
  const total = sorted.length;
  const offset = clampPageOffset(query.offset, total, limit);
  return {
    items: sorted.slice(offset, offset + limit),
    total,
    limit,
    offset,
    years: collectTaxYearsFromFunds(filtered),
    hasMore: false,
  };
}
