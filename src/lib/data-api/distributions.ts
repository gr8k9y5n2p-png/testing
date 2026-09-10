import { aggregateDistributions, type DataDistribution } from "@/data/aggregate-distributions";
import { chicagoTodayIso, isUpcomingFund } from "@/data/distribution-bucket";
import { mapFundsApiItem, type FundsApiItem } from "@/data/funds-list";
import { mergeFundWithDistributions } from "@/data/hydrate-funds";
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
  category?: string;
  publicationStage?: string;
  year?: number;
  page?: number;
  pageSize?: number;
  limit?: number;
  offset?: number;
  exDateFrom?: string;
  exDateTo?: string;
  asOfFrom?: string;
  signal?: AbortSignal;
};

export type DistributionPageResult = {
  items: DataDistribution[];
  total: number;
  page: number;
  pageSize: number;
  ok: boolean;
  status: number;
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

function distributionSearchParams(query: DistributionRowQuery): URLSearchParams {
  const pageSize = Math.min(
    DISTRIBUTION_PAGE_SIZE,
    Math.max(
      1,
      Math.trunc(query.pageSize ?? query.limit ?? DISTRIBUTION_PAGE_SIZE),
    ),
  );
  const offset =
    query.offset != null
      ? Math.max(0, Math.trunc(query.offset))
      : Math.max(0, (Math.max(1, Math.trunc(query.page ?? 1)) - 1) * pageSize);
  const page = Math.floor(offset / pageSize) + 1;
  const params = new URLSearchParams();
  params.set("page", String(page));
  params.set("page_size", String(pageSize));
  params.set("limit", String(pageSize));
  params.set("offset", String(offset));
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
  if (query.category?.trim()) {
    params.set("category", query.category.trim());
  }
  if (query.publicationStage?.trim()) {
    params.set("publication_stage", query.publicationStage.trim());
  }
  if (query.year && Number.isFinite(query.year)) {
    params.set("year", String(query.year));
    params.set("tax_year", String(query.year));
  }
  if (query.exDateFrom?.trim()) {
    params.set("ex_date_from", query.exDateFrom.trim());
  }
  if (query.exDateTo?.trim()) {
    params.set("ex_date_to", query.exDateTo.trim());
  }
  if (query.asOfFrom?.trim()) {
    params.set("as_of_from", query.asOfFrom.trim());
  }
  return params;
}

/** One GET /distributions page. Never walks the book. */
export async function loadDistributionPage(
  query: DistributionRowQuery = {},
): Promise<DistributionPageResult> {
  const pageSize = Math.min(
    DISTRIBUTION_PAGE_SIZE,
    Math.max(
      1,
      Math.trunc(query.pageSize ?? query.limit ?? DISTRIBUTION_PAGE_SIZE),
    ),
  );
  const offset =
    query.offset != null
      ? Math.max(0, Math.trunc(query.offset))
      : Math.max(0, (Math.max(1, Math.trunc(query.page ?? 1)) - 1) * pageSize);
  const page = Math.floor(offset / pageSize) + 1;
  const params = distributionSearchParams({
    ...query,
    page,
    pageSize,
    limit: pageSize,
    offset,
  });
  const response = await fetchDataApi(`/distributions?${params.toString()}`, {
    signal: query.signal,
  });
  if (!response.ok) {
    return { items: [], total: 0, page, pageSize, ok: false, status: response.status };
  }
  const payload = (await response.json()) as {
    items?: DataDistribution[];
    data?: DataDistribution[];
    total?: number;
    count?: number;
  };
  const items = Array.isArray(payload.items)
    ? payload.items
    : Array.isArray(payload.data)
      ? payload.data
      : [];
  const total =
    typeof payload.total === "number"
      ? payload.total
      : typeof payload.count === "number"
        ? payload.count
        : items.length;
  return { items, total, page, pageSize, ok: true, status: response.status };
}

export async function loadDistributionRows(
  query: DistributionRowQuery = {},
): Promise<DataDistribution[]> {
  const items: DataDistribution[] = [];
  for (let page = 1; page <= DISTRIBUTION_MAX_PAGES; page += 1) {
    const result = await loadDistributionPage({
      ...query,
      page,
      pageSize: DISTRIBUTION_PAGE_SIZE,
    });
    items.push(...result.items);
    if (result.items.length < DISTRIBUTION_PAGE_SIZE) break;
    if (items.length >= result.total) break;
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
      (ticker) => loadDistributionRows({ ticker }),
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
      const params = new URLSearchParams();
      params.set("q", key);
      params.set("limit", "5");
      params.set("offset", "0");
      const response = await fetchDataApi(`/funds?${params.toString()}`);
      if (!response.ok) {
        if (attempt < 2) continue;
        return null;
      }
      const items = fundsApiItemsFromPayload(await response.json());
      const match = items.find(
        (row) => (row.ticker ?? "").trim().toUpperCase() === key,
      );
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

export async function loadUpcomingAnnouncedFromDataApi(
  today = chicagoTodayIso(),
): Promise<FundEstimateView[]> {
  try {
    const rows = dedupeRows([
      ...(await loadDistributionRows({
        publicationStage: "preliminary_estimate",
        exDateFrom: today,
      })),
      ...(await loadDistributionRows({
        publicationStage: "updated_estimate",
        exDateFrom: today,
      })),
    ]);
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
