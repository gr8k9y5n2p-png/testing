import { aggregateDistributions, type DataDistribution } from "@/data/aggregate-distributions";
import { withPeerContext } from "@/data/queries";
import type { FundEstimateView } from "@/data/types";
import { looksLikeExactTicker, normalizeTickerSymbol } from "@/lib/data-api/request-ticker";
import { fetchDataApi } from "@/lib/data-api/fetch";

export type { DataDistribution } from "@/data/aggregate-distributions";
export { aggregateDistributions } from "@/data/aggregate-distributions";

const DISTRIBUTION_PAGE_SIZE = 200;
const DISTRIBUTION_MAX_PAGES = 5;
const TICKER_FETCH_CONCURRENCY = 8;

export type DistributionRowQuery = {
  q?: string;
  ticker?: string;
  fundIdentifier?: string;
  fundFamily?: string;
};

function dedupeRows(rows: DataDistribution[]): DataDistribution[] {
  const seen = new Set<string>();
  const out: DataDistribution[] = [];
  for (const row of rows) {
    const key = row.id || [
      row.ticker,
      row.fund_identifier,
      row.estimate_type,
      row.as_of,
      row.ex_date,
      row.amount,
    ].join("|");
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(row);
  }
  return out;
}

export async function loadDistributionRows(
  query: DistributionRowQuery = {},
): Promise<DataDistribution[]> {
  const items: DataDistribution[] = [];
  for (let page = 1; page <= DISTRIBUTION_MAX_PAGES; page += 1) {
    const params = new URLSearchParams();
    params.set("page", String(page));
    params.set("page_size", String(DISTRIBUTION_PAGE_SIZE));
    if (query.q?.trim()) params.set("q", query.q.trim());
    if (query.ticker?.trim()) {
      params.set("ticker", normalizeTickerSymbol(query.ticker));
    }
    if (query.fundIdentifier?.trim()) {
      params.set("fund_identifier", query.fundIdentifier.trim());
    }
    if (query.fundFamily?.trim()) {
      params.set("fund_family", query.fundFamily.trim());
    }
    const response = await fetchDataApi(`/distributions?${params.toString()}`);
    if (!response.ok) break;
    const payload = (await response.json()) as {
      items?: DataDistribution[];
      total?: number;
    };
    const pageItems = Array.isArray(payload.items) ? payload.items : [];
    items.push(...pageItems);
    if (pageItems.length < DISTRIBUTION_PAGE_SIZE) break;
    if (typeof payload.total === "number" && items.length >= payload.total) break;
  }
  return items;
}

async function mapPool<T, R>(
  items: T[],
  concurrency: number,
  fn: (item: T) => Promise<R>,
): Promise<R[]> {
  const results: R[] = [];
  let index = 0;
  async function worker() {
    while (index < items.length) {
      const current = index;
      index += 1;
      results[current] = await fn(items[current]);
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(concurrency, items.length) }, () => worker()),
  );
  return results;
}

/**
 * Distribution rows for Search / Sample Estimates hydration.
 * Prefer `q` / exact `ticker` — never invent amounts.
 */
export async function loadDistributionsForFundPage(input: {
  q?: string;
  family?: string;
  tickers?: string[];
  fundIdentifiers?: string[];
}): Promise<DataDistribution[]> {
  const rows: DataDistribution[] = [];
  const q = input.q?.trim();
  if (q) {
    rows.push(...(await loadDistributionRows({ q, fundFamily: input.family })));
    if (looksLikeExactTicker(q)) {
      rows.push(...(await loadDistributionRows({ ticker: q })));
    }
  }

  const covered = new Set(
    rows
      .map((row) => (row.ticker ?? "").trim().toUpperCase())
      .filter(Boolean),
  );
  const missingTickers = [...new Set(input.tickers ?? [])]
    .map((ticker) => ticker.trim().toUpperCase())
    .filter((ticker) => ticker && ticker !== "—" && !covered.has(ticker));
  // Search / small picker pages only — do not fan out 50 ticker GETs on browse.
  const fetchEachTicker = Boolean(q) || missingTickers.length <= 8;
  if (fetchEachTicker && missingTickers.length) {
    const extra = await mapPool(
      missingTickers,
      TICKER_FETCH_CONCURRENCY,
      (ticker) => loadDistributionRows({ ticker }),
    );
    for (const batch of extra) rows.push(...batch);
  }

  const missingIdents = [...new Set(input.fundIdentifiers ?? [])]
    .map((value) => value.trim())
    .filter((value) => value && value !== "unknown");
  if (fetchEachTicker && missingIdents.length && missingTickers.length === 0) {
    const extra = await mapPool(
      missingIdents,
      TICKER_FETCH_CONCURRENCY,
      (fundIdentifier) => loadDistributionRows({ fundIdentifier }),
    );
    for (const batch of extra) rows.push(...batch);
  }

  return dedupeRows(rows);
}

export async function loadFundsFromDataApi(): Promise<FundEstimateView[] | null> {
  try {
    const items: DataDistribution[] = [];
    for (let page = 1; page <= DISTRIBUTION_MAX_PAGES; page += 1) {
      const response = await fetchDataApi(
        `/distributions?page_size=${DISTRIBUTION_PAGE_SIZE}&page=${page}`,
      );
      if (!response.ok) {
        return items.length ? withPeerContext(aggregateDistributions(items)) : null;
      }
      const payload = (await response.json()) as {
        items?: DataDistribution[];
        total?: number;
      };
      const pageItems = Array.isArray(payload.items) ? payload.items : [];
      items.push(...pageItems);
      if (pageItems.length < DISTRIBUTION_PAGE_SIZE) break;
      if (typeof payload.total === "number" && items.length >= payload.total) break;
    }
    if (!items.length) return null;
    return withPeerContext(aggregateDistributions(items));
  } catch {
    return null;
  }
}
