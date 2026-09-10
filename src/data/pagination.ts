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

/** Homepage Paid History window. Users toggle 1–50; Data API max is 200. */
export const PAID_HISTORY_PAGE_SIZE = 50;
export const PAID_HISTORY_PAGE_SIZE_MAX = 50;
export const PAID_HISTORY_PAGE_SIZES = [1, 10, 25, 50] as const;

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
  /** Skip /distributions hydrate — weekly NAV identity only. */
  navOnly?: boolean;
  /** Search Upcoming universe — unpaid announced only. */
  upcoming?: boolean;
  /** Search Paid History year book — finals/paid only from GET /distributions. */
  paidHistory?: boolean;
};

export type FundPageResult = {
  items: FundEstimateView[];
  total: number;
  limit: number;
  offset: number;
  /** Tax years observed on this page / Data payload. Never an invented range. */
  years?: number[];
  /**
   * More funds may exist beyond this window. Set when a Data page was full
   * and the filtered fund count is not yet known — never a global row total.
   */
  hasMore?: boolean;
  /** Honest live / partial / unavailable label for `/api/funds`. */
  sourceLabel?: string;
};

export function clampPageSize(value: number | string | null | undefined): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return FUND_PAGE_SIZE;
  return Math.min(FUND_PAGE_SIZE_MAX, Math.max(1, Math.trunc(parsed)));
}

export function clampPaidHistoryPageSize(
  value: number | string | null | undefined,
): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return PAID_HISTORY_PAGE_SIZE;
  return Math.min(PAID_HISTORY_PAGE_SIZE_MAX, Math.max(1, Math.trunc(parsed)));
}

export function clampOffset(value: number | string | null | undefined): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < 0) return 0;
  return Math.trunc(parsed);
}

export function isSortKey(value: string | null | undefined): value is SortKey {
  return Boolean(value && (FUND_SORT_KEYS as readonly string[]).includes(value));
}

/**
 * Search-table paging. Prefer `limit` / `offset` (`GET /funds`).
 * `/distributions` row pages use `page` / `page_size` — aliases:
 *   limit ≡ page_size
 *   offset ≡ (page - 1) * page_size
 */
export function parseFundPageQuery(
  searchParams: URLSearchParams,
): FundPageQuery {
  const yearValue = searchParams.get("year");
  const sort = searchParams.get("sort");
  const direction = searchParams.get("direction");
  const family =
    searchParams.get("fund_family") ?? searchParams.get("family") ?? undefined;
  const paidHistory = searchParams.get("paid_history") === "1";
  const limit = paidHistory
    ? clampPaidHistoryPageSize(
        searchParams.get("limit") ?? searchParams.get("page_size") ?? undefined,
      )
    : clampPageSize(
        searchParams.get("limit") ?? searchParams.get("page_size") ?? undefined,
      );
  const rawOffset = searchParams.get("offset");
  const rawPage = searchParams.get("page");
  const offset =
    rawOffset != null
      ? clampOffset(rawOffset)
      : rawPage != null
        ? clampOffset((Number(rawPage) - 1) * limit)
        : 0;
  return {
    query: searchParams.get("q") ?? undefined,
    family,
    category: searchParams.get("category") ?? undefined,
    year: yearValue ? Number(yearValue) : undefined,
    sort: isSortKey(sort) ? sort : undefined,
    direction: direction === "desc" || direction === "asc" ? direction : undefined,
    limit,
    offset,
    navOnly: searchParams.get("nav_only") === "1",
    upcoming: searchParams.get("upcoming") === "1",
    paidHistory,
  };
}

/** Map limit/offset onto the existing Data `page` / `page_size` contract. */
export function offsetToPage(offset: number, limit: number): number {
  return Math.floor(offset / limit) + 1;
}

/**
 * Keep Previous/Next on a page that has rows when the book is shorter
 * than the requested offset (thin year, Family/Category collapse).
 */
export function clampPageOffset(
  offset: number | string | null | undefined,
  total: number,
  limit: number,
): number {
  const size = Math.max(1, Math.trunc(limit) || 1);
  const safeTotal = Number.isFinite(total) && total > 0 ? Math.trunc(total) : 0;
  const raw = clampOffset(offset);
  if (safeTotal <= 0) return 0;
  if (raw < safeTotal) return raw;
  return Math.floor((safeTotal - 1) / size) * size;
}

export function paginateViews(
  funds: FundEstimateView[],
  query: FundPageQuery = {},
): FundPageResult {
  const limit = query.paidHistory
    ? clampPaidHistoryPageSize(query.limit)
    : clampPageSize(query.limit);
  const filtered = searchFunds(funds, query);
  const sorted = sortFunds(
    filtered,
    query.sort ?? "fundName",
    query.direction ?? (query.sort === "fundName" || !query.sort ? "asc" : "desc"),
  );
  const offset = query.paidHistory
    ? clampPageOffset(query.offset, filtered.length, limit)
    : clampOffset(query.offset);
  return {
    items: sorted.slice(offset, offset + limit),
    total: filtered.length,
    limit,
    offset,
  };
}

export function fundPageSearchParams(query: FundPageQuery): URLSearchParams {
  const limit = query.paidHistory
    ? clampPaidHistoryPageSize(query.limit)
    : clampPageSize(query.limit);
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
  if (query.navOnly) params.set("nav_only", "1");
  if (query.upcoming) params.set("upcoming", "1");
  if (query.paidHistory) params.set("paid_history", "1");
  return params;
}
