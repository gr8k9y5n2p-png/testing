/**
 * Homepage Paid History: finals/paid from GET /distributions, paged by funds.
 *
 * Never walks the year book in one request. Year / Family / Category are
 * passed to Data so each page is already scoped. A short Data page (or a
 * trustworthy filtered row `total`) yields the filtered fund count. A full
 * Data page sets hasMore — never the unfiltered global row total (~25515).
 * Never hydrates the book in the browser. Never pulls Upcoming prelims.
 */

import { normalizePublicationStage } from "@/data/distribution-bucket";
import type { FundPageQuery, FundPageResult } from "@/data/pagination";
import {
  emptyPaidHistoryPage,
  loadPaidHistoryPage,
  PAID_HISTORY_DATA_PAGE_SIZE,
  PAID_HISTORY_SOURCE_UNAVAILABLE,
  type PaidHistoryDataPage,
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
  PAID_HISTORY_BUDGET_MS,
  PAID_HISTORY_DATA_PAGE_SIZE,
  PAID_HISTORY_MAX_DATA_PAGES,
  PAID_HISTORY_SOURCE_LIVE,
  PAID_HISTORY_SOURCE_PARTIAL,
  PAID_HISTORY_SOURCE_UNAVAILABLE,
} from "@/data/paid-history-walk";

function isFinalOrPaidRow(row: { publication_stage: string | null }): boolean {
  const stage = normalizePublicationStage(row.publication_stage);
  return stage === "final" || stage === "paid";
}

export async function fetchPaidHistoryDataPage(
  query: FundPageQuery,
  page: number,
  signal?: AbortSignal,
): Promise<PaidHistoryDataPage> {
  const shared = {
    q: query.query,
    fundFamily: query.family,
    category: query.category,
    year: query.year,
    page,
    pageSize: PAID_HISTORY_DATA_PAGE_SIZE,
    signal,
  };
  const [finals, paids]: DistributionPageResult[] = await Promise.all([
    loadDistributionPage({ ...shared, publicationStage: "final" }),
    loadDistributionPage({ ...shared, publicationStage: "paid" }),
  ]);
  const rows = [...finals.items, ...paids.items].filter(isFinalOrPaidRow);
  const failed = !finals.ok && !paids.ok;
  const short =
    !failed &&
    finals.items.length < PAID_HISTORY_DATA_PAGE_SIZE &&
    paids.items.length < PAID_HISTORY_DATA_PAGE_SIZE;
  return {
    rows,
    short,
    failed,
    finalsCount: finals.items.length,
    paidsCount: paids.items.length,
    finalsTotal: finals.ok ? finals.total : undefined,
    paidsTotal: paids.ok ? paids.total : undefined,
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
