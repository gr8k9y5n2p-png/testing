/**
 * Filtered Paid History fund book. `total` is unique funds after year /
 * Family / Category — never a Data `/distributions` row count.
 *
 * Column sorts reorder this in-memory window. Data `GET /distributions`
 * has no order/sort param — do not walk the year book to globally rank.
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

/**
 * Reserved for Data additive `sort=` / `direction=` on GET `/distributions`.
 * Empty until Data documents the contract — unknown params have 400'd
 * (category). Current-page order stays in `paidHistorySort` / `sortFunds`.
 */
export function paidHistoryDataOrderParams(_query: FundPageQuery): {
  sort?: SortKey;
  direction?: SortDirection;
} {
  return {};
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
