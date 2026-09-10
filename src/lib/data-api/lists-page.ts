import { aggregateDistributions, type DataDistribution } from "@/data/aggregate-distributions";
import {
  findHydratedFund,
  indexFundsByIdentity,
  mergeFundWithDistributions,
} from "@/data/hydrate-funds";
import { withPeerContext } from "@/data/queries";
import type { FundEstimateView } from "@/data/types";
import { isRemoteDataApi } from "@/lib/data-api/config";
import {
  loadDistributionsForFundPage,
  loadFundIdentityByTicker,
} from "@/lib/data-api/distributions";
import { normalizeTickerSymbol } from "@/lib/data-api/request-ticker";
import {
  emptyListRow,
  listRowFromFund,
  orderListRows,
  type ListRow,
} from "@/lib/lists/rows";

const TICKER_FETCH_CONCURRENCY = 8;

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

async function loadFundIdentity(ticker: string): Promise<FundEstimateView | null> {
  return loadFundIdentityByTicker(ticker);
}

function rowsForTicker(rows: DataDistribution[], ticker: string): DataDistribution[] {
  return rows.filter((row) => {
    const symbol = (row.ticker ?? "").trim().toUpperCase();
    const ident = (row.fund_identifier ?? "").trim().toUpperCase();
    return symbol === ticker || ident === ticker;
  });
}

/**
 * Lists hydrate: GET /funds identity (NAV) + GET /distributions unpaid Upcoming.
 * Unknown tickers stay in order as not-found. Paid-only funds keep NAV and
 * never invent Upcoming from history.
 */
export async function loadListRowsFromDataApi(input: {
  tickers: string[];
  catalog?: FundEstimateView[];
  today?: string;
}): Promise<ListRow[]> {
  const tickers = input.tickers
    .map((ticker) => normalizeTickerSymbol(ticker))
    .filter(Boolean);
  if (!tickers.length) return [];

  const catalogIndex = new Map(
    (input.catalog ?? []).map((fund) => [fund.ticker.trim().toUpperCase(), fund]),
  );

  const [identities, distRows] = await Promise.all([
    isRemoteDataApi()
      ? mapPool(tickers, TICKER_FETCH_CONCURRENCY, loadFundIdentity)
      : Promise.resolve(tickers.map((ticker) => catalogIndex.get(ticker) ?? null)),
    loadDistributionsForFundPage({ tickers, hydrateAll: true }),
  ]);

  const hydrated = distRows.length
    ? withPeerContext(aggregateDistributions(distRows, input.today))
    : [];
  const distIndex = indexFundsByIdentity(hydrated);

  const rows = tickers.map((ticker, index) => {
    const identity = identities[index] ?? catalogIndex.get(ticker) ?? null;
    const fromDists = findHydratedFund(
      identity ?? { ticker, id: `fund:${ticker}` },
      distIndex,
    );
    const fund = identity
      ? mergeFundWithDistributions(identity, fromDists)
      : fromDists
        ? withPeerContext([fromDists])[0]
        : null;
    const snapshotRows = rowsForTicker(distRows, ticker);
    const found = Boolean(identity || fromDists || snapshotRows.length);
    if (!found) return emptyListRow(ticker, "not_found");
    return listRowFromFund({
      ticker,
      fund,
      distributionRows: snapshotRows,
      found: true,
      today: input.today,
    });
  });

  return orderListRows(tickers, rows);
}
