import type { FundEstimateView, SearchFilters } from "./types.ts";
import {
  sortFunds,
  type SortDirection,
  type SortKey,
} from "../lib/format.ts";
import { searchFunds } from "./queries.ts";

/** Default Search table page size (hybrid #4). */
export const FUND_PAGE_SIZE = 50;
export const FUND_PAGE_SIZE_MAX = 200;

export const FUND_SORT_KEYS = [
  "fundName",
  "family",
  "category",
  "estimatedDistributionPctNav",
  "publishedAt",
  "vsCategoryPctNav",
] as const satisfies readonly SortKey[];

export type FundPageQuery = SearchFilters & {
  limit?: number;
  offset?: number;
  sort?: SortKey;
  direction?: SortDirection;
};

export type FundPageResult = {
  items: FundEstimateView[];
  total: number;
  limit: number;
  offset: number;
};

export function clampPageSize(value: number | string | null | undefined): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return FUND_PAGE_SIZE;
  return Math.min(FUND_PAGE_SIZE_MAX, Math.max(1, Math.trunc(parsed)));
}

export function clampOffset(value: number | string | null | undefined): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) return 0;
  return Math.trunc(parsed);
}

export function isSortKey(value: string | null | undefined): value is SortKey {
  return Boolean(value && (FUND_SORT_KEYS as readonly string[]).includes(value));
}

export function parseFundPageQuery(
  searchParams: URLSearchParams,
): FundPageQuery {
  const yearValue = searchParams.get("year");
  const sort = searchParams.get("sort");
  const direction = searchParams.get("direction");
  return {
    query: searchParams.get("q") ?? undefined,
    family: searchParams.get("family") ?? undefined,
    category: searchParams.get("category") ?? undefined,
    year: yearValue ? Number(yearValue) : undefined,
    sort: isSortKey(sort) ? sort : undefined,
    direction: direction === "desc" || direction === "asc" ? direction : undefined,
    limit: clampPageSize(searchParams.get("limit") ?? undefined),
    offset: clampOffset(searchParams.get("offset") ?? undefined),
  };
}

/** Map limit/offset onto the existing Data `page` / `page_size` contract. */
export function offsetToPage(offset: number, limit: number): number {
  return Math.floor(offset / limit) + 1;
}

export function paginateViews(
  funds: FundEstimateView[],
  query: FundPageQuery = {},
): FundPageResult {
  const limit = clampPageSize(query.limit);
  const offset = clampOffset(query.offset);
  const filtered = searchFunds(funds, query);
  const sorted = sortFunds(
    filtered,
    query.sort ?? "fundName",
    query.direction ?? (query.sort === "fundName" || !query.sort ? "asc" : "desc"),
  );
  return {
    items: sorted.slice(offset, offset + limit),
    total: filtered.length,
    limit,
    offset,
  };
}

export function fundPageSearchParams(query: FundPageQuery): URLSearchParams {
  const limit = clampPageSize(query.limit);
  const offset = clampOffset(query.offset);
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  params.set("page_size", String(limit));
  params.set("page", String(offsetToPage(offset, limit)));
  if (query.query?.trim()) params.set("q", query.query.trim());
  if (query.family) {
    params.set("family", query.family);
    params.set("fund_family", query.family);
  }
  if (query.category) params.set("category", query.category);
  if (query.year) params.set("year", String(query.year));
  if (query.sort) params.set("sort", query.sort);
  if (query.direction) params.set("direction", query.direction);
  return params;
}
