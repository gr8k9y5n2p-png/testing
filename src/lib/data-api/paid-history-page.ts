/**
 * Homepage Paid History: finals/paid from GET /distributions, paged by funds.
 * Walks the year-filtered book server-side so `total` is the filtered fund
 * count — never Data's global row total. Never hydrates the book in the
 * browser. Never pulls Upcoming prelims.
 */

import { aggregateDistributions, type DataDistribution } from "@/data/aggregate-distributions";
import { normalizePublicationStage } from "@/data/distribution-bucket";
import {
  clampPaidHistoryPageSize,
  type FundPageQuery,
  type FundPageResult,
} from "@/data/pagination";
import { pagePaidHistoryFunds } from "@/data/paid-history-book";
import { withPeerContext } from "@/data/queries";
import { isRemoteDataApi } from "@/lib/data-api/config";
import {
  loadDistributionPage,
  type DistributionPageResult,
} from "@/lib/data-api/distributions";

export {
  filterPaidHistoryFunds,
  pagePaidHistoryFunds,
} from "@/data/paid-history-book";

/** Data `/distributions` max `page_size`. User windows stay 1–50 funds. */
export const PAID_HISTORY_DATA_PAGE_SIZE = 200;
/** Safety cap on year-filtered Data pages (200 rows each, final+paid). */
export const PAID_HISTORY_WALK_MAX_PAGES = 64;
const PAID_HISTORY_WALK_BATCH = 8;

function isFinalOrPaidRow(row: DataDistribution): boolean {
  const stage = normalizePublicationStage(row.publication_stage);
  return stage === "final" || stage === "paid";
}

function emptyPaidPage(query: FundPageQuery): FundPageResult {
  const limit = clampPaidHistoryPageSize(query.limit);
  return {
    items: [],
    total: 0,
    limit,
    offset: 0,
    years: [],
  };
}

async function fetchFinalsAndPaids(
  query: FundPageQuery,
  page: number,
): Promise<{ rows: DataDistribution[]; short: boolean }> {
  const shared = {
    q: query.query,
    fundFamily: query.family,
    category: query.category,
    year: query.year,
    page,
    pageSize: PAID_HISTORY_DATA_PAGE_SIZE,
  };
  const [finals, paids]: DistributionPageResult[] = await Promise.all([
    loadDistributionPage({ ...shared, publicationStage: "final" }),
    loadDistributionPage({ ...shared, publicationStage: "paid" }),
  ]);
  const rows = [...finals.items, ...paids.items].filter(isFinalOrPaidRow);
  const short =
    finals.items.length < PAID_HISTORY_DATA_PAGE_SIZE &&
    paids.items.length < PAID_HISTORY_DATA_PAGE_SIZE;
  return { rows, short };
}

/**
 * Year / Family / Category filtered finals+paid. Stops on a short Data page
 * so a thin year is one request — never uses the unfiltered row `total`.
 */
export async function loadPaidHistoryDistributionRows(
  query: FundPageQuery,
): Promise<DataDistribution[]> {
  const first = await fetchFinalsAndPaids(query, 1);
  const rows = [...first.rows];
  if (first.short) return rows;

  for (
    let start = 2;
    start <= PAID_HISTORY_WALK_MAX_PAGES;
    start += PAID_HISTORY_WALK_BATCH
  ) {
    const pages = Array.from(
      {
        length: Math.min(
          PAID_HISTORY_WALK_BATCH,
          PAID_HISTORY_WALK_MAX_PAGES - start + 1,
        ),
      },
      (_, index) => start + index,
    );
    const batch = await Promise.all(
      pages.map((page) => fetchFinalsAndPaids(query, page)),
    );
    for (const part of batch) rows.push(...part.rows);
    if (batch.some((part) => part.short)) break;
  }
  return rows;
}

export async function loadPaidHistoryPageFromDataApi(
  query: FundPageQuery = {},
): Promise<FundPageResult> {
  const empty = emptyPaidPage(query);
  if (!isRemoteDataApi()) return empty;

  try {
    const rows = await loadPaidHistoryDistributionRows(query);
    if (!rows.length) return empty;
    return pagePaidHistoryFunds(
      withPeerContext(aggregateDistributions(rows)),
      query,
    );
  } catch {
    return empty;
  }
}
