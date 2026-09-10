/**
 * Paid History year window. One Data `limit`/`offset` fetch against
 * `ex_date_from`/`ex_date_to` — never a multi-page Data walk.
 * Pager `total` is Data's filtered `total` when trustworthy, otherwise
 * the unique-fund count on this window.
 */

import { aggregateDistributions, type DataDistribution } from "./aggregate-distributions.ts";
import {
  clampPageOffset,
  clampPaidHistoryPageSize,
  type FundPageQuery,
  type FundPageResult,
} from "./pagination.ts";
import { filterPaidHistoryFunds } from "./paid-history-book.ts";
import { withPeerContext } from "./queries.ts";
import { collectTaxYearsFromFunds } from "./tax-years.ts";

/** User windows stay 1–50; passed through as Data `limit`. */
export const PAID_HISTORY_DATA_PAGE_SIZE = 50;
/** Requested window + optional thin-year clamp refetch. Never a book walk. */
export const PAID_HISTORY_MAX_FETCH_ROUNDS = 2;
/** Wall-clock budget so 502 / timeouts cannot hang Vercel or the browser. */
export const PAID_HISTORY_BUDGET_MS = 8_000;

export const PAID_HISTORY_SOURCE_LIVE = "Data API /distributions";
export const PAID_HISTORY_SOURCE_PARTIAL = "Data API /distributions (partial)";
export const PAID_HISTORY_SOURCE_UNAVAILABLE =
  "Data API /distributions unavailable";

export type PaidHistoryFetchWindow = {
  limit: number;
  offset: number;
  signal?: AbortSignal;
};

export type PaidHistoryDataPage = {
  rows: DataDistribution[];
  failed: boolean;
  filteredTotal?: number;
};

export type PaidHistoryPageFetcher = (
  query: FundPageQuery,
  window: PaidHistoryFetchWindow,
) => Promise<PaidHistoryDataPage>;

export type PaidHistoryWalkOptions = {
  budgetMs?: number;
  now?: () => number;
  fetchPage: PaidHistoryPageFetcher;
};

export function paidHistoryExDateWindow(year?: number): {
  exDateFrom?: string;
  exDateTo?: string;
} {
  if (year == null || !Number.isFinite(year)) return {};
  const y = Math.trunc(year);
  if (y < 1990 || y > 2100) return {};
  return { exDateFrom: `${y}-01-01`, exDateTo: `${y}-12-31` };
}

/**
 * Year-window `total` is trustworthy unless a short page reports a much
 * larger book — that is the unfiltered global leak from #121.
 */
export function isTrustworthyFilteredRowTotal(
  itemCount: number,
  limit: number,
  reported: number | undefined,
  offset = 0,
): reported is number {
  if (reported == null || !Number.isFinite(reported) || reported < 0) {
    return false;
  }
  if (itemCount < limit && reported > offset + itemCount && reported > limit) {
    return false;
  }
  return true;
}

export function emptyPaidHistoryPage(
  query: FundPageQuery,
  sourceLabel = PAID_HISTORY_SOURCE_UNAVAILABLE,
): FundPageResult {
  const limit = clampPaidHistoryPageSize(query.limit);
  return {
    items: [],
    total: 0,
    limit,
    offset: 0,
    years: [],
    hasMore: false,
    sourceLabel,
  };
}

function uniquePaidFundsFromRows(
  rows: DataDistribution[],
  query: FundPageQuery,
) {
  if (!rows.length) return [];
  return filterPaidHistoryFunds(
    withPeerContext(aggregateDistributions(rows)),
    query,
  );
}

function pagerTotal(input: {
  uniqueFunds: number;
  rowCount: number;
  limit: number;
  offset: number;
  reported: number | undefined;
}): number {
  if (
    isTrustworthyFilteredRowTotal(
      input.rowCount,
      input.limit,
      input.reported,
      input.offset,
    )
  ) {
    return input.reported;
  }
  return input.offset + input.uniqueFunds;
}

function isAbortError(error: unknown): boolean {
  const name = error instanceof Error ? error.name : "";
  return name === "TimeoutError" || name === "AbortError";
}

/**
 * One year-window page. At most two Data rounds (requested offset + clamp).
 * 502 / timeout → honest empty, never a hang.
 */
export async function loadPaidHistoryPage(
  query: FundPageQuery = {},
  options: PaidHistoryWalkOptions,
): Promise<FundPageResult> {
  const fetchPage = options.fetchPage;
  const budgetMs = options.budgetMs ?? PAID_HISTORY_BUDGET_MS;
  const now = options.now ?? Date.now;
  const deadline = now() + budgetMs;
  const limit = clampPaidHistoryPageSize(query.limit);
  let offset = Math.max(0, Math.trunc(query.offset ?? 0));
  let rounds = 0;

  const pull = async (off: number): Promise<PaidHistoryDataPage | "timeout"> => {
    if (rounds >= PAID_HISTORY_MAX_FETCH_ROUNDS) {
      return { rows: [], failed: true };
    }
    if (now() >= deadline) return "timeout";
    rounds += 1;
    const remaining = Math.max(1, deadline - now());
    const signal =
      typeof AbortSignal !== "undefined" && "timeout" in AbortSignal
        ? AbortSignal.timeout(remaining)
        : undefined;
    try {
      return await fetchPage(query, { limit, offset: off, signal });
    } catch (error) {
      if (isAbortError(error)) return "timeout";
      throw error;
    }
  };

  let part = await pull(offset);
  if (part === "timeout") {
    return emptyPaidHistoryPage(query, PAID_HISTORY_SOURCE_UNAVAILABLE);
  }
  if (part.failed && !part.rows.length) {
    return emptyPaidHistoryPage(query, PAID_HISTORY_SOURCE_UNAVAILABLE);
  }

  let funds = uniquePaidFundsFromRows(part.rows, query);
  let total = pagerTotal({
    uniqueFunds: funds.length,
    rowCount: part.rows.length,
    limit,
    offset,
    reported: part.filteredTotal,
  });

  const clamped = clampPageOffset(offset, total, limit);
  if (clamped !== offset) {
    const again = await pull(clamped);
    if (again === "timeout") {
      if (!funds.length) {
        return emptyPaidHistoryPage(query, PAID_HISTORY_SOURCE_UNAVAILABLE);
      }
    } else if (again.failed && !again.rows.length) {
      if (!funds.length) {
        return emptyPaidHistoryPage(query, PAID_HISTORY_SOURCE_UNAVAILABLE);
      }
    } else {
      part = again;
      offset = clamped;
      funds = uniquePaidFundsFromRows(part.rows, query);
      total = pagerTotal({
        uniqueFunds: funds.length,
        rowCount: part.rows.length,
        limit,
        offset,
        reported: part.filteredTotal,
      });
    }
  }

  if (!funds.length) {
    return emptyPaidHistoryPage(query, PAID_HISTORY_SOURCE_LIVE);
  }

  const hasMore = offset + limit < total;
  return {
    items: funds.slice(0, limit),
    total,
    limit,
    offset,
    years: collectTaxYearsFromFunds(funds),
    hasMore,
    sourceLabel: hasMore
      ? PAID_HISTORY_SOURCE_PARTIAL
      : PAID_HISTORY_SOURCE_LIVE,
  };
}
