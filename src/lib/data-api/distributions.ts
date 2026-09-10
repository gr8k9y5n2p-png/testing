import { aggregateDistributions, type DataDistribution } from "@/data/aggregate-distributions";
import { chicagoTodayIso, isUpcomingFund } from "@/data/distribution-bucket";
import { mapFundsApiItem, type FundsApiItem } from "@/data/funds-list";
import { mergeFundWithDistributions } from "@/data/hydrate-funds";
import { withPeerContext } from "@/data/queries";
import type { FundEstimateView } from "@/data/types";
import { fundPageSearchParams } from "@/data/pagination";
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
  publicationStage?: string;
  exDateFrom?: string;
  asOfFrom?: string;
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
    if (query.publicationStage?.trim()) {
      params.set("publication_stage", query.publicationStage.trim());
    }
    if (query.exDateFrom?.trim()) {
      params.set("ex_date_from", query.exDateFrom.trim());
    }
    if (query.asOfFrom?.trim()) {
      params.set("as_of_from", query.asOfFrom.trim());
    }
    const response = await fetchDistributionPage(params);
    if (!response.ok) {
      if (response.status >= 500) {
        throw new Error(`distributions ${response.status}`);
      }
      break;
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
  return items;
}

async function fetchDistributionPage(params: URLSearchParams): Promise<Response> {
  let last: Response | null = null;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      last = await fetchDataApi(`/distributions?${params.toString()}`);
      if (last.ok || last.status < 500 || attempt === 2) return last;
    } catch (error) {
      if (attempt === 2) throw error;
    }
  }
  return last ?? new Response(null, { status: 502 });
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
  /** Lists / exact ticker batches — hydrate every ticker, not the browse prefix. */
  hydrateAll?: boolean;
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
  // Search hydrates every missing ticker. Browse hydrates the first 8 so
  // FXAIX/VFIAX YE finals land in Paid history without 50 hobby-plan GETs.
  // Lists passes hydrateAll so a pasted batch is not capped at 8.
  const tickersToFetch = Boolean(q) || input.hydrateAll
    ? missingTickers
    : missingTickers.slice(0, 8);
  if (tickersToFetch.length) {
    const extra = await mapPool(
      tickersToFetch,
      TICKER_FETCH_CONCURRENCY,
      async (ticker) => {
        const byTicker = await loadDistributionRows({ ticker });
        if (byTicker.length) return byTicker;
        // Search uses `q=` when an exact ticker is typed. Render `ticker=`
        // can 502 / return empty while `q=` still finds unpaid FBGRX.
        return loadDistributionRows({ q: ticker });
      },
    );
    for (const batch of extra) rows.push(...batch);
  }

  const missingIdents = [...new Set(input.fundIdentifiers ?? [])]
    .map((value) => value.trim())
    .filter((value) => value && value !== "unknown");
  const identsToFetch = Boolean(q)
    ? missingIdents
    : missingIdents.slice(0, 8);
  if (tickersToFetch.length === 0 && identsToFetch.length) {
    const extra = await mapPool(
      identsToFetch,
      TICKER_FETCH_CONCURRENCY,
      (fundIdentifier) => loadDistributionRows({ fundIdentifier }),
    );
    for (const batch of extra) rows.push(...batch);
  }

  return dedupeRows(rows);
}

function isFundsApiItem(row: unknown): row is FundsApiItem {
  if (!row || typeof row !== "object") return false;
  const record = row as Record<string, unknown>;
  return (
    "fund_name" in record ||
    "fund_identifier" in record ||
    "fundName" in record ||
    "ticker" in record
  );
}

/** Accept `{ items }`, `{ data }`, or a bare array. One bad row does not drop the page. */
function fundsApiItemsFromPayload(payload: unknown): FundsApiItem[] {
  if (Array.isArray(payload)) return payload.filter(isFundsApiItem);
  if (!payload || typeof payload !== "object") return [];
  const record = payload as { items?: unknown; data?: unknown };
  const raw = Array.isArray(record.items)
    ? record.items
    : Array.isArray(record.data)
      ? record.data
      : [];
  return raw.filter(isFundsApiItem);
}

/**
 * GET /funds identity (weekly `nav_per_share`). Retries. Never require
 * `has_estimate` — Lists / Search still need NAV when the catalog flag is stale.
 */
export async function loadFundIdentityByTicker(
  ticker: string,
): Promise<FundEstimateView | null> {
  const key = ticker.trim().toUpperCase();
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const params = fundPageSearchParams({ query: key, limit: 10, offset: 0 });
      const response = await fetchDataApi(`/funds?${params.toString()}`);
      if (!response.ok) {
        if (attempt < 2) continue;
        return null;
      }
      const items = fundsApiItemsFromPayload(await response.json());
      const match = items.find((row) => {
        const ticker = (row.ticker ?? "").trim().toUpperCase();
        const ident = (row.fund_identifier ?? "").trim().toUpperCase();
        return ticker === key || ident === key;
      });
      return match ? mapFundsApiItem(match) : null;
    } catch {
      if (attempt < 2) continue;
      return null;
    }
  }
  return null;
}

async function attachWeeklyNavFromFunds(
  funds: FundEstimateView[],
): Promise<FundEstimateView[]> {
  const tickers = [
    ...new Set(
      funds
        .map((fund) => fund.ticker.trim().toUpperCase())
        .filter((ticker) => ticker && ticker !== "—"),
    ),
  ];
  if (!tickers.length) return funds;
  const identities = await mapPool(
    tickers,
    TICKER_FETCH_CONCURRENCY,
    loadFundIdentityByTicker,
  );
  const byTicker = new Map<string, FundEstimateView>();
  for (const ident of identities) {
    if (!ident) continue;
    const ticker = ident.ticker.trim().toUpperCase();
    if (ticker) byTicker.set(ticker, ident);
  }
  return funds.map((fund) => {
    const ident = byTicker.get(fund.ticker.trim().toUpperCase());
    return ident ? mergeFundWithDistributions(ident, fund) : fund;
  });
}

const NAV_ATTACH_BUDGET_MS = 2500;

async function attachWeeklyNavBestEffort(
  funds: FundEstimateView[],
): Promise<FundEstimateView[]> {
  if (!funds.length) return funds;
  return Promise.race([
    attachWeeklyNavFromFunds(funds),
    new Promise<FundEstimateView[]>((resolve) => {
      setTimeout(() => resolve(funds), NAV_ATTACH_BUDGET_MS);
    }),
  ]).catch(() => funds);
}

/**
 * Same unpaid announced snapshot Search Upcoming uses. Lists falls back
 * here when `ticker=` / `q=` GETs come back empty or 502.
 */
export async function loadUpcomingDistributionRows(
  today = chicagoTodayIso(),
): Promise<DataDistribution[]> {
  return dedupeRows([
    ...(await loadDistributionRows({
      publicationStage: "preliminary_estimate",
      exDateFrom: today,
    })),
    ...(await loadDistributionRows({
      publicationStage: "updated_estimate",
      exDateFrom: today,
    })),
  ]);
}

export function distributionRowsForTickers(
  rows: DataDistribution[],
  tickers: readonly string[],
): DataDistribution[] {
  const want = new Set(
    tickers.map((ticker) => ticker.trim().toUpperCase()).filter(Boolean),
  );
  if (!want.size) return [];
  return rows.filter((row) => {
    const symbol = (row.ticker ?? "").trim().toUpperCase();
    const ident = (row.fund_identifier ?? "").trim().toUpperCase();
    return want.has(symbol) || want.has(ident);
  });
}

export async function loadUpcomingAnnouncedFromDataApi(
  today = chicagoTodayIso(),
): Promise<FundEstimateView[]> {
  try {
    const rows = await loadUpcomingDistributionRows(today);
    if (!rows.length) return [];
    const upcoming = withPeerContext(aggregateDistributions(rows, today)).filter(
      (fund) => isUpcomingFund({ ...fund, hasEstimate: true }, today),
    );
    // Weekly NAV is best-effort. Never drop unpaid announced because identity
    // fan-out is slow or Render dropped GET /funds.
    return attachWeeklyNavBestEffort(upcoming);
  } catch {
    return [];
  }
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
