/**
 * Parse Website BFF GET /api/funds. A down Data API is not an empty catalog.
 * Keep this module free of `@/` so node:test can load it.
 */

import { looksLikeExactTicker } from "./request-ticker.ts";
import {
  FUNDS_SEARCH_CACHE_TTL_MS,
  createInflightCache,
} from "./inflight-cache.ts";

const fundsSearchCache = createInflightCache<FundsApiClientResult<unknown>>(
  FUNDS_SEARCH_CACHE_TTL_MS,
);

const fundsLookupCache = createInflightCache<FundsApiClientResult<unknown>>(
  FUNDS_SEARCH_CACHE_TTL_MS,
);

export function resetFundsSearchCache(): void {
  fundsSearchCache.clear();
  fundsLookupCache.clear();
}

export type FundsApiClientResult<T = unknown> = {
  items: T[];
  unavailable: boolean;
  notInUniverse?: boolean;
};

export type SearchPickerEmptyState =
  | "searching"
  | "unavailable"
  | "add_to_universe"
  | "no_match";

/**
 * Data 404 / empty exact-ticker /funds is the miss.
 * Exact ticker → Add to universe. Name / partial misses keep “No funds match.”
 */
export function searchPickerEmptyState(input: {
  pending: boolean;
  unavailable: boolean;
  notInUniverse?: boolean;
  exactTicker: boolean;
}): SearchPickerEmptyState {
  if (input.pending) return "searching";
  if (input.unavailable) return "unavailable";
  if (input.notInUniverse || input.exactTicker) return "add_to_universe";
  return "no_match";
}

export function tickerFromFundsItem(item: unknown): string {
  if (!item || typeof item !== "object") return "";
  return String((item as { ticker?: unknown }).ticker ?? "")
    .trim()
    .toUpperCase();
}

export function fundsPageHasExactTicker(
  items: readonly unknown[],
  query: string,
): boolean {
  const key = query.trim().toUpperCase();
  if (!looksLikeExactTicker(key)) return false;
  return items.some((item) => tickerFromFundsItem(item) === key);
}

function sourceLabel(body: unknown): string {
  if (!body || typeof body !== "object") return "";
  const source = (body as { source?: { label?: unknown } }).source;
  return String(source?.label ?? "");
}

export function isFundsApiUnavailable(ok: boolean, body: unknown): boolean {
  if (!ok) return true;
  if (!body || typeof body !== "object") return false;
  const record = body as { error?: unknown };
  if (record.error === "upstream") return true;
  return /unavailable/i.test(sourceLabel(body));
}

export function parseFundsApiResponse<T = unknown>(
  ok: boolean,
  body: unknown,
): FundsApiClientResult<T> {
  const record =
    body && typeof body === "object"
      ? (body as { items?: unknown; data?: unknown })
      : null;
  const items = Array.isArray(record?.items)
    ? record.items
    : Array.isArray(record?.data)
      ? record.data
      : [];
  // A live hit must never be dropped because a stale/soft-empty
  // "unavailable" label arrived with the same payload.
  if (items.length) return { items: items as T[], unavailable: false };
  if (isFundsApiUnavailable(ok, body)) return { items: [], unavailable: true };
  return { items: [], unavailable: false };
}

/** Same-origin Website BFF. Search / Compare / Portfolio share this path. */
export const FUNDS_SEARCH_PATH = "/api/funds";
/** Exact confirm. Data /funds/lookup?ticker= — never /funds?ticker=. */
export const FUNDS_LOOKUP_PATH = "/api/funds/lookup";

/**
 * Autocomplete query for apex GET /api/funds.
 * Identity-only (`nav_only=1`) so AGTHX (has_estimate=false) stays in the
 * book. Paid History must pass `{ navOnly: false }` to hydrate /distributions.
 * Do not call Data `/funds` from the picker — seed lag there is not a miss.
 */
export function fundsSearchParams(
  query: string,
  limit = 10,
  options?: { navOnly?: boolean },
): URLSearchParams {
  const params = new URLSearchParams();
  params.set("q", query.trim());
  params.set("limit", String(limit));
  params.set("offset", "0");
  if (options?.navOnly !== false) {
    params.set("nav_only", "1");
  }
  return params;
}

/**
 * Add to universe only when the shared /api/funds search returned no rows.
 * Family / name hits (Blackrock → BlackRock / iShares) stay selectable
 * even without an exact ticker token.
 */
export function fundsSearchNotInUniverse(
  items: readonly unknown[],
  query: string,
): boolean {
  if (items.length > 0) return false;
  return looksLikeExactTicker(query);
}

export function fundsLookupParams(ticker: string): URLSearchParams {
  const params = new URLSearchParams();
  params.set("ticker", ticker.trim().toUpperCase());
  return params;
}

export async function fetchFundsSearch<T = unknown>(
  query: string,
  limit = 10,
  options?: { navOnly?: boolean },
): Promise<FundsApiClientResult<T>> {
  const q = query.trim();
  if (!q) return { items: [], unavailable: false };
  const navOnly = options?.navOnly !== false;
  const key = `${q.toUpperCase()}\0${limit}\0${navOnly ? "1" : "0"}`;
  return fundsSearchCache.remember(key, () =>
    fetchFundsSearchUncached<T>(q, limit, options),
  ) as Promise<FundsApiClientResult<T>>;
}

async function fetchFundsSearchUncached<T>(
  query: string,
  limit: number,
  options?: { navOnly?: boolean },
): Promise<FundsApiClientResult<T>> {
  const params = fundsSearchParams(query, limit, options);
  try {
    const response = await fetch(`${FUNDS_SEARCH_PATH}?${params.toString()}`, {
      cache: "no-store",
    });
    const body = await response.json().catch(() => null);
    const page = parseFundsApiResponse<T>(response.ok, body);
    if (page.unavailable) return page;
    if (!fundsSearchNotInUniverse(page.items, query)) return page;
    return { items: page.items, unavailable: false, notInUniverse: true };
  } catch {
    return { items: [], unavailable: true };
  }
}

/**
 * Exact ticker confirm. Thin apex → Data GET /funds/lookup?ticker=.
 * 404 is not_in_universe. Never hydrates /distributions.
 */
export async function fetchFundLookup<T = unknown>(
  ticker: string,
): Promise<FundsApiClientResult<T>> {
  const key = ticker.trim().toUpperCase();
  if (!looksLikeExactTicker(key)) return { items: [], unavailable: false };
  return fundsLookupCache.remember(`lookup:${key}`, () =>
    fetchFundLookupUncached<T>(key),
  ) as Promise<FundsApiClientResult<T>>;
}

async function fetchFundLookupUncached<T>(
  ticker: string,
): Promise<FundsApiClientResult<T>> {
  try {
    const response = await fetch(
      `${FUNDS_LOOKUP_PATH}?${fundsLookupParams(ticker).toString()}`,
      { cache: "no-store" },
    );
    const body = await response.json().catch(() => null);
    if (response.status === 404) {
      return { items: [], unavailable: false, notInUniverse: true };
    }
    const page = parseFundsApiResponse<T>(response.ok, body);
    if (page.unavailable) return page;
    if (!page.items.length) {
      return { items: [], unavailable: false, notInUniverse: true };
    }
    return page;
  } catch {
    return { items: [], unavailable: true };
  }
}
