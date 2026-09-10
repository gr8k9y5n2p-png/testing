/**
 * Homepage Paid History: finals/paid from GET /distributions.
 *
 * Pages the year window with `limit`/`offset` + `ex_date_from`/`ex_date_to`.
 * Never walks successive Data pages. Family is `fund_family`.
 * Category is passed through when present — Data may not filter it yet.
 * Never hydrates the book in the browser. Never pulls Upcoming prelims.
 */

import { normalizePublicationStage } from "@/data/distribution-bucket";
import type { FundPageQuery, FundPageResult } from "@/data/pagination";
import {
  emptyPaidHistoryPage,
  loadPaidHistoryPage,
  paidHistoryExDateWindow,
  PAID_HISTORY_SOURCE_UNAVAILABLE,
  type PaidHistoryDataPage,
  type PaidHistoryFetchWindow,
} from "@/data/paid-history-walk";
import { isRemoteDataApi } from "@/lib/data-api/config";
import {
  loadDistributionPage,
  type DistributionPageResult,
} from "@/lib/data-api/distributions";

export {
  filterPaidHistoryFunds,
  pagePaidHistoryFunds,
} from "@/data/paid-history-book";
export {
  isTrustworthyFilteredRowTotal,
  loadPaidHistoryPage,
  paidHistoryExDateWindow,
  PAID_HISTORY_BUDGET_MS,
  PAID_HISTORY_DATA_PAGE_SIZE,
  PAID_HISTORY_MAX_FETCH_ROUNDS,
  PAID_HISTORY_SOURCE_LIVE,
  PAID_HISTORY_SOURCE_PARTIAL,
  PAID_HISTORY_SOURCE_UNAVAILABLE,
} from "@/data/paid-history-walk";

function isFinalOrPaidRow(row: { publication_stage: string | null }): boolean {
  const stage = normalizePublicationStage(row.publication_stage);
  return stage === "final" || stage === "paid";
}

function combinedFilteredTotal(
  finals: DistributionPageResult,
  paids: DistributionPageResult,
): number | undefined {
  const parts: number[] = [];
  if (finals.ok && Number.isFinite(finals.total) && finals.total >= 0) {
    parts.push(finals.total);
  }
  if (paids.ok && Number.isFinite(paids.total) && paids.total >= 0) {
    parts.push(paids.total);
  }
  if (!parts.length) return undefined;
  return parts.reduce((sum, value) => sum + value, 0);
}

export async function fetchPaidHistoryDataPage(
  query: FundPageQuery,
  window: PaidHistoryFetchWindow,
): Promise<PaidHistoryDataPage> {
  const { exDateFrom, exDateTo } = paidHistoryExDateWindow(query.year);
  const shared = {
    fundFamily: query.family,
    // Pass through only — Data may not honor category yet. Do not invent.
    category: query.category?.trim() || undefined,
    exDateFrom,
    exDateTo,
    limit: window.limit,
    offset: window.offset,
    signal: window.signal,
  };
  const [finals, paids]: DistributionPageResult[] = await Promise.all([
    loadDistributionPage({ ...shared, publicationStage: "final" }),
    loadDistributionPage({ ...shared, publicationStage: "paid" }),
  ]);
  const rows = [...finals.items, ...paids.items].filter(isFinalOrPaidRow);
  const failed = !finals.ok && !paids.ok;
  return {
    rows,
    failed,
    filteredTotal: failed ? undefined : combinedFilteredTotal(finals, paids),
  };
}

export async function loadPaidHistoryPageFromDataApi(
  query: FundPageQuery = {},
): Promise<FundPageResult> {
  const empty = emptyPaidHistoryPage(query, PAID_HISTORY_SOURCE_UNAVAILABLE);
  if (!isRemoteDataApi()) return empty;

  try {
    return await loadPaidHistoryPage(query, {
      fetchPage: fetchPaidHistoryDataPage,
    });
  } catch {
    return empty;
  }
}
