import { aggregateDistributions, type DataDistribution } from "@/data/aggregate-distributions";
import {
  clampOffset,
  clampPageSize,
  fundPageSearchParams,
  paginateViews,
  type FundPageQuery,
  type FundPageResult,
} from "@/data/pagination";
import { withPeerContext } from "@/data/queries";
import type { FundEstimateView } from "@/data/types";
import { isRemoteDataApi } from "@/lib/data-api/config";
import { fetchDataApi } from "@/lib/data-api/fetch";

/**
 * Data API pagination contract (for the ingest / Data PR):
 *
 *   GET /funds?limit=50&offset=0&q=&family=&category=&year=&sort=&direction=
 *   → `{ items, total }`
 *
 * `items` must already be one row per fund (aggregated). `total` is the
 * filtered fund count. Existing `GET /distributions` uses `page` /
 * `page_size` / `total` on raw distribution rows — this adapter sends both
 * param pairs. Until Data pages aggregated funds, Search paginates the
 * repository views in memory and does not invent seed rows.
 */
const PAGE_PATHS = ["/funds", "/distributions"] as const;

type PagePayload = {
  items?: unknown[];
  data?: unknown[];
  results?: unknown[];
  total?: number;
  count?: number;
};

function payloadItems(payload: PagePayload): unknown[] {
  if (Array.isArray(payload.items)) return payload.items;
  if (Array.isArray(payload.data)) return payload.data;
  if (Array.isArray(payload.results)) return payload.results;
  return [];
}

function looksLikeDistribution(row: unknown): row is DataDistribution {
  if (!row || typeof row !== "object") return false;
  const record = row as Record<string, unknown>;
  return (
    "fund_identifier" in record ||
    "estimate_type" in record ||
    "amount_unit" in record
  );
}

function looksLikeFundView(row: unknown): row is FundEstimateView {
  if (!row || typeof row !== "object") return false;
  const record = row as Record<string, unknown>;
  return typeof record.ticker === "string" && typeof record.fundName === "string";
}

function toViews(items: unknown[]): FundEstimateView[] | null {
  if (!items.length) return [];
  if (items.every(looksLikeFundView)) return items.filter(looksLikeFundView);
  if (items.every(looksLikeDistribution)) {
    return withPeerContext(aggregateDistributions(items as DataDistribution[]));
  }
  return null;
}

async function fetchPagePath(
  path: string,
  query: FundPageQuery,
): Promise<FundPageResult | null> {
  const params = fundPageSearchParams(query);
  // Never fall back to /api/funds from this loader (the route calls us).
  const response = await fetchDataApi(`${path}?${params.toString()}`, {
    fallbackPath: `${path}?${params.toString()}`,
  });
  if (!response.ok) return null;
  const payload = (await response.json()) as PagePayload;
  const rawItems = payloadItems(payload);
  const views = toViews(rawItems);
  if (views == null) return null;

  const limit = clampPageSize(query.limit);
  const offset = clampOffset(query.offset);
  const reportedTotal =
    typeof payload.total === "number"
      ? payload.total
      : typeof payload.count === "number"
        ? payload.count
        : undefined;

  if (rawItems.some(looksLikeDistribution) || views.length > limit) {
    return paginateViews(views, query);
  }

  return {
    items: views,
    total: reportedTotal ?? (offset === 0 && views.length < limit ? views.length : views.length),
    limit,
    offset,
  };
}

export async function loadFundPageFromDataApi(
  query: FundPageQuery = {},
): Promise<FundPageResult | null> {
  if (!isRemoteDataApi()) return null;
  try {
    for (const path of PAGE_PATHS) {
      const page = await fetchPagePath(path, query);
      if (page) return page;
    }
    return null;
  } catch {
    return null;
  }
}
