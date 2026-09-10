/**
 * Bounded Paid History year-book walk. Testable without `@/` aliases.
 * Stops at a short Data page, the requested fund window, the page cap,
 * or the time budget — never an unbounded loop.
 */

import { aggregateDistributions, type DataDistribution } from "./aggregate-distributions.ts";
import {
  clampPaidHistoryPageSize,
  type FundPageQuery,
  type FundPageResult,
} from "./pagination.ts";
import { filterPaidHistoryFunds, pagePaidHistoryFunds } from "./paid-history-book.ts";
import { withPeerContext } from "./queries.ts";

/** Data `/distributions` max `page_size`. User windows stay 1–50 funds. */
export const PAID_HISTORY_DATA_PAGE_SIZE = 200;
/** Hard cap — never walk a dense year (~25k rows) in one request. */
export const PAID_HISTORY_MAX_DATA_PAGES = 5;
/** Wall-clock budget for the bounded walk (Vercel / browser must not hang). */
export const PAID_HISTORY_BUDGET_MS = 8_000;

export const PAID_HISTORY_SOURCE_LIVE = "Data API /distributions";
export const PAID_HISTORY_SOURCE_PARTIAL = "Data API /distributions (partial)";
export const PAID_HISTORY_SOURCE_UNAVAILABLE =
  "Data API /distributions unavailable";

export type PaidHistoryDataPage = {
  rows: DataDistribution[];
  short: boolean;
  failed: boolean;
  finalsCount: number;
  paidsCount: number;
  finalsTotal?: number;
  paidsTotal?: number;
};

export type PaidHistoryPageFetcher = (
  query: FundPageQuery,
  page: number,
  signal?: AbortSignal,
) => Promise<PaidHistoryDataPage>;

export type PaidHistoryWalkOptions = {
  budgetMs?: number;
  now?: () => number;
  fetchPage: PaidHistoryPageFetcher;
};

/**
 * Data's filtered row `total` is trustworthy only when it agrees with a
 * year-scoped short page. A huge total on a short page is the unfiltered
 * global leak from #121 — never a fund-pager total.
 */
export function isTrustworthyFilteredRowTotal(
  itemCount: number,
  pageSize: number,
  reported: number | undefined,
): reported is number {
  if (reported == null || !Number.isFinite(reported) || reported < 0) {
    return false;
  }
  if (itemCount < pageSize && reported > pageSize) return false;
  return true;
}

function stageComplete(
  itemCount: number,
  pageSize: number,
  reported: number | undefined,
  collected: number,
): boolean {
  if (itemCount < pageSize) return true;
  return (
    isTrustworthyFilteredRowTotal(itemCount, pageSize, reported) &&
    collected >= reported
  );
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

export async function loadPaidHistoryPage(
  query: FundPageQuery = {},
  options: PaidHistoryWalkOptions,
): Promise<FundPageResult> {
  const fetchPage = options.fetchPage;
  const budgetMs = options.budgetMs ?? PAID_HISTORY_BUDGET_MS;
  const now = options.now ?? Date.now;
  const deadline = now() + budgetMs;
  const limit = clampPaidHistoryPageSize(query.limit);
  const requestedOffset = Math.max(0, Math.trunc(query.offset ?? 0));
  const needFunds = requestedOffset + limit;

  const rows: DataDistribution[] = [];
  let collectedFinals = 0;
  let collectedPaids = 0;
  let lastFull = false;
  let sawFailure = false;
  let timedOut = false;
  let knownComplete = false;

  for (let page = 1; page <= PAID_HISTORY_MAX_DATA_PAGES; page += 1) {
    if (now() >= deadline) {
      timedOut = true;
      break;
    }
    const remaining = Math.max(1, deadline - now());
    const signal =
      typeof AbortSignal !== "undefined" && "timeout" in AbortSignal
        ? AbortSignal.timeout(remaining)
        : undefined;
    let part: PaidHistoryDataPage;
    try {
      part = await fetchPage(query, page, signal);
    } catch (error) {
      const name = error instanceof Error ? error.name : "";
      if (name === "TimeoutError" || name === "AbortError") {
        timedOut = true;
        break;
      }
      throw error;
    }

    if (part.failed && !part.rows.length) {
      sawFailure = true;
      if (!rows.length) {
        return emptyPaidHistoryPage(query, PAID_HISTORY_SOURCE_UNAVAILABLE);
      }
      break;
    }

    rows.push(...part.rows);
    collectedFinals += part.finalsCount;
    collectedPaids += part.paidsCount;
    lastFull =
      part.finalsCount >= PAID_HISTORY_DATA_PAGE_SIZE ||
      part.paidsCount >= PAID_HISTORY_DATA_PAGE_SIZE;

    const finalsDone = stageComplete(
      part.finalsCount,
      PAID_HISTORY_DATA_PAGE_SIZE,
      part.finalsTotal,
      collectedFinals,
    );
    const paidsDone = stageComplete(
      part.paidsCount,
      PAID_HISTORY_DATA_PAGE_SIZE,
      part.paidsTotal,
      collectedPaids,
    );
    if (part.short || (finalsDone && paidsDone)) {
      knownComplete = true;
      break;
    }

    const uniqueSoFar = uniquePaidFundsFromRows(rows, query).length;
    if (uniqueSoFar >= needFunds) break;
  }

  if (!rows.length) {
    return emptyPaidHistoryPage(
      query,
      sawFailure || timedOut
        ? PAID_HISTORY_SOURCE_UNAVAILABLE
        : PAID_HISTORY_SOURCE_LIVE,
    );
  }

  const funds = withPeerContext(aggregateDistributions(rows));
  const paged = pagePaidHistoryFunds(funds, query);
  const hasMore = !knownComplete && lastFull;
  return {
    ...paged,
    hasMore,
    sourceLabel: knownComplete
      ? PAID_HISTORY_SOURCE_LIVE
      : PAID_HISTORY_SOURCE_PARTIAL,
  };
}
