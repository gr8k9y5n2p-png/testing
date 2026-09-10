import { aggregateDistributions } from "@/data/aggregate-distributions";
import { mapFundsApiItem, type FundsApiItem } from "@/data/funds-list";
import {
  findHydratedFund,
  indexFundsByIdentity,
  mergeFundWithDistributions,
} from "@/data/hydrate-funds";
import {
  clampOffset,
  clampPageSize,
  fundPageSearchParams,
  type FundPageQuery,
  type FundPageResult,
} from "@/data/pagination";
import { withPeerContext } from "@/data/queries";
import { collectTaxYearsFromFunds, mergeTaxYears, taxYearsFromPayload } from "@/data/tax-years";
import type { FundEstimateView } from "@/data/types";
import { isRemoteDataApi } from "@/lib/data-api/config";
import {
  loadDistributionsForFundPage,
  loadUpcomingAnnouncedFromDataApi,
} from "@/lib/data-api/distributions";
import { fetchDataApi } from "@/lib/data-api/fetch";

export { mapFundsApiItem, type FundsApiItem } from "@/data/funds-list";

/**
 * Sample Estimates / Search unique-fund pages: Data `GET /funds` for identity.
 *
 *   GET /funds?limit=50&offset=0&q=&fund_family=
 *   → `{ items, limit, offset, total }`
 *
 * Paid history / historical Est. dist hydrate from `GET /distributions`
 * (final / paid YE rows). `has_estimate` is unpaid Upcoming only — never
 * gate paid/final history on that flag, and never invent Upcoming from the
 * catalog flag / `latest_as_of` / `$0` placeholders. 404 / down → empty
 * page (honest), not a dump.
 */
type PagePayload = {
  items?: unknown[];
  data?: unknown[];
  total?: number;
  count?: number;
  limit?: number;
  offset?: number;
};

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

export async function loadFundPageFromDataApi(
  query: FundPageQuery = {},
): Promise<FundPageResult | null> {
  if (!isRemoteDataApi()) return null;
  if (query.upcoming) {
    try {
      const items = await loadUpcomingAnnouncedFromDataApi();
      const limit = clampPageSize(query.limit);
      return {
        items,
        total: items.length,
        limit,
        offset: 0,
        years: collectTaxYearsFromFunds(items),
      };
    } catch {
      // Down is not an empty Upcoming catalog — caller returns 503.
      return null;
    }
  }
  const params = fundPageSearchParams(query);
  try {
    const response = await fetchFundsPage(params);
    if (!response.ok) return null;
    const payload = (await response.json()) as PagePayload;
    const raw = Array.isArray(payload.items)
      ? payload.items
      : Array.isArray(payload.data)
        ? payload.data
        : [];
    const catalog = raw.filter(isFundsApiItem).map((row) => mapFundsApiItem(row));
    const items = query.navOnly
      ? catalog
      : await hydrateFundPage(catalog, query);
    const limit = clampPageSize(payload.limit ?? query.limit);
    const offset = clampOffset(payload.offset ?? query.offset);
    const total =
      typeof payload.total === "number"
        ? payload.total
        : typeof payload.count === "number"
          ? payload.count
          : items.length;
    return {
      items,
      total,
      limit,
      offset,
      years: mergeTaxYears(taxYearsFromPayload(payload), collectTaxYearsFromFunds(items)),
    };
  } catch {
    return null;
  }
}

async function hydrateFundPage(
  items: FundEstimateView[],
  query: FundPageQuery,
): Promise<FundEstimateView[]> {
  if (!items.length) return items;
  try {
    const rows = await loadDistributionsForFundPage({
      q: query.query,
      family: query.family,
      tickers: items.map((item) => item.ticker),
      fundIdentifiers: items
        .map((item) =>
          item.id.startsWith("fund:") ? item.id.slice("fund:".length) : "",
        )
        .filter((value) => value && value !== "unknown"),
    });
    if (!rows.length) return items;
    const hydrated = withPeerContext(aggregateDistributions(rows));
    const index = indexFundsByIdentity(hydrated);
    return items.map((item) =>
      mergeFundWithDistributions(item, findHydratedFund(item, index)),
    );
  } catch {
    return items;
  }
}

async function fetchFundsPage(params: URLSearchParams): Promise<Response> {
  let last: Response | null = null;
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      last = await fetchDataApi(`/funds?${params.toString()}`, {
        fallbackPath: `/funds?${params.toString()}`,
      });
      if (last.ok || last.status < 500 || attempt === 2) return last;
    } catch (error) {
      if (attempt === 2) throw error;
    }
  }
  return last ?? new Response(null, { status: 502 });
}
