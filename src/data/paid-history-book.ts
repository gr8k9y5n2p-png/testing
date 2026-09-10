/**
 * Filtered Paid History fund book. `total` is unique funds after year /
 * Family / Category — never a Data `/distributions` row count.
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
  const total = filtered.length;
  const offset = clampPageOffset(query.offset, total, limit);
  return {
    items: filtered.slice(offset, offset + limit),
    total,
    limit,
    offset,
    years: collectTaxYearsFromFunds(filtered),
    hasMore: false,
  };
}
